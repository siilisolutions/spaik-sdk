from siili_ai_sdk.server.pubsub.cancellation_publisher import CancellationPublisher
from siili_ai_sdk.server.pubsub.cancellation_subscriber import CancellationSubscriber


class LocalCancellationPubsub:
    def __init__(self):
        self.publisher = LocalCancellationPublisher()

    def create_subscriber(self, id: str) -> CancellationSubscriber:
        return LocalCancellationSubscriber(id, self.publisher)

    def get_publisher(self) -> CancellationPublisher:
        return self.publisher


class LocalCancellationSubscriber(CancellationSubscriber):
    def __init__(self, id: str, publisher: "LocalCancellationPublisher"):
        self.publisher = publisher
        super().__init__(id)

    def _subscribe_to_cancellation(self) -> None:
        self.publisher.subscribe(self)

    def _unsubscribe_from_cancellation(self) -> None:
        self.publisher.unsubscribe(self)


class LocalCancellationPublisher(CancellationPublisher):
    def __init__(self):
        self.subscribers: list[CancellationSubscriber] = []

    def subscribe(self, subscriber: CancellationSubscriber) -> None:
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber: CancellationSubscriber) -> None:
        self.subscribers.remove(subscriber)

    def publish_cancellation(self, id: str) -> None:
        for subscriber in self.subscribers:
            if subscriber.id == id:
                subscriber.on_cancellation()


local_cancellation_pubsub = LocalCancellationPubsub()


def get_local_cancellation_pubsub() -> LocalCancellationPubsub:
    return local_cancellation_pubsub
