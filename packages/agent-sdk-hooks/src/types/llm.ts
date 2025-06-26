
// TODO: move these to more appropriate files

// API request/response schemas

// Streaming state types

// Configuration types
export interface LLMClientConfig {
    baseUrl: string;
    timeout?: number;
    sessionId?: string;
    retryAttempts?: number;
    retryDelay?: number;
} 