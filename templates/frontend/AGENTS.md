# AGENTS.md

This React/Vite app uses [spaik-sdk-material](https://github.com/siilisolutions/spaik-sdk/blob/main/packages/agent-sdk-material/README.md) and [spaik-sdk-react](https://github.com/siilisolutions/spaik-sdk/blob/main/packages/agent-sdk-hooks/README.md) 1.x on the official AG-UI client. Run `bun install` and `bun run dev`.

## Using the Spaik UI

- `<AgentChat baseUrl="...">` talks to a Spaik backend with managed threads. `<AgentChat agent={new HttpAgent({ url, threadId })}>` talks to any other AG-UI backend. Wrap it in `AgentThemeProvider`.
- Messages are AG-UI `Message` objects; use `messageText(message)` from `spaik-sdk-react` for their text. The AG-UI client owns message and run state, and the hooks subscribe to it. Do not parse the event stream yourself.
- Customise display with `renderMessage` and `renderState`, not by forking the message components. For your own persistence backend, implement `ThreadRepository` and `createAgent(threadId)`.

## Conventions

- Use zod for type guards and zustand for state.
- Use `function` declarations and named exports, exported where they are declared. Do not add `index.ts` files.
- Name props interfaces `Props` and use `interface`, not `type`. Do not use `null` types.
- Comments are a code smell. Keep files and functions small.
- Folders: `src/components` (reusable; a main component and its subcomponents share a folder), `src/views` (single-use), `src/stores`, `src/api`, `src/utils`.
- After changes, run `bun run build && bun run lint`.
