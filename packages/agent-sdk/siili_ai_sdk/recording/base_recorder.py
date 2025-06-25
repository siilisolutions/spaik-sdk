from abc import ABC, abstractmethod
from typing import Any, Dict

from siili_ai_sdk.recording.langchain_serializer import ensure_json_serializable, serialize_token_data


class BaseRecorder(ABC):
    """Abstract base class for recording LLM interactions."""

    def __init__(self, recording_name: str = "default"):
        self.recording_name = recording_name
        self.current_session = 1

    def record_token(self, token_data: Dict[str, Any]) -> None:
        """Record a streaming token from LLM response."""
        # Serialize LangChain objects before passing to implementation
        serialized_data = serialize_token_data(token_data)
        safe_data = ensure_json_serializable(serialized_data)
        self._record_token_impl(safe_data)

    def record_structured(self, data: Dict[str, Any]) -> None:
        """Record structured response and immediately bump session counter."""
        # Serialize LangChain objects before passing to implementation
        serialized_data = serialize_token_data(data)
        safe_data = ensure_json_serializable(serialized_data)
        self._record_structured_impl(safe_data)

    @abstractmethod
    def _record_token_impl(self, token_data: Dict[str, Any]) -> None:
        """Implementation-specific token recording. Data is already serialized."""
        pass

    @abstractmethod
    def _record_structured_impl(self, data: Dict[str, Any]) -> None:
        """Implementation-specific structured recording. Data is already serialized."""
        pass

    @abstractmethod
    def request_completed(self) -> None:
        """Mark current request as completed and bump to next session."""
        pass

    @abstractmethod
    def get_current_session(self) -> int:
        """Get the current session number."""
        pass

    def get_recording_name(self) -> str:
        """Get the recording name."""
        return self.recording_name
