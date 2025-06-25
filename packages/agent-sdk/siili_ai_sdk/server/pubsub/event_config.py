from typing import Any, Optional, Set

from pydantic import BaseModel, Field


class EventConfig(BaseModel):
    """Configuration for which events to publish"""

    # Which event types to publish (using simple strings)
    enabled_events: Optional[Set[str]] = None

    # Whether to include reasoning blocks
    include_reasoning: bool = True

    # Whether to include tool details
    include_tools: bool = True

    # Custom metadata to include with events
    metadata: dict[str, Any] = Field(default_factory=dict)

    def should_publish_event(self, event_type: str) -> bool:
        """Check if this event type should be published"""
        if self.enabled_events is None:
            return True
        return event_type in self.enabled_events
