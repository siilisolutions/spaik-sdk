# AGENTS.md — spaik-sdk-react (hooks)

Read the [root AGENTS.md](../../AGENTS.md) first. The official AG-UI client (`@ag-ui/client`) owns messages, state and run lifecycle. This package subscribes to it and adds optional thread management, uploads and audio. Do not add custom event parsing or duplicate message renderers.

## Conventions

- Use zod for type guards.
- Use `function` declarations for named functions, not `const` arrow functions.
- Use named exports, exported where the function is declared. Public API goes through `src/index.ts`; do not add other `index.ts` files.
- Name a component's props interface `Props` unless it conflicts or must be exported. Use `interface`, not `type`.
- Use zustand for state.
- API clients use axios and extend `BaseApiClient`.
- Do not use `null` types.
- Comments are a code smell. Keep files and functions small.

## Layout

- `src/api`: backend clients
- `src/client`: `AgentSdkClient` and its provider
- `src/stores`: zustand stores
- `src/types`, `src/utils`
- `tests`: contract tests against AG-UI fixtures

## Checks

After a substantial change, run in this directory:

```bash
bun run type-check && bun run lint:fix && bun test tests
```

Then run the browser tests from the repo root with `bunx playwright test`.
