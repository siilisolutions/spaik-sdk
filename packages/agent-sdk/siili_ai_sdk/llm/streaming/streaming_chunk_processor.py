from typing import AsyncGenerator, Optional

from siili_ai_sdk.llm.streaming.block_manager import BlockManager
from siili_ai_sdk.llm.streaming.content_parser import ContentParser
from siili_ai_sdk.llm.streaming.models import StreamingEvent
from siili_ai_sdk.llm.streaming.streaming_content_handler import StreamingContentHandler
from siili_ai_sdk.llm.streaming.streaming_state_manager import StreamingStateManager
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class StreamingChunkProcessor:
    """Processes individual streaming chunks and manages content flow."""

    def __init__(
        self,
        content_parser: ContentParser,
        block_manager: BlockManager,
        state_manager: StreamingStateManager,
        content_handler: StreamingContentHandler,
    ):
        self.content_parser = content_parser
        self.block_manager = block_manager
        self.state_manager = state_manager
        self.content_handler = content_handler

    async def process_chunk(self, chunk) -> AsyncGenerator[StreamingEvent, None]:
        """Handle individual stream chunk."""
        # Enhanced debug logging
        if hasattr(chunk, "additional_kwargs") and chunk.additional_kwargs:
            logger.trace(f"Chunk additional_kwargs: {chunk.additional_kwargs}")

            # Check for reasoning activity (OpenAI format)
            reasoning_data = chunk.additional_kwargs.get("reasoning")
            if reasoning_data:
                self.block_manager.mark_reasoning_detected()

        # Check for Google thinking activity via usage metadata
        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
            # Google reports thinking tokens in usage_metadata.output_token_details.reasoning
            if hasattr(chunk.usage_metadata, "output_token_details"):
                reasoning_tokens = getattr(chunk.usage_metadata.output_token_details, "reasoning", 0)
                if reasoning_tokens and reasoning_tokens > 0:
                    self.block_manager.mark_reasoning_detected()
                    logger.trace(f"Google thinking detected: {reasoning_tokens} reasoning tokens used")

        # Check for tool calls in the chunk
        tool_call_id, tool_name, tool_args = self.content_parser.parse_tool_calls(chunk)
        if tool_call_id and tool_name:
            logger.debug(f"Tool call detected: {tool_name} (id: {tool_call_id})")
            async for streaming_event in self.content_handler.handle_tool_use(tool_call_id, tool_name, tool_args or {}):
                yield streaming_event

        # Check for tool responses in the chunk
        tool_response_id, tool_response_content, tool_error = self.content_parser.parse_tool_response(chunk)
        if tool_response_id and (tool_response_content is not None or tool_error):
            logger.debug(f"Tool response detected for id: {tool_response_id}")
            async for streaming_event in self.content_handler.handle_tool_response(
                tool_response_id, tool_response_content or "", tool_error
            ):
                yield streaming_event

        # Check for Anthropic thinking format and detect interleaved thinking
        current_block_type = self._detect_block_type(chunk)

        # Parse content from chunk
        reasoning_content, regular_content = self.content_parser.parse_chunk_content(chunk)

        # Debug log parsed content
        if reasoning_content:
            logger.trace(f"Parsed reasoning content: {reasoning_content[:100]}...")
        if regular_content:
            logger.trace(f"Parsed regular content: {regular_content[:100]}...")

        # Debug state before processing
        logger.trace(
            "🔍 State: thinking=%s, last=%s, current=%s",
            self.state_manager.in_thinking_session,
            self.state_manager.last_block_type,
            current_block_type,
        )
        logger.trace("🔍 Content: reasoning=%s, regular=%s", bool(reasoning_content), bool(regular_content))
        # Detect mid-response thinking: create new reasoning block when transitioning from text
        # to thinking
        if self.state_manager.should_create_new_thinking_session(bool(reasoning_content), current_block_type or ""):
            logger.debug("NEW mid-response thinking session detected! Creating new reasoning block")
            logger.debug(
                "State: has_text=%s, last_type=%s, current_type=%s",
                self.state_manager.has_text_content,
                self.state_manager.last_block_type,
                current_block_type,
            )
            # Force creation of a new reasoning block for mid-response thinking
            self.block_manager.reset_reasoning_block()

        # Handle reasoning content or create empty reasoning block
        if reasoning_content:
            # Set thinking session flag whenever we have reasoning content
            self.state_manager.start_thinking_session()

            async for streaming_event in self.content_handler.handle_reasoning_content(reasoning_content):
                yield streaming_event
        elif self.block_manager.has_reasoning_activity() and self.block_manager.get_reasoning_block_id() is None:
            # Create empty reasoning block when we first detect reasoning activity
            # For Google models, this creates a placeholder since thinking isn't streamed
            async for streaming_event in self.content_handler.handle_reasoning_content(""):
                yield streaming_event

        # Handle regular content
        if regular_content:
            # Check if we need to end the current thinking session
            async for streaming_event in self.content_handler.end_thinking_session_if_needed():
                yield streaming_event

            async for streaming_event in self.content_handler.handle_regular_content(regular_content):
                yield streaming_event
            self.state_manager.mark_text_content_received()

        # Update state tracking
        if current_block_type:
            self.state_manager.update_block_type(current_block_type)

    def _detect_block_type(self, chunk) -> Optional[str]:
        """Detect the block type from chunk content."""
        current_block_type = None
        if hasattr(chunk, "content") and isinstance(chunk.content, list):
            for content_block in chunk.content:
                if isinstance(content_block, dict):
                    block_type = content_block.get("type")
                    if block_type in ["thinking", "thinking_content"]:
                        self.block_manager.mark_reasoning_detected()
                        current_block_type = "thinking"
                        break
                    elif block_type == "text":
                        current_block_type = "text"
        return current_block_type
