# Migrating to Spaik 1.0

Spaik 1.0 replaces the custom block protocol with official AG-UI messages and events. This guide covers the breaking changes and how to move existing applications and stored threads.

| | 0.11.x (legacy) | 1.0 |
| --- | --- | --- |
| Python | 3.10+ | 3.11+ |
| `spaik-sdk-react` / `spaik-sdk-material` | 0.x, legacy Spaik protocol | 1.0, AG-UI |
| `spaik-coding-agents` | Final 0.2.3, pins `spaik-sdk==0.11.1` | Not supported |
| `spaik-agent-workflows` | Final 0.3.2, pins `spaik-sdk==0.11.1` | Not supported |

## Runtime

Spaik 1.0 requires Python 3.11 or later. Python 3.10 fails to propagate nested async model callbacks in the upstream agent execution path, which can produce an empty streamed transcript. The previous event-loop workaround is removed. See [LangGraph async streaming requirements](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/streaming.mdx).

## Models

`ModelRegistry` presets and `LLMModel` work as before, and the registry no longer limits which models you can use. Choose a model in one of these ways, in order of preference:

1. A preset: `llm_model=ModelRegistry.CLAUDE_SONNET_5_5`, or an alias with `ModelRegistry.from_name("sonnet")`.
2. A model without a preset: `llm_model=LLMModel(family="anthropic", name="claude-new-model", reasoning=True)`. Its family's reasoning and token settings apply whichever provider hosts it.
3. A plain string ID with an explicit provider: `llm_model="your-model-id", provider="openai"`. An ID that matches a preset uses that preset's settings; any other ID uses provider defaults.

`provider_kwargs` override every setting. Spaik providers build all models for the providers they know; other provider names go through LangChain's `init_chat_model`. As a last resort, `chat_model=` accepts a fully configured LangChain model, which bypasses environment defaults and Spaik's model settings; do not combine it with `llm_model` or `llm_config`. Install only the provider extra you use, such as `spaik-sdk[openai,server]`.

`LLMConfig.temperature` now defaults to the provider's own default and is sent only when you set it; 0.x sent 0.1 to models without reasoning. Remove `temperature` for reasoning models, which reject it. `LLMConfig.tool_usage` is removed. `streaming=False` disables model streaming for every provider.

Azure deployment names are supplied as model IDs or provider kwargs; per-model deployment environment variables have been removed. Existing proxy authentication remains available.

## Messages and runs

`get_response()`/`get_response_async()` now return official AG-UI assistant messages; use `.content` or `message_text(message)` instead of `.blocks` or `.get_text_content()`. Streaming methods yield official AG-UI events. Replace `/messages/stream` with `/threads/{id}/runs`, `RunAgentInput`, and an official `HttpAgent`. Legacy block/event schemas and custom stream framing are removed.

The backend owns history. Clients may submit existing unchanged messages and new user messages. IDs deduplicate unchanged input; conflicting IDs, changed history, reused run IDs and overlapping runs are rejected. Thread ownership exists at creation, including empty threads. Private system prompts/provider replay data are omitted from GET responses. Server-owned display metadata lives in `message.metadata.spaik` so snapshots carry timestamps, authors, and attachments; preserve message metadata verbatim when submitting history.

The built-in runner coordinates one server process: use one worker per repository. Application integrations must supply distributed run coordination if using multiple workers. Client-side tool execution and interrupt resume are not implemented by this convenience runner; other AG-UI backends may implement them.

## Costs

`get_cost()` returns `CostSummary | None` from persisted invocation records. `totals` is keyed by currency; `complete` is false if any invocation cost is missing. Token usage stays available regardless of cost availability. There are no price tables or inferred costs. Missing charges log a deduplicated console message and never prevent a response. OpenRouter uses response `usage.cost`, falling back to one cached generation lookup. Aggregate provider billing reports are not request-level charges.

## Storage and integrations

Spaik 1.0 stores threads as versioned JSON (`ThreadContainer.to_dict()`, with `schema_version`). 1.0 cannot read pickles. For threads in your own database, see [Threads in your own database](#threads-in-your-own-database); for the built-in local file store, see [Local file store](#local-file-store). Back up original data before switching applications.

Tavily's bundled search helper, Azure Functions queue helpers and SignalR streaming negotiation have been removed. Supply application-owned tools through ToolProvider, and use AG-UI HTTP streaming. MCP, provider SDKs, server and audio are optional extras.

Coding-agent wrappers (`spaik-coding-agents`, final 0.2.3) and YAML workflows (`spaik-agent-workflows`, final 0.3.2) are deprecated and removed from 1.0. Both require `spaik-sdk==0.11.1` and cannot be installed in the same environment as Spaik 1.0; keep existing usage in a separate legacy environment. There is no 1.0 replacement package: orchestrate steps in application code with `BaseAgent` and `ToolProvider`. Published artifacts and the `spaik-coding-agents-v0.2.3` and `spaik-agent-workflows-v0.3.2` source tags remain available.

## React and Material

The conversation model is AG-UI `Message`. Use `AgentChat agent={new HttpAgent(...)}` for another AG-UI backend or `AgentChat baseUrl="..."` for Spaik's managed threads. A custom `ThreadRepository` plus `createAgent(threadId)` integrates other persistence backends. Sidebar requires a repository. The official AG-UI client owns message and run state; hooks subscribe to it. Use `renderMessage` and `renderState` for custom presentation.

## Threads in your own database

Applications that store threads in SQL, Cosmos DB or similar keep their data where it is. Spaik 1.0 converts legacy threads when it reads them, so no batch job or downtime is needed:

1. **Read both formats.** In your `BaseThreadRepository.load_thread`, pass the stored JSON to `load_thread_data`:

   ```python
   from spaik_sdk.thread.migration import load_thread_data

   thread = load_thread_data(row_json, fallback_owner=row.user_id)
   ```

   Data with `schema_version` loads as 1.0. Legacy data, `{"id", "messages": [ThreadMessage.to_dict(), ...], "system_prompt", "last_activity_time"}`, is converted in memory. If you stored message rows separately, build this dict from them. The owner is the first user message's author; `fallback_owner` applies to threads without one.
2. **Write 1.0 data to a new column or container**, for example `data_v1`, and read `data_v1` first, falling back to the legacy column. Legacy rows are never overwritten, so you can roll back to 0.11 at any time. Drop the legacy column once you no longer need rollback.
3. **Optionally convert everything up front** from your existing migration pipeline, by calling the same function on each row and writing `thread.to_dict()` to the new column. It is safe to re-run: rows with `schema_version` are already done.

If you stored pickled `ThreadContainer` objects, 1.0 cannot read them. Run a job in an environment with `spaik-sdk==0.11.1` that unpickles each row and calls `export_thread` from [scripts/export_legacy_threads.py](../scripts/export_legacy_threads.py); store its JSON output and continue from step 1.

## Local file store

In a separate environment containing `spaik-sdk==0.11.1`, run:

```sh
python scripts/export_legacy_threads.py old-data export.json
```

Only export your own trusted legacy pickle store. Under 1.0, import to a new directory:

```sh
python -m spaik_sdk.thread.migration export.json new-data
```

The export contains attachment references, not file bytes. Copy a local file store to the new location, keeping IDs and metadata intact:

```sh
cp -R old-data/files new-data/files
```

Configure `ApiBuilder.stateful(..., file_storage=LocalFileStorage("new-data/files"))` to read the copied store. For remote file storage, retain the application's existing storage mapping. The default local file store remains `data/files`; explicitly select the copied location when migrating.

Supply `--empty-owner USER_ID` if a legacy thread has no user message. Existing destination IDs are rejected. Original IDs, ordering, authors, timestamps, attachments and tool-provider references are preserved; legacy block IDs are retained as metadata. Reasoning/tool results become canonical AG-UI messages. Signatures absent from legacy persistence cannot be reconstructed. Historical token counts are retained; historical price-table estimates are not imported as reported charges.
