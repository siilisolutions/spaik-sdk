from abc import ABC, abstractmethod
from typing import Optional


class TraceSink(ABC):
    """Abstract base class for trace storage backends.

    Implementations can write traces to local files, remote APIs, databases, etc.
    """

    @abstractmethod
    def save_trace(
        self,
        name: str,
        trace_content: str,
        system_prompt: str,
        agent_instance_id: Optional[str] = None,
    ) -> None:
        """Save a trace with its system prompt.

        Args:
            name: Identifier for the trace (e.g., agent class name)
            trace_content: The formatted trace content (without system prompt)
            system_prompt: The system prompt used for the agent
            agent_instance_id: Optional UUID identifying the agent instance for correlation.
                              Custom sinks can use this to correlate traces in observability
                              backends (e.g., Datadog, OpenTelemetry).
        """
        pass
