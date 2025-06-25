from typing import List, Optional

from siili_ai_sdk.server.storage.base_thread_repository import BaseThreadRepository
from siili_ai_sdk.server.storage.thread_filter import ThreadFilter
from siili_ai_sdk.server.storage.thread_metadata import ThreadMetadata
from siili_ai_sdk.thread.models import ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer


class ThreadService:
    """High-level service for thread and message operations"""

    def __init__(self, repository: BaseThreadRepository):
        self.repository = repository

    # Thread operations
    async def create_thread(self, thread_container: ThreadContainer) -> ThreadContainer:
        """Create a new thread"""
        await self.repository.save_thread(thread_container)
        return thread_container

    async def get_thread(self, thread_id: str) -> Optional[ThreadContainer]:
        """Get thread by ID"""
        return await self.repository.load_thread(thread_id)

    async def update_thread(self, thread_container: ThreadContainer) -> Optional[ThreadContainer]:
        """Update an existing thread"""
        if not await self.repository.thread_exists(thread_container.thread_id):
            return None

        await self.repository.save_thread(thread_container)
        return thread_container

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete thread and all its messages"""
        return await self.repository.delete_thread(thread_id)

    async def thread_exists(self, thread_id: str) -> bool:
        """Check if thread exists"""
        return await self.repository.thread_exists(thread_id)

    async def list_threads(self, filter: ThreadFilter) -> List[ThreadMetadata]:
        """List threads matching filter"""
        return await self.repository.list_threads(filter)

    # Message operations
    async def get_message(self, thread_id: str, message_id: str) -> Optional[ThreadMessage]:
        """Get message by thread ID and message ID"""
        return await self.repository.get_message(thread_id, message_id)

    async def add_message(self, thread_id: str, message: ThreadMessage) -> Optional[ThreadMessage]:
        """Add message to thread"""
        if not await self.repository.thread_exists(thread_id):
            return None

        await self.repository.upsert_message(thread_id, message)
        return message

    async def update_message(self, thread_id: str, message: ThreadMessage) -> Optional[ThreadMessage]:
        """Update existing message in thread"""
        if not await self.repository.thread_exists(thread_id):
            return None

        # Check if message exists
        existing_message = await self.repository.get_message(thread_id, message.id)
        if not existing_message:
            return None

        await self.repository.upsert_message(thread_id, message)
        return message

    async def delete_message(self, thread_id: str, message_id: str) -> bool:
        """Delete message from thread"""
        if not await self.repository.thread_exists(thread_id):
            return False

        # Check if message exists
        existing_message = await self.repository.get_message(thread_id, message_id)
        if not existing_message:
            return False

        await self.repository.delete_message(thread_id, message_id)
        return True

    async def get_thread_messages(self, thread_id: str) -> List[ThreadMessage]:
        """Get all messages for a thread"""
        thread = await self.repository.load_thread(thread_id)
        if not thread:
            return []

        return thread.messages
