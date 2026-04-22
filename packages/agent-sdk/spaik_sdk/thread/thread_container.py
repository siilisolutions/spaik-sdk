import copy
import time
import uuid
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage

from spaik_sdk.attachments.storage.base_file_storage import BaseFileStorage
from spaik_sdk.llm.consumption.token_usage import TokenUsage
from spaik_sdk.llm.converters import convert_thread_message_to_langchain, convert_thread_message_to_langchain_multimodal
from spaik_sdk.thread.models import (
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
from spaik_sdk.utils.init_logger import init_logger

if TYPE_CHECKING:
    from spaik_sdk.tools.tool_provider import ToolProvider

logger = init_logger(__name__)


class ThreadContainer:
    def __init__(self, system_prompt: Optional[str] = None):
        self.messages: List[ThreadMessage] = []
        self.streaming_content: Dict[str, str] = {}
        self.tool_call_responses: Dict[str, ToolCallResponse] = {}
        self.system_prompt = system_prompt
        self._subscribers: List[Callable[[ThreadEvent], None]] = []

        self._version = 0
        self._last_activity_time = int(time.time() * 1000)
        self.thread_id = str(uuid.uuid4())
        self.job_id = "unknown"

    def subscribe(self, callback: Callable[[ThreadEvent], None]) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[ThreadEvent], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _emit_event(self, event: ThreadEvent) -> None:
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    def _increment_version(self) -> None:
        self._version += 1
        self._last_activity_time = int(time.time() * 1000)

    def get_version(self) -> int:
        return self._version

    def get_last_activity_time(self) -> int:
        return self._last_activity_time

    def add_streaming_message_chunk(self, block_id: str, content: str) -> None:
        if block_id in self.streaming_content:
            self.streaming_content[block_id] += content
        else:
            self.streaming_content[block_id] = content

        self._emit_event(StreamingUpdatedEvent(block_id=block_id, content=content, total_content=self.streaming_content[block_id]))
        self._increment_version()

    def add_message(self, msg: ThreadMessage) -> None:
        self.messages.append(msg)
        self._emit_event(MessageAddedEvent(message=self._copy_message_without_live_providers(msg)))
        self._increment_version()

    def add_message_block(self, message_id: str, block: MessageBlock) -> None:
        for message in self.messages:
            if message.id != message_id:
                continue

            existing_block_index = next((index for index, existing_block in enumerate(message.blocks) if existing_block.id == block.id), -1)
            is_new_block = existing_block_index == -1
            if is_new_block:
                message.blocks.append(block)
            else:
                existing_block = message.blocks[existing_block_index]
                if block.tool_call_response is None:
                    block.tool_call_response = existing_block.tool_call_response
                if block.tool_call_error is None:
                    block.tool_call_error = existing_block.tool_call_error
                message.blocks[existing_block_index] = block

            self._emit_event(BlockAddedEvent(message_id=message_id, block_id=block.id, block=self._copy_block_without_live_provider(block)))

            if is_new_block and block.type == MessageBlockType.TOOL_USE and block.tool_call_id:
                self._emit_event(
                    ToolCallStartedEvent(
                        tool_call_id=block.tool_call_id,
                        tool_name=block.tool_name or "unknown",
                        message_id=message_id,
                        block_id=block.id,
                    )
                )

            self._increment_version()
            break

    def add_tool_call_response(self, response: ToolCallResponse) -> None:
        """Record a tool call response and finalize the matching tool-use block.

        Always emits ToolResponseReceivedEvent. BlockFullyAddedEvent is emitted via
        _mark_block_complete only on the streaming->done transition, so calling this
        twice for the same tool_call_id emits the completion event at most once.
        """
        self.tool_call_responses[response.id] = response

        target_message_id: Optional[str] = None
        target_block: Optional[MessageBlock] = None
        for message in self.messages:
            for block in message.blocks:
                if block.tool_call_id == response.id:
                    block.tool_call_response = response.response
                    block.tool_call_error = response.error
                    target_block = block
                    target_message_id = message.id
                    break
            if target_block is not None:
                break

        block_id = target_block.id if target_block is not None else None
        self._emit_event(
            ToolResponseReceivedEvent(tool_call_id=response.id, response=response.response, error=response.error, block_id=block_id)
        )

        if target_block is not None and target_message_id is not None:
            self._mark_block_complete(target_message_id, target_block)

        self._increment_version()

    def update_tool_use_block_with_response(self, tool_call_id: str, response: str, error: Optional[str] = None) -> None:
        """Record a tool response and finalize its block. Thin wrapper over add_tool_call_response."""
        self.add_tool_call_response(ToolCallResponse(id=tool_call_id, response=response, error=error))

    def add_error_message(self, error_text: str, author_id: str = "system", author_name: str = "system") -> str:
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
                    content=error_text,
                )
            ],
        )
        self.add_message(error_message)
        return message_id

    def finalize_streaming_blocks(self, message_id: str, block_ids: List[str]) -> None:
        """Mark specified blocks as non-streaming (completed)."""
        completed_blocks: List[str] = []

        for message in self.messages:
            if message.id != message_id:
                continue
            for block in message.blocks:
                if block.id in block_ids and self._mark_block_complete(message_id, block):
                    completed_blocks.append(block.id)
            break

        if completed_blocks:
            self._increment_version()
            if not self.is_streaming_active():
                self._emit_event(StreamingEndedEvent(message_id=message_id, completed_blocks=completed_blocks))

    def cancel_generation(self) -> None:
        """Cancel the generation and finalize any in-flight blocks."""
        logger.info(f"Cancelling generation. Current streaming content: {self.streaming_content}")
        for message in self.messages:
            completed_blocks: List[str] = []
            for block in message.blocks:
                if self._mark_block_complete(message.id, block):
                    completed_blocks.append(block.id)
            if completed_blocks:
                self._increment_version()
                if not self.is_streaming_active():
                    self._emit_event(StreamingEndedEvent(message_id=message.id, completed_blocks=completed_blocks))

    def _mark_block_complete(self, message_id: str, block: MessageBlock) -> bool:
        """Finalize a streaming block: flush buffered content, flip streaming flag,
        emit BlockFullyAddedEvent. Idempotent; returns True iff the block transitioned."""
        if not block.streaming:
            return False
        block.streaming = False
        if block.id in self.streaming_content:
            block.content = self.streaming_content[block.id]
        self._emit_event(
            BlockFullyAddedEvent(
                block_id=block.id,
                message_id=message_id,
                block=self._copy_block_without_live_provider(block),
            )
        )
        return True

    def complete_generation(self) -> None:
        latest_message = self.get_latest_ai_message()
        if latest_message:
            self._emit_event(MessageFullyAddedEvent(message=self._copy_message_without_live_providers(latest_message)))

    def is_streaming_active(self) -> bool:
        for message in self.messages:
            for block in message.blocks:
                if block.streaming:
                    return True
        return False

    def get_latest_ai_message(self) -> Optional[ThreadMessage]:
        for message in reversed(self.messages):
            if message.ai:
                return message
        return None

    def get_latest_message(self) -> ThreadMessage:
        return self.messages[-1]

    def get_message_by_id(self, message_id: str) -> Optional[ThreadMessage]:
        for message in self.messages:
            if message.id == message_id:
                return message
        return None

    def get_block_content(self, block: MessageBlock) -> str:
        if block.content is not None:
            return block.content

        if block.id in self.streaming_content:
            return self.streaming_content[block.id]

        if block.type == MessageBlockType.TOOL_USE and block.tool_call_id and block.tool_call_id in self.tool_call_responses:
            return self.tool_call_responses[block.tool_call_id].response

        return ""

    def get_system_prompt(self) -> str:
        if self.system_prompt is None:
            raise ValueError("System prompt is not set")
        return self.system_prompt

    def get_streaming_blocks(self) -> List[str]:
        return [block.id for message in self.messages for block in message.blocks if block.streaming]

    def has_errors(self) -> bool:
        for message in self.messages:
            for block in message.blocks:
                if block.type == MessageBlockType.ERROR:
                    return True

        return any(response.error for response in self.tool_call_responses.values())

    def get_final_text_content(self) -> str:
        latest_message = self.get_latest_ai_message()
        if not latest_message:
            return ""

        text_parts: List[str] = []
        for block in latest_message.blocks:
            if block.type != MessageBlockType.PLAIN or block.streaming:
                continue
            content = self.get_block_content(block)
            if content:
                text_parts.append(content)
        return " ".join(text_parts).strip()

    def _find_message_id_by_block(self, block_id: str) -> Optional[str]:
        for message in self.messages:
            for block in message.blocks:
                if block.id == block_id:
                    return message.id
        return None

    def get_langchain_messages(self) -> List[BaseMessage]:
        messages: List[BaseMessage] = [SystemMessage(content=self.get_system_prompt())]
        messages.extend(convert_thread_message_to_langchain(msg) for msg in self.messages)
        return messages

    async def get_langchain_messages_multimodal(
        self,
        file_storage: BaseFileStorage,
        provider_family: str = "openai",
    ) -> List[BaseMessage]:
        messages: List[BaseMessage] = [SystemMessage(content=self.get_system_prompt())]
        for msg in self.messages:
            converted = await convert_thread_message_to_langchain_multimodal(
                msg,
                file_storage,
                provider_family,
            )
            messages.append(converted)
        return messages

    def bind_tool_providers(self, tool_providers: List["ToolProvider"]) -> None:
        provider_by_id = {provider.get_provider_id(): provider for provider in tool_providers}
        for message in self.messages:
            for block in message.blocks:
                if block.type != MessageBlockType.TOOL_USE:
                    continue
                if block.tool_provider_id is None:
                    continue
                block.tool_provider = provider_by_id.get(block.tool_provider_id)

    def get_nof_messages_including_system(self) -> int:
        return len(self.messages) + 1

    def add_consumption_metadata(self, message_id: str, consumption_metadata: TokenUsage) -> None:
        for message in self.messages:
            if message.id == message_id:
                message.consumption_metadata = consumption_metadata
                self._increment_version()
                break

    def get_total_consumption(self) -> TokenUsage:
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
        for message in self.messages:
            if message.id == message_id and message.consumption_metadata:
                return message.consumption_metadata
        return None

    def get_latest_token_usage(self) -> Optional[TokenUsage]:
        latest_message = self.get_latest_ai_message()
        if latest_message and latest_message.consumption_metadata:
            return latest_message.consumption_metadata
        return None

    def __str__(self) -> str:
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
        print(str(self))

    def create_serializable_copy(self) -> "ThreadContainer":
        """Create a copy that can be safely pickled, with live providers and subscribers stripped."""
        thread_copy = ThreadContainer.__new__(ThreadContainer)
        thread_copy.messages = [self._copy_message_without_live_providers(message) for message in self.messages]
        thread_copy.streaming_content = self.streaming_content.copy()
        thread_copy.tool_call_responses = copy.deepcopy(self.tool_call_responses)
        thread_copy.system_prompt = self.system_prompt
        thread_copy._version = self._version
        thread_copy._last_activity_time = self._last_activity_time
        thread_copy.thread_id = self.thread_id
        thread_copy.job_id = self.job_id
        thread_copy._subscribers = []
        return thread_copy

    def _copy_block_without_live_provider(self, block: MessageBlock) -> MessageBlock:
        return MessageBlock(
            id=block.id,
            streaming=block.streaming,
            type=block.type,
            content=block.content,
            tool_provider_id=block.tool_provider_id,
            tool_call_id=block.tool_call_id,
            tool_call_args=copy.deepcopy(block.tool_call_args),
            tool_name=block.tool_name,
            tool_call_response=block.tool_call_response,
            tool_call_error=block.tool_call_error,
        )

    def _copy_message_without_live_providers(self, message: ThreadMessage) -> ThreadMessage:
        return ThreadMessage(
            id=message.id,
            ai=message.ai,
            author_id=message.author_id,
            author_name=message.author_name,
            timestamp=message.timestamp,
            blocks=[self._copy_block_without_live_provider(block) for block in message.blocks],
            consumption_metadata=copy.deepcopy(message.consumption_metadata),
            attachments=copy.deepcopy(message.attachments),
        )
