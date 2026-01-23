# AI Instructions - Frontend (React Hooks)

This document provides comprehensive instructions for working with the Agent SDK React hooks package (`packages/agent-sdk-hooks/`).

## Overview

The React hooks package provides type-safe, streaming-enabled React integration for the Agent SDK. It uses Zustand for state management and offers hooks for thread management, real-time messaging, and streaming responses.

## Core Components

### Client Setup

#### AgentSdkClientProvider (`src/client/AgentSdkClientProvider.tsx`)

Provider component that configures the SDK client for your React application:

```tsx
import { AgentSdkClientProvider } from 'spaik-sdk-react';

function App() {
    return (
        <AgentSdkClientProvider baseUrl="http://localhost:8000">
            <YourAppComponents />
        </AgentSdkClientProvider>
    );
}
```

#### useAgentSdkClient Hook

Access the configured client within provider context:

```tsx
import { useAgentSdkClient } from 'spaik-sdk-react';

function MyComponent() {
    const client = useAgentSdkClient();
    // Use client for direct API calls if needed
}
```

### AgentSdkClient (`src/client/AgentSdkClient.ts:4`)

Main client class with public methods:

- **`getThreads(filters?: ListThreadsFilters): Promise<ThreadSummary[]>`** (`src/client/AgentSdkClient.ts:10`)
  - Retrieves list of thread summaries
  - Optional filtering by date, user, etc.

- **`createThread(request?: CreateThreadRequest): Promise<Thread>`** (`src/client/AgentSdkClient.ts:15`)
  - Creates new conversation thread
  - Returns complete Thread object

- **`getThread(threadId: Id): Promise<Thread>`** (`src/client/AgentSdkClient.ts:19`)
  - Retrieves specific thread with full message history
  - Throws error if thread not found

- **`sendMessage(threadId: Id, request: CreateMessageRequest): Promise<void>`** (`src/client/AgentSdkClient.ts:23`)
  - Sends message to thread with streaming response
  - Automatically handles real-time updates

## Thread Management Hooks

### useThread Hook (`src/stores/threadStore.ts:148`)

Primary hook for managing individual thread state:

```tsx
import { useThread } from 'spaik-sdk-react';

function ThreadView({ threadId }: { threadId: string }) {
    const { thread, loading, error } = useThread(threadId);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!thread) return <div>Thread not found</div>;

    return (
        <div>
            {thread.messages.map(message => (
                <MessageComponent key={message.id} message={message} />
            ))}
        </div>
    );
}
```

**Returns:**
- `thread: Thread | undefined` - Current thread data
- `loading: boolean` - Loading state for initial thread fetch
- `error: string | undefined` - Error message if loading failed

### useThreadActions Hook (`src/stores/threadStore.ts:167`)

Hook for thread actions (creating threads, sending messages):

```tsx
import { useThreadActions } from 'spaik-sdk-react';

function MessageInput({ threadId }: { threadId: string }) {
    const { createThread, sendMessage } = useThreadActions();
    const [message, setMessage] = useState('');

    const handleSend = async () => {
        if (threadId) {
            await sendMessage(threadId, { content: message });
        } else {
            const newThread = await createThread({});
            await sendMessage(newThread.id, { content: message });
        }
        setMessage('');
    };

    return (
        <div>
            <input 
                value={message} 
                onChange={(e) => setMessage(e.target.value)} 
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend}>Send</button>
        </div>
    );
}
```

**Returns:**
- `createThread: (request: CreateThreadRequest) => Promise<Thread>`
- `sendMessage: (threadId: Id, request: CreateMessageRequest) => Promise<void>`

### getStreamingHandlers Function (`src/stores/threadStore.ts:177`)

Access to low-level streaming handlers for custom implementations:

```tsx
import { getStreamingHandlers } from 'spaik-sdk-react';

function CustomStreamingComponent() {
    const handlers = getStreamingHandlers();
    
    // Use handlers for custom streaming logic
    // handlers.appendStreamingContent(threadId, blockId, content);
    // handlers.completeBlockStreaming(threadId, blockId);
    // handlers.addMessage(threadId, message);
}
```

**Available Handlers:**
- `appendStreamingContent(threadId: Id, blockId: Id, content: string): void`
- `completeBlockStreaming(threadId: Id, blockId: Id): void`
- `completeMessageStreaming(threadId: Id, messageId: Id): void`
- `addMessage(threadId: Id, message: Message): void`
- `addBlock(threadId: Id, messageId: Id, block: MessageBlock): void`
- `addToolCallResponse(threadId: Id, blockId: Id, response: string): void`

## Thread List Management Hooks

### useThreadList Hook (`src/stores/threadListStore.ts:50`)

Hook for managing list of threads:

```tsx
import { useThreadList } from 'spaik-sdk-react';

function ThreadList() {
    const { threadSummaries, loading, error, refresh } = useThreadList();

    return (
        <div>
            <button onClick={refresh}>Refresh</button>
            {loading && <div>Loading threads...</div>}
            {error && <div>Error: {error}</div>}
            {threadSummaries.map(summary => (
                <ThreadSummaryItem key={summary.id} summary={summary} />
            ))}
        </div>
    );
}
```

**Returns:**
- `threadSummaries: ThreadSummary[]` - Array of thread summaries
- `loading: boolean` - Loading state for thread list
- `error: string | undefined` - Error message if loading failed
- `refresh: () => Promise<void>` - Function to refresh thread list

### useThreadSelection Hook (`src/stores/threadListStore.ts:77`)

Hook for managing thread selection state:

```tsx
import { useThreadSelection } from 'spaik-sdk-react';

function ThreadSelector() {
    const { selectedThreadId, selectThread } = useThreadSelection();

    return (
        <div>
            <p>Selected: {selectedThreadId || 'None'}</p>
            <button onClick={() => selectThread('thread-123')}>
                Select Thread
            </button>
            <button onClick={() => selectThread(undefined)}>
                Clear Selection
            </button>
        </div>
    );
}
```

**Returns:**
- `selectedThreadId: Id | undefined` - Currently selected thread ID
- `selectThread: (threadId?: Id) => void` - Function to select/deselect thread

### useThreadListActions Hook (`src/stores/threadListStore.ts:87`)

Hook for thread list actions:

```tsx
import { useThreadListActions } from 'spaik-sdk-react';

function ThreadListControls() {
    const { loadThreads, refresh } = useThreadListActions();

    const loadRecentThreads = () => {
        loadThreads({ limit: 10, sortBy: 'updated_at' });
    };

    return (
        <div>
            <button onClick={refresh}>Refresh All</button>
            <button onClick={loadRecentThreads}>Load Recent</button>
        </div>
    );
}
```

**Returns:**
- `loadThreads: (filters?: ListThreadsFilters) => Promise<void>`
- `refresh: () => Promise<void>`

## Type Definitions

### Core Types (`src/stores/messageTypes.ts`)

```tsx
export type Id = string;

export interface Thread {
    id: Id;
    messages: Message[];
    created_at: string;
    updated_at: string;
}

export interface Message {
    id: Id;
    author: 'user' | 'assistant';
    blocks: MessageBlock[];
    created_at: string;
    streaming?: boolean;
}

export interface MessageBlock {
    id: Id;
    type: BlockType;
    content?: string;
    tool_name?: string;
    tool_arguments?: Record<string, any>;
    tool_call_response?: string;
    streaming?: boolean;
}

export type BlockType = 'text' | 'tool_call' | 'tool_response';
```

### API Types

```tsx
export interface CreateThreadRequest {
    title?: string;
    metadata?: Record<string, any>;
}

export interface CreateMessageRequest {
    content: string;
    metadata?: Record<string, any>;
}

export interface ThreadSummary {
    id: Id;
    title?: string;
    created_at: string;
    updated_at: string;
    message_count: number;
}

export interface ListThreadsFilters {
    limit?: number;
    offset?: number;
    sortBy?: 'created_at' | 'updated_at';
    sortOrder?: 'asc' | 'desc';
}
```

## API Client

### ThreadsApiClient (`src/api/ThreadsApiClient.ts`)

Low-level API client (usually not used directly):

```tsx
import { createThreadsApiClient } from 'spaik-sdk-react';

const apiClient = createThreadsApiClient({
    baseUrl: 'http://localhost:8000',
    // Additional configuration
});
```

### BaseApiClient (`src/api/BaseApiClient.ts`)

Base client with common configuration:

```tsx
export interface BaseApiClientConfig {
    baseUrl: string;
    timeout?: number;
    headers?: Record<string, string>;
}
```

## Complete Example

```tsx
import React, { useState } from 'react';
import { 
    AgentSdkClientProvider, 
    useThread, 
    useThreadActions, 
    useThreadList,
    useThreadSelection
} from 'spaik-sdk-react';

function App() {
    return (
        <AgentSdkClientProvider baseUrl="http://localhost:8000">
            <div style={{ display: 'flex', height: '100vh' }}>
                <ThreadListSidebar />
                <ChatArea />
            </div>
        </AgentSdkClientProvider>
    );
}

function ThreadListSidebar() {
    const { threadSummaries, loading } = useThreadList();
    const { selectedThreadId, selectThread } = useThreadSelection();
    const { createThread } = useThreadActions();

    const handleNewThread = async () => {
        const newThread = await createThread({});
        selectThread(newThread.id);
    };

    return (
        <div style={{ width: '300px', borderRight: '1px solid #ccc' }}>
            <button onClick={handleNewThread}>New Thread</button>
            {loading ? (
                <div>Loading...</div>
            ) : (
                threadSummaries.map(summary => (
                    <div 
                        key={summary.id}
                        onClick={() => selectThread(summary.id)}
                        style={{ 
                            padding: '10px',
                            cursor: 'pointer',
                            backgroundColor: selectedThreadId === summary.id ? '#e0e0e0' : 'white'
                        }}
                    >
                        Thread {summary.id.slice(0, 8)}...
                        <small>{new Date(summary.updated_at).toLocaleDateString()}</small>
                    </div>
                ))
            )}
        </div>
    );
}

function ChatArea() {
    const { selectedThreadId } = useThreadSelection();
    
    if (!selectedThreadId) {
        return <div>Select a thread to start chatting</div>;
    }
    
    return <ThreadChat threadId={selectedThreadId} />;
}

function ThreadChat({ threadId }: { threadId: string }) {
    const { thread, loading, error } = useThread(threadId);
    const { sendMessage } = useThreadActions();
    const [message, setMessage] = useState('');

    const handleSend = async () => {
        if (message.trim()) {
            await sendMessage(threadId, { content: message });
            setMessage('');
        }
    };

    if (loading) return <div>Loading thread...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!thread) return <div>Thread not found</div>;

    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
                {thread.messages.map(message => (
                    <div 
                        key={message.id}
                        style={{ 
                            marginBottom: '20px',
                            textAlign: message.author === 'user' ? 'right' : 'left'
                        }}
                    >
                        <strong>{message.author}:</strong>
                        {message.blocks.map(block => (
                            <div key={block.id}>
                                {block.type === 'text' && <p>{block.content}</p>}
                                {block.type === 'tool_call' && (
                                    <div>
                                        <strong>Tool:</strong> {block.tool_name}
                                        {block.tool_call_response && (
                                            <div><strong>Response:</strong> {block.tool_call_response}</div>
                                        )}
                                    </div>
                                )}
                                {block.streaming && <span>...</span>}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
            <div style={{ padding: '20px', borderTop: '1px solid #ccc' }}>
                <input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type your message..."
                    style={{ width: 'calc(100% - 100px)', padding: '10px' }}
                />
                <button onClick={handleSend} style={{ width: '80px', padding: '10px' }}>
                    Send
                </button>
            </div>
        </div>
    );
}
```

## Development Commands

```bash
cd packages/agent-sdk-hooks

# Development
yarn build                 # Build library
yarn dev                   # Build in watch mode
yarn type-check            # TypeScript checking
yarn lint                  # ESLint
yarn lint:fix              # ESLint with fixes
```

## Best Practices

1. **Provider Setup**: Always wrap your app with AgentSdkClientProvider
2. **Error Handling**: Check error states from hooks and display user-friendly messages
3. **Loading States**: Show loading indicators for better UX
4. **Real-time Updates**: Hooks automatically handle streaming; no manual intervention needed
5. **Type Safety**: Use provided TypeScript types for better development experience
6. **Performance**: Thread and thread list data is cached and shared across components
7. **Memory Management**: Hooks handle cleanup automatically; no manual subscription management needed