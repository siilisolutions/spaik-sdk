import { useCallback, useEffect, useState } from 'react';
import { ThreadSummary, ListThreadsFilters } from '../api/ThreadsApiClient';
import { useAgentContext, useAgentSdkClient } from '../client/AgentSdkClientProvider';

export function useThreadList() {
    const client = useAgentSdkClient();
    const [threadSummaries, setThreads] = useState<ThreadSummary[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>();
    const refresh = useCallback(async () => {
        if (!client.threadRepository) return;
        setLoading(true);
        try { setThreads(await client.getThreads()); setError(undefined); }
        catch (error) { setError(String(error)); }
        finally { setLoading(false); }
    }, [client]);
    useEffect(() => { void refresh(); }, [refresh]);
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
