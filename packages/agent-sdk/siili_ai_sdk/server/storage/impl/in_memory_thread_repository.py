from typing import Dict, List, Optional

from siili_ai_sdk.server.storage.base_thread_repository import BaseThreadRepository
from siili_ai_sdk.server.storage.thread_filter import ThreadFilter
from siili_ai_sdk.server.storage.thread_metadata import ThreadMetadata
from siili_ai_sdk.thread.models import ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer


class InMemoryThreadRepository(BaseThreadRepository):
    """In-memory implementation of thread repository for testing/development"""

    def __init__(self):
        self._threads: Dict[str, ThreadContainer] = {}
        self._metadata: Dict[str, ThreadMetadata] = {}

    async def save_thread(self, thread_container: ThreadContainer) -> None:
        """Save complete thread container to memory"""
        self._threads[thread_container.thread_id] = thread_container
        # Update metadata
        metadata = ThreadMetadata.from_thread_container(thread_container)
        self._metadata[thread_container.thread_id] = metadata

    async def load_thread(self, thread_id: str) -> Optional[ThreadContainer]:
        """Load thread container from memory"""
        return self._threads.get(thread_id)

    async def get_message(self, thread_id: str, message_id: str) -> Optional[ThreadMessage]:
        """Get message from memory"""
        thread = self._threads.get(thread_id)
        if not thread:
            return None

        for message in thread.messages:
            if message.id == message_id:
                return message
        return None

    async def upsert_message(self, thread_id: str, message: ThreadMessage) -> None:
        """Upsert message to memory"""
        thread = self._threads.get(thread_id)
        if not thread:
            return

        # Find existing message and replace, or add new one
        for i, existing_msg in enumerate(thread.messages):
            if existing_msg.id == message.id:
                thread.messages[i] = message
                break
        else:
            thread.messages.append(message)

        # Update metadata
        metadata = ThreadMetadata.from_thread_container(thread)
        self._metadata[thread_id] = metadata

    async def delete_message(self, thread_id: str, message_id: str) -> None:
        """Delete message from memory"""
        thread = self._threads.get(thread_id)
        if not thread:
            return

        thread.messages = [msg for msg in thread.messages if msg.id != message_id]

        # Update metadata
        metadata = ThreadMetadata.from_thread_container(thread)
        self._metadata[thread_id] = metadata

    async def thread_exists(self, thread_id: str) -> bool:
        """Check if thread exists in memory"""
        return thread_id in self._threads

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete thread and all its messages from memory"""
        if thread_id in self._threads:
            del self._threads[thread_id]
            if thread_id in self._metadata:
                del self._metadata[thread_id]
            return True
        return False

    async def list_threads(self, filter: ThreadFilter) -> List[ThreadMetadata]:
        """List threads matching the filter from memory"""
        result = []
        for metadata in self._metadata.values():
            if filter.matches(metadata):
                result.append(metadata)

        # Sort by last activity time (most recent first)
        result.sort(key=lambda x: x.last_activity_time, reverse=True)
        return result

    def clear_all(self) -> None:
        """Clear all data (useful for testing)"""
        self._threads.clear()
        self._metadata.clear()

    def get_thread_count(self) -> int:
        """Get total number of threads stored"""
        return len(self._threads)
