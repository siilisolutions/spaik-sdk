import { HttpAgent } from '@ag-ui/client';
import { z } from 'zod';
import { BaseApiClient, BaseApiClientConfig } from './BaseApiClient.js';
import { Attachment, Thread, ThreadSchema } from '../stores/messageTypes.js';

export interface ThreadRepository {
    createThread(request?: CreateThreadRequest): Promise<Thread>;
    getThread(threadId: string): Promise<Thread>;
    deleteThread(threadId: string): Promise<unknown>;
    listThreads(filters?: ListThreadsFilters): Promise<{ threads: ThreadSummary[]; total_count: number }>;
    cancelGeneration?(threadId: string): Promise<unknown>;
}

export class ThreadsApiClient extends BaseApiClient implements ThreadRepository {
    constructor(private readonly config: BaseApiClientConfig) { super(config); }
    createThread(request: CreateThreadRequest = {}): Promise<Thread> {
        return this.post('/threads', ThreadSchema, request);
    }
    getThread(id: string): Promise<Thread> { return this.get(`/threads/${encodeURIComponent(id)}`, ThreadSchema); }
    deleteThread(id: string) { return this.delete(`/threads/${encodeURIComponent(id)}`, z.unknown()); }
    listThreads(filters: ListThreadsFilters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => { if (value !== undefined) params.set(key, String(value)); });
        return this.get(`/threads?${params}`, z.object({ threads: z.array(ThreadSummarySchema), total_count: z.number() }));
    }
    cancelGeneration(id: string) {
        return this.post(`/threads/${encodeURIComponent(id)}/cancel`, z.unknown(), {});
    }
    createAgent(id: string): HttpAgent {
        return new HttpAgent({ threadId: id, url: `${this.config.baseUrl.replace(/\/$/, '')}/threads/${encodeURIComponent(id)}/runs`, headers: this.config.headers });
    }
}
export const createThreadsApiClient = (config: BaseApiClientConfig) => new ThreadsApiClient(config);
export type CreateThreadRequest = { metadata?: Record<string, unknown> };
export type AttachmentRequest = Attachment;
export type CreateMessageRequest = { content: string; attachments?: Attachment[] };
export type ListThreadsFilters = { thread_type?: string; title_contains?: string; min_messages?: number; max_messages?: number; hours_ago?: number };
export const ThreadSummarySchema = z.object({ thread_id: z.string(), title: z.string(), message_count: z.number(), last_activity_time: z.number(), created_at: z.number(), author_id: z.string(), type: z.string() });
export type ThreadSummary = z.infer<typeof ThreadSummarySchema>;
