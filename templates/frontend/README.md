# Spaik agent chat

A React/Vite chat app built on the [spaik-sdk-material](https://github.com/siilisolutions/spaik-sdk/blob/main/packages/agent-sdk-material/README.md) UI kit and the official AG-UI client.

It needs Bun and Node.js 20.19+ or 22.12+ (for Vite 8). Run `bun install` and `bun run dev`, then open http://localhost:5173. By default the app talks to a Spaik backend at http://localhost:8000. To use another AG-UI backend, open the app with `?agent=<endpoint URL>` or pass your own `HttpAgent` in `src/App.tsx`.

Against a Spaik backend you get managed threads, tool calls and reasoning, attachments, copy, speech input and output, and cancellation. See the [1.0 migration guide](https://github.com/siilisolutions/spaik-sdk/blob/main/docs/MIGRATING_TO_1_0.md) if you are upgrading from 0.x.
