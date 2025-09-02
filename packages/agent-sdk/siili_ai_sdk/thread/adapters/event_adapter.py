"""
Simple synchronous adapter for ThreadContainer
"""

from typing import List

from siili_ai_sdk.thread.models import ThreadEvent
from siili_ai_sdk.thread.thread_container import ThreadContainer


class EventAdapter:
    def __init__(self, container: ThreadContainer):
        self.events: List[ThreadEvent] = []
        self.container = container

        self.container.subscribe(self._handle_event)

    def _handle_event(self, event: ThreadEvent):
        self.events.append(event)

    def flush(self) -> List[ThreadEvent]:
        ret = self.events
        self.events = []
        return ret

    def cleanup(self):
        """Unsubscribe from events"""
        self.container.unsubscribe(self._handle_event)
