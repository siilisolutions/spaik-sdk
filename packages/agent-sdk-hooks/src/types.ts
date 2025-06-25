import { z } from 'zod';

export const MessageSchema = z.object({
    id: z.string(),
    content: z.string(),
    role: z.enum(['user', 'assistant', 'system']),
    timestamp: z.date(),
});

export type Message = z.infer<typeof MessageSchema>;

export interface AgentState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    connectionStatus: 'disconnected' | 'connecting' | 'connected';
}

export interface AgentActions {
    sendMessage: (content: string) => Promise<void>;
    clearMessages: () => void;
    connect: () => Promise<void>;
    disconnect: () => void;
} 