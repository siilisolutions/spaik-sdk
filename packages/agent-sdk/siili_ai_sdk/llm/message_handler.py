import time
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

from siili_ai_sdk.llm.streaming.streaming_event_handler import EventType, StreamingEventHandler
from siili_ai_sdk.recording.base_recorder import BaseRecorder
from siili_ai_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class MessageHandler:
    """Manages conversation message history using ThreadContainer."""

    def __init__(
        self,
        thread_container: ThreadContainer,
        assistant_name: str,
        assistant_id: str,
        recorder: Optional[BaseRecorder] = None,
    ):
        self.thread_container = thread_container
        self.streaming_handler = StreamingEventHandler(recorder)
        self.assistant_name = assistant_name
        self.assistant_id = assistant_id
        self._update_previous_message_count()

    def _update_previous_message_count(self) -> None:
        self._previous_message_count = self.thread_container.get_nof_messages_including_system() + 1

    def add_user_message(self, user_input: str, author_id: str, author_name: str) -> None:
        """Add a user message to both thread container and LangChain messages."""

        # Add to thread container
        block_id = str(uuid.uuid4())
        user_message = ThreadMessage(
            id=str(uuid.uuid4()),
            ai=False,
            author_id=author_id,
            author_name=author_name,
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id=block_id,
                    streaming=False,
                    type=MessageBlockType.PLAIN,
                    content=user_input,
                )
            ],
        )
        self.thread_container.add_message(user_message)

        # Add to LangChain messages for compatibility
        self._update_previous_message_count()

    def add_error(self, error_text: str, author_id: str = "system") -> str:
        """Add an error message to the thread container and return message ID"""
        return self.thread_container.add_error_message(error_text, author_id)

    def handle_cancellation(self) -> None:
        """Handle cancellation of the agent."""
        self.thread_container.cancel_generation()

    async def process_agent_token_stream(
        self,
        agent_stream,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process agent event stream for individual tokens and yield them in real-time."""
        async for streaming_event in self.streaming_handler.process_stream(agent_stream):
            if streaming_event.event_type == EventType.MESSAGE_START:
                logger.debug(f"🔍 Processing MESSAGE_START for message: {streaming_event.message_id}")
                # Create AI message in thread container
                assert streaming_event.message_id is not None
                ai_message = ThreadMessage(
                    id=streaming_event.message_id,
                    ai=True,
                    author_id=self.assistant_id,
                    author_name=self.assistant_name,
                    timestamp=int(time.time() * 1000),
                    blocks=[],
                )
                self.thread_container.add_message(ai_message)

            elif streaming_event.event_type == EventType.BLOCK_START:
                logger.debug(f"🔍 Processing BLOCK_START for block: {streaming_event.block_id}")
                # Add new block to the message
                assert streaming_event.block_id is not None
                assert streaming_event.block_type is not None
                assert streaming_event.message_id is not None
                new_block = MessageBlock(
                    id=streaming_event.block_id,
                    streaming=True,
                    type=streaming_event.block_type,
                    tool_call_id=streaming_event.tool_call_id,
                    tool_call_args=streaming_event.tool_args,
                    tool_name=streaming_event.tool_name,
                )
                self.thread_container.add_message_block(streaming_event.message_id, new_block)

            elif streaming_event.event_type == EventType.BLOCK_END:
                logger.debug(f"🔚 Processing BLOCK_END for block: {streaming_event.block_id}")
                # Mark individual block as non-streaming (completed)
                assert streaming_event.block_id is not None
                assert streaming_event.message_id is not None
                logger.debug(f"🔚 Processing BLOCK_END for block: {streaming_event.block_id}")
                self.thread_container.finalize_streaming_blocks(streaming_event.message_id, [streaming_event.block_id])
                logger.debug(f"✅ Block {streaming_event.block_id} marked as completed")

            elif streaming_event.event_type in [EventType.REASONING, EventType.REASONING_SUMMARY, EventType.TOKEN]:
                logger.debug(f"🔍 Processing {streaming_event.event_type.value} for block: {streaming_event.block_id}")
                # Add streaming content
                assert streaming_event.block_id is not None
                assert streaming_event.content is not None
                self.thread_container.add_streaming_message_chunk(streaming_event.block_id, streaming_event.content)

                # Yield for external consumption
                yield {
                    "type": streaming_event.event_type.value,
                    "content": streaming_event.content,
                    "block_id": streaming_event.block_id,
                    "message_id": streaming_event.message_id,
                }

            elif streaming_event.event_type == EventType.USAGE_METADATA:
                logger.info(f"📊 Processing USAGE_METADATA for message: {streaming_event.message_id}")
                # Store consumption metadata in ThreadContainer
                if streaming_event.message_id and streaming_event.usage_metadata:
                    self.thread_container.add_consumption_metadata(streaming_event.message_id, streaming_event.usage_metadata)
                # Yield usage metadata for external consumption
                yield {
                    "type": "usage_metadata",
                    "message_id": streaming_event.message_id,
                    "usage_metadata": streaming_event.usage_metadata,
                }

            elif streaming_event.event_type == EventType.COMPLETE:
                logger.debug(f"🔍 Processing COMPLETE for message: {streaming_event.message_id}")
                # Mark all blocks as non-streaming
                if streaming_event.message_id and streaming_event.blocks:
                    self.thread_container.finalize_streaming_blocks(streaming_event.message_id, streaming_event.blocks)

                yield {
                    "type": "complete",
                    "message": streaming_event.message,
                    "blocks": streaming_event.blocks,
                    "message_id": streaming_event.message_id,
                }

            elif streaming_event.event_type == EventType.TOOL_USE:
                logger.debug(f"🔍 Processing TOOL_USE for block: {streaming_event.block_id}")
                # Handle tool use event - the block is already created, just yield for external consumption
                yield {
                    "type": "tool_use",
                    "tool_call_id": streaming_event.tool_call_id,
                    "tool_name": streaming_event.tool_name,
                    "tool_args": streaming_event.tool_args,
                    "block_id": streaming_event.block_id,
                    "message_id": streaming_event.message_id,
                }

            elif streaming_event.event_type == EventType.TOOL_RESPONSE:
                logger.debug(f"🔍 Processing TOOL_RESPONSE for block: {streaming_event.block_id}")
                # Handle tool response - update the thread container with the response
                assert streaming_event.tool_call_id is not None
                assert streaming_event.content is not None
                self.thread_container.update_tool_use_block_with_response(
                    streaming_event.tool_call_id, streaming_event.content, streaming_event.error
                )

                # Yield for external consumption
                yield {
                    "type": "tool_response",
                    "tool_call_id": streaming_event.tool_call_id,
                    "response": streaming_event.content,
                    "error": streaming_event.error,
                    "block_id": streaming_event.block_id,
                    "message_id": streaming_event.message_id,
                }
