# Spaik frontend example

A React/Vite chat app built on the shared `spaik-sdk-material` UI kit and the official AG-UI client. Message rendering lives in the kit and is not duplicated here.

From the repository root, run `bun install`, `bun run build:packages`, then `bun run dev:backend` and `bun run dev:frontend`, and open http://localhost:5173. To use another AG-UI backend, open the app with `?agent=<endpoint URL>`.

Against the example backend you get managed threads, tool calls and reasoning, attachments, copy, speech input and output, and cancellation. See [the UI kit](../../packages/agent-sdk-material/README.md) and [the 1.0 migration guide](../../docs/MIGRATING_TO_1_0.md).
