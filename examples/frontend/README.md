# Frontend Example

React frontend demonstrating the Spaik SDK hooks.

## Setup

```bash
cd examples/frontend
bun install
```

## Run

```bash
bun run dev
```

Open `http://localhost:5173`

Requires the backend running at `http://localhost:8000`.

## Structure

```
frontend/
├── src/
│   ├── App.tsx                    # Main app with provider setup
│   ├── components/
│   │   ├── ThreadList/            # Thread sidebar
│   │   ├── ThreadView/            # Chat area
│   │   ├── MessageRenderer/       # Message display
│   │   ├── MessageBlockRenderer/  # Block display (text, tools, etc.)
│   │   └── FileUpload/            # File attachment UI
│   └── utils/
│       └── nullToUndefined.ts
├── index.html
└── vite.config.ts
```

## Key Components

### Provider Setup

```tsx
import { AgentSdkClientProvider, AgentSdkClient } from '@spaik/react';

const client = new AgentSdkClient({ baseUrl: 'http://localhost:8000' });

function App() {
  return (
    <AgentSdkClientProvider apiClient={client}>
      <ChatInterface />
    </AgentSdkClientProvider>
  );
}
```

### Thread List

```tsx
import { useThreadList, useThreadSelection } from '@spaik/react';

function ThreadList() {
  const { threadSummaries } = useThreadList();
  const { selectedThreadId, selectThread } = useThreadSelection();
  
  return (
    <ul>
      {threadSummaries.map(t => (
        <li key={t.thread_id} onClick={() => selectThread(t.thread_id)}>
          {t.title}
        </li>
      ))}
    </ul>
  );
}
```

### Message Input

```tsx
import { useThreadActions, useThreadSelection } from '@spaik/react';

function MessageInput() {
  const { selectedThreadId } = useThreadSelection();
  const { sendMessage, createThread } = useThreadActions();
  const [text, setText] = useState('');

  const handleSend = async () => {
    let threadId = selectedThreadId;
    if (!threadId) {
      const thread = await createThread({});
      threadId = thread.id;
    }
    await sendMessage(threadId, { content: text });
    setText('');
  };

  return (
    <input
      value={text}
      onChange={e => setText(e.target.value)}
      onKeyDown={e => e.key === 'Enter' && handleSend()}
    />
  );
}
```

### Message Display

```tsx
import { useThread, useThreadSelection } from '@spaik/react';

function Messages() {
  const { selectedThreadId } = useThreadSelection();
  const { thread } = useThread(selectedThreadId);

  return (
    <div>
      {thread?.messages.map(msg => (
        <div key={msg.id} className={msg.ai ? 'ai' : 'user'}>
          {msg.blocks.map(block => (
            <div key={block.id}>
              {block.type === 'tool_use' ? (
                <ToolDisplay block={block} />
              ) : (
                <p>{block.content}</p>
              )}
              {block.streaming && <span>▋</span>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

## Development

```bash
bun run dev      # Start dev server
bun run build    # Build for production
bun run preview  # Preview production build
```
