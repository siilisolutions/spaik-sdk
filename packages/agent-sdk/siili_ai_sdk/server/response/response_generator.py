from abc import ABC, abstractmethod
from typing import Optional

from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.thread.thread_container import ThreadContainer


class ResponseGenerator(ABC):
    @abstractmethod
    async def trigger_response(self, thread: ThreadContainer, cancellation_handle: Optional[CancellationHandle] = None) -> None:
        pass
