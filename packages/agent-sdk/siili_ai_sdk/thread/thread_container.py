import copy
import time
import uuid
from typing import Callable, Dict, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage

from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
from siili_ai_sdk.llm.converters import convert_thread_message_to_langchain
from siili_ai_sdk.thread.models import (
    BlockAddedEvent,
    BlockFullyAddedEvent,
    MessageAddedEvent,
    MessageBlock,
    MessageBlockType,
    MessageFullyAddedEvent,
    StreamingEndedEvent,
    StreamingUpdatedEvent,
    ThreadEvent,
    ThreadMessage,
    ToolCallResponse,
    ToolCallStartedEvent,
    ToolResponseReceivedEvent,
)
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ThreadContainer:
    def __init__(self, system_prompt: Optional[str] = None):
        self.messages: List[ThreadMessage] = []
        self.streaming_content: Dict[str, str] = {}
        self.tool_call_responses: Dict[str, ToolCallResponse] = {}
        self.system_prompt = system_prompt
        # Single event stream with multiple subscribers
        self._subscribers: List[Callable[[ThreadEvent], None]] = []

        # Version tracking
        self._version = 0
        self._last_activity_time = int(time.time() * 1000)
        self.thread_id = str(uuid.uuid4())
        self.job_id = "unknown"

    def subscribe(self, callback: Callable[[ThreadEvent], None]) -> None:
        """Subscribe to the event stream"""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[ThreadEvent], None]) -> None:
        """Unsubscribe from the event stream"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _emit_event(self, event: ThreadEvent) -> None:
        """Emit a typed event to all subscribers"""
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    def _increment_version(self) -> None:
        """Increment version and update activity time"""
        self._version += 1
        self._last_activity_time = int(time.time() * 1000)

    def get_version(self) -> int:
        """Get current version for incremental updates"""
        return self._version

    def get_last_activity_time(self) -> int:
        """Get timestamp of last activity"""
        return self._last_activity_time

    def add_streaming_message_chunk(self, block_id: str, content: str) -> None:
        """Update streaming content by appending new content to existing content for the block_id"""
        if block_id in self.streaming_content:
            self.streaming_content[block_id] += content
        else:
            self.streaming_content[block_id] = content

        # Emit streaming update event
        self._emit_event(StreamingUpdatedEvent(block_id=block_id, content=content, total_content=self.streaming_content[block_id]))

        self._increment_version()

    def add_message(self, msg: ThreadMessage) -> None:
        """Add a new message to the thread"""
        self.messages.append(msg)
        self._emit_event(MessageAddedEvent(message=copy.deepcopy(msg)))
        self._increment_version()

    def add_message_block(self, message_id: str, block: MessageBlock) -> None:
        """Add a message block to an existing message by message_id"""
        for message in self.messages:
            if message.id == message_id:
                message.blocks.append(block)

                # Emit block added event
                self._emit_event(BlockAddedEvent(message_id=message_id, block_id=block.id, block=copy.deepcopy(block)))

                # If it's a tool block, emit tool call started
                if block.type == MessageBlockType.TOOL_USE and block.tool_call_id:
                    tool_name = block.tool_name or "unknown"

                    self._emit_event(
                        ToolCallStartedEvent(tool_call_id=block.tool_call_id, tool_name=tool_name, message_id=message_id, block_id=block.id)
                    )

                self._increment_version()
                break

    def add_tool_call_response(self, response: ToolCallResponse) -> None:
        """Add a tool call response by its ID"""
        self.tool_call_responses[response.id] = response

        # Find the corresponding block ID
        block_id = None
        for message in self.messages:
            for block in message.blocks:
                if block.tool_call_id == response.id:
                    block.streaming = False
                    block.tool_call_response = response.response
                    block.tool_call_error = response.error
                    block_id = block.id
                    break
            if block_id:
                break

        # Emit tool response event
        self._emit_event(
            ToolResponseReceivedEvent(tool_call_id=response.id, response=response.response, error=response.error, block_id=block_id)
        )

        self._increment_version()

    def update_tool_use_block_with_response(self, tool_call_id: str, response: str, error: Optional[str] = None) -> None:
        """Update a tool use block with the tool response and mark it as completed."""
        logger.debug(f"🔧 DEBUG: Updating tool response for {tool_call_id}")
        logger.debug(f"🔧 DEBUG: Response: {response[:100]}...")
        logger.debug(f"🔧 DEBUG: Error: {error}")

        # Add the tool response to our responses dict
        tool_response = ToolCallResponse(id=tool_call_id, response=response, error=error)
        self.add_tool_call_response(tool_response)

        # Find the message and block with this tool_call_id and mark it as non-streaming
        for message in self.messages:
            for block in message.blocks:
                if block.tool_call_id == tool_call_id:
                    block.streaming = False
                    logger.debug(f"🔧 DEBUG: Found and updated block {block.id} for tool {tool_call_id}")
                    self._increment_version()
                    return

        logger.debug(f"🔧 DEBUG: Could not find block for tool_call_id: {tool_call_id}")

    def add_error_message(self, error_text: str, author_id: str = "system", author_name: str = "system") -> str:
        """Add an error message and return the message ID"""
        message_id = str(uuid.uuid4())
        error_message = ThreadMessage(
            id=message_id,
            ai=True,
            author_id=author_id,
            author_name=author_name,
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.ERROR,
                )
            ],
        )
        self.add_message(error_message)
        return message_id

    def finalize_streaming_blocks(self, message_id: str, block_ids: List[str]) -> None:
        """Mark specified blocks as non-streaming (completed)."""
        completed_blocks = []

        for message in self.messages:
            if message.id == message_id:
                for block in message.blocks:
                    if block.id in block_ids and block.streaming:
                        block.streaming = False
                        # Move content from streaming_content to block.content when streaming finishes
                        if block.id in self.streaming_content:
                            block.content = self.streaming_content[block.id]
                            # lets not do this, access is needed at least for now
                            # # Optionally remove from streaming_content to save memory
                            # del self.streaming_content[block.id]
                        completed_blocks.append(block.id)

                        # Emit block fully added event for each completed block
                        self._emit_event(BlockFullyAddedEvent(block_id=block.id, message_id=message_id, block=copy.deepcopy(block)))
                break

        if completed_blocks:
            self._increment_version()

            # Check if streaming has ended
            if not self.is_streaming_active():
                self._emit_event(StreamingEndedEvent(message_id=message_id, completed_blocks=completed_blocks))

    def cancel_generation(self) -> None:
        """Cancel the generation"""
        logger.info(f"Cancelling generation. Current streaming content: {self.streaming_content}")
        logger.info(f"Messages: {self.messages}")
        for message in self.messages:
            completed_blocks = []
            for block in message.blocks:
                block.streaming = False
                # Move content from streaming_content to block.content when streaming finishes
                if block.id in self.streaming_content:
                    block.content = self.streaming_content[block.id]
                    logger.info(f"🔧 Block {block.id} content: {block.content}")
                completed_blocks.append(block.id)
                self._emit_event(BlockFullyAddedEvent(block_id=block.id, message_id=message.id, block=copy.deepcopy(block)))
            self.finalize_streaming_blocks(message.id, completed_blocks)
        if completed_blocks:
            self._increment_version()

            # Check if streaming has ended
            if not self.is_streaming_active():
                self._emit_event(StreamingEndedEvent(message_id=message.id, completed_blocks=completed_blocks))

    def complete_generation(self) -> None:
        """Mark the message as fully added and emit the event"""
        latest_message = self.get_latest_ai_message()
        if latest_message:
            self._emit_event(MessageFullyAddedEvent(message=copy.deepcopy(latest_message)))

    def is_streaming_active(self) -> bool:
        """Check if any blocks are currently streaming"""
        for message in self.messages:
            for block in message.blocks:
                if block.streaming:
                    return True
        return False

    def get_latest_ai_message(self) -> Optional[ThreadMessage]:
        """Get the most recent AI message"""
        for message in reversed(self.messages):
            if message.ai:
                return message
        return None

    def get_latest_message(self) -> ThreadMessage:
        """Get the most recent message"""
        return self.messages[-1]

    def get_message_by_id(self, message_id: str) -> Optional[ThreadMessage]:
        """Get message by ID"""
        for message in self.messages:
            if message.id == message_id:
                return message
        return None

    def get_block_content(self, block: MessageBlock) -> str:
        """Get content for a specific block"""
        # First check if block has content directly
        if block.content is not None:
            return block.content

        # For streaming blocks, check streaming_content
        if block.id in self.streaming_content:
            return self.streaming_content[block.id]

        if block.type == MessageBlockType.TOOL_USE:
            if block.tool_call_id and block.tool_call_id in self.tool_call_responses:
                response = self.tool_call_responses[block.tool_call_id]
                return response.response

        return ""

    def get_system_prompt(self) -> str:
        if self.system_prompt is None:
            raise ValueError("System prompt is not set")
        return self.system_prompt

    def get_streaming_blocks(self) -> List[str]:
        """Get list of currently streaming block IDs"""
        streaming_blocks = []
        for message in self.messages:
            for block in message.blocks:
                if block.streaming:
                    streaming_blocks.append(block.id)
        return streaming_blocks

    def has_errors(self) -> bool:
        """Check if there are any error blocks or tool errors"""
        for message in self.messages:
            for block in message.blocks:
                if block.type == MessageBlockType.ERROR:
                    return True

        for response in self.tool_call_responses.values():
            if response.error:
                return True

        return False

    def get_final_text_content(self) -> str:
        """Get clean final text from the latest AI message"""
        latest_message = self.get_latest_ai_message()
        if not latest_message:
            return ""

        text_parts = []
        for block in latest_message.blocks:
            if block.type == MessageBlockType.PLAIN and not block.streaming:
                content = self.get_block_content(block)
                if content:
                    text_parts.append(content)

        return " ".join(text_parts).strip()

    def _find_message_id_by_block(self, block_id: str) -> Optional[str]:
        """Find message ID that contains the given block ID"""
        for message in self.messages:
            for block in message.blocks:
                if block.id == block_id:
                    return message.id
        return None

    def get_langchain_messages(self) -> List[BaseMessage]:
        """Get all messages as LangChain BaseMessages"""
        messages: List[BaseMessage] = [SystemMessage(content=self.get_system_prompt())]
        messages.extend([convert_thread_message_to_langchain(msg) for msg in self.messages])
        return messages

    def get_nof_messages_including_system(self) -> int:
        """Get number of messages including system message"""
        return len(self.messages) + 1

    def add_consumption_metadata(self, message_id: str, consumption_metadata: TokenUsage) -> None:
        """Add consumption metadata to a specific message"""
        for message in self.messages:
            if message.id == message_id:
                message.consumption_metadata = consumption_metadata
                self._increment_version()
                break

    def get_total_consumption(self) -> TokenUsage:
        """Calculate total consumption across all messages with consumption metadata"""
        total_tokens = TokenUsage()

        for message in self.messages:
            if message.consumption_metadata and isinstance(message.consumption_metadata, TokenUsage):
                token_usage = message.consumption_metadata
                total_tokens.input_tokens += token_usage.input_tokens
                total_tokens.output_tokens += token_usage.output_tokens
                total_tokens.total_tokens += token_usage.total_tokens
                total_tokens.reasoning_tokens += token_usage.reasoning_tokens
                total_tokens.cache_creation_tokens += token_usage.cache_creation_tokens
                total_tokens.cache_read_tokens += token_usage.cache_read_tokens

        return total_tokens

    def get_consumption_by_message(self, message_id: str) -> Optional[TokenUsage]:
        """Get consumption metadata for a specific message"""
        for message in self.messages:
            if message.id == message_id and message.consumption_metadata:
                return message.consumption_metadata
        return None

    def get_latest_token_usage(self) -> Optional[TokenUsage]:
        """Get consumption metadata for the latest message"""
        latest_message = self.get_latest_ai_message()
        if latest_message and latest_message.consumption_metadata:
            return latest_message.consumption_metadata
        return None

    def __str__(self) -> str:
        """String representation of the entire thread container"""
        lines = ["=== THREAD CONTAINER ==="]
        lines.append(f"Version: {self._version} | Active streaming: {self.is_streaming_active()}")

        lines.append(f"\n📨 MESSAGES ({len(self.messages)}):")
        for i, msg in enumerate(self.messages):
            author = "🤖 AI" if msg.ai else f"👤 {msg.author_id}"
            lines.append(f"  [{i}] {author} | {msg.id} | {msg.timestamp}")
            for j, block in enumerate(msg.blocks):
                if block.type == MessageBlockType.ERROR:
                    stream_indicator = "❌"
                elif block.type == MessageBlockType.REASONING:
                    stream_indicator = "🧠" if not block.streaming else "🤔"
                elif block.streaming:
                    stream_indicator = "🌊"
                else:
                    stream_indicator = "✅"
                tool_info = f" | tool_id: {block.tool_call_id}" if block.tool_call_id else ""

                # Get content preview for the block
                content = self.get_block_content(block)
                content_preview = content[:50] + "..." if len(content) > 50 else content
                content_info = f" | {repr(content_preview)}" if content else " (no content)"

                lines.append(f"    [{j}] {stream_indicator} {block.type.value} | {block.id}{tool_info}{content_info}")

        lines.append(f"\n🌊 STREAMING CONTENT ({len(self.streaming_content)}):")
        for block_id, content in self.streaming_content.items():
            preview = content[:50] + "..." if len(content) > 50 else content
            lines.append(f"  {block_id}: {repr(preview)}")

        lines.append(f"\n🔧 TOOL CALL RESPONSES ({len(self.tool_call_responses)}):")
        for tool_id, response in self.tool_call_responses.items():
            error_indicator = "❌" if response.error else "✅"
            preview = response.response[:50] + "..." if len(response.response) > 50 else response.response
            lines.append(f"  {error_indicator} {tool_id}: {repr(preview)}")
            if response.error:
                lines.append(f"    Error: {response.error}")

        # Add consumption summary
        total_consumption = self.get_total_consumption()
        consumption_messages = sum(1 for msg in self.messages if msg.consumption_metadata)
        total_messages = len(self.messages)
        lines.append(f"\n📊 CONSUMPTION SUMMARY ({consumption_messages}/{total_messages} messages):")

        if consumption_messages > 0:
            lines.append(f"  Total tokens: {total_consumption.total_tokens:,}")
            lines.append(f"  Input: {total_consumption.input_tokens:,} | Output: {total_consumption.output_tokens:,}")
            if total_consumption.reasoning_tokens > 0:
                lines.append(f"  Reasoning: {total_consumption.reasoning_tokens:,}")
            if total_consumption.cache_creation_tokens > 0 or total_consumption.cache_read_tokens > 0:
                lines.append(
                    f"  Cache create: {total_consumption.cache_creation_tokens:,} | Cache read: {total_consumption.cache_read_tokens:,}"
                )
        else:
            lines.append("  No consumption data available")

        return "\n".join(lines)

    def print_all(self) -> None:
        """Print everything to console for debugging"""
        print(str(self))

    def create_serializable_copy(self) -> "ThreadContainer":
        """Create a copy of this ThreadContainer that can be safely pickled"""
        # Create new instance without calling __init__ to avoid subscriber initialization
        copy = ThreadContainer.__new__(ThreadContainer)

        # Copy all serializable attributes
        copy.messages = self.messages.copy()
        copy.streaming_content = self.streaming_content.copy()
        copy.tool_call_responses = self.tool_call_responses.copy()
        copy.system_prompt = self.system_prompt
        copy._version = self._version
        copy._last_activity_time = self._last_activity_time
        copy.thread_id = self.thread_id
        copy.job_id = self.job_id

        # Initialize empty subscribers list (will be empty when loaded)
        copy._subscribers = []

        return copy
