from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from siili_ai_sdk.thread.models import MessageBlockType

if TYPE_CHECKING:
    from siili_ai_sdk.llm.consumption.token_usage import TokenUsage


class EventType(str, Enum):
    """Types of streaming events."""

    MESSAGE_START = "message_start"
    BLOCK_START = "block_start"
    BLOCK_END = "block_end"
    REASONING = "reasoning"
    REASONING_SUMMARY = "reasoning_summary"
    TOKEN = "token"
    TOOL_USE = "tool_use"
    TOOL_RESPONSE = "tool_response"
    USAGE_METADATA = "usage_metadata"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class StreamingEvent:
    """Represents a processed streaming event."""

    event_type: EventType
    content: Optional[str] = None
    block_id: Optional[str] = None
    message_id: Optional[str] = None
    block_type: Optional[MessageBlockType] = None
    blocks: Optional[List[str]] = None
    message: Optional[Any] = None
    error: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    usage_metadata: Optional["TokenUsage"] = None
