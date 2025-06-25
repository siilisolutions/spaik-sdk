import { create } from 'zustand';
import type { AgentState, AgentActions, Message } from './types';

const useAgentStore = create<AgentState & AgentActions>((set, get) => ({
    // State
    messages: [],
    isLoading: false,
    error: null,
    connectionStatus: 'disconnected',

    // Actions
    sendMessage: async (content: string) => {
        set({ isLoading: true, error: null });
        try {
            // TODO: Implement actual API call
            const newMessage: Message = {
                id: Date.now().toString(),
                content,
                role: 'user',
                timestamp: new Date(),
            };
            set({ messages: [...get().messages, newMessage], isLoading: false });
        } catch (error) {
            set({ error: 'Failed to send message', isLoading: false });
        }
    },

    clearMessages: () => set({ messages: [], error: null }),

    connect: async () => {
        set({ connectionStatus: 'connecting' });
        // TODO: Implement actual connection logic
        setTimeout(() => {
            set({ connectionStatus: 'connected' });
        }, 1000);
    },

    disconnect: () => set({ connectionStatus: 'disconnected' }),
}));

export const useAgent = () => {
    const store = useAgentStore();
    return store;
}; 