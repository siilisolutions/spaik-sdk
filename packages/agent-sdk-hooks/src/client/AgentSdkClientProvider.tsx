import { createContext, ReactNode, useContext } from "react";
import { AgentSdkClient } from "./AgentSdkClient";

// Create a context for the API client
const AgentContext = createContext<AgentSdkClient | undefined>(undefined);

// Provider component
export function AgentSdkClientProvider({ children, apiClient }: {
  children: ReactNode,
  apiClient: AgentSdkClient
}) {
  return (
    <AgentContext.Provider value={apiClient} >
      {children}
    </AgentContext.Provider>
  );
}

export function useAgentSdkClient() {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error('useAgentSdkClient must be used within an AgentSdkClientProvider');
  }
  return context;
}