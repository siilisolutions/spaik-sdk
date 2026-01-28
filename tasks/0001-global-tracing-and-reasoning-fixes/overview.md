# Global Tracing Configuration and Reasoning Fixes

This task addresses two related issues in the SDK:

1. **Global tracing configuration** - Enable users to configure a trace sink once at application startup that applies to all agents, with proper precedence (env var LOCAL → global sink → no-op default).

2. **Reasoning disable fixes** - Ensure that setting `reasoning=False` in the BaseAgent constructor actually disables reasoning for Google Gemini and OpenAI GPT-5.x models.

Additionally, introduces agent instance IDs (UUIDs) for trace correlation in observability backends.

## Sub-tasks

| Step | Title | Done | Description |
|------|-------|------|-------------|
| [001](001.md) | Add NoOpTraceSink and global tracing configuration | [x] | Create NoOpTraceSink, add configure_tracing function, update get_trace_sink resolution logic |
| [002](002.md) | Add agent instance ID to tracing | [ ] | Generate UUID in BaseAgent, pass through AgentTrace to TraceSink interface |
| [003](003.md) | Fix Google Gemini reasoning disable | [ ] | Set thinking_budget=0 when reasoning=False in GoogleModelFactory |
| [004](004.md) | Fix OpenAI reasoning disable | [ ] | Check config.reasoning instead of model capability, set appropriate effort level per model version |
| [005](005.md) | Update env config defaults | [ ] | Change TRACE_SINK_MODE default from "local" to unset, handle gracefully in TraceSinkMode |
