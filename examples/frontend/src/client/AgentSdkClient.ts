import { ThreadsApiClient, CreateThreadRequest, ListThreadsFilters, ThreadSummary, CreateMessageRequest } from "../api/ThreadsApiClient";
import { Id, Thread } from "../stores/messageTypes";

export class AgentSdkClient {
    constructor(
        private readonly threadsApiClient: ThreadsApiClient
    ) { }


    async getThreads(filters?: ListThreadsFilters): Promise<ThreadSummary[]> {
        const response = await this.threadsApiClient.listThreads(filters);
        return response.threads;
    }

    async createThread(request: CreateThreadRequest = {}): Promise<Thread> {
        return this.threadsApiClient.createThread(request);
    }

    async getThread(threadId: Id): Promise<Thread> {
        return this.threadsApiClient.getThread(threadId);
    }

    async sendMessage(threadId: Id, request: CreateMessageRequest): Promise<void> {
        await this.threadsApiClient.sendMessageWithStream(threadId, request);
    }

}