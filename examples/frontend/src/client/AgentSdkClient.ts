import { JobsApiClient, LaunchJobRequest } from "../api/JobsApiClient";
import { ThreadsApiClient, CreateThreadRequest, ListThreadsFilters, ThreadResponse, ThreadMessage, ThreadSummary } from "../api/ThreadsApiClient";
import { SSEClient } from "../api/SSEClient";
import { Id, Thread, Message } from "../stores/messageTypes";
import { addThread, getThread as getThreadFromStore } from "../stores/threadStore";
import { addMessage } from "../stores/messageStore";

export class AgentSdkClient {
    private jobThreadMap = new Map<Id, Id>(); // jobId -> threadId mapping
    private onStreamingComplete?: (threadId: Id) => void;
    private onMessageAdded?: (threadId: Id, messageId: Id) => void;

    constructor(
        private readonly jobsApiClient: JobsApiClient,
        private readonly threadsApiClient: ThreadsApiClient
    ) { }

    // Set callback for when streaming completes
    setStreamingCompleteCallback(callback: (threadId: Id) => void): void {
        this.onStreamingComplete = callback;
    }

    // Set callback for when messages are added
    setMessageAddedCallback(callback: (threadId: Id, messageId: Id) => void): void {
        this.onMessageAdded = callback;
    }

    // Convert API ThreadResponse to store Thread type
    private convertApiThreadToStoreThread(apiThread: ThreadResponse): Thread {
        return {
            id: apiThread.thread_id,
            messages: [] // Will be populated when messages are loaded
        };
    }

    // Convert API ThreadMessage to store Message type
    private convertApiMessageToStoreMessage(apiMessage: ThreadMessage): Message {
        return {
            id: apiMessage.id,
            ai: apiMessage.ai,
            author_id: apiMessage.author_id,
            author_name: apiMessage.author_name,
            timestamp: apiMessage.timestamp,
            blocks: apiMessage.blocks
        };
    }

    // Thread management
    async getThreads(filters?: ListThreadsFilters): Promise<ThreadSummary[]> {
        const response = await this.threadsApiClient.listThreads(filters);
        return response.threads;
    }

    async createThread(request?: CreateThreadRequest): Promise<ThreadResponse> {
        const apiThread = await this.threadsApiClient.createThread(request || {});

        // Update store
        const storeThread = this.convertApiThreadToStoreThread(apiThread);
        addThread(storeThread);

        return apiThread;
    }

    async getThread(threadId: Id): Promise<ThreadResponse> {
        const apiThread = await this.threadsApiClient.getThread(threadId);

        // Update store if not already present
        const existingThread = getThreadFromStore(threadId);
        if (!existingThread) {
            const storeThread = this.convertApiThreadToStoreThread(apiThread);
            addThread(storeThread);
        }

        return apiThread;
    }

    async getThreadMessages(threadId: Id): Promise<ThreadMessage[]> {
        const apiMessages = await this.threadsApiClient.getThreadMessages(threadId);

        // Sort messages by timestamp to ensure proper ordering
        const sortedMessages = apiMessages.sort((a, b) => a.timestamp - b.timestamp);

        // Update stores
        const messageIds: Id[] = [];
        for (const apiMessage of sortedMessages) {
            const storeMessage = this.convertApiMessageToStoreMessage(apiMessage);
            addMessage(storeMessage);
            messageIds.push(storeMessage.id);
        }

        // Update thread with message IDs in correct order
        const existingThread = getThreadFromStore(threadId);
        if (existingThread) {
            const updatedThread: Thread = {
                ...existingThread,
                messages: messageIds
            };
            addThread(updatedThread);
        }

        return sortedMessages;
    }

    // Message sending methods removed - use launchJob instead

    // Job launching (for creating new messages/agents)
    async launchJob(request: LaunchJobRequest): Promise<void> {
        const jobId = await this.jobsApiClient.launchJob(request);
        const eventsClient = new SSEClient({
            baseUrl: 'http://localhost:8000',
            sessionId: jobId,
        });
        eventsClient.connect(jobId);
    }

    // Convenience method to launch job with thread context
    async launchJobForThread(threadId: Id, message: string): Promise<void> {
        const jobId = await this.jobsApiClient.launchJob({
            message,
            thread_id: threadId
        });

        // Track job-thread mapping for event handling
        this.jobThreadMap.set(jobId, threadId);

        const eventsClient = new SSEClient({
            baseUrl: 'http://localhost:8000',
            sessionId: jobId,
        });
        eventsClient.connect(
            jobId,
            this.getThreadIdForJob.bind(this),
            this.onStreamingComplete,
            this.onMessageAdded
        );
    }

    // Method to get thread ID for a job (for event handling)
    getThreadIdForJob(jobId: Id): Id | undefined {
        return this.jobThreadMap.get(jobId);
    }

    // Add optimistic message to stores
    addOptimisticMessage(message: ThreadMessage, threadId: Id): void {
        // Convert ThreadMessage to store Message format
        const storeMessage = this.convertApiMessageToStoreMessage(message);

        // Add to message store
        addMessage(storeMessage);

        // Add to thread
        const existingThread = getThreadFromStore(threadId);
        if (existingThread) {
            const updatedThread: Thread = {
                ...existingThread,
                messages: [...existingThread.messages, message.id]
            };
            addThread(updatedThread);
        }
    }

    // Convenience method removed - create thread and launch job separately
}