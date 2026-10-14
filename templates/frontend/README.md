# Spaik frontend template

A React/Vite app consuming the shared `spaik-sdk-material` UI kit and official AG-UI client. Message rendering belongs to the kit.

After copying this template, run `bun install` and `bun run dev`. Start a Spaik backend at http://localhost:8000, or update `src/App.tsx` to pass an independent `HttpAgent`.

The UI retains managed threads, tools/reasoning, attachments, copy, speech and cancellation. See [the UI kit](../../packages/agent-sdk-material/README.md) and [migration guide](../../docs/MIGRATING_TO_1_0.md).
