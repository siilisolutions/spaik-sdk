import asyncio
from typing import Any, AsyncGenerator, Dict

from siili_ai_sdk.server.pubsub.thread_event_publisher import ThreadEventPublisher


class LocalThreadEventSubscriber:
    def __init__(self):
        self._event_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._stopped = False

    def on_event(self, event: Dict[str, Any]) -> None:
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            # Handle queue full case - could log warning or drop oldest events
            pass

    async def events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator that yields events as they arrive"""
        while not self._stopped:
            event = await self._event_queue.get()
            yield event

    def stop(self) -> None:
        self._stopped = True


class LocalThreadEventPublisher(ThreadEventPublisher):
    def __init__(self, subscriber: LocalThreadEventSubscriber):
        self.subscriber = subscriber

    def publish_event(self, event: Dict[str, Any]) -> None:
        self.subscriber.on_event(event)


class LocalThreadEventPubsub:
    def __init__(self):
        self.subscriber = LocalThreadEventSubscriber()
        self.publisher = LocalThreadEventPublisher(self.subscriber)

    async def events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator that yields events as they arrive"""
        async for event in self.subscriber.events():
            yield event

    def stop(self) -> None:
        self.subscriber.stop()

    def get_publisher(self) -> ThreadEventPublisher:
        return self.publisher
