from spaik_sdk.tracing.trace_sink import TraceSink


class NoOpTraceSink(TraceSink):
    """TraceSink implementation that does nothing.

    Used as the default when no tracing is configured, ensuring traces
    are silently discarded without any side effects.
    """

    def save_trace(self, name: str, trace_content: str, system_prompt: str) -> None:
        """Do nothing - silently discard the trace."""
        pass
