# AGENTS.md — example frontend

Read the [root AGENTS.md](../../AGENTS.md) first. This app shows how to consume `spaik-sdk-material` and `spaik-sdk-react`. Message rendering belongs in the Material kit; fix rendering there instead of re-implementing it here.

## Conventions

- Use zod for type guards and zustand for state.
- Use `function` declarations and named exports, exported where they are declared. Do not add `index.ts` files.
- Name props interfaces `Props` and use `interface`, not `type`.
- Do not use `null` types. Comments are a code smell. Keep files and functions small.
- Folders, when the app grows: `src/components` for reusable components (a main component and its subcomponents share a folder named after it), `src/views` for single-use views, `src/stores`, `src/api`, `src/utils`.

## Checks

From the repo root, run `bun run build:packages` first, because the app consumes the built packages. Then run in this directory:

```bash
bun run build && bun run lint
```

Run it with `bun run dev:backend` and `bun run dev:frontend` from the repo root.
