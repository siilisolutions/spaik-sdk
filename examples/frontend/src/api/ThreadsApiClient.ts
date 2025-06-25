import { BaseApiClient, BaseApiClientConfig } from './BaseApiClient';
import { Id, IdSchema, MessageBlockSchema } from '../stores/messageTypes';
import { z } from 'zod';
import { nullToUndefined } from '../utils/nullToUndefined';

export class ThreadsApiClient extends BaseApiClient {
    constructor(config: BaseApiClientConfig) {
        super(config);
    }

    // Thread endpoints
    async createThread(request: CreateThreadRequest): Promise<ThreadResponse> {
        try {
            const validatedRequest = CreateThreadRequestSchema.parse(request);
            const response = await this.post<ThreadResponse>('/threads', validatedRequest);
            const cleanedData = nullToUndefined(response.data);
            const validatedResponse = ThreadResponseSchema.parse(cleanedData);
            return validatedResponse;
        } catch (error) {
            throw new Error(`Failed to create thread: ${error}`);
        }
    }

    async getThread(threadId: Id): Promise<ThreadResponse> {
        try {
            const validatedThreadId = IdSchema.parse(threadId);
            const response = await this.get<ThreadResponse>(`/threads/${validatedThreadId}`);
            const cleanedData = nullToUndefined(response.data);
            const validatedResponse = ThreadResponseSchema.parse(cleanedData);
            return validatedResponse;
        } catch (error) {
            throw new Error(`Failed to get thread: ${error}`);
        }
    }

    async deleteThread(threadId: Id): Promise<DeleteResponse> {
        try {
            const validatedThreadId = IdSchema.parse(threadId);
            const response = await this.delete<DeleteResponse>(`/threads/${validatedThreadId}`);
            const cleanedData = nullToUndefined(response.data);
            const validatedResponse = DeleteResponseSchema.parse(cleanedData);
            return validatedResponse;
        } catch (error) {
            throw new Error(`Failed to delete thread: ${error}`);
        }
    }

    async listThreads(filters?: ListThreadsFilters): Promise<ListThreadsResponse> {
        try {
            const validatedFilters = filters ? ListThreadsFiltersSchema.parse(filters) : {};
            const params = new URLSearchParams();

            if (validatedFilters.author_id) params.append('author_id', validatedFilters.author_id);
            if (validatedFilters.thread_type) params.append('thread_type', validatedFilters.thread_type);
            if (validatedFilters.title_contains) params.append('title_contains', validatedFilters.title_contains);
            if (validatedFilters.min_messages) params.append('min_messages', validatedFilters.min_messages.toString());
            if (validatedFilters.max_messages) params.append('max_messages', validatedFilters.max_messages.toString());
            if (validatedFilters.hours_ago) params.append('hours_ago', validatedFilters.hours_ago.toString());

            const url = `/threads${params.toString() ? `?${params.toString()}` : ''}`;
            const response = await this.get<ListThreadsResponse>(url);
            const cleanedData = nullToUndefined(response.data);
            const validatedResponse = ListThreadsResponseSchema.parse(cleanedData);
            return validatedResponse;
        } catch (error) {
            throw new Error(`Failed to list threads: ${error}`);
        }
    }

    // Message endpoints
    async getThreadMessages(threadId: Id): Promise<ThreadMessage[]> {
        try {
            const validatedThreadId = IdSchema.parse(threadId);
            const response = await this.get<ThreadMessage[]>(`/threads/${validatedThreadId}/messages`);
            const cleanedData = nullToUndefined(response.data);
            const validatedResponse = z.array(ThreadMessageSchema).parse(cleanedData);
            return validatedResponse;
        } catch (error) {
            throw new Error(`Failed to get thread messages: ${error}`);
        }
    }

    async getMessage(threadId: Id, messageId: Id): Promise<ThreadMessage> {
        try {
            const validatedThreadId = IdSchema.parse(threadId);
            const validatedMessageId = IdSchema.parse(messageId);
            const response = await this.get<ThreadMessage>(`/threads/${validatedThreadId}/messages/${validatedMessageId}`);
            const cleanedData = nullToUndefined(response.data);
            const validatedResponse = ThreadMessageSchema.parse(cleanedData);
            return validatedResponse;
        } catch (error) {
            throw new Error(`Failed to get message: ${error}`);
        }
    }

    // Message creation/update/delete methods removed - use launch job instead
}

export function createThreadsApiClient(config: BaseApiClientConfig): ThreadsApiClient {
    return new ThreadsApiClient(config);
}

// Schemas
export const CreateThreadRequestSchema = z.object({
    job_id: z.string().optional(),
});

export const ThreadResponseSchema = z.object({
    thread_id: IdSchema,
    job_id: z.string(),
    version: z.number(),
    last_activity_time: z.number(),
    message_count: z.number(),
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

// Type exports
export type CreateThreadRequest = z.infer<typeof CreateThreadRequestSchema>;
export type ThreadResponse = z.infer<typeof ThreadResponseSchema>;
export type DeleteResponse = z.infer<typeof DeleteResponseSchema>;
export type ListThreadsFilters = z.infer<typeof ListThreadsFiltersSchema>;
export type ThreadSummary = z.infer<typeof ThreadSummarySchema>;
export type ListThreadsResponse = z.infer<typeof ListThreadsResponseSchema>;
export type ThreadMessage = z.infer<typeof ThreadMessageSchema>; 