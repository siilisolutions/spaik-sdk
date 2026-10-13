# Spaik SDK

Thread management, agent convenience, and a reusable React/Material chat UI built on [AG-UI](https://docs.ag-ui.com).

**This branch prepares 1.0.** Stable publication is gated by the [implementation plan](docs/SPAIK_1_0_PLAN.md). The catalog/deprecation work is isolated on `chore/pre-1-model-refresh`; breaking changes are on `feat/spaik-1-ag-ui`.

## Python agent

Use Python 3.11+ and install the provider you use; provider SDKs are optional:

```sh
pip install 'spaik-sdk[openai,server]'
```

```python
from spaik_sdk import BaseAgent

agent = BaseAgent(
    system_prompt="You are a helpful assistant.",
    llm_model="your-provider-model-id",
    provider="openai",
    provider_kwargs={"temperature": 0.2},
)
print(agent.get_response_text("Hello"))
```

Alternatively pass `chat_model=YourLangChainChatModel(...)`. Optional `ModelRegistry` presets select sensible defaults; model IDs never need catalog membership. Configure an Azure deployment by its actual deployment ID and Azure provider kwargs, rather than per-model environment variables.

The SDK retains ToolProvider/LangChain tools, structured responses, cancellation, attachments, audio, recording, tracing, isolated `spawn()`, and the optional code-first orchestrator. `get_response()` returns an AG-UI assistant message; streaming methods yield official AG-UI events.

## Managed threads

```python
from fastapi import FastAPI
from spaik_sdk.server.api.routers.api_builder import ApiBuilder

app = FastAPI()
api = ApiBuilder.local(agent=agent)
app.include_router(api.build_thread_router())
app.include_router(api.build_file_router())
# Install [audio] and configure provider credentials to enable speech routes.
app.include_router(api.build_audio_router())
```

Threads have explicit owners from creation. Storage, authorization and agent factories are replaceable. The local runner supports one server process per repository; distributed execution is an application integration.

Thread routes: create/list/read/delete under `/threads`, AG-UI `POST /threads/{id}/runs`, and `POST /threads/{id}/cancel`. Stored history is authoritative. Runs reject conflicting message IDs, history edits and overlapping execution; cancellation/disconnect saves partial output. Local persistence uses versioned JSON under `data-v1`.

## React UI

```tsx
import { AgentChat, AgentThemeProvider } from 'spaik-sdk-material';

export function App() {
  return <AgentThemeProvider><AgentChat baseUrl="http://localhost:8000" /></AgentThemeProvider>;
}
```

For another AG-UI backend, supply `agent={new HttpAgent({ url, threadId })}`. Thread persistence is optional: use a `ThreadRepository` and `createAgent(threadId)` when needed. The UI supports text, tools/results, reasoning summaries, state, attachments, speech, cancellation, themes and custom renderers. Examples/templates consume this shared kit.

## Usage and costs

Token usage comes from provider responses. Charges come from provider-reported metadata or a supported request-level API; Spaik maintains no price tables. `get_cost()` returns `CostSummary | None`, with totals per currency and completeness information. Missing cost prints a deduplicated console message and does not fail inference. OpenRouter response charges and cached generation lookup are supported; organization billing totals are not attributed to threads.

## Packages and development

- [`spaik-sdk`](packages/agent-sdk/README.md): Python threads, agents, server and optional integrations.
- [`spaik-sdk-react`](packages/agent-sdk-hooks/README.md): AG-UI hooks and optional thread management.
- [`spaik-sdk-material`](packages/agent-sdk-material/README.md): themeable chat components.
- [`spaik-agent-workflows`](packages/agent-workflows/README.md): optional YAML workflow convenience.
- [`spaik-coding-agents`](packages/coding-agents/README.md): deprecated legacy integration, pinned to SDK 0.11.1; no 1.0 compatibility.

```sh
bun install
bun run build:packages
bun test packages/agent-sdk-hooks/tests
bunx playwright test
cd packages/agent-sdk
uv sync --all-extras --dev --locked
make test-unit
make lint
make typecheck
```

Use `bun run dev:backend` and `bun run dev:frontend` for the example application. Supply `DEFAULT_MODEL` and `MODEL_PROVIDER` for environment-selected models. Direct mode uses the relevant provider key; proxy mode retains `LLM_AUTH_MODE=proxy`, `LLM_PROXY_BASE_URL`, `LLM_PROXY_API_KEY`, and `LLM_PROXY_HEADERS`.

See the [migration guide](docs/MIGRATING_TO_1_0.md), [catalog verification](docs/MODEL_REFRESH_2026_10.md), and [release plan](docs/SPAIK_1_0_PLAN.md), and [validation results](docs/1_0_VALIDATION.md).

MIT — Copyright (c) 2026 Siili Solutions Oyj. An open-source project by Siili engineers, not an official Siili product.
