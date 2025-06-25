from abc import ABC, abstractmethod

from siili_ai_sdk.llm.cancellation_handle import CancellationHandle


class CancellationSubscriberHandler(CancellationHandle):
    cancelled: bool = False

    async def is_cancelled(self) -> bool:
        return self.cancelled

    def cancel(self) -> None:
        self.cancelled = True


class CancellationSubscriber(ABC):
    def __init__(self, id: str):
        self.id = id
        self.cancellation_handle = CancellationSubscriberHandler()
        self._subscribe_to_cancellation()

    @abstractmethod
    def _subscribe_to_cancellation(self) -> None:
        pass

    @abstractmethod
    def _unsubscribe_from_cancellation(self) -> None:
        pass

    def get_cancellation_handle(self) -> CancellationHandle:
        return self.cancellation_handle

    def on_cancellation(self) -> None:
        self.cancellation_handle.cancel()

    def stop(self) -> None:
        self._unsubscribe_from_cancellation()
