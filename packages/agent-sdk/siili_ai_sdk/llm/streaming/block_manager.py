import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from siili_ai_sdk.llm.streaming.models import EventType, StreamingEvent
from siili_ai_sdk.thread.models import MessageBlockType


class BlockManager:
    """Manages different types of content blocks during streaming."""

    def __init__(self):
        self.current_blocks: Dict[str, str] = {}  # block_id -> block_type
        self.block_timestamps: Dict[str, float] = {}  # block_id -> creation_timestamp
        self.reasoning_block_id: Optional[str] = None
        self.regular_block_id: Optional[str] = None
        self.summary_block_id: Optional[str] = None
        self.tool_use_blocks: Dict[str, str] = {}  # tool_call_id -> block_id
        self.reasoning_detected = False
        self.last_block_type: Optional[str] = None  # Track the last type of block created

    def reset(self):
        """Reset block manager state."""
        self.current_blocks = {}
        self.block_timestamps = {}
        self.reasoning_block_id = None
        self.regular_block_id = None
        self.summary_block_id = None
        self.tool_use_blocks = {}
        self.reasoning_detected = False
        self.last_block_type = None

    def mark_reasoning_detected(self):
        """Mark that reasoning activity has been detected."""
        self.reasoning_detected = True

    def reset_reasoning_block(self):
        """Reset reasoning block for mid-response thinking (creates new reasoning block)."""
        if self.reasoning_block_id:
            # Remove the current reasoning block from tracking
            self.current_blocks.pop(self.reasoning_block_id, None)
            self.block_timestamps.pop(self.reasoning_block_id, None)  # Remove timestamp too
        self.reasoning_block_id = None

    def get_block_ids(self) -> List[str]:
        """Get list of all current block IDs."""
        return list(self.current_blocks.keys())

    def should_create_new_reasoning_block(self) -> bool:
        """Check if we need a new reasoning block based on timestamps.

        Rule: If there's any tool call newer than the current reasoning block, create new reasoning block.
        This ensures reasoning gets properly segmented around tool calls.
        """
        if self.reasoning_block_id is None:
            return False

        current_reasoning_timestamp = self.block_timestamps.get(self.reasoning_block_id, 0)

        # Check if any tool block is newer than our current reasoning block
        for tool_block_id in self.tool_use_blocks.values():
            tool_timestamp = self.block_timestamps.get(tool_block_id, 0)
            if tool_timestamp > current_reasoning_timestamp:
                return True

        return False

    async def ensure_tool_use_block(
        self, message_id: str, tool_call_id: str, tool_name: str, tool_args: Dict[str, Any]
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Ensure tool use block exists for the given tool call, create if needed."""
        if tool_call_id not in self.tool_use_blocks:
            block_id = f"tool_{uuid.uuid4()}"
            self.tool_use_blocks[tool_call_id] = block_id
            self.current_blocks[block_id] = "tool_use"
            self.block_timestamps[block_id] = time.time()
            self.last_block_type = "tool_use"  # Track that we created a tool block

            yield StreamingEvent(
                event_type=EventType.BLOCK_START,
                block_id=block_id,
                block_type=MessageBlockType.TOOL_USE,
                message_id=message_id,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                tool_args=tool_args,
            )

    def get_tool_use_block_id(self, tool_call_id: str) -> Optional[str]:
        """Get the block ID for a specific tool call."""
        return self.tool_use_blocks.get(tool_call_id)

    async def ensure_reasoning_block(self, message_id: str) -> AsyncGenerator[StreamingEvent, None]:
        """Ensure reasoning block exists, create if needed."""
        if self.reasoning_block_id is None:
            self.reasoning_block_id = f"reasoning_{uuid.uuid4()}"
            self.current_blocks[self.reasoning_block_id] = "reasoning"
            self.block_timestamps[self.reasoning_block_id] = time.time()
            self.last_block_type = "reasoning"  # Track that we created a reasoning block

            yield StreamingEvent(
                event_type=EventType.BLOCK_START,
                block_id=self.reasoning_block_id,
                block_type=MessageBlockType.REASONING,
                message_id=message_id,
            )

    async def ensure_regular_block(self, message_id: str) -> AsyncGenerator[StreamingEvent, None]:
        """Ensure regular content block exists, create if needed."""
        # Create a new regular block if:
        # 1. No regular block exists yet, OR
        # 2. The last block created was not a regular block (meaning there was an interruption)
        should_create_new_block = self.regular_block_id is None or self.last_block_type not in [None, "plain"]

        if should_create_new_block:
            self.regular_block_id = f"plain_{uuid.uuid4()}"
            self.current_blocks[self.regular_block_id] = "plain"
            self.block_timestamps[self.regular_block_id] = time.time()
            self.last_block_type = "plain"  # Track that we created a regular block

            yield StreamingEvent(
                event_type=EventType.BLOCK_START, block_id=self.regular_block_id, block_type=MessageBlockType.PLAIN, message_id=message_id
            )

    async def ensure_summary_block(self, message_id: str) -> AsyncGenerator[StreamingEvent, None]:
        """Ensure summary block exists, create if needed."""
        if self.summary_block_id is None:
            self.summary_block_id = f"summary_{uuid.uuid4()}"
            self.current_blocks[self.summary_block_id] = "summary"
            self.block_timestamps[self.summary_block_id] = time.time()
            self.last_block_type = "summary"  # Track that we created a summary block

        # Note: We don't yield BLOCK_START for summary blocks as they're handled differently
        # This is an async generator so we need at least one yield or return to make it work
        return
        yield  # This line will never be reached but satisfies the type checker

    def get_reasoning_block_id(self) -> Optional[str]:
        """Get the reasoning block ID."""
        return self.reasoning_block_id

    def get_regular_block_id(self) -> Optional[str]:
        """Get the regular content block ID."""
        return self.regular_block_id

    def get_summary_block_id(self) -> Optional[str]:
        """Get the summary block ID."""
        return self.summary_block_id

    def has_reasoning_activity(self) -> bool:
        """Check if reasoning activity has been detected."""
        return self.reasoning_detected
