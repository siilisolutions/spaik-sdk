import { create } from 'zustand';

export type UploadStatus = 'pending' | 'uploading' | 'completed' | 'error';

export interface PendingUpload {
    id: string;
    file: File;
    status: UploadStatus;
    progress: number;
    fileId?: string;
    mimeType?: string;
    error?: string;
}

interface FileUploadState {
    uploads: Record<string, PendingUpload>;
    addUpload: (file: File) => string;
    updateProgress: (id: string, progress: number) => void;
    completeUpload: (id: string, fileId: string, mimeType: string) => void;
    failUpload: (id: string, error: string) => void;
    removeUpload: (id: string) => void;
    clearCompleted: () => void;
    getPendingUploads: () => PendingUpload[];
    getCompletedUploads: () => PendingUpload[];
}

export const useFileUploadStore = create<FileUploadState>((set, get) => ({
    uploads: {},

    addUpload: (file: File) => {
        const id = crypto.randomUUID();
        set((state) => ({
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
        set((state) => {
            const upload = state.uploads[id];
            if (!upload) return state;
            return {
                uploads: {
                    ...state.uploads,
                    [id]: { ...upload, status: 'uploading', progress },
                },
            };
        });
    },

    completeUpload: (id: string, fileId: string, mimeType: string) => {
        set((state) => {
            const upload = state.uploads[id];
            if (!upload) return state;
            return {
                uploads: {
                    ...state.uploads,
                    [id]: { ...upload, status: 'completed', progress: 100, fileId, mimeType },
                },
            };
        });
    },

    failUpload: (id: string, error: string) => {
        set((state) => {
            const upload = state.uploads[id];
            if (!upload) return state;
            return {
                uploads: {
                    ...state.uploads,
                    [id]: { ...upload, status: 'error', error },
                },
            };
        });
    },

    removeUpload: (id: string) => {
        set((state) => {
            const newUploads = { ...state.uploads };
            delete newUploads[id];
            return { uploads: newUploads };
        });
    },

    clearCompleted: () => {
        set((state) => {
            const filtered: Record<string, PendingUpload> = {};
            for (const [key, upload] of Object.entries(state.uploads)) {
                if (upload.status !== 'completed') {
                    filtered[key] = upload;
                }
            }
            return { uploads: filtered };
        });
    },

    getPendingUploads: () => {
        const uploads = get().uploads;
        return Object.values(uploads).filter((u) => u.status === 'pending' || u.status === 'uploading');
    },

    getCompletedUploads: () => {
        const uploads = get().uploads;
        return Object.values(uploads).filter((u) => u.status === 'completed');
    },
}));

