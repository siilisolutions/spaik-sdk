from abc import ABC, abstractmethod


class TraceSink(ABC):
    """Abstract base class for trace storage backends.

    Implementations can write traces to local files, remote APIs, databases, etc.
    """

    @abstractmethod
    def save_trace(self, name: str, trace_content: str, system_prompt: str) -> None:
        """Save a trace with its system prompt.

        Args:
            name: Identifier for the trace (e.g., agent class name)
            trace_content: The formatted trace content (without system prompt)
            system_prompt: The system prompt used for the agent
        """
        pass
