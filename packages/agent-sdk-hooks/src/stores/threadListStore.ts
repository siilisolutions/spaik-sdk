import { useCallback, useEffect, useState } from 'react';
import { ThreadSummary, ListThreadsFilters } from '../api/ThreadsApiClient.js';
import { useAgentContext, useAgentSdkClient } from '../client/AgentSdkClientProvider.js';

export function useThreadList() {
    const client = useAgentSdkClient();
    const [threadSummaries, setThreads] = useState<ThreadSummary[]>([]);
    const [loading, setLoading] = useState(() => Boolean(client.threadRepository));
    const [error, setError] = useState<string>();
    const refresh = useCallback(async () => {
        if (!client.threadRepository) return;
        setLoading(true);
        try { setThreads(await client.getThreads()); setError(undefined); }
        catch (error) { setError(String(error)); }
        finally { setLoading(false); }
    }, [client]);
    useEffect(() => client.subscribeThreadList(setThreads), [client]);
    useEffect(() => {
        if (!client.threadRepository) return;
        let active = true;
        client.getThreads().then(
            threads => { if (active) { setThreads(threads); setError(undefined); setLoading(false); } },
            error => { if (active) { setError(String(error)); setLoading(false); } },
        );
        return () => { active = false; };
    }, [client]);
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
