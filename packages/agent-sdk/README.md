# spaik-sdk

Python 3.11+ thread management and agent convenience using canonical AG-UI messages/events. Upgrading from 0.x? See the [migration guide](../../docs/MIGRATING_TO_1_0.md).

```python
from spaik_sdk import BaseAgent, LLMModel
from spaik_sdk.models.model_registry import ModelRegistry

agent = BaseAgent(system_prompt="Be helpful.", llm_model=ModelRegistry.CLAUDE_SONNET_5_5)
# A model without a preset: llm_model=LLMModel(family="anthropic", name="claude-new-model")
# A plain ID with an explicit provider: llm_model="my-deployment", provider="azure"
print(agent.get_response_text("Hello"))
```

Every model is an `LLMModel`: a family, the exact API ID and capability flags (`reasoning`, `reasoning_min_effort`, `prompt_caching`). Reasoning and token settings come from the model's family, whichever provider hosts it, so a preset, an `LLMModel` with the same name and the same string ID build the same model. A string that matches no preset uses provider defaults; opt into reasoning with `LLMModel(..., reasoning=True)`. `provider_kwargs` override everything except the model ID. `temperature` is sent only when set.

Spaik providers build every model for the providers they know, including credentials and proxy mode. Other provider names go through LangChain's `init_chat_model`, and `chat_model=` accepts a fully configured LangChain model as a last resort. Current aliases for `ModelRegistry.from_name` are `sonnet`, `opus`, `haiku`, `fable`, `gpt` and `gemini flash`.

## Tools and agent methods

Subclass `ToolProvider.get_tools()` to supply LangChain `BaseTool` objects or pass `tools` directly. Application-owned search tools can use any service; the bundled Tavily helper is removed. `persist_tool_block_history=False` keeps a tool marker in model replay while retaining the full UI transcript. `render_tool_block_for_history(ToolCallHistory)` customizes replay; its argument is now a tool-history record rather than a message block.

- `get_response_text()` / `get_response_text_async()` return final text.
- `get_response()` / `get_response_async()` return an AG-UI `AssistantMessage`.
- `get_event_stream()` / `get_response_stream()` yield AG-UI events.
- `get_structured_response()` / `get_structured_response_async()` return the supplied Pydantic schema and collect raw usage/costs. They use the model's minimum reasoning by default; raise it per call with `reasoning_effort="high"` or for every call with `LLMConfig(structured_reasoning_effort=...)`.
- `spawn()` / `run_isolated()` isolate nested agent callback contexts.
- `get_langchain_model()` and `get_react_agent()` expose configured LangChain/LangGraph integrations.
- `run_cli()` supplies a minimal interactive console without additional CLI dependencies.
- `get_cost()` reads recorded charges; it never calls billing APIs.

`thread_container.messages` contains official AG-UI messages. `message_text(message)` extracts text. A versioned persistence envelope holds owners, timestamps, attachments, invocation usage/costs and private provider replay data. Signed reasoning and provider-required response data stay separate from display messages.

## Server, storage, and optional dependencies

`ApiBuilder.local(agent=...)` supplies thread CRUD, `/threads/{id}/runs` SSE, cancellation and file routes. `ApiBuilder.stateful(repository, authorizer, agent=...)` injects persistence/authorization; `agent_factory(thread)` constructs application-specific agents. Empty threads have owners. The built-in runner coordinates a single process per repository; use an application integration for distributed workers. It executes backend tools; client tool execution and interrupt resume are outside its current convenience contract.

Install extras as needed: `[server]`, `[openai]`, `[anthropic]`, `[google]`, `[azure]`, `[ollama]`, `[deepseek]`, `[mistral]`, `[cohere]`, `[xai]`, `[audio]`, `[mcp]`, `[dev]`. Audio helpers use HTTP directly. Core does not import optional model integrations eagerly.

Local persistence uses JSON at `data-v1/threads`. Application repositories read stored threads with `spaik_sdk.thread.migration.load_thread_data`, which also converts legacy 0.x JSON in memory. Legacy local pickle stores are exported in the old SDK environment and imported with `python -m spaik_sdk.thread.migration export.json new-data-dir`. See the [migration guide](../../docs/MIGRATING_TO_1_0.md) for both.

## Provider-reported costs

`CostProvider.resolve(CostContext)` returns a reported charge or `None`. OpenRouter reads response usage and performs at most one cached generation lookup when needed. Charges have currency; aggregate `CostSummary.totals` preserves currencies, and `complete` is false when charges are missing. Unknown costs never become zero. Account-level billing reports and token-price estimates are not used. Token usage remains available independently.

## Development

```sh
uv sync --all-extras --dev --locked
make test-unit
make test-integration
make lint
make typecheck
```

Unit tests are deterministic. Integration tests cover persistence, usage and optional MCP; live provider smoke checks are a separate release gate. The repository's frontend tests consume Python-produced AG-UI SSE and exercise both Spaik and an independent backend.
