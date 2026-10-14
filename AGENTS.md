# AGENTS.md

Guidance for assistants working on Spaik SDK.

## Product and architecture

Spaik's core is thread management and a reusable React/Material UI kit. Canonical transcripts and frontend events use official AG-UI types. Retain BaseAgent/tool convenience, structured responses, streaming, cancellation, attachments/audio, recording and tracing. Avoid price tables, model eligibility lists, duplicate stream parsers and renderer implementations.

- `packages/agent-sdk/spaik_sdk/agent/base_agent.py`: BaseAgent and AG-UI lifecycle.
- `thread/`: canonical messages, private replay metadata, versioned envelope and migration.
- `llm/langchain_service.py`: LangChain -> AG-UI execution; every model invocation records usage/reported charges.
- `models/`: `LLMModel` describes every model (presets, custom models and plain IDs). `family_settings.py` applies per-family reasoning/token settings by `model.family`, never by registry membership; Spaik providers build every model they know. Provider kwargs override; `chat_model` injection is a last resort.
- `llm/cost/`: provider-reported charge resolver; absent charge is None with a console message. Never infer price or zero.
- `server/api/routers/`: authorized thread CRUD, `/threads/{id}/runs` SSE, cancellation/files/audio.
- `packages/agent-sdk-hooks`: official AG-UI client state plus optional ThreadRepository, selection/uploads/audio.
- `packages/agent-sdk-material`: shared themed UI; examples/templates consume it.
- Deprecated and removed in 1.0: `spaik-coding-agents` (final 0.2.3) and `spaik-agent-workflows` (final 0.3.2), both pinned to SDK 0.11.1.

## Commands

Python: `cd packages/agent-sdk; uv sync --all-extras --dev --locked`, `make test-unit`, `make test-integration`, `make lint`, `make typecheck`. Ruff configuration enables fixes; use `ruff check --no-fix` for read-only inspection.

Frontend: root `bun install`, `bun run build:packages`, `bun test packages/agent-sdk-hooks/tests`, `bunx playwright test`. Package `bun run type-check`/`lint` are available. Examples run with root `bun run dev:backend`/`dev:frontend`.

## Usage

```python
from spaik_sdk import BaseAgent, LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
agent = BaseAgent(system_prompt="Be helpful.", llm_model=ModelRegistry.CLAUDE_SONNET_5_5)
# Or llm_model=LLMModel(family="openai", name="new-model-id"), or llm_model="any-id", provider="openai".
print(agent.get_response_text("Hello"))
```

AG-UI assistant messages expose `.content`; use `message_text(message)` to extract display text. ToolProvider history hooks receive `ToolCallHistory`, preserving provider-owned markers/custom replay without losing UI tool transcripts. Provider SDKs and server/audio/MCP are optional extras and must be imported lazily.

Keep ownership authoritative from thread creation. Reject overwriting stored messages, conflicting IDs and overlapping runs; save tool/model checkpoints and partial output on cancellation/disconnect. Never expose private replay/system prompts through thread APIs. Built-in coordination is single-process; applications own distributed integrations.

## Package-specific instructions

Nested `AGENTS.md` files hold the rules for each area. Before editing files in one of these directories, read its file, even if your tool only loads this root file:

- [packages/agent-sdk/AGENTS.md](packages/agent-sdk/AGENTS.md): Python style, logging, tests.
- [packages/agent-sdk-hooks/AGENTS.md](packages/agent-sdk-hooks/AGENTS.md): React/TypeScript conventions for the hooks package.
- [examples/frontend/AGENTS.md](examples/frontend/AGENTS.md): example app conventions.
- `templates/{agent,server,frontend}/AGENTS.md`: instructions shipped to projects created from the templates. Keep them in sync with public API changes.

Skills live in `.agents/skills` (`.claude/skills` links to it). To add or change model presets, follow [model-update](.agents/skills/model-update/SKILL.md).

## Work and release discipline

Work on branches and commit each validated chunk with its docs. Update READMEs/templates/examples with public API changes and record breaking changes in [the migration guide](docs/MIGRATING_TO_1_0.md).

Each package has its own manual release workflow on main: `release-agent-sdk.yml`, `release-hooks.yml` and `release-material.yml`. Each bumps the version (patch/minor/major), runs checks, publishes, then commits the bump and tags it. Tick *prerelease* to publish a release candidate (`1.0.0rc1`, npm `1.0.0-rc.1` under the `next` tag); running again with it ticked gives the next RC, and unticked publishes the final version. Release hooks before Material, which peer-depends on it. Keep legacy tags for rollback.

Tests must cover AG-UI Python/TypeScript contracts, independent backends, browser thread lifecycle, replay/migration, arbitrary models, cost unknown/zero/partial handling and minimal/extra installed packages.

MIT — Copyright (c) 2026 Siili Solutions Oyj.
