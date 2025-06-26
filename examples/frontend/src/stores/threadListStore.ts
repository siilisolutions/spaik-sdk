import { create } from 'zustand';
import { ThreadSummary, ListThreadsFilters } from '../api/ThreadsApiClient';
import { AgentSdkClient } from '../client/AgentSdkClient';
import { useAgentSdkClient } from '../client/AgentSdkClientProvider';
import { Id } from './messageTypes';
import { useCallback, useEffect } from 'react';

interface ThreadListStore {
    threadSummaries: ThreadSummary[];
    selectedThreadId?: Id;
    loading: boolean;
    error?: string;
    loadThreads: (client: AgentSdkClient, filters?: ListThreadsFilters) => Promise<void>;
    selectThread: (threadId?: Id) => void;
    setLoading: (loading: boolean) => void;
}

export const useThreadListStore = create<ThreadListStore>()((set) => ({
    threadSummaries: [],
    selectedThreadId: undefined,
    loading: false,

    async loadThreads(client: AgentSdkClient, filters?: ListThreadsFilters) {
        set({ loading: true });
        try {
            const summaries = await client.getThreads(filters);
            set({ threadSummaries: summaries });
        } catch (error) {
            console.error('Failed to load threads:', error);
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
        } finally {
            set({ loading: false });
        }
    },
    async initialize(client: AgentSdkClient) {
        await this.loadThreads(client);
    },

    selectThread(threadId?: Id) {
        set({ selectedThreadId: threadId });
    },

    setLoading(loading: boolean) {
        set({ loading: loading });
    },
}));

let initialized = false;

export function useThreadList() {
    const client = useAgentSdkClient();

    const threadSummaries = useThreadListStore(state => state.threadSummaries);
    const loading = useThreadListStore(state => state.loading);
    const error = useThreadListStore(state => state.error);
    const loadThreads = useThreadListStore(state => state.loadThreads);

    useEffect(() => {
        if (!initialized) {
            initialized = true;
            loadThreads(client);
        }
    }, [initialized]);

    const refresh = useCallback(async () => {
        loadThreads(client);
    }, [loadThreads, client]);

    return {
        threadSummaries,
        error,
        loading,
        refresh,
    };
}

export function useThreadSelection() {
    const selectedThreadId = useThreadListStore(state => state.selectedThreadId);
    const selectThread = useThreadListStore(state => state.selectThread);

    return {
        selectedThreadId,
        selectThread,
    };
}

export function useThreadListActions() {
    const client = useAgentSdkClient();
    const loadThreads = useThreadListStore(state => state.loadThreads);

    return {
        loadThreads: (filters?: ListThreadsFilters) => loadThreads(client, filters),
        refresh: () => loadThreads(client),
    };
} 