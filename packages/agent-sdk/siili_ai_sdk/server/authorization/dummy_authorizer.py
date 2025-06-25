from typing import Optional

from fastapi import Request

from siili_ai_sdk.server.authorization.base_authorizer import BaseAuthorizer
from siili_ai_sdk.server.authorization.base_user import BaseUser
from siili_ai_sdk.thread.thread_container import ThreadContainer


class DummyAuthorizer(BaseAuthorizer[BaseUser]):
    """Dummy authorizer that always returns True"""

    async def get_user(self, request: Request) -> Optional[BaseUser]:
        return BaseUser("user")

    def is_thread_owner(self, user: BaseUser, thread_container: ThreadContainer) -> bool:
        return True
