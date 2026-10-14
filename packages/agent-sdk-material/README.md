# spaik-sdk-material

Themeable Material UI chat components backed by AG-UI. Upgrading from 0.x? See the [migration guide](../../docs/MIGRATING_TO_1_0.md).

```sh
npm install spaik-sdk-material spaik-sdk-react @mui/material @emotion/react @emotion/styled
```

React, React DOM, MUI and emotion are peer dependencies, so the kit renders with your application's copies and theme. It supports React 18 and 19, and `@mui/material` 5.15 or later, 6, 7 and 9.

```tsx
import { HttpAgent } from 'spaik-sdk-react';
import { AgentChat, AgentThemeProvider } from 'spaik-sdk-material';

const agent = new HttpAgent({ url: 'https://your-agent.example/run', threadId: 'conversation' });

export function App() {
  return <AgentThemeProvider><AgentChat agent={agent} /></AgentThemeProvider>;
}
```

For Spaik thread management, use `<AgentChat baseUrl="http://localhost:8000" />`. The sidebar appears when a thread repository is available. Alternatively supply `threadRepository` and `createAgent(threadId)` for application-owned persistence. `headers` configures authentication for Spaik thread/run requests.

`AgentChat` supports text, reasoning, tool calls/results, activity messages, state, attachments, errors and cancellation. Use `renderMessage(message, messages)` and `renderState(state)` for custom presentation; use `customComponents` for custom markdown components. `enableTTS`, `enableSTT`, `enableCopy`, and `sttLanguage` retain audio/copy controls. Audio and stored attachments require a configured `baseUrl` and corresponding backend routes.

Standalone components include `ChatPanel`, `MessageCard`, `MessageList`, `ThreadSidebar`, `MessageInput`, reasoning/tool/text displays, attachment gallery, audio controls and markdown renderers. Message components accept official AG-UI messages, not legacy blocks. Preserve component instances across stream updates.

See [migration guide](../../docs/MIGRATING_TO_1_0.md) and [React hooks](../agent-sdk-hooks/README.md).

```sh
bun run build
bun run type-check
```
