import { create } from 'zustand';
import { Id, Thread, Message, MessageBlock } from './messageTypes';
import { AgentSdkClient } from '../client/AgentSdkClient';
import { useAgentSdkClient } from '../client/AgentSdkClientProvider';
import { CreateMessageRequest, CreateThreadRequest } from '../api/ThreadsApiClient';
import { useEffect } from 'react';

interface ThreadStore {
    threads: Map<Id, Thread>;
    loading: Map<Id, boolean>;
    error: Map<Id, string | undefined>;
    generating: Map<Id, boolean>;
    createThread: (client: AgentSdkClient, request: CreateThreadRequest) => Promise<Thread>;
    loadThread: (client: AgentSdkClient, threadId: Id) => Promise<void>;
    sendMessage: (client: AgentSdkClient, threadId: Id, message: CreateMessageRequest) => Promise<void>;
    cancelGeneration: (client: AgentSdkClient, threadId: Id) => Promise<void>;
    setGenerating: (threadId: Id, isGenerating: boolean) => void;
    appendStreamingContent: (threadId: Id, blockId: Id, content: string) => void;
    completeBlockStreaming: (threadId: Id, blockId: Id) => void;
    completeMessageStreaming: (threadId: Id, messageId: Id) => void;
    addMessage: (threadId: Id, message: Message) => void;
    addBlock: (threadId: Id, messageId: Id, block: MessageBlock) => void;
    addToolCallResponse: (threadId: Id, blockId: Id, response: string) => void;
}

const useThreadStore = create<ThreadStore>()((set, get) => {
    function updateThread(thread: Thread) {
        const state = get();
        set({ threads: new Map(state.threads.set(thread.id, { ...thread })) });
        return thread;
    }
    function indexOfMessageContainingBlock(thread: Thread, blockId: Id): number {
        for (let i = 0; i < thread.messages.length; i++) {
            const message = thread.messages[i];
            if (message.blocks.some(b => b.id === blockId)) {
                return i;
            }
        }
        return -1;
    }

    function updateBlock(threadId: Id, blockId: Id, updateFunction: (block: MessageBlock) => MessageBlock) {
        const thread = get().threads.get(threadId);
        if (!thread) {
            console.error(`Thread ${threadId} not found`);
            return;
        }
        const messageIndex = indexOfMessageContainingBlock(thread, blockId);
        if (messageIndex === -1) {
            console.error(`Block ${blockId} not found in any message`);
            return;
        }
        const message = thread.messages[messageIndex];
        const blockIndex = message.blocks.findIndex(b => b.id === blockId);
        if (blockIndex === -1) {
            console.error(`Block ${blockId} not found in message ${message.id}`);
            return;
        }
        const block = message.blocks[blockIndex];

        const newBlock = updateFunction(block);
        message.blocks[blockIndex] = newBlock;
        thread.messages = [
            ...thread.messages.slice(0, messageIndex),
            { ...message },
            ...thread.messages.slice(messageIndex + 1)
        ];
        updateThread(thread);
    }
    function updateMessage(threadId: Id, messageId: Id, updateFunction: (message: Message) => Message) {
        const thread = get().threads.get(threadId);
        if (!thread) {
            console.error(`Thread ${threadId} not found`);
            return;
        }
        const oldMessage = thread.messages.find(m => m.id === messageId);
        if (!oldMessage) {
            console.error(`Message ${messageId} not found in thread ${threadId}`);
            return;
        }
        const newMessage = updateFunction(oldMessage);
        thread.messages = thread.messages.map(m => m.id === messageId ? newMessage : m);
        updateThread(thread);
    }

    return {
        threads: new Map(),
        loading: new Map(),
        error: new Map(),
        generating: new Map(),
        setGenerating(threadId: Id, isGenerating: boolean) {
            set({ generating: new Map(get().generating.set(threadId, isGenerating)) });
        },
        async loadThread(client: AgentSdkClient, threadId: Id) {
            set({
                loading: new Map(get().loading.set(threadId, true)),
                error: new Map(get().error.set(threadId, ''))
            });
            try {
                const thread = await client.getThread(threadId);
                updateThread(thread)
            } catch (error) {
                set({ error: new Map(get().error.set(threadId, error instanceof Error ? error.message : 'Unknown error')) });
            } finally {
                set({ loading: new Map(get().loading.set(threadId, false)) });
            }
        },
        async createThread(client: AgentSdkClient, request: CreateThreadRequest) {
            const newThread = await client.createThread(request);
            return updateThread(newThread);
        },
        async sendMessage(client: AgentSdkClient, threadId: Id, request: CreateMessageRequest) {
            get().setGenerating(threadId, true);
            try {
                await client.sendMessage(threadId, request);
            } finally {
                get().setGenerating(threadId, false);
            }
        },
        async cancelGeneration(client: AgentSdkClient, threadId: Id) {
            try {
                await client.cancelGeneration(threadId);
            } catch (error) {
                console.error('Failed to cancel generation:', error);
            }
            get().setGenerating(threadId, false);
        },
        appendStreamingContent(threadId: Id, blockId: Id, content: string) {
            updateBlock(threadId, blockId, (block) => {
                if (!block.content) {
                    block.content = '';
                }
                return { ...block, content: block.content + content };
            });
        },
        completeBlockStreaming(threadId: Id, blockId: Id) {
            console.log("completing block streaming", blockId);
            updateBlock(threadId, blockId, (block) => ({ ...block, streaming: false }));
        },
        completeMessageStreaming(threadId: Id, messageId: Id) {
            console.log("completing message streaming", messageId);
            updateMessage(threadId, messageId, (message) => {
                const newBlocks = message.blocks.map(b => ({ ...b, streaming: false }));
                return { ...message, blocks: newBlocks, streaming: false };
            });
        },
        addMessage(threadId: Id, message: Message) {
            const thread = get().threads.get(threadId);
            if (!thread) {
                console.error(`Thread ${threadId} not found`);
                return;
            }
            console.log("adding message", message);
            thread.messages.push(message);
            updateThread(thread);
        },
        addBlock(threadId: Id, messageId: Id, block: MessageBlock) {
            console.log("adding block", block);
            updateMessage(threadId, messageId, (message) => ({ ...message, blocks: [...message.blocks, block] }));
        },
        addToolCallResponse(threadId: Id, blockId: Id, response: string) {
            console.log("adding tool call response", response);
            updateBlock(threadId, blockId, (block) => ({ ...block, tool_call_response: response }));
        },
    };
});

export function useThread(threadId: Id) {
    const client = useAgentSdkClient();
    const thread = useThreadStore(state => state.threads.get(threadId));
    const loading = useThreadStore(state => state.loading.get(threadId));
    const error = useThreadStore(state => state.error.get(threadId));
    const isGenerating = useThreadStore(state => state.generating.get(threadId) ?? false);

    const loadThread = useThreadStore(state => state.loadThread);
    useEffect(() => {
        if (!thread) {
            loadThread(client, threadId);
        }
    }, [threadId]);
    return {
        thread,
        loading,
        error,
        isGenerating,
    };
}

export function useThreadActions() {
    const client = useAgentSdkClient();
    const createThread = useThreadStore(state => state.createThread);
    const sendMessage = useThreadStore(state => state.sendMessage);
    const cancelGeneration = useThreadStore(state => state.cancelGeneration);
    return {
        createThread: (request: CreateThreadRequest) => createThread(client, request),
        sendMessage: (threadId: Id, request: CreateMessageRequest) => sendMessage(client, threadId, request),
        cancelGeneration: (threadId: Id) => cancelGeneration(client, threadId),
    }
}

export function getStreamingHandlers() {
    const {
        appendStreamingContent,
        completeBlockStreaming,
        completeMessageStreaming,
        addMessage,
        addBlock,
        addToolCallResponse,
    } = useThreadStore.getState();
    return {
        appendStreamingContent,
        completeBlockStreaming,
        completeMessageStreaming,
        addMessage,
        addBlock,
        addToolCallResponse,
    };
}
