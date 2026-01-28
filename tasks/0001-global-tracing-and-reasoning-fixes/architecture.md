# Architecture

## Components Affected

### Tracing Module (`spaik_sdk/tracing/`)

**get_trace_sink.py**
- Currently returns `LocalTraceSink` when mode is LOCAL, throws otherwise
- Needs to check for a globally configured sink before falling back
- Needs to return a no-op sink as the final fallback instead of throwing
- Resolution order changes to: LOCAL env var → global sink → no-op

**New: NoOpTraceSink**
- A new TraceSink implementation that does nothing when `save_trace` is called
- Serves as the silent default when no tracing is configured

**New: Global sink registry**
- Module-level storage for a user-configured TraceSink
- A public function to set this global sink (called once at app startup)
- The `get_trace_sink` function checks this registry

**trace_sink.py (TraceSink interface)**
- The `save_trace` method signature needs an additional parameter for agent instance ID
- Existing implementations must be updated to accept this parameter (LocalTraceSink ignores it)

**agent_trace.py (AgentTrace class)**
- Constructor needs to accept an agent instance ID parameter
- Stores the instance ID and passes it through to TraceSink.save_trace calls

**__init__.py**
- Export the new `configure_tracing` function for users to call

### Config Module (`spaik_sdk/config/`)

**env.py**
- The `get_trace_sink_mode` method currently defaults to "local"
- Needs to handle the case where TRACE_SINK_MODE is unset (return None or a sentinel value)
- The `get_trace_sink` function will interpret unset as "use global or no-op"

**trace_sink_mode.py**
- The `from_name` method needs to handle empty/unset values gracefully
- Should return None when the env var is not set rather than throwing

### Agent Module (`spaik_sdk/agent/`)

**base_agent.py**
- Constructor needs to generate a UUID for the agent instance
- Pass this UUID to AgentTrace during construction
- Store as `self.agent_instance_id` for potential external access

### Model Factories (`spaik_sdk/models/factories/`)

**google_factory.py**
- Currently only sets `thinking_budget` when reasoning is enabled
- When `config.reasoning` is False, must explicitly set `thinking_budget=0` to disable thinking
- Gemini models think by default, so omitting the parameter doesn't disable it

**openai_factory.py**
- Currently checks `config.model.reasoning` (model capability) instead of `config.reasoning` (user preference)
- Must check `config.reasoning` to respect user's explicit disable request
- When reasoning is disabled on GPT-5.1+ models, set reasoning effort to "none"
- When reasoning is disabled on GPT-5 base models (5, 5-mini, 5-nano), set reasoning effort to "minimal" (full disable not supported by API)
- Need to distinguish between model versions to apply correct effort level

**anthropic_factory.py**
- No changes needed - already correctly handles reasoning=False by not passing thinking config

**ollama_factory.py**
- No changes needed - already passes reasoning flag through correctly

## New Entities

### NoOpTraceSink
- Implements TraceSink interface
- `save_trace` method does nothing (empty implementation)
- Used as default when no tracing is configured

### configure_tracing function
- Public API for setting the global trace sink
- Takes a TraceSink instance as parameter
- Stores it in module-level variable for get_trace_sink to access

### agent_instance_id
- UUID generated per BaseAgent instance
- Flows through AgentTrace to TraceSink for correlation

## Integration Points

### Trace Sink Resolution Flow
1. `get_trace_sink()` is called (by AgentTrace or directly)
2. Check if TRACE_SINK_MODE env var is explicitly set to "local" → return LocalTraceSink
3. Check if global sink was configured via `configure_tracing()` → return that sink
4. Neither configured → return NoOpTraceSink

### Agent Instance ID Flow
1. BaseAgent constructor generates UUID
2. UUID passed to AgentTrace constructor
3. AgentTrace stores UUID and passes to TraceSink.save_trace on each save
4. Custom TraceSinks use ID for correlation; LocalTraceSink ignores it

### Reasoning Configuration Flow (Google)
1. User creates agent with `reasoning=False`
2. BaseAgent.create_llm_config sets `LLMConfig.reasoning=False`
3. GoogleModelFactory.get_model_specific_config checks `config.reasoning`
4. When False, sets `thinking_budget=0` in model config
5. LangChain passes this to Gemini API, actually disabling thinking

### Reasoning Configuration Flow (OpenAI)
1. User creates agent with `reasoning=False`
2. BaseAgent.create_llm_config sets `LLMConfig.reasoning=False`
3. OpenAIModelFactory.get_model_specific_config checks `config.reasoning` (not `config.model.reasoning`)
4. When False, determines model version from config.model.name
5. For GPT-5.1+: sets reasoning effort to "none"
6. For GPT-5 base: sets reasoning effort to "minimal"
7. LangChain passes this to OpenAI API

## Failure Modes

### Invalid TraceSink Configuration
- If user calls `configure_tracing()` with None, should be treated as "clear global config" (revert to no-op default)
- If user calls `configure_tracing()` multiple times, last one wins (no error)

### TraceSink.save_trace Failures
- Existing behavior: exceptions from save_trace propagate up
- No change to this behavior - custom sinks are responsible for their own error handling
- NoOpTraceSink cannot fail (does nothing)

### Missing Agent Instance ID
- If AgentTrace is created without an instance ID (backward compatibility), should generate one internally or use a sentinel value
- TraceSink implementations must handle None/missing instance ID gracefully

### Env Var Parsing
- If TRACE_SINK_MODE is set to an invalid value (not "local", not empty), current behavior throws ValueError
- New behavior: only "local" is recognized; anything else (including invalid values) falls through to global/no-op
- This makes the system more forgiving - typos don't crash the app

### Model Version Detection for OpenAI
- Need reliable way to distinguish GPT-5 base from GPT-5.1+
- Should use model name string comparison (e.g., starts with "gpt-5.1" or "gpt-5.2")
- If detection fails or model is unknown, default to safer behavior (minimal effort)

## Files to Reference for Consistency

- `spaik_sdk/tracing/local_trace_sink.py` - Pattern for TraceSink implementations
- `spaik_sdk/models/factories/anthropic_factory.py` - Correct reasoning disable pattern
- `spaik_sdk/config/env.py` - Pattern for env var handling with defaults
- `spaik_sdk/tracing/__init__.py` - What to export from the module
