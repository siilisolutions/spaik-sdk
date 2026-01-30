from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from fastapi import Request

from spaik_sdk.server.authorization.base_user import BaseUser
from spaik_sdk.thread.models import ThreadMessage
from spaik_sdk.thread.thread_container import ThreadContainer

if TYPE_CHECKING:
    from spaik_sdk.attachments.models import FileMetadata

TUser = TypeVar("TUser", bound=BaseUser)


class BaseAuthorizer(ABC, Generic[TUser]):
    """Abstract base for authorization"""

    @abstractmethod
    async def get_user(self, request: Request) -> Optional[TUser]:
        """Get user from request"""
        pass

    async def can_create_thread(
        self,
        user: TUser,
    ) -> bool:
        """Check if user has permission for the thread"""
        return True

    async def can_read_thread(self, user: TUser, thread_container: ThreadContainer) -> bool:
        """Check if user has permission to read the thread"""
        return self.is_thread_owner(user, thread_container)

    async def can_post_message(self, user: TUser, thread_container: ThreadContainer) -> bool:
        """Check if user has permission to post a message to the thread"""
        return self.is_thread_owner(user, thread_container)

    async def can_edit_message(self, user: TUser, thread_container: ThreadContainer, message: ThreadMessage) -> bool:
        """Check if user has permission to edit a message in the thread"""
        return message.author_id == user.get_id()

    async def can_delete_thread(self, user: TUser, thread_container: ThreadContainer) -> bool:
        """Check if user has permission to delete the thread"""
        return self.is_thread_owner(user, thread_container)

    def is_thread_owner(self, user: TUser, thread_container: ThreadContainer) -> bool:
        """Check if user is the owner of the thread"""
        return thread_container.messages[0].author_id == user.get_id()

    async def can_upload_file(self, user: TUser) -> bool:
        """Check if user has permission to upload files"""
        return True

    async def can_read_file(self, user: TUser, file_metadata: "FileMetadata") -> bool:
        """Check if user has permission to read a file.

        By default, users can read files they own, or files owned by 'system' (agent-generated).
        """
        return file_metadata.owner_id == user.get_id() or file_metadata.owner_id == "system"

    async def can_delete_file(self, user: TUser, file_metadata: "FileMetadata") -> bool:
        """Check if user has permission to delete a file"""
        return file_metadata.owner_id == user.get_id()
