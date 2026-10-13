# AGENTS.md

Guidance for assistants working on Spaik SDK.

## Product and architecture

Spaik's core is thread management and a reusable React/Material UI kit. Canonical transcripts and frontend events use official AG-UI types. Retain BaseAgent/tool convenience, structured responses, streaming, cancellation, attachments/audio, recording and tracing. Avoid price tables, model eligibility lists, duplicate stream parsers and renderer implementations.

- `packages/agent-sdk/spaik_sdk/agent/base_agent.py`: BaseAgent and AG-UI lifecycle.
- `thread/`: canonical messages, private replay metadata, versioned envelope and migration.
- `llm/langchain_service.py`: LangChain -> AG-UI execution; every model invocation records usage/reported charges.
- `models/llm_config.py`: arbitrary provider/model IDs, provider kwargs or injected BaseChatModel. Optional presets are not required for construction.
- `llm/cost/`: provider-reported charge resolver; absent charge is None with a console message. Never infer price or zero.
- `server/api/routers/`: authorized thread CRUD, `/threads/{id}/runs` SSE, cancellation/files/audio.
- `packages/agent-sdk-hooks`: official AG-UI client state plus optional ThreadRepository, selection/uploads/audio.
- `packages/agent-sdk-material`: shared themed UI; examples/templates consume it.
- `packages/agent-workflows`: optional YAML convenience, no runtime redesign in 1.0.
- `packages/coding-agents`: deprecated legacy source; remove only after final legacy publication/tag.

## Commands

Python: `cd packages/agent-sdk; uv sync --all-extras --dev --locked`, `make test-unit`, `make test-integration`, `make lint`, `make typecheck`. Ruff configuration enables fixes; use `ruff check --no-fix` for read-only inspection.

Frontend: root `bun install`, `bun run build:packages`, `bun test packages/agent-sdk-hooks/tests`, `bunx playwright test`. Package `bun run type-check`/`lint` are available. Examples run with root `bun run dev:backend`/`dev:frontend`.

## Usage

```python
from spaik_sdk import BaseAgent
agent = BaseAgent(system_prompt="Be helpful.", llm_model="any-model-id", provider="openai", provider_kwargs={})
# Or inject chat_model=YourBaseChatModel(...).
print(agent.get_response_text("Hello"))
```

AG-UI assistant messages expose `.content`; use `message_text(message)` to extract display text. ToolProvider history hooks receive `ToolCallHistory`, preserving provider-owned markers/custom replay without losing UI tool transcripts. Provider SDKs and server/audio/MCP are optional extras and must be imported lazily.

Keep ownership authoritative from thread creation. Reject overwriting stored messages, conflicting IDs and overlapping runs; save tool/model checkpoints and partial output on cancellation/disconnect. Never expose private replay/system prompts through thread APIs. Built-in coordination is single-process; applications own distributed integrations.

## Work and release discipline

Work on branches and commit each validated chunk with docs. Keep [the implementation/release plan](docs/SPAIK_1_0_PLAN.md) current. For a deployment between milestones, merge the independently validated preparatory change to main before publishing; do not publish partially migrated 1.0 as stable. Retain original storage and legacy tags for rollback. Update READMEs/templates/examples with public API changes. Follow [migration documentation](docs/MIGRATING_TO_1_0.md).

Tests must cover AG-UI Python/TypeScript contracts, independent backends, browser thread lifecycle, replay/migration, arbitrary models, cost unknown/zero/partial handling and minimal/extra installed packages. No new feature is required for 1.0; additions belong in a separate 1.1 proposal.

MIT — Copyright (c) 2026 Siili Solutions Oyj.
