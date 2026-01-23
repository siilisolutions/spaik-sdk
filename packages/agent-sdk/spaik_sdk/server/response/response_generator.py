from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

from spaik_sdk.llm.cancellation_handle import CancellationHandle
from spaik_sdk.thread.thread_container import ThreadContainer


class ResponseGenerator(ABC):
    @abstractmethod
    def stream_response(
        self, thread: ThreadContainer, cancellation_handle: Optional[CancellationHandle] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass
