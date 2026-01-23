from abc import ABC, abstractmethod


class CancellationPublisher(ABC):
    @abstractmethod
    def publish_cancellation(self, id: str) -> None:
        pass
