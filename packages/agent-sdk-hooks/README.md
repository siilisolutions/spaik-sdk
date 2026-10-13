# spaik-sdk-react

React hooks for AG-UI conversations and optional persisted thread management. The official AG-UI client owns messages, state and run lifecycle. This branch is preparing 1.0; see [release gates](../../docs/SPAIK_1_0_PLAN.md).

```tsx
import { HttpAgent, AgentSdkClient, AgentSdkClientProvider, useThread, useThreadSelection, useThreadActions } from 'spaik-sdk-react';

const agent = new HttpAgent({ url: 'https://your-agent.example/run', threadId: 'conversation' });
const client = new AgentSdkClient({ agent });

function Chat() {
  const { selectedThreadId } = useThreadSelection();
  const { thread, state, isGenerating, error } = useThread(selectedThreadId ?? '');
  const { sendMessage, cancelGeneration } = useThreadActions();
  // Render official AG-UI messages from thread.messages and state.
  return <button disabled={isGenerating} onClick={() => sendMessage('conversation', { content: 'Hello' })}>Send</button>;
}

export function App() {
  return <AgentSdkClientProvider apiClient={client}><Chat /></AgentSdkClientProvider>;
}
```

For Spaik's managed threads, use `new AgentSdkClient(createThreadsApiClient({ baseUrl, headers }))`. `ThreadRepository` supplies create/read/list/delete and optional cancellation; pair a custom repository with `createAgent(threadId)` for another backend. Thread persistence and sidebars are optional. A provider scopes thread selection to its client.

Hooks: `useAgent(agent)`, `useThread(id)`, `useThreadActions()`, `useThreadList()`, `useThreadSelection()`, `useFileUploadStore()`, `useTextToSpeech()`, `useSpeechToText()`, `usePushToTalk()`. Use official `AgentSubscriber` callbacks for custom AG-UI integrations. Spaik uploads are forwarded as `forwardedProps.attachments[messageId]`.

The old custom events, streaming handlers, message blocks and raw stream parser are removed. `Message` is AG-UI's type; `messageText(message)` extracts display text. See [migration guide](../../docs/MIGRATING_TO_1_0.md).

```sh
bun run build
bun run type-check
bun run lint
bun test tests
```
