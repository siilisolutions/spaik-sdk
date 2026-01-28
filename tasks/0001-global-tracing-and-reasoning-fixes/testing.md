# Testing Plan

## Unit Tests

### NoOpTraceSink
- [ ] Calling save_trace does not throw and has no side effects
- [ ] Calling save_trace with any combination of parameters succeeds silently

### configure_tracing Function
- [ ] After calling configure_tracing with a custom sink, get_trace_sink returns that sink
- [ ] Calling configure_tracing multiple times replaces the previous sink
- [ ] Calling configure_tracing with None clears the global sink (reverts to default behavior)

### get_trace_sink Resolution
- [ ] When TRACE_SINK_MODE=local env var is set, returns LocalTraceSink regardless of global config
- [ ] When TRACE_SINK_MODE=noop env var is set, returns NoOpTraceSink regardless of global config
- [ ] When TRACE_SINK_MODE is unset and global sink is configured, returns the global sink
- [ ] When TRACE_SINK_MODE is unset and no global sink configured, returns NoOpTraceSink
- [ ] When TRACE_SINK_MODE is set to invalid value, falls through to global/no-op (no error)
- [ ] Env var LOCAL takes precedence over configure_tracing (escape hatch works)
- [ ] Env var NOOP takes precedence over configure_tracing

### TraceSink Interface
- [ ] save_trace method accepts agent_instance_id parameter
- [ ] LocalTraceSink ignores agent_instance_id (file naming unchanged)
- [ ] Custom TraceSink implementations receive agent_instance_id in save_trace calls

### AgentTrace
- [ ] Constructor accepts agent_instance_id parameter
- [ ] When save is called, agent_instance_id is passed to TraceSink.save_trace
- [ ] AgentTrace created without instance_id generates its own UUID (backward compatibility)

### BaseAgent Instance ID
- [ ] Each BaseAgent instance has a unique agent_instance_id
- [ ] Two agents created from same class have different instance IDs
- [ ] The agent_instance_id is passed to AgentTrace during construction

### GoogleModelFactory Reasoning
- [ ] When config.reasoning is True, thinking_budget is set to configured value
- [ ] When config.reasoning is False, thinking_budget is explicitly set to 0
- [ ] When config.reasoning is False, include_thoughts is not set (or set to False)

### OpenAIModelFactory Reasoning
- [ ] Factory checks config.reasoning (user preference), not config.model.reasoning (capability)
- [ ] When reasoning=False on GPT-5.1 model, reasoning effort is set to "none"
- [ ] When reasoning=False on GPT-5.1-codex model, reasoning effort is set to "none"
- [ ] When reasoning=False on GPT-5.2 model, reasoning effort is set to "none"
- [ ] When reasoning=False on GPT-5 model, reasoning effort is set to "minimal"
- [ ] When reasoning=False on GPT-5-mini model, reasoning effort is set to "minimal"
- [ ] When reasoning=False on GPT-5-nano model, reasoning effort is set to "minimal"
- [ ] When reasoning=True, existing behavior unchanged (Responses API enabled, effort configurable)

### EnvConfig Trace Sink Mode
- [ ] get_trace_sink_mode returns None when TRACE_SINK_MODE env var is not set
- [ ] get_trace_sink_mode returns TraceSinkMode.LOCAL when env var is "local"
- [ ] get_trace_sink_mode handles empty string as unset

### TraceSinkMode
- [ ] from_name returns LOCAL for "local" string
- [ ] from_name returns NOOP for "noop" string
- [ ] from_name returns None for empty string
- [ ] from_name returns None for unset/None input

## Integration Tests

**Note**: Most integration tests require API keys. Focus on unit tests with mocked responses where possible. Integration tests are optional and run only when API keys are available.

### Global Tracing Configuration Flow (no API keys needed)
- [ ] Configure custom trace sink at startup, create multiple agents, verify all use the custom sink
- [ ] Configure custom sink, set TRACE_SINK_MODE=local, verify LocalTraceSink is used instead
- [ ] Configure custom sink, set TRACE_SINK_MODE=noop, verify NoOpTraceSink is used
- [ ] Create agents without any tracing config, verify no filesystem writes occur (no-op behavior)

### Agent Instance ID Correlation (no API keys needed)
- [ ] Create agent, verify instance ID is set
- [ ] Create two agents of same class, verify instance IDs differ
- [ ] Custom trace sink receives correct instance ID for correlation (mock sink)

### API-Dependent Tests (optional, skipped without keys)
These tests verify actual API behavior and should be skipped when API keys are unavailable:
- [ ] Google Gemini: verify API call includes thinking_budget=0 when reasoning=False
- [ ] OpenAI GPT-5.1: verify API call sets reasoning effort to "none" when reasoning=False
- [ ] OpenAI GPT-5: verify API call sets reasoning effort to "minimal" when reasoning=False

## Browser/E2E Tests
Not applicable - this is backend/library code with no UI components.

## Manual Testing
**Minimal** - API-dependent integration tests may be run manually when keys are available. Unit tests must be automated.
