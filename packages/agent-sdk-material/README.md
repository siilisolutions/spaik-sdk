# Spaik SDK Material

Material UI components for building AI chat interfaces.

## Installation

```bash
npm install @spaik/material
```

Requires peer dependencies:

```bash
npm install @spaik/react react react-dom
```

## Quick Start

```tsx
import { AgentSdkClientProvider, AgentSdkClient } from '@spaik/react';
import { AgentChat, AgentThemeProvider } from '@spaik/material';

const client = new AgentSdkClient({ baseUrl: 'http://localhost:8000' });

function App() {
  return (
    <AgentSdkClientProvider apiClient={client}>
      <AgentThemeProvider>
        <AgentChat />
      </AgentThemeProvider>
    </AgentSdkClientProvider>
  );
}
```

## Components

### AgentChat

Full chat interface with sidebar and message area.

```tsx
import { AgentChat } from '@spaik/material';

<AgentChat />
```

### ChatPanel

Message list with input, without sidebar.

```tsx
import { ChatPanel } from '@spaik/material';

<ChatPanel threadId={selectedThreadId} />
```

### ThreadSidebar

Thread list for navigation.

```tsx
import { ThreadSidebar } from '@spaik/material';

<ThreadSidebar
  onThreadSelect={setSelectedThreadId}
  selectedThreadId={selectedThreadId}
/>
```

### MessageCard

Individual message display.

```tsx
import { MessageCard } from '@spaik/material';

<MessageCard message={message} />
```

### MessageInput

Chat input with attachments.

```tsx
import { MessageInput } from '@spaik/material';

<MessageInput
  onSend={(content, attachments) => sendMessage(threadId, { content, attachments })}
  disabled={isStreaming}
/>
```

### Audio Controls

```tsx
import { SpeakButton, PushToTalkButton } from '@spaik/material';

// Text-to-speech for a message
<SpeakButton text={message.blocks.map(b => b.content).join('')} />

// Voice input
<PushToTalkButton onTranscription={handleVoiceInput} />
```

## Theming

### Default Theme

```tsx
import { AgentThemeProvider } from '@spaik/material';

<AgentThemeProvider>
  <App />
</AgentThemeProvider>
```

### Custom Theme

```tsx
import { AgentThemeProvider, createAgentTheme } from '@spaik/material';

const theme = createAgentTheme({
  palette: {
    primary: { main: '#1976d2' },
    background: { default: '#f5f5f5' },
  },
  messageColors: {
    user: '#e3f2fd',
    assistant: '#fff',
  },
});

<AgentThemeProvider theme={theme}>
  <App />
</AgentThemeProvider>
```

### useAgentTheme

Access theme in components:

```tsx
import { useAgentTheme } from '@spaik/material';

function MyComponent() {
  const theme = useAgentTheme();
  return <div style={{ color: theme.palette.primary.main }}>...</div>;
}
```

## Message Blocks

Components for different block types:

```tsx
import {
  TextBlock,
  ReasoningBlock,
  ToolCallBlock,
  ErrorBlock,
} from '@spaik/material';

// Automatically rendered by MessageCard, or use directly:
<TextBlock content={block.content} streaming={block.streaming} />
<ReasoningBlock content={block.content} />
<ToolCallBlock block={block} />
<ErrorBlock content={block.content} />
```

## Markdown

Built-in markdown rendering with GFM support:

```tsx
import { MarkdownRenderer } from '@spaik/material';

<MarkdownRenderer content="# Hello **world**" />
```

## Development

```bash
bun install
bun run build
bun run dev        # Watch mode
bun run type-check
bun run lint
```

## License

MIT - Copyright (c) 2025 Siili Solutions Oyj
