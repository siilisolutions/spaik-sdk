# GPT-5.2 Spec Review

## Overall Assessment
The specs are improved but still contain contradictions and missing behavior definitions that will create ambiguous implementation and brittle tests. The tracing changes alter default behavior and API surface without a clear compatibility story, and the reasoning-disable logic still lacks model naming and override-precedence clarity.

## Recent Changes Review
`claude_changes.md` exists and the updates are helpful:
- Added explicit `TRACE_SINK_MODE=noop`, clarified the precedence order, and extended testing around no-op behavior.
- Clarified `AgentTrace` behavior when `agent_instance_id` is missing (generate a UUID).
- Clarified Gemini `include_thoughts` behavior in `003.md`.
- Reduced testing burden by marking API-dependent tests as optional.

Remaining gaps after those changes:
- `testing.md` still allows "include_thoughts not set or False," which conflicts with `003.md`'s explicit False requirement.
- Backward-compatibility strategy for the `TraceSink.save_trace` signature change is still unspecified.
- Non-goals still conflict with `configure_tracing(None)` and repeated calls.
- OpenAI model variant list still appears unverified against `ModelRegistry` and alias handling.

## Critical Issues
- **TraceSink backward compatibility is undefined**: Requirements say compatibility must be preserved, but `save_trace` adds a required parameter. Without a compatibility mechanism (default arg, `**kwargs`, adapter), existing custom sinks will break.
- **Per-agent vs global precedence is missing**: There is no defined behavior for `BaseAgent(trace_sink=...)` relative to global `configure_tracing()` and env vars. This can silently ignore explicit user intent.
- **Existing agents after reconfiguration are undefined**: Specs only mention "subsequently created agents" but do not define whether already-constructed agents update or remain pinned to their sink.
- **Non-goals contradict acceptance criteria**: "No runtime switching/reset" conflicts with `configure_tracing(None)` and "last one wins" semantics.
- **OpenAI model naming is ambiguous**: Acceptance criteria reference variants that may not exist in `ModelRegistry`, risking dead code and failing tests unless canonical names/aliases are defined.
- **Reasoning-disable override precedence is unclear**: If users set custom reasoning effort/budget or `include_thoughts`, it is unclear whether `reasoning=False` overrides, errors, or merges.
- **Invalid `TRACE_SINK_MODE` handling is risky**: Silent fallthrough can mask misconfiguration and may inadvertently deprecate existing modes; supported values and warnings should be explicit.

## Suggestions
- Add a migration note for the default change from filesystem tracing to no-op, including versioning or release-note expectations.
- Specify `agent_instance_id` type and exposure (UUID object vs string, attribute name, public access guarantees).
- Define case-sensitivity and whitespace handling for `TRACE_SINK_MODE`.
- Document thread-safety/multi-process expectations for the global sink registry and configuration timing.
- Align test assertions to payload-level verification (recorded requests or config objects), not model output content.

## Per-File Notes

### requirements.md
- Compatibility requirement conflicts with the `TraceSink.save_trace` signature change; define a compatibility strategy or adjust the requirement.
- Precedence order omits explicit per-agent `trace_sink` overrides; clarify whether constructor arguments trump global config.
- Non-goals ("no runtime switching/reset") conflict with `configure_tracing(None)` and repeated calls; reconcile.
- Default behavior change to no-op is a breaking change; include migration/documentation guidance.
- Behavior for unknown or future OpenAI models when `reasoning=False` is unspecified.

### testing.md
- Gemini test still says `include_thoughts` "not set or False" while `003.md` requires explicit False; align.
- No tests cover compatibility with legacy TraceSink implementations that lack the new parameter.
- "No filesystem writes occur" needs concrete verification steps (temp dir, monkeypatch, explicit file assertions).
- OpenAI model variants in tests should be sourced from `ModelRegistry` or documented alias mapping.
- API-dependent tests should verify request payloads or recorded calls, not response content.

### architecture.md
- `configure_tracing` is described as taking a TraceSink instance, but behavior for `None` (clear) is not documented here.
- Global sink registry behavior for existing agents and per-agent overrides is undefined.
- Invalid `TRACE_SINK_MODE` fallback may conflict with other modes; the supported set and deprecation story should be explicit.
- OpenAI model detection relies on string prefixes without defining canonical names or alias resolution.
- Multi-process and thread-safety expectations are not stated.

### overview.md
- Dependencies between steps are not explicit (e.g., 001 before 002/005, env changes after resolution logic).
- The breaking nature of default tracing behavior and signature changes is not mentioned.
- Scope for 004 may be large due to model-variant matrix; consider constraining to registry-backed names.

### 001.md
- Precedence between global config and explicit per-agent `trace_sink` is not defined.
- Behavior for already-created agents when `configure_tracing` is called later is not specified.
- `configure_tracing(None)` conflicts with non-goals; clarify whether it is supported.
- Thread-safety or reentrancy expectations for concurrent configuration calls are missing.

### 002.md
- Backward compatibility for external TraceSink implementations is not addressed despite being the main interface change.
- `agent_instance_id` type and public exposure are unspecified; tests should assert a concrete type.
- Clarify whether AgentTrace-generated UUIDs are only for legacy instantiation and how correlation is affected.

### 003.md
- Specify how `reasoning=False` interacts with user-supplied `include_thoughts` or `thinking_budget` values.
- Ensure test expectations match the explicit `include_thoughts=False` requirement.
- Clarify whether this applies to all Gemini models or only those supporting thinking budgets.

### 004.md
- Model list includes unverified variants; align with `ModelRegistry` and alias handling.
- Define fallback behavior for unknown/unsupported model names when `reasoning=False`.
- Clarify how user-specified reasoning effort is handled when reasoning is disabled.
- Specify the exact matching rule (prefix, exact match, registry lookup) used for model detection.

### 005.md
- Dependency on step 001 should be explicit because it relies on no-op sink resolution.
- Invalid `TRACE_SINK_MODE` handling (warn vs silent) is not specified here despite being a global behavior change.
- Call out the behavioral break from default "local" to unset and provide migration guidance.
- Clarify case-sensitivity and whitespace handling for the env var in acceptance criteria.

### claude_changes.md
- Useful as a summary, but it is not authoritative; ensure changes are reflected in the actual spec files.
