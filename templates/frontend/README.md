# LLM Interaction Library

A highly configurable React library for interacting with LLM APIs that support streaming responses via Server-Sent Events (SSE).

## Features

- 🚀 **Real-time streaming** - Live updates as the LLM generates responses
- 🔧 **Highly configurable** - Flexible API client configuration 
- 📦 **Type-safe** - Full TypeScript support with Zod validation
- ⚡ **Optimized state management** - Zustand store for efficient updates
- 🎯 **React hooks** - Simple `useThread(threadId)` hook for easy integration
- 📱 **Ready-to-use components** - Pre-built UI components for common use cases
- 🔄 **Auto-reconnection** - Robust SSE connection handling with retry logic
- 🧩 **Block-based messages** - Support for different content types (reasoning, tool use, etc.)

## Installation

```bash
bun add @your-org/llm-library
# or
npm install @your-org/llm-library
```

## Quick Start

### 1. Wrap your app with LLMProvider

```tsx
import { LLMProvider } from '@your-org/llm-library';

const config = {
  baseUrl: 'http://localhost:8000',
  sessionId: 'user-session-123',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

function App() {
  return (
    <LLMProvider config={config}>
      <YourAppComponents />
    </LLMProvider>
  );
}
```

### 2. Use the useThread hook

```tsx
import { useThread } from '@your-org/llm-library';
import type { ThreadId } from '@your-org/llm-library';

function ChatComponent() {
  const threadId: ThreadId = 'my-thread-1';
  const { thread, sendMessage, isStreaming, hasError, error } = useThread(threadId);

  const handleSendMessage = async () => {
    try {
      await sendMessage('Hello, AI assistant!');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <div>
      {hasError && <div>Error: {error}</div>}
      
      {thread?.messages.map((message) => (
        <div key={message.id}>
          <strong>{message.ai ? 'AI' : 'User'}:</strong>
          {message.blocks.map((block) => (
            <div key={block.id}>{block.content}</div>
          ))}
        </div>
      ))}
      
      {isStreaming && <div>AI is typing...</div>}
      
      <button onClick={handleSendMessage} disabled={isStreaming}>
        Send Message
      </button>
    </div>
  );
}
```

### 3. Or use the pre-built ThreadView component

```tsx
import { ThreadView } from '@your-org/llm-library';

function ChatComponent() {
  const threadId: ThreadId = 'my-thread-1';

  return (
    <div>
      <ThreadView threadId={threadId} />
      {/* Your input controls */}
    </div>
  );
}
```

## API Reference

### LLMProvider

Initializes the library and provides configuration to child components.

```tsx
interface LLMClientConfig {
  baseUrl: string;          // Base URL of your LLM API
  timeout?: number;         // Request timeout in milliseconds (default: 30000)
  sessionId?: string;       // Session identifier (default: 'default')
  retryAttempts?: number;   // SSE reconnection attempts (default: 3)
  retryDelay?: number;      // Delay between retries in ms (default: 1000)
}
```

### useThread Hook

The main hook for interacting with LLM threads.

```tsx
function useThread(threadId: ThreadId): UseThreadResult {
  // Returns thread state and control functions
}

interface UseThreadResult {
  thread: ThreadState | undefined;
  sendMessage: (message: string) => Promise<void>;
  isStreaming: boolean;
  isConnected: boolean;
  hasError: boolean;
  error?: string;
  streamingState: StreamingState;
}
```

### Additional Hooks

```tsx
// Get streaming content for display during generation
function useThreadStreamingContent(threadId: ThreadId): string

// Check if any thread is currently streaming
function useIsAnyThreadStreaming(): boolean
```

### Components

#### ThreadView
Displays a complete thread with all messages and streaming indicators.

```tsx
interface Props {
  threadId: ThreadId;
  className?: string;
}
```

#### MessageBlock
Displays individual message blocks with type-specific styling.

```tsx
interface Props {
  block: MessageBlockType;
  isStreaming?: boolean;
  streamingContent?: string;
}
```

## Message Structure

Messages are composed of blocks that can have different types:

```tsx
type BlockType = 'plain' | 'reasoning' | 'tool_use' | 'tool_response';

interface MessageBlock {
  id: BlockId;
  type: BlockType;
  content: string;
}

interface Message {
  id: MessageId;
  ai: boolean;
  author_id: string;
  timestamp: number;
  blocks: MessageBlock[];
}
```

## SSE Event Types

The library handles these SSE event types automatically:

- `connected` - Initial connection established
- `heartbeat` - Keep-alive signal
- `streaming_updated` - Real-time content updates
- `block_added` - New message block started
- `block_fully_added` - Message block completed
- `message_fully_added` - Complete message with all blocks
- `tool_call_started` - Tool execution began
- `tool_response_received` - Tool execution completed
- `streaming_ended` - Job processing finished

## Advanced Usage

### Direct API Access

For advanced use cases, you can access the underlying API clients:

```tsx
import { createLLMApiClient, createSSEClient } from '@your-org/llm-library';

const apiClient = createLLMApiClient({
  baseUrl: 'http://localhost:8000'
});

const sseClient = createSSEClient({
  baseUrl: 'http://localhost:8000',
  sessionId: 'custom-session'
});

// Use clients directly
const jobId = await apiClient.launchJob({ message: 'Hello' });
sseClient.connect(jobId);
sseClient.onEvent((event) => {
  console.log('SSE Event:', event);
});
```

### Custom State Management

Access the Zustand store directly:

```tsx
import { useLLMStore } from '@your-org/llm-library';

function CustomComponent() {
  const store = useLLMStore();
  
  // Access all threads
  const allThreads = Array.from(store.threads.values());
  
  // Manual operations
  store.createThread('new-thread');
  store.sendMessage('thread-id', 'message');
}
```

## Error Handling

The library provides comprehensive error handling:

```tsx
function ChatComponent() {
  const { hasError, error, streamingState } = useThread(threadId);
  
  if (hasError) {
    return <div>Connection error: {error}</div>;
  }
  
  if (streamingState === 'connecting') {
    return <div>Connecting to AI...</div>;
  }
  
  // ... rest of component
}
```

## Development

This library is built with:
- **React 18+** with hooks
- **TypeScript** for type safety
- **Zustand** for state management
- **Zod** for runtime validation
- **Axios** for HTTP requests
- **Server-Sent Events** for real-time streaming

## API Server Requirements

Your LLM API server should implement:

1. **Health Check**: `GET /health`
2. **Launch Job**: `POST /jobs/launch` → `{ job_id: string }`
3. **Stream Events**: `GET /jobs/{job_id}/stream?session_id={session_id}`

See the type definitions for exact schemas.

## License

MIT 