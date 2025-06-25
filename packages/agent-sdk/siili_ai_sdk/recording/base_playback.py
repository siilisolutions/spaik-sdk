import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional

from siili_ai_sdk.recording.langchain_serializer import deserialize_token_data


class BasePlayback(ABC):
    """Abstract base class for playing back recorded LLM interactions."""

    def __init__(self, recording_name: str = "default", delay: float = 0.001):
        self.recording_name = recording_name
        self.current_session = 1
        self._iterator: Optional[Iterator[Dict[str, Any]]] = None
        self.delay = delay

    @abstractmethod
    def _load_session_data_impl(self, session_num: int) -> Iterator[Dict[str, Any]]:
        """Load raw data for a specific session number. Returns plain dicts."""
        pass

    def _load_session_data(self, session_num: int) -> Iterator[Dict[str, Any]]:
        """Load data for a specific session number and deserialize LangChain objects."""
        for raw_data in self._load_session_data_impl(session_num):
            # Deserialize LangChain objects after loading from implementation
            yield deserialize_token_data(raw_data)

    @abstractmethod
    def _session_exists(self, session_num: int) -> bool:
        """Check if a session file exists."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if playback data is available."""
        pass

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Make the playback object iterable."""
        return self

    def __aiter__(self):
        """Make the playback object async iterable."""
        return self

    async def __anext__(self) -> Dict[str, Any]:
        """Async version of __next__."""
        try:
            return self.__next__()
        except StopIteration:
            raise StopAsyncIteration

    def __next__(self) -> Dict[str, Any]:
        """Get the next token/response from current session only."""
        # Initialize iterator if not set
        if self._iterator is None:
            if not self._session_exists(self.current_session):
                raise StopIteration("No recorded sessions found")
            self._iterator = self._load_session_data(self.current_session)

        try:
            time.sleep(self.delay)
            return next(self._iterator)
        except StopIteration:
            # Current session exhausted, auto-bump to next session
            self.current_session += 1
            self._iterator = None
            raise StopIteration("Current session exhausted")

    def reset(self) -> None:
        """Reset playback to first session."""
        self.current_session = 1
        self._iterator = None

    def get_current_session(self) -> int:
        """Get the current session number."""
        return self.current_session

    def get_recording_name(self) -> str:
        """Get the recording name."""
        return self.recording_name

    def next_session(self) -> None:
        """Manually advance to next session."""
        self.current_session += 1
        self._iterator = None

    def has_next_session(self) -> bool:
        """Check if there's a next session available."""
        return self._session_exists(self.current_session + 1)
