import { useCallback, useEffect, useState } from 'react';
import { ThreadSummary, ListThreadsFilters } from '../api/ThreadsApiClient.js';
import { useAgentContext, useAgentSdkClient } from '../client/AgentSdkClientProvider.js';

export function useThreadList() {
    const client = useAgentSdkClient();
    const [threadSummaries, setThreadSummaries] = useState<ThreadSummary[]>([]);
    const [loadedClient, setLoadedClient] = useState<typeof client>();
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string>();
    const refresh = useCallback(async () => {
        if (!client.threadRepository) return;
        setRefreshing(true);
        try { setThreadSummaries(await client.getThreads()); setError(undefined); }
        catch (error) { setError(String(error)); }
        finally { setRefreshing(false); }
    }, [client]);
    useEffect(() => client.subscribeThreadList(setThreadSummaries), [client]);
    useEffect(() => {
        if (!client.threadRepository) return;
        let active = true;
        client.getThreads().then(
            threads => { if (active) { setThreadSummaries(threads); setError(undefined); setLoadedClient(client); } },
            error => { if (active) { setError(String(error)); setLoadedClient(client); } },
        );
        return () => { active = false; };
    }, [client]);
    const loading = refreshing || (Boolean(client.threadRepository) && loadedClient !== client);
    return { threadSummaries, loading, error, refresh };
}
export function useThreadSelection() {
    const { selectedThreadId, selectThread } = useAgentContext();
    return { selectedThreadId, selectThread };
}
export function useThreadListActions() {
    const client = useAgentSdkClient();
    const loadThreads = useCallback((filters?: ListThreadsFilters) => client.getThreads(filters), [client]);
    return { loadThreads, refresh: loadThreads };
}
