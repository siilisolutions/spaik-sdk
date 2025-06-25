from abc import ABC, abstractmethod
from typing import List, Optional

from siili_ai_sdk.server.storage.thread_filter import ThreadFilter
from siili_ai_sdk.server.storage.thread_metadata import ThreadMetadata
from siili_ai_sdk.thread.models import ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer


class BaseThreadRepository(ABC):
    """Abstract base class for thread persistence"""

    @abstractmethod
    async def save_thread(self, thread_container: ThreadContainer) -> None:
        """Save complete thread container to storage"""
        pass

    @abstractmethod
    async def load_thread(self, thread_id: str) -> Optional[ThreadContainer]:
        """Load thread container from storage"""
        pass

    @abstractmethod
    async def get_message(self, thread_id: str, message_id: str) -> Optional[ThreadMessage]:
        """Get message from storage"""
        pass

    @abstractmethod
    async def upsert_message(self, thread_id: str, message: ThreadMessage) -> None:
        """Upsert message to storage"""
        pass

    @abstractmethod
    async def delete_message(self, thread_id: str, message_id: str) -> None:
        """Delete message from storage"""
        pass

    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """Check if thread exists"""
        pass

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete thread and all its messages"""
        pass

    @abstractmethod
    async def list_threads(self, filter: ThreadFilter) -> List[ThreadMetadata]:
        """List threads for a given filter"""
        pass
