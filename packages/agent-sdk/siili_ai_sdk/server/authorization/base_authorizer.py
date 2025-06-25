from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from fastapi import Request

from siili_ai_sdk.server.authorization.base_user import BaseUser
from siili_ai_sdk.thread.models import ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer

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
