import json
import time
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from siili_ai_sdk.llm.consumption.token_usage import TokenUsage


class MessageBlockType(Enum):
    PLAIN = "plain"
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    ERROR = "error"


@dataclass
class MessageBlock:
    id: str
    streaming: bool
    type: MessageBlockType
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_call_args: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = None
    tool_call_response: Optional[str] = None
    tool_call_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "streaming": self.streaming,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
            "tool_call_args": self.tool_call_args,
            "tool_name": self.tool_name,
            "type": self.type.value,
        }


@dataclass
class ThreadMessage:
    id: str
    ai: bool
    author_id: str
    author_name: str
    timestamp: int  # UTC millis
    blocks: List[MessageBlock]
    consumption_metadata: Optional["TokenUsage"] = None

    def get_text_content(self) -> str:
        return "\n".join([(block.content or "") for block in self.blocks if block.type == MessageBlockType.PLAIN])

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "ai": self.ai,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "timestamp": self.timestamp,
            "blocks": [block.to_dict() for block in self.blocks],
        }
        if self.consumption_metadata:
            result["consumption_metadata"] = self.consumption_metadata
        return result

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        blocks_info = []
        for block in self.blocks:
            block_repr = f"{block.type.value} ({block.id}, {block.streaming}):"
            if block.content:
                content_preview = block.content[:50] + "..." if len(block.content) > 50 else block.content
                block_repr += f":{content_preview}"
            if block.tool_name:
                block_repr += f"[{block.tool_name}]"
            blocks_info.append(block_repr)

        return (
            f"ThreadMessage(id='{self.id}', ai={self.ai}, "
            f"author='{self.author_name}', timestamp={self.timestamp}, "
            f"blocks=[{', '.join(blocks_info)}])"
        )


@dataclass
class ToolCallResponse:
    id: str
    response: str
    error: Optional[str] = None


# Event system
@dataclass
class ThreadEvent(ABC):
    """Abstract base class for all thread events"""

    def get_event_type(self) -> str:
        """Return the event type identifier"""
        return fix_event_type(self.__class__.__name__)

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        """Return the event data."""
        return None

    def is_publishable(self) -> bool:
        """Return True if the event is publishable."""
        return False

    def dump_json(self, thread_id: str) -> str:
        return json.dumps(
            {
                "thread_id": thread_id,
                "event_type": self.get_event_type(),
                "timestamp": int(time.time() * 1000),
                "data": self.get_event_data(),
            }
        )


@dataclass
class PublishableEvent(ThreadEvent):
    """Abstract base class for all publishable events"""

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        """Return the event data."""
        return self.__dict__

    def is_publishable(self) -> bool:
        """Return True if the event is publishable."""
        return True


@dataclass
class InternalEvent(ThreadEvent):
    """Abstract base class for all publishable events"""

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        return None

    def is_publishable(self) -> bool:
        return False


def fix_event_type(event_type: str) -> str:
    """Fix the event type to be a valid event type"""
    return event_type.replace("Event", "")


@dataclass
class StreamingUpdatedEvent(PublishableEvent):
    block_id: str
    content: str
    total_content: str

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        return {
            "block_id": self.block_id,
            "content": self.content,
        }


@dataclass
class BlockAddedEvent(PublishableEvent):
    message_id: str
    block_id: str
    block: MessageBlock

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        return {"message_id": self.message_id, "block": self.block.to_dict()}


@dataclass
class ToolCallStartedEvent(InternalEvent):
    tool_call_id: str
    tool_name: str
    message_id: str
    block_id: str


@dataclass
class ToolResponseReceivedEvent(PublishableEvent):
    tool_call_id: str
    response: str
    error: Optional[str] = None
    block_id: Optional[str] = None


@dataclass
class StreamingEndedEvent(InternalEvent):
    message_id: str
    completed_blocks: List[str]


@dataclass
class MessageAddedEvent(PublishableEvent):
    message: ThreadMessage

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        return self.message.to_dict()


@dataclass
class MessageFullyAddedEvent(PublishableEvent):
    message: ThreadMessage

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        return {"message_id": self.message.id}


@dataclass
class BlockFullyAddedEvent(PublishableEvent):
    block_id: str
    message_id: str
    block: MessageBlock

    def get_event_data(self) -> Optional[Dict[str, Any]]:
        return {"message_id": self.message_id, "block_id": self.block_id}
