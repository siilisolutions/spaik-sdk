from typing import Optional

from spaik_sdk.tracing.local_trace_sink import LocalTraceSink
from spaik_sdk.tracing.trace_sink import TraceSink
from spaik_sdk.tracing.trace_sink_mode import TraceSinkMode


def get_trace_sink(mode: Optional[TraceSinkMode] = None) -> TraceSink:
    # Lazy import to avoid circular dependency with env.py
    from spaik_sdk.config.env import env_config

    mode = mode or env_config.get_trace_sink_mode()
    if mode == TraceSinkMode.LOCAL:
        return LocalTraceSink()
    raise ValueError(f"Unknown TraceSinkMode: {mode}")
