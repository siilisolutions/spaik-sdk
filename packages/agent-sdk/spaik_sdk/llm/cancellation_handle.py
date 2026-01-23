from abc import ABC, abstractmethod


class CancellationHandle(ABC):
    """Abstract base class for handling cancellation of LLM operations."""

    @abstractmethod
    async def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        pass
