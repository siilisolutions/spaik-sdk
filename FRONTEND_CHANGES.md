# Frontend Changes Required for Attachments Support

This document outlines the changes needed in the `packages/agent-sdk-hooks` package to support file attachments.

## Overview

The backend now supports multimodal attachments (images, PDFs, audio, video) on messages. The frontend needs to be updated to:

1. Add attachment types and schemas
2. Update API client for file upload/download
3. Update message request types
4. Update stores to handle attachments

## Type Changes

### New Types (`stores/messageTypes.ts`)

Add the following schema and types:

```typescript
// Attachment schema (align with backend Attachment)
export const AttachmentSchema = z.object({
    file_id: z.string(),
    mime_type: z.string(),
    filename: z.string().optional(),
});

export type Attachment = z.infer<typeof AttachmentSchema>;
```

### Update MessageSchema

```typescript
export const MessageSchema = z.object({
    id: IdSchema,
    ai: z.boolean(),
    author_id: z.string(),
    author_name: z.string(),
    timestamp: z.number(),
    blocks: z.array(MessageBlockSchema),
    attachments: z.array(AttachmentSchema).optional(),  // NEW
});
```

## API Client Changes

### New File API Client (`api/FilesApiClient.ts`)

Create a new API client for file operations:

```typescript
export interface FileUploadResponse {
    file_id: string;
    mime_type: string;
    filename?: string;
    size_bytes: number;
}

export class FilesApiClient extends BaseApiClient {
    async uploadFile(file: File): Promise<FileUploadResponse> {
        const formData = new FormData();
        formData.append('file', file);
        return this.postFormData('/files', FileUploadResponseSchema, formData);
    }

    async getFileUrl(fileId: string): string {
        return `${this.baseUrl}/files/${fileId}`;
    }

    async deleteFile(fileId: string): Promise<{ success: boolean }> {
        return this.delete(`/files/${fileId}`, DeleteResponseSchema);
    }
}
```

### Update CreateMessageRequest (`api/ThreadsApiClient.ts`)

```typescript
export const CreateMessageRequestSchema = z.object({
    content: z.string(),
    attachments: z.array(z.object({
        file_id: z.string(),
        mime_type: z.string(),
        filename: z.string().optional(),
    })).optional(),
});

export type CreateMessageRequest = z.infer<typeof CreateMessageRequestSchema>;
```

## Store Changes

### Update Thread Store (`stores/threadStore.ts`)

The store should already work with the updated message schema since attachments are optional and handled by the existing message flow.

### New File Upload Store (`stores/fileUploadStore.ts`)

Create a dedicated Zustand store to manage file uploads and track their state:

```typescript
import { create } from 'zustand';

export interface PendingUpload {
    id: string;          // Local ID for tracking
    file: File;
    status: 'pending' | 'uploading' | 'completed' | 'error';
    progress: number;    // 0-100
    fileId?: string;     // Set after successful upload
    error?: string;
}

interface FileUploadState {
    uploads: Record<string, PendingUpload>;
    
    // Actions
    addUpload: (file: File) => string;
    updateProgress: (id: string, progress: number) => void;
    completeUpload: (id: string, fileId: string) => void;
    failUpload: (id: string, error: string) => void;
    removeUpload: (id: string) => void;
    clearCompleted: () => void;
    
    // Selectors
    getPendingUploads: () => PendingUpload[];
    getCompletedUploads: () => PendingUpload[];
}

export const useFileUploadStore = create<FileUploadState>((set, get) => ({
    uploads: {},

    addUpload: (file: File) => {
        const id = crypto.randomUUID();
        set(state => ({
            uploads: {
                ...state.uploads,
                [id]: {
                    id,
                    file,
                    status: 'pending',
                    progress: 0,
                },
            },
        }));
        return id;
    },

    updateProgress: (id: string, progress: number) => {
        set(state => ({
            uploads: {
                ...state.uploads,
                [id]: { ...state.uploads[id], status: 'uploading', progress },
            },
        }));
    },

    completeUpload: (id: string, fileId: string) => {
        set(state => ({
            uploads: {
                ...state.uploads,
                [id]: { ...state.uploads[id], status: 'completed', progress: 100, fileId },
            },
        }));
    },

    failUpload: (id: string, error: string) => {
        set(state => ({
            uploads: {
                ...state.uploads,
                [id]: { ...state.uploads[id], status: 'error', error },
            },
        }));
    },

    removeUpload: (id: string) => {
        set(state => {
            const { [id]: _, ...rest } = state.uploads;
            return { uploads: rest };
        });
    },

    clearCompleted: () => {
        set(state => ({
            uploads: Object.fromEntries(
                Object.entries(state.uploads).filter(([_, u]) => u.status !== 'completed')
            ),
        }));
    },

    getPendingUploads: () => Object.values(get().uploads).filter(u => u.status === 'pending' || u.status === 'uploading'),
    getCompletedUploads: () => Object.values(get().uploads).filter(u => u.status === 'completed'),
}));
```

### File Upload Hook (`hooks/useFileUpload.ts`)

Create a hook that combines the store with the API client:

```typescript
import { useFileUploadStore } from '../stores/fileUploadStore';
import { useFilesApiClient } from './useFilesApiClient';

export function useFileUpload() {
    const store = useFileUploadStore();
    const filesClient = useFilesApiClient();

    const uploadFile = async (file: File): Promise<string | null> => {
        const localId = store.addUpload(file);
        
        try {
            store.updateProgress(localId, 10);
            const result = await filesClient.uploadFile(file);
            store.completeUpload(localId, result.file_id);
            return result.file_id;
        } catch (error) {
            store.failUpload(localId, error instanceof Error ? error.message : 'Upload failed');
            return null;
        }
    };

    const uploadFiles = async (files: File[]): Promise<string[]> => {
        const results = await Promise.all(files.map(uploadFile));
        return results.filter((id): id is string => id !== null);
    };

    return {
        uploadFile,
        uploadFiles,
        pendingUploads: store.getPendingUploads(),
        completedUploads: store.getCompletedUploads(),
        clearCompleted: store.clearCompleted,
    };
}
```

### File Cache Store (`stores/fileCacheStore.ts`)

For caching retrieved file URLs/blobs to avoid re-fetching:

```typescript
import { create } from 'zustand';

interface FileCacheState {
    cache: Record<string, string>;  // fileId -> objectURL or base64
    
    getFileUrl: (fileId: string) => string | undefined;
    setFileUrl: (fileId: string, url: string) => void;
    clearCache: () => void;
}

export const useFileCacheStore = create<FileCacheState>((set, get) => ({
    cache: {},

    getFileUrl: (fileId: string) => get().cache[fileId],

    setFileUrl: (fileId: string, url: string) => {
        set(state => ({
            cache: { ...state.cache, [fileId]: url },
        }));
    },

    clearCache: () => {
        // Revoke all object URLs to prevent memory leaks
        Object.values(get().cache).forEach(url => {
            if (url.startsWith('blob:')) {
                URL.revokeObjectURL(url);
            }
        });
        set({ cache: {} });
    },
}));
```

## Usage Example

```tsx
import { useThreadActions } from '@siilisolutions/ai-sdk-react';

function ChatWithAttachments() {
    const { sendMessage } = useThreadActions();
    const filesClient = useFilesClient(); // New hook needed

    const handleSendWithImage = async (threadId: string, text: string, file: File) => {
        // 1. Upload file first
        const uploadResult = await filesClient.uploadFile(file);
        
        // 2. Send message with attachment
        await sendMessage(threadId, {
            content: text,
            attachments: [{
                file_id: uploadResult.file_id,
                mime_type: uploadResult.mime_type,
                filename: uploadResult.filename,
            }],
        });
    };

    return (
        // ... component with file input
    );
}
```

## New Endpoints

The backend now exposes these new endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/files` | Upload a file (multipart/form-data) |
| GET | `/files/{file_id}` | Download a file |
| DELETE | `/files/{file_id}` | Delete a file |

## Displaying Attachments

When rendering messages, check for attachments and display them appropriately:

```tsx
function MessageAttachments({ attachments }: { attachments?: Attachment[] }) {
    if (!attachments?.length) return null;
    
    return (
        <div className="attachments">
            {attachments.map(att => {
                if (att.mime_type.startsWith('image/')) {
                    return <img key={att.file_id} src={`/files/${att.file_id}`} alt={att.filename} />;
                }
                // Handle other types...
            })}
        </div>
    );
}
```

## Supported MIME Types

The backend supports the following attachment types:

**Images:**
- `image/png`
- `image/jpeg`
- `image/gif`
- `image/webp`
- `image/svg+xml`

**Documents:**
- `application/pdf`

**Audio:**
- `audio/mpeg`
- `audio/wav`
- `audio/ogg`
- `audio/webm`

**Video:**
- `video/mp4`
- `video/webm`
- `video/quicktime`

**Text:**
- `text/plain`
- `text/html`
- `text/csv`

