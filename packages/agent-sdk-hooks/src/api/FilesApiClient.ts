import { z } from 'zod';
import { BaseApiClient, BaseApiClientConfig } from './BaseApiClient';

export const FileMetadataSchema = z.object({
    file_id: z.string(),
    mime_type: z.string(),
    filename: z.string().optional(),
    size: z.number().optional(),
    uploaded_at: z.number().optional(),
    owner_id: z.string().optional(),
});

export const DeleteFileResponseSchema = z.object({
    success: z.boolean(),
});

export type FileMetadata = z.infer<typeof FileMetadataSchema>;
export type DeleteFileResponse = z.infer<typeof DeleteFileResponseSchema>;

export class FilesApiClient extends BaseApiClient {
    constructor(config: BaseApiClientConfig) {
        super(config);
    }

    async uploadFile(file: File): Promise<FileMetadata> {
        const formData = new FormData();
        formData.append('file', file);
        return this.postFormData('/files', FileMetadataSchema, formData);
    }

    async getFileBlob(fileId: string): Promise<Blob> {
        return this.getBlob(`/files/${fileId}`);
    }

    getFileUrl(fileId: string): string {
        return `${this.axiosInstance.defaults.baseURL}/files/${fileId}`;
    }

    async deleteFile(fileId: string): Promise<DeleteFileResponse> {
        return this.delete(`/files/${fileId}`, DeleteFileResponseSchema);
    }
}

export function createFilesApiClient(config: BaseApiClientConfig): FilesApiClient {
    return new FilesApiClient(config);
}

