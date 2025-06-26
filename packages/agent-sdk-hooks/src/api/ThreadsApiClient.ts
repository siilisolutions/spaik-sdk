import { BaseApiClient, BaseApiClientConfig } from './BaseApiClient';
import { Id, IdSchema, MessageBlockSchema, Thread, ThreadSchema } from '../stores/messageTypes';
import { z } from 'zod';
import { EventProcessor } from '../event/EventProcessor';

export class ThreadsApiClient extends BaseApiClient {
    constructor(config: BaseApiClientConfig) {
        super(config);
    }

    // Thread endpoints
    async createThread(request: CreateThreadRequest): Promise<Thread> {
        return this.post('/threads', ThreadSchema, request);
    }

    async getThread(threadId: Id): Promise<Thread> {
        return this.get(`/threads/${threadId}`, ThreadSchema);
    }

    async deleteThread(threadId: Id): Promise<DeleteResponse> {
        return this.delete(`/threads/${threadId}`, DeleteResponseSchema);
    }

    async listThreads(filters: ListThreadsFilters = {}): Promise<ListThreadsResponse> {
        try {
            const params = new URLSearchParams();

            if (filters.author_id) params.append('author_id', filters.author_id);
            if (filters.thread_type) params.append('thread_type', filters.thread_type);
            if (filters.title_contains) params.append('title_contains', filters.title_contains);
            if (filters.min_messages) params.append('min_messages', filters.min_messages.toString());
            if (filters.max_messages) params.append('max_messages', filters.max_messages.toString());
            if (filters.hours_ago) params.append('hours_ago', filters.hours_ago.toString());

            const url = `/threads${params.toString() ? `?${params.toString()}` : ''}`;
            return this.get(url, ListThreadsResponseSchema);
        } catch (error) {
            throw new Error(`Failed to list threads: ${error}`);
        }
    }

    async sendMessageWithStream(
        threadId: Id,
        request: CreateMessageRequest,
        signal?: AbortSignal
    ): Promise<void> {
        const url = `/threads/${threadId}/messages/stream`;
        const eventProcessor = new EventProcessor(threadId);
        await this.postStream(url, request, (chunk) => {
            eventProcessor.handleRawEvent(chunk);
        }, signal);
    }

}

export function createThreadsApiClient(config: BaseApiClientConfig): ThreadsApiClient {
    return new ThreadsApiClient(config);
}

// Schemas
export const CreateThreadRequestSchema = z.object({
    metadata: z.record(z.string(), z.any()).optional(),
});


export const DeleteResponseSchema = z.object({
    message: z.string(),
});

export const ListThreadsFiltersSchema = z.object({
    author_id: z.string().optional(),
    thread_type: z.string().optional(),
    title_contains: z.string().optional(),
    min_messages: z.number().optional(),
    max_messages: z.number().optional(),
    hours_ago: z.number().optional(),
});

export const ThreadSummarySchema = z.object({
    thread_id: IdSchema,
    title: z.string(),
    message_count: z.number(),
    last_activity_time: z.number(),
    created_at: z.number(),
    author_id: z.string(),
    type: z.string(),
});

export const ListThreadsResponseSchema = z.object({
    threads: z.array(ThreadSummarySchema),
    total_count: z.number(),
});

// Full message schema for API responses (matches the API documentation)
export const ThreadMessageSchema = z.object({
    id: IdSchema,
    ai: z.boolean(),
    author_id: z.string(),
    author_name: z.string(),
    timestamp: z.number(),
    blocks: z.array(MessageBlockSchema),
});

export const CreateMessageRequestSchema = z.object({
    content: z.string(),
});

// Type exports
export type CreateThreadRequest = z.infer<typeof CreateThreadRequestSchema>;
export type CreateMessageRequest = z.infer<typeof CreateMessageRequestSchema>;
export type DeleteResponse = z.infer<typeof DeleteResponseSchema>;
export type ListThreadsFilters = z.infer<typeof ListThreadsFiltersSchema>;
export type ThreadSummary = z.infer<typeof ThreadSummarySchema>;
export type ListThreadsResponse = z.infer<typeof ListThreadsResponseSchema>;
export type ThreadMessage = z.infer<typeof ThreadMessageSchema>; 