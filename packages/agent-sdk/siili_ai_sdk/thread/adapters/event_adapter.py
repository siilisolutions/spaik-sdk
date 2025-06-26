"""
Simple synchronous adapter for ThreadContainer
"""

import asyncio
import time
from typing import List, Optional

from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.thread.models import StreamingEndedEvent, ThreadEvent, ThreadMessage
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
