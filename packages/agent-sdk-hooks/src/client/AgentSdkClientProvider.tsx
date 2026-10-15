import { createContext, ReactNode, useContext, useMemo, useState } from 'react';
import { AgentSdkClient } from './AgentSdkClient.js';

interface ClientContext {
    client: AgentSdkClient;
    selectedThreadId?: string;
    selectThread: (id?: string) => void;
}
const AgentContext = createContext<ClientContext | undefined>(undefined);

export function AgentSdkClientProvider({ children, apiClient }: { children: ReactNode; apiClient: AgentSdkClient }) {
    const [selectedThreadId, setSelectedThreadId] = useState(apiClient.defaultThreadId);
    const context = useMemo(() => ({ client: apiClient, selectedThreadId, selectThread: setSelectedThreadId }), [apiClient, selectedThreadId]);
    return <AgentContext.Provider value={context}>{children}</AgentContext.Provider>;
}
export function useAgentContext() {
    const context = useContext(AgentContext);
    if (!context) throw new Error('Use AgentSdkClientProvider');
    return context;
}
export function useAgentSdkClient() { return useAgentContext().client; }
