# Requirements

## Problem Statement

The SDK has two related issues that make it difficult to use in production:

1. **Tracing cannot be configured globally** - Each agent instance creates its own trace sink, and there's no way to set a global tracing provider for all agents. Library users need to either pass `trace_sink` to every agent constructor or rely on environment variables that only support a limited set of modes. For production observability (Datadog, OpenTelemetry, custom backends), users need a way to configure tracing once at application startup.

2. **Setting `reasoning=False` doesn't actually disable reasoning for some providers** - When users explicitly disable reasoning in the BaseAgent constructor, it doesn't translate to the correct API calls for certain providers, particularly Google Gemini models which require an explicit parameter to disable thinking rather than just omitting the enable parameter.

Additionally, there's no way to correlate traces across multiple calls to the same agent instance, as agents are only identified by class name rather than a unique instance identifier.

## Success Criteria

### Global Tracing Configuration
- [ ] Users can call a single function at application startup to configure tracing for all agents
- [ ] The configured trace sink is used by all subsequently created agents without needing to pass it to each constructor
- [ ] Environment variable `TRACE_SINK_MODE=local` overrides any programmatically configured sink (escape hatch for local debugging)
- [ ] When no tracing is configured (no env var, no global sink), tracing is silently disabled (no-op) rather than writing to filesystem
- [ ] The default behavior changes from writing to filesystem to no-op

### Agent Instance Identification
- [ ] Each agent instance gets a unique identifier (UUID) upon construction
- [ ] This identifier is available to trace sinks for correlation purposes
- [ ] The local filesystem trace sink can ignore this identifier (existing behavior unchanged)
- [ ] Custom trace sinks receive the instance ID to enable correlation in observability backends

### Reasoning Disable Fixes
- [ ] Setting `reasoning=False` on a Google Gemini agent actually disables thinking/reasoning
- [ ] Setting `reasoning=False` on an OpenAI GPT-5.1+ agent actually disables reasoning
- [ ] Setting `reasoning=False` on an OpenAI GPT-5/5-mini/5-nano agent sets reasoning to minimal effort (the lowest available) since full disable is not supported by the API
- [ ] The OpenAI factory checks the user's `reasoning` preference, not just whether the model supports reasoning

## Constraints

- This is library code - users import it into their applications, so global configuration must be explicit (called by user code) rather than automatic
- Must maintain backward compatibility with existing TraceSink implementations
- The precedence order for trace sink resolution must be: env var LOCAL → global configured sink → no-op
- Cannot fully disable reasoning on GPT-5 base models (API limitation) - must use minimal effort as best alternative

## Non-Goals

- Adding new TraceSinkMode enum values for no-op (no-op is the fallback, not a mode)
- Supporting per-async-context trace sinks (single global is sufficient)
- Runtime switching of trace sinks after initial configuration
- Supporting o1/o3 models (considered legacy)
- Adding a "reset to default" function for tracing configuration
