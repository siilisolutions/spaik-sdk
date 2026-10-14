# Spaik SDK

Thread management, agent convenience, and a reusable React/Material chat UI built on [AG-UI](https://docs.ag-ui.com).

Upgrading from 0.x? See the [migration guide](docs/MIGRATING_TO_1_0.md).

## Python agent

Use Python 3.11+ and install the provider you use; provider SDKs are optional:

```sh
pip install 'spaik-sdk[openai,server]'
```

```python
from spaik_sdk import BaseAgent, LLMModel
from spaik_sdk.models.model_registry import ModelRegistry

agent = BaseAgent(system_prompt="You are a helpful assistant.", llm_model=ModelRegistry.GPT_6_1_SOL)
print(agent.get_response_text("Hello"))

# A model without a preset: describe it, and Spaik applies its family's settings.
agent = BaseAgent(
    system_prompt="You are a helpful assistant.",
    llm_model=LLMModel(family="openai", name="your-model-id", reasoning=True),
)
```

A plain string ID with an explicit `provider` also works; it uses the preset's settings when the ID matches one and provider defaults otherwise. `provider_kwargs` override everything. Configure an Azure deployment by its actual deployment ID and Azure provider kwargs, rather than per-model environment variables.

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

Deprecated legacy packages, removed from the 1.0 line: `spaik-coding-agents` (final 0.2.3) and `spaik-agent-workflows` (final 0.3.2). Both pin `spaik-sdk==0.11.1`, have no 1.0 compatibility and must be installed in a separate environment. Their source remains in the legacy release tags.

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

MIT — Copyright (c) 2026 Siili Solutions Oyj. An open-source project by Siili engineers, not an official Siili product.
