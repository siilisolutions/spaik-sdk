import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import type { AbstractAgent, AgentSubscriber } from '@ag-ui/client';
import { useAgentSdkClient } from '../client/AgentSdkClientProvider.js';
import { CreateMessageRequest, CreateThreadRequest } from '../api/ThreadsApiClient.js';

function observeAgent(agent: AbstractAgent) {
    let snapshot = { messages: agent.messages, state: agent.state, isGenerating: agent.isRunning, error: undefined as string | undefined };
    const listeners = new Set<() => void>();
    const update = (error = snapshot.error) => {
        snapshot = { messages: agent.messages, state: agent.state, isGenerating: agent.isRunning, error };
        listeners.forEach(listener => listener());
    };
    let subscription: ReturnType<AbstractAgent['subscribe']> | undefined;
    const subscriber: AgentSubscriber = {
        onMessagesChanged: () => update(), onStateChanged: () => update(),
        onRunInitialized: () => { snapshot.error = undefined; update(); }, onRunFinalized: () => update(),
        onRunFailed: ({ error }) => update(error.message), onRunErrorEvent: ({ event }) => update(event.message),
    };
    return {
        getSnapshot: () => snapshot,
        subscribe: (listener: () => void) => {
            listeners.add(listener);
            if (!subscription) { subscription = agent.subscribe(subscriber); update(); }
            return () => { listeners.delete(listener); if (!listeners.size) { subscription?.unsubscribe(); subscription = undefined; } };
        },
    };
}

export function useThread(threadId: string) {
    const client = useAgentSdkClient();
    const agent = threadId ? client.getAgent(threadId) : undefined;
    const observer = useMemo(() => agent ? observeAgent(agent) : undefined, [agent]);
    const empty = useMemo(() => ({ messages: [], state: {}, isGenerating: false, error: undefined }), []);
    const snapshot = useSyncExternalStore(observer?.subscribe ?? (() => () => {}), observer?.getSnapshot ?? (() => empty), observer?.getSnapshot ?? (() => empty));
    const [loading, setLoading] = useState(false);
    const [loadError, setLoadError] = useState<string>();
    useEffect(() => {
        let active = true;
        setLoadError(undefined);
        if (!threadId || !client.threadRepository) return;
        setLoading(true);
        client.getThread(threadId).catch(error => { if (active) setLoadError(String(error)); }).finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, [client, threadId]);
    return { thread: threadId ? { id: threadId, messages: snapshot.messages, message_metadata: client.getMessageMetadata(threadId) } : undefined,
        agent, state: snapshot.state, loading, error: loadError ?? snapshot.error, isGenerating: snapshot.isGenerating };
}

export function useThreadActions() {
    const client = useAgentSdkClient();
    return useMemo(() => ({
        createThread: (request: CreateThreadRequest = {}) => client.createThread(request),
        sendMessage: (id: string, request: CreateMessageRequest) => client.sendMessage(id, request),
        cancelGeneration: (id: string) => client.cancelGeneration(id),
        deleteThread: (id: string) => client.deleteThread(id),
    }), [client]);
}

export function useAgent(agent: AbstractAgent) {
    const observer = useMemo(() => observeAgent(agent), [agent]);
    const snapshot = useSyncExternalStore(observer.subscribe, observer.getSnapshot, observer.getSnapshot);
    const run = useCallback(() => agent.runAgent(), [agent]);
    const cancel = useCallback(() => agent.abortRun(), [agent]);
    return { ...snapshot, run, cancel };
}
