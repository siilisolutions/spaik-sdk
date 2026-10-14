# Migrating to Spaik 1.0

This branch is an unreleased migration. The release gates in [the implementation plan](SPAIK_1_0_PLAN.md) must pass before publishing stable packages.

## Runtime

Spaik 1.0 requires Python 3.11 or later. Python 3.10 fails to propagate nested async model callbacks in the upstream agent execution path, which can produce an empty streamed transcript. The previous event-loop workaround is removed. See [LangGraph async streaming requirements](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/streaming.mdx).

## Models

Presets are conveniences, not an eligibility list. Pass any model ID with `BaseAgent(system_prompt="...", llm_model="your-model-id", provider="openai", provider_kwargs={...})`, or inject `chat_model=YourLangChainModel(...)`. An injected model bypasses environment defaults and catalog lookup. Do not combine injection with llm_model/llm_config. Explicit provider kwargs override preset defaults. Install only the provider extra you use, such as `spaik-sdk[openai,server]`.

Azure deployment names are supplied as model IDs or provider kwargs; per-model deployment environment variables have been removed. Existing proxy authentication remains available. Provider-specific capabilities belong in provider kwargs for arbitrary IDs.

## Messages and runs

`get_response()`/`get_response_async()` now return official AG-UI assistant messages; use `.content` or `message_text(message)` instead of `.blocks` or `.get_text_content()`. Streaming methods yield official AG-UI events. Replace `/messages/stream` with `/threads/{id}/runs`, `RunAgentInput`, and an official `HttpAgent`. Legacy block/event schemas and custom stream framing are removed.

The backend owns history. Clients may submit existing unchanged messages and new user messages. IDs deduplicate unchanged input; conflicting IDs, changed history, reused run IDs and overlapping runs are rejected. Thread ownership exists at creation, including empty threads. Private system prompts/provider replay data are omitted from GET responses. Server-owned display metadata lives in `message.metadata.spaik` so snapshots carry timestamps, authors, and attachments; preserve message metadata verbatim when submitting history.

The built-in runner coordinates one server process: use one worker per repository. Application integrations must supply distributed run coordination if using multiple workers. Client-side tool execution and interrupt resume are not implemented by this convenience runner; other AG-UI backends may implement them.

## Costs

`get_cost()` returns `CostSummary | None` from persisted invocation records. `totals` is keyed by currency; `complete` is false if any invocation cost is missing. Token usage stays available regardless of cost availability. There are no price tables or inferred costs. Missing charges log a deduplicated console message and never prevent a response. OpenRouter uses response `usage.cost`, falling back to one cached generation lookup. Aggregate provider billing reports are not request-level charges.

## Storage and integrations

Local storage writes versioned JSON to `data-v1`, separate from legacy pickle files. Never point a new install at an old store expecting automatic unpickling. Export under SDK 0.11.x, then import into a new directory under 1.0. Back up original data before switching applications.

Tavily's bundled search helper, Azure Functions queue helpers and SignalR streaming negotiation have been removed. Supply application-owned tools through ToolProvider, and use AG-UI HTTP streaming. MCP, provider SDKs, server and audio are optional extras.

Coding-agent wrappers (`spaik-coding-agents`, final 0.2.3) and YAML workflows (`spaik-agent-workflows`, final 0.3.2) are deprecated and removed from 1.0. Both require `spaik-sdk==0.11.1` and cannot be installed in the same environment as Spaik 1.0; keep existing usage in a separate legacy environment. There is no 1.0 replacement package: orchestrate steps in application code with `BaseAgent` and `ToolProvider`. See [the legacy release notes](MODEL_REFRESH_2026_10.md). Published artifacts and tagged legacy source remain available.

## React and Material

The conversation model is AG-UI `Message`. Use `AgentChat agent={new HttpAgent(...)}` for another AG-UI backend or `AgentChat baseUrl="..."` for Spaik's managed threads. A custom `ThreadRepository` plus `createAgent(threadId)` integrates other persistence backends. Sidebar requires a repository. The official AG-UI client owns message and run state; hooks subscribe to it. Use `renderMessage` and `renderState` for custom presentation.

### Legacy export/import commands

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
