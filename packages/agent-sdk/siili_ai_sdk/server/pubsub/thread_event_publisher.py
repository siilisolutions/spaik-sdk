import time
from typing import Any, Dict, Optional

from siili_ai_sdk.server.pubsub.event_config import EventConfig
from siili_ai_sdk.server.pubsub.event_publisher import EventPublisher
from siili_ai_sdk.thread.models import (
    MessageBlockType,
    ThreadEvent,
    ToolCallStartedEvent,
    ToolResponseReceivedEvent,
)
from siili_ai_sdk.thread.thread_container import ThreadContainer
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ThreadEventPublisher(EventPublisher):
    """Base publisher that binds to ThreadContainer events"""

    def __init__(self, config: Optional[EventConfig] = None):
        self.config = config if config else EventConfig()

    def bind_container(self, thread_container: ThreadContainer) -> None:
        self.thread_container = thread_container
        self.thread_container.subscribe(self._handle_thread_event)

    def _handle_thread_event(self, event: ThreadEvent) -> None:
        """Handle ThreadContainer event and publish if needed"""

        try:
            if not event.is_publishable():
                return

            # Check if we should publish this event
            if not self.config.should_publish_event(event.get_event_type()):
                return

            # Filter based on config
            if not self._should_include_event(event):
                return

            # Convert to publishable format
            pub_event = self._convert_event(event, event.get_event_type())
            if pub_event is None:
                return
            # Publish the event
            self.publish_event(pub_event)

        except Exception as e:
            logger.error(f"Error handling thread event: {e}")

    def _should_include_event(self, event: ThreadEvent) -> bool:
        """Apply config-based filtering"""

        # Filter reasoning blocks if not enabled
        if hasattr(event, "block") and event.block:
            if event.block.type == MessageBlockType.REASONING and not self.config.include_reasoning:
                return False

        # Filter tool events if not enabled
        if isinstance(event, (ToolCallStartedEvent, ToolResponseReceivedEvent)) and not self.config.include_tools:
            return False

        return True

    # TODO: use this format: EventStreamResponse
    def _convert_event(self, event: ThreadEvent, event_type: str) -> Optional[Dict[str, Any]]:
        """Convert ThreadContainer event to publishable format"""

        return {
            "thread_id": self.thread_container.thread_id,
            "event_type": event_type,
            "timestamp": int(time.time() * 1000),
            "metadata": self.config.metadata.copy(),
            "data": event.get_event_data(),
        }

    def disconnect(self) -> None:
        """Disconnect from ThreadContainer"""
        try:
            self.thread_container.unsubscribe(self._handle_thread_event)
            logger.debug("Publisher disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting publisher: {e}")
