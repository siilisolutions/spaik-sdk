# Siili AI SDK React

A React hooks library for building AI agent chat interfaces with real-time streaming capabilities. Built with Zustand for state management and Zod for type safety.

## TLDR

This library provides React hooks to easily integrate AI chat interfaces with siili-ai-sdk based backends. Just wrap your app in the provider, use the hooks to manage threads and messages, and get real-time streaming chat with minimal setup.

```tsx
// 1. Setup provider
<AgentSdkClientProvider apiClient={apiClient}>
  <YourChatApp />
</AgentSdkClientProvider>

// 2. Use hooks in components
const { threadSummaries } = useThreadList();
const { thread } = useThread(selectedThreadId);
const { sendMessage } = useThreadActions();
```

## Purpose

This library wraps and streamlines integration with siili-ai-sdk based backends, handling API connections out of the box even in complex serverless environments. It abstracts away the complexity of:

- WebSocket connections and reconnection logic
- Real-time message streaming
- Thread and message state management  
- Error handling and retry logic
- Type-safe API interactions

Perfect for building production-ready AI chat applications without dealing with the underlying infrastructure complexity.

## Installation

```bash
npm install @siilisolutions/ai-sdk-react
# or
yarn add @siilisolutions/ai-sdk-react
```

## Quick Start

### 1. Setup the Provider

```tsx
import { AgentSdkClientProvider, createThreadsApiClient } from '@siilisolutions/ai-sdk-react';

// Create API client
const apiClient = createThreadsApiClient({
  baseUrl: 'https://your-agent-api.com',
  headers: {
    'Authorization': 'Bearer your-token'
  }
});

// Wrap your app
function App() {
  return (
    <AgentSdkClientProvider apiClient={apiClient}>
      <ChatInterface />
    </AgentSdkClientProvider>
  );
}
```

### 2. Build Chat Interface

```tsx
import {
  useThreadList,
  useThreadSelection, 
  useThread,
  useThreadActions
} from '@siilisolutions/ai-sdk-react';

function ChatInterface() {
  // Get list of threads
  const { threadSummaries, loading, refresh } = useThreadList();
  
  // Handle thread selection
  const { selectedThreadId, selectThread } = useThreadSelection();
  
  // Get current thread data
  const { thread, loading: threadLoading } = useThread(selectedThreadId);
  
  // Actions for creating/messaging
  const { createThread, sendMessage } = useThreadActions();

  const handleSendMessage = async (content: string) => {
    if (!selectedThreadId) {
      // Create new thread first
      const newThread = await createThread({ metadata: {} });
      selectThread(newThread.id);
      await sendMessage(newThread.id, { content });
    } else {
      await sendMessage(selectedThreadId, { content });
    }
  };

  return (
    <div className="chat-interface">
      {/* Thread list */}
      <aside>
        {threadSummaries.map(summary => (
          <button
            key={summary.thread_id}
            onClick={() => selectThread(summary.thread_id)}
            className={selectedThreadId === summary.thread_id ? 'active' : ''}
          >
            {summary.title}
          </button>
        ))}
      </aside>

      {/* Chat area */}
      <main>
        {thread?.messages.map(message => (
          <div key={message.id} className={message.ai ? 'ai-message' : 'user-message'}>
            <strong>{message.author_name}</strong>
            {message.blocks.map(block => (
              <div key={block.id} className={`block-${block.type}`}>
                {block.content}
                {block.streaming && <span className="cursor">▋</span>}
              </div>
            ))}
          </div>
        ))}
        
        <MessageInput onSend={handleSendMessage} />
      </main>
    </div>
  );
}
```

## API Reference

### Hooks

#### `useThreadList()`
Manages the list of conversation threads.

**Returns:**
- `threadSummaries: ThreadSummary[]` - Array of thread summaries
- `loading: boolean` - Loading state
- `error?: string` - Error message if any
- `refresh: () => Promise<void>` - Refresh thread list

#### `useThread(threadId: string)`
Loads and manages a specific thread's messages.

**Returns:**
- `thread?: Thread` - Thread data with messages
- `loading?: boolean` - Loading state for this thread
- `error?: string` - Error message if any

#### `useThreadActions()`
Provides actions for creating threads and sending messages.

**Returns:**
- `createThread: (request: CreateThreadRequest) => Promise<Thread>`
- `sendMessage: (threadId: string, request: CreateMessageRequest) => Promise<void>`

#### `useThreadSelection()`
Manages which thread is currently selected.

**Returns:**
- `selectedThreadId?: string` - Currently selected thread ID
- `selectThread: (threadId?: string) => void` - Select a thread

### Components

#### `AgentSdkClientProvider`
Context provider that makes the API client available to hooks.

**Props:**
- `apiClient: AgentSdkClient` - The configured API client
- `children: ReactNode` - Child components

### API Client

#### `createThreadsApiClient(config)`
Creates a configured API client instance.

**Config:**
```typescript
{
  baseUrl: string;           // API base URL
  timeout?: number;          // Request timeout (default: 30s)
  headers?: Record<string, string>; // Additional headers
}
```

## Message Structure

Messages are organized into blocks with different types:

```typescript
type MessageBlock = {
  id: string;
  type: 'plain' | 'reasoning' | 'tool_use' | 'error';
  content?: string;
  streaming: boolean;
  
  // Tool-related fields
  tool_call_id?: string;
  tool_call_args?: Record<string, any>;
  tool_name?: string;
  tool_call_response?: string;
  tool_call_error?: string;
};
```

## Streaming

The library automatically handles real-time streaming updates:

- New messages appear as they're created
- Content streams in block by block  
- Tool calls and responses are tracked
- Streaming state is managed automatically

## Error Handling

All hooks provide error states and the API client includes built-in error handling:

```tsx
const { thread, loading, error } = useThread(threadId);

if (error) {
  return <div>Error: {error}</div>;
}
```

## Development

```bash
# Install dependencies
yarn install

# Build library
yarn build

# Type check
yarn tsc

# Lint and fix
yarn lint --fix

# Run tests
yarn test
```
