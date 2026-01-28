from typing import Optional

from spaik_sdk.tracing.local_trace_sink import LocalTraceSink
from spaik_sdk.tracing.noop_trace_sink import NoOpTraceSink
from spaik_sdk.tracing.trace_sink import TraceSink
from spaik_sdk.tracing.trace_sink_mode import TraceSinkMode

# Module-level storage for globally configured trace sink
_global_trace_sink: Optional[TraceSink] = None


def configure_tracing(sink: Optional[TraceSink]) -> None:
    """Configure the global trace sink used by all agents.

    Call this once at application startup to set a custom trace sink
    that will be used by all subsequently created agents.

    Resolution order:
    1. TRACE_SINK_MODE=local env var -> LocalTraceSink (escape hatch)
    2. TRACE_SINK_MODE=noop env var -> NoOpTraceSink
    3. Global sink set via this function -> the configured sink
    4. No configuration -> NoOpTraceSink (silent default)

    Args:
        sink: The TraceSink to use globally, or None to clear the global
              configuration (reverts to default no-op behavior).

    Example:
        from spaik_sdk.tracing import configure_tracing, LocalTraceSink

        # At application startup
        configure_tracing(LocalTraceSink(traces_dir="my_traces"))

        # Or with a custom sink for observability
        configure_tracing(MyDatadogTraceSink())

        # Clear global config
        configure_tracing(None)
    """
    global _global_trace_sink
    _global_trace_sink = sink


def get_trace_sink(mode: Optional[TraceSinkMode] = None) -> TraceSink:
    """Get the appropriate trace sink based on configuration.

    Resolution order:
    1. If mode parameter is provided, use that mode
    2. Check TRACE_SINK_MODE env var (LOCAL or NOOP override everything)
    3. Check for globally configured sink via configure_tracing()
    4. Default to NoOpTraceSink (silent no-op)

    Args:
        mode: Optional explicit mode to use (overrides all other config).

    Returns:
        The appropriate TraceSink instance.
    """
    # Lazy import to avoid circular dependency with env.py
    from spaik_sdk.config.env import env_config

    # If explicit mode parameter provided, use it
    if mode is None:
        mode = env_config.get_trace_sink_mode()

    # Step 1-2: Check env var mode (LOCAL or NOOP)
    if mode == TraceSinkMode.LOCAL:
        return LocalTraceSink()
    if mode == TraceSinkMode.NOOP:
        return NoOpTraceSink()

    # Step 3: Check global sink
    if _global_trace_sink is not None:
        return _global_trace_sink

    # Step 4: Default to no-op
    return NoOpTraceSink()
