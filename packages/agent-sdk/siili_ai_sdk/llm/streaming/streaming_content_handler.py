import uuid
from typing import Any, AsyncGenerator, Dict, Optional

from siili_ai_sdk.llm.streaming.block_manager import BlockManager
from siili_ai_sdk.llm.streaming.models import EventType, StreamingEvent
from siili_ai_sdk.llm.streaming.streaming_state_manager import StreamingStateManager
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class StreamingContentHandler:
    """Handles processing of reasoning and regular content during streaming."""

    def __init__(self, block_manager: BlockManager, state_manager: StreamingStateManager):
        self.block_manager = block_manager
        self.state_manager = state_manager

    async def handle_reasoning_content(self, reasoning_content: str) -> AsyncGenerator[StreamingEvent, None]:
        """Handle reasoning content and yield events."""
        async for event in self._ensure_streaming_started():
            yield event

        # Type guard to ensure message_id is not None
        if self.state_manager.current_message_id is None:
            return

        # Check if we need a new reasoning block based on timestamps
        if self.block_manager.should_create_new_reasoning_block():
            # Reset current reasoning block to force creation of a new one
            self.block_manager.reset_reasoning_block()

        # Check if this is creating a new reasoning block
        creating_new_block = self.block_manager.get_reasoning_block_id() is None

        # Ensure reasoning block exists
        async for streaming_event in self.block_manager.ensure_reasoning_block(self.state_manager.current_message_id):
            yield streaming_event

        # Track that we've created a reasoning block
        if creating_new_block:
            self.state_manager.increment_reasoning_blocks()

        # For Google models with thinking_budget, we might not have actual reasoning content
        # but we still want to show that reasoning is happening
        if not reasoning_content and self.block_manager.has_reasoning_activity():
            reasoning_content = "[Thinking process active - reasoning tokens being used internally]"

        # Always yield reasoning content (even if empty) to ensure thread container tracks it
        yield StreamingEvent(
            event_type=EventType.REASONING,
            content=reasoning_content,  # This could be empty string or placeholder text
            block_id=self.block_manager.get_reasoning_block_id(),
            message_id=self.state_manager.current_message_id,
        )

    async def handle_regular_content(self, regular_content: str) -> AsyncGenerator[StreamingEvent, None]:
        """Handle regular content and yield events."""
        async for event in self._ensure_streaming_started():
            yield event

        # Type guard to ensure message_id is not None
        if self.state_manager.current_message_id is None:
            return

        # Ensure regular block exists
        async for streaming_event in self.block_manager.ensure_regular_block(self.state_manager.current_message_id):
            yield streaming_event

        yield StreamingEvent(
            event_type=EventType.TOKEN,
            content=regular_content,
            block_id=self.block_manager.get_regular_block_id(),
            message_id=self.state_manager.current_message_id,
        )

    async def end_thinking_session_if_needed(self) -> AsyncGenerator[StreamingEvent, None]:
        """End thinking session and emit BLOCK_END event if needed."""
        if self.state_manager.in_thinking_session:
            self.state_manager.end_thinking_session()
            # Emit BLOCK_END event for the current reasoning block
            current_reasoning_block_id = self.block_manager.get_reasoning_block_id()
            if current_reasoning_block_id and self.state_manager.current_message_id:
                logger.debug(f"🔚 Emitting BLOCK_END for reasoning block: {current_reasoning_block_id}")
                yield StreamingEvent(
                    event_type=EventType.BLOCK_END, block_id=current_reasoning_block_id, message_id=self.state_manager.current_message_id
                )
            else:
                logger.debug(
                    "❌ Cannot emit BLOCK_END - block_id: %s, message_id: %s",
                    current_reasoning_block_id,
                    self.state_manager.current_message_id,
                )

    async def end_final_thinking_session_if_needed(self) -> AsyncGenerator[StreamingEvent, None]:
        """End thinking session at stream end if still active."""
        if self.state_manager.in_thinking_session:
            current_reasoning_block_id = self.block_manager.get_reasoning_block_id()
            if current_reasoning_block_id and self.state_manager.current_message_id:
                logger.debug(f"🔚 Stream ending - emitting BLOCK_END for final reasoning block: {current_reasoning_block_id}")
                yield StreamingEvent(
                    event_type=EventType.BLOCK_END, block_id=current_reasoning_block_id, message_id=self.state_manager.current_message_id
                )
            self.state_manager.end_thinking_session()

    async def _ensure_streaming_started(self) -> AsyncGenerator[StreamingEvent, None]:
        """Ensure streaming has been initialized and yield MESSAGE_START if needed."""
        if not self.state_manager.streaming_started:
            self.state_manager.current_message_id = str(uuid.uuid4())
            self.state_manager.streaming_started = True

            yield StreamingEvent(event_type=EventType.MESSAGE_START, message_id=self.state_manager.current_message_id)

    async def handle_tool_use(self, tool_call_id: str, tool_name: str, tool_args: Dict[str, Any]) -> AsyncGenerator[StreamingEvent, None]:
        """Handle tool use and yield events."""
        async for event in self._ensure_streaming_started():
            yield event

        # Type guard to ensure message_id is not None
        if self.state_manager.current_message_id is None:
            return

        # Ensure tool use block exists
        async for streaming_event in self.block_manager.ensure_tool_use_block(
            self.state_manager.current_message_id, tool_call_id, tool_name, tool_args
        ):
            yield streaming_event

        # Emit tool use event
        yield StreamingEvent(
            event_type=EventType.TOOL_USE,
            block_id=self.block_manager.get_tool_use_block_id(tool_call_id),
            message_id=self.state_manager.current_message_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_args=tool_args,
        )

    async def handle_tool_response(
        self, tool_call_id: str, response: str, error: Optional[str] = None
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Handle tool response and yield events."""
        if self.state_manager.current_message_id is None:
            return

        # Get the tool use block for this tool call
        block_id = self.block_manager.get_tool_use_block_id(tool_call_id)
        if block_id:
            # Emit tool response event
            yield StreamingEvent(
                event_type=EventType.TOOL_RESPONSE,
                content=response,
                block_id=block_id,
                message_id=self.state_manager.current_message_id,
                tool_call_id=tool_call_id,
                error=error,
            )
