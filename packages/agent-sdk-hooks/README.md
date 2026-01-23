# Spaik SDK React

React hooks for building AI chat interfaces with real-time streaming.

Spaik SDK is an open-source project developed by engineers at Siili Solutions Oyj. This is not an official Siili product.

## Installation

```bash
npm install spaik-sdk-react
# or
bun add spaik-sdk-react
```

## Quick Start

```tsx
import {
  AgentSdkClientProvider,
  AgentSdkClient,
  useThreadList,
  useThread,
  useThreadActions,
  useThreadSelection,
} from 'spaik-sdk-react';

const client = new AgentSdkClient({ baseUrl: 'http://localhost:8000' });

function App() {
  return (
    <AgentSdkClientProvider apiClient={client}>
      <ChatApp />
    </AgentSdkClientProvider>
  );
}

function ChatApp() {
  const { threadSummaries, loading } = useThreadList();
  const { selectedThreadId, selectThread } = useThreadSelection();
  const { thread } = useThread(selectedThreadId);
  const { createThread, sendMessage } = useThreadActions();

  const handleSend = async (content: string) => {
    if (!selectedThreadId) {
      const newThread = await createThread({});
      selectThread(newThread.id);
      await sendMessage(newThread.id, { content });
    } else {
      await sendMessage(selectedThreadId, { content });
    }
  };

  return (
    <div>
      <aside>
        {threadSummaries.map(t => (
          <button key={t.thread_id} onClick={() => selectThread(t.thread_id)}>
            {t.title}
          </button>
        ))}
      </aside>
      <main>
        {thread?.messages.map(msg => (
          <div key={msg.id}>
            <strong>{msg.ai ? 'AI' : 'User'}</strong>
            {msg.blocks.map(block => (
              <p key={block.id}>{block.content}</p>
            ))}
          </div>
        ))}
      </main>
    </div>
  );
}
```

## Hooks

### useThreadList

Manages the list of conversation threads.

```tsx
const {
  threadSummaries,  // ThreadSummary[]
  loading,          // boolean
  error,            // string | undefined
  refresh,          // () => Promise<void>
} = useThreadList();
```

### useThread

Loads a specific thread with all messages.

```tsx
const {
  thread,   // Thread | undefined
  loading,  // boolean | undefined
  error,    // string | undefined
} = useThread(threadId);
```

### useThreadActions

Actions for creating threads and sending messages.

```tsx
const {
  createThread,  // (request: CreateThreadRequest) => Promise<Thread>
  sendMessage,   // (threadId: string, request: CreateMessageRequest) => Promise<void>
} = useThreadActions();
```

### useThreadSelection

Manages which thread is currently selected.

```tsx
const {
  selectedThreadId,  // string | undefined
  selectThread,      // (threadId?: string) => void
} = useThreadSelection();
```

### useFileUploadStore

File upload management.

```tsx
const {
  pendingUploads,  // PendingUpload[]
  addFiles,        // (files: File[]) => void
  removeFile,      // (id: string) => void
  clearAll,        // () => void
} = useFileUploadStore();
```

### useTextToSpeech

Text-to-speech functionality.

```tsx
const {
  speak,     // (text: string) => Promise<void>
  stop,      // () => void
  speaking,  // boolean
} = useTextToSpeech({ model: 'tts-1' });
```

### useSpeechToText

Speech-to-text functionality.

```tsx
const {
  startRecording,   // () => void
  stopRecording,    // () => Promise<string>
  recording,        // boolean
  transcription,    // string
} = useSpeechToText({ model: 'whisper-1' });
```

### usePushToTalk

Combined voice input with callback.

```tsx
const {
  isRecording,
  startRecording,
  stopRecording,
} = usePushToTalk({
  onTranscription: (text) => sendMessage(threadId, { content: text }),
});
```

## API Client

### AgentSdkClient

Main client that combines all API functionality.

```tsx
const client = new AgentSdkClient({
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Authorization': 'Bearer token',
  },
});
```

### Individual API Clients

```tsx
import {
  createThreadsApiClient,
  createFilesApiClient,
  createAudioApiClient,
} from 'spaik-sdk-react';

const threadsApi = createThreadsApiClient({ baseUrl: '...' });
const filesApi = createFilesApiClient({ baseUrl: '...' });
const audioApi = createAudioApiClient({ baseUrl: '...' });
```

## Types

### Thread

```typescript
interface Thread {
  id: string;
  messages: Message[];
  metadata?: Record<string, unknown>;
}
```

### Message

```typescript
interface Message {
  id: string;
  ai: boolean;
  author_id: string;
  author_name: string;
  timestamp: number;
  blocks: MessageBlock[];
  attachments?: Attachment[];
}
```

### MessageBlock

```typescript
interface MessageBlock {
  id: string;
  type: 'plain' | 'reasoning' | 'tool_use' | 'error';
  content?: string;
  streaming: boolean;
  tool_name?: string;
  tool_call_id?: string;
  tool_call_args?: Record<string, unknown>;
  tool_call_response?: string;
  tool_call_error?: string;
}
```

### ThreadSummary

```typescript
interface ThreadSummary {
  thread_id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count: number;
}
```

## Streaming

The library handles SSE streaming automatically:

```tsx
function Chat({ threadId }) {
  const { thread } = useThread(threadId);
  
  return (
    <>
      {thread?.messages.map(msg => (
        <div key={msg.id}>
          {msg.blocks.map(block => (
            <span key={block.id}>
              {block.content}
              {block.streaming && <span className="cursor">▋</span>}
            </span>
          ))}
        </div>
      ))}
    </>
  );
}
```

SSE events handled:
- `streaming_updated` - Content delta
- `block_added` - New block started
- `block_fully_added` - Block completed
- `message_fully_added` - Message completed
- `tool_response_received` - Tool result

## File Attachments

```tsx
function FileInput({ threadId }) {
  const { sendMessage } = useThreadActions();
  const filesApi = useAgentSdkClient().files;

  const handleFiles = async (files: FileList) => {
    const attachments = await Promise.all(
      Array.from(files).map(async (file) => {
        const metadata = await filesApi.upload(file);
        return { file_id: metadata.file_id };
      })
    );
    
    await sendMessage(threadId, {
      content: 'Here are some files',
      attachments,
    });
  };

  return <input type="file" onChange={e => handleFiles(e.target.files!)} />;
}
```

## Development

```bash
# Install
bun install

# Build
bun run build

# Watch mode
bun run dev

# Type check
bun run type-check

# Lint
bun run lint
bun run lint:fix
```

## License

MIT - Copyright (c) 2026 Siili Solutions Oyj
