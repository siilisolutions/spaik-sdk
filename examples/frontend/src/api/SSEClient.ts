import { Id } from '../stores/messageTypes';
import { EventReaderClient } from './EventReaderClient';

export interface SSEClientConfig {
    baseUrl: string;
    sessionId?: string;
    reconnectAttempts?: number;
    reconnectDelay?: number;
}

export class SSEClient extends EventReaderClient {
    private eventSource?: EventSource;
    private config: Required<SSEClientConfig>;
    private reconnectCount = 0;
    private reconnectTimeout?: number;

    constructor(config: SSEClientConfig) {
        super();
        this.config = {
            sessionId: 'default',
            reconnectAttempts: 3,
            reconnectDelay: 1000,
            ...config,
        };
    }

    connect(
        jobId: Id,
        getThreadIdForJob?: (jobId: Id) => Id | undefined,
        onStreamingComplete?: (threadId: Id) => void,
        onMessageAdded?: (threadId: Id, messageId: Id) => void
    ): void {
        this.disconnect();
        this.reconnectCount = 0;

        // Set job context if provided
        if (getThreadIdForJob) {
            this.setJobContext(jobId, getThreadIdForJob, onStreamingComplete, onMessageAdded);
        }

        this.createConnection(jobId);
    }

    private createConnection(jobId: Id): void {
        const url = this.buildStreamUrl(jobId);

        try {
            this.eventSource = new EventSource(url);
            this.setupEventListeners(jobId);
        } catch (error) {
            console.error('Failed to create EventSource:', error);
        }
    }

    private buildStreamUrl(jobId: Id): string {
        const url = new URL(`/jobs/${jobId}/stream`, this.config.baseUrl);
        url.searchParams.set('session_id', this.config.sessionId);
        return url.toString();
    }

    private setupEventListeners(jobId: Id): void {
        if (!this.eventSource) return;

        this.eventSource.onopen = () => {
            console.log('🔗 SSE Connection opened');
            this.reconnectCount = 0;
        };

        // Register listeners for all custom event types

        for (const type of this.getEventTypes()) {
            this.eventSource.addEventListener(type, (event) => {
                this.handleRawEvent(event as MessageEvent);
            });
        }

        // Optionally, still handle generic messages (if server sends untyped events)
        this.eventSource.onmessage = (event) => {
            this.handleRawEvent(event);
        };

        this.eventSource.onerror = (error) => {
            console.log('⚠️ SSE Error event:', error, 'ReadyState:', this.eventSource?.readyState);

            // Only handle as error if connection is actually broken
            // ReadyState 2 = CLOSED, which is expected when stream ends normally
            if (this.eventSource?.readyState === EventSource.CLOSED) {
                console.log('📡 SSE Connection closed normally');
                // Don't reconnect when stream closes normally
            } else if (this.eventSource?.readyState === EventSource.CONNECTING) {
                console.log('🔄 SSE Reconnecting...');
                // Don't spam reconnection attempts while already connecting
            } else {
                console.log('💥 SSE Connection error, attempting reconnect...');
                this.handleConnectionError(jobId);
            }
        };
    }

    private handleConnectionError(jobId: Id): void {
        if (this.reconnectCount < this.config.reconnectAttempts) {
            this.reconnectCount++;
            this.reconnectTimeout = window.setTimeout(() => {
                this.createConnection(jobId);
            }, this.config.reconnectDelay * this.reconnectCount);
        } else {
            // The EventManager will handle notifying error handlers
            const error = new Error('Maximum reconnection attempts reached');
            console.error('SSE max reconnection attempts reached:', error);
        }
    }

    async disconnect(): Promise<void> {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = undefined;
        }

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = undefined;
        }
    }

    get isConnected(): boolean {
        return this.eventSource?.readyState === EventSource.OPEN;
    }
}

export function createSSEClient(config: SSEClientConfig): SSEClient {
    return new SSEClient(config);
} 