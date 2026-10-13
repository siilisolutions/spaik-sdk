import { AbstractAgent, AgentSubscriber } from '@ag-ui/client';
import type { State } from '@ag-ui/core';
import { CreateMessageRequest, CreateThreadRequest, ListThreadsFilters, ThreadRepository, ThreadsApiClient } from '../api/ThreadsApiClient';
import { Thread } from '../stores/messageTypes';

export interface AgentSdkClientConfig {
    agent?: AbstractAgent;
    threadRepository?: ThreadRepository;
    createAgent?: (threadId: string) => AbstractAgent;
}

export class AgentSdkClient {
    readonly threadRepository?: ThreadRepository;
    readonly defaultThreadId?: string;
    private readonly agents = new Map<string, AbstractAgent>();
    private readonly threads = new Map<string, Thread>();
    private readonly loads = new Map<string, Promise<Thread>>();
    private readonly createAgent?: (id: string) => AbstractAgent;

    constructor(config: AgentSdkClientConfig | ThreadsApiClient) {
        if (config instanceof ThreadsApiClient) {
            this.threadRepository = config;
            this.createAgent = id => config.createAgent(id);
        } else {
            this.threadRepository = config.threadRepository;
            this.createAgent = config.createAgent;
            if (config.agent) {
                this.defaultThreadId = config.agent.threadId;
                this.agents.set(config.agent.threadId, config.agent);
            }
        }
    }
    getAgent(id: string): AbstractAgent {
        let agent = this.agents.get(id);
        if (!agent) {
            if (!this.createAgent) throw new Error('Supply an AG-UI agent or createAgent factory');
            agent = this.createAgent(id);
            this.agents.set(id, agent);
        }
        return agent;
    }
    getThreads(filters?: ListThreadsFilters) { return this.requireRepository().listThreads(filters).then(r => r.threads); }
    async createThread(request: CreateThreadRequest = {}) {
        const thread = await this.requireRepository().createThread(request);
        this.threads.set(thread.id, thread);
        this.getAgent(thread.id).setMessages(thread.messages);
        return thread;
    }
    getThread(id: string): Promise<Thread> {
        const cached = this.threads.get(id);
        if (cached) return Promise.resolve(cached);
        const pending = this.loads.get(id);
        if (pending) return pending;
        const load = this.requireRepository().getThread(id).then(thread => {
            this.threads.set(id, thread);
            this.getAgent(id).setMessages(thread.messages);
            return thread;
        }).finally(() => this.loads.delete(id));
        this.loads.set(id, load);
        return load;
    }
    getMessageMetadata(id: string) { return this.threads.get(id)?.message_metadata ?? {}; }
    async deleteThread(id: string) {
        this.getAgent(id).abortRun();
        await this.requireRepository().deleteThread(id);
        this.agents.delete(id);
        this.threads.delete(id);
    }
    async sendMessage(id: string, request: CreateMessageRequest, subscriber?: AgentSubscriber) {
        if (this.threadRepository) await this.getThread(id);
        const agent = this.getAgent(id);
        if (agent.isRunning) throw new Error('This thread is already running');
        const messageId = crypto.randomUUID();
        const thread = this.threads.get(id);
        if (thread) thread.message_metadata[messageId] = { timestamp: Date.now(), attachments: request.attachments ?? [] };
        agent.addMessage({ id: messageId, role: 'user', content: request.content });
        let failure: Error | undefined;
        await agent.runAgent({ forwardedProps: { attachments: { [messageId]: request.attachments ?? [] } } }, {
            ...subscriber,
            onRunErrorEvent: params => { failure = new Error(params.event.message); return subscriber?.onRunErrorEvent?.(params); },
        });
        if (failure) throw failure;
    }
    async cancelGeneration(id: string) {
        // Aborting HTTP also cancels the backend on disconnect. A repository may offer explicit cancellation.
        this.getAgent(id).abortRun();
        await this.threadRepository?.cancelGeneration?.(id);
        if (this.threadRepository) {
            this.threads.delete(id);
            await this.getThread(id);
        }
    }
    private requireRepository(): ThreadRepository {
        if (!this.threadRepository) throw new Error('Thread persistence requires a threadRepository');
        return this.threadRepository;
    }
}

export type AgentState = State;
