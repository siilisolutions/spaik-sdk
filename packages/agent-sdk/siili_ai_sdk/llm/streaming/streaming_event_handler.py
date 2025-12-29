from typing import AsyncGenerator, Optional, Union

from langchain_core.messages import AIMessage, AIMessageChunk

from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
from siili_ai_sdk.llm.streaming.block_manager import BlockManager
from siili_ai_sdk.llm.streaming.models import EventType, StreamingEvent
from siili_ai_sdk.llm.streaming.streaming_content_handler import StreamingContentHandler
from siili_ai_sdk.llm.streaming.streaming_state_manager import StreamingStateManager
from siili_ai_sdk.recording.base_recorder import BaseRecorder
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)

AIMessageType = Union[AIMessage, AIMessageChunk]


class StreamingEventHandler:
    """Handles LangChain 1.x streaming events."""

    def __init__(self, recorder: Optional[BaseRecorder] = None):
        self.recorder = recorder
        self.block_manager = BlockManager()
        self.state_manager = StreamingStateManager()
        self.content_handler = StreamingContentHandler(self.block_manager, self.state_manager)
        self._processed_message_ids: set[str] = set()
        self._final_message: Optional[AIMessageType] = None
        self._got_chat_model_stream: bool = False

    def reset(self) -> None:
        self.block_manager.reset()
        self.state_manager.reset()
        self._processed_message_ids.clear()
        self._final_message = None
        self._got_chat_model_stream = False

    async def process_stream(self, agent_stream) -> AsyncGenerator[StreamingEvent, None]:
        """Process LangChain 1.x agent stream events."""
        self.reset()

        async for event in agent_stream:
            if self.recorder is not None:
                self.recorder.record_token(event)

            event_type = event.get("event", "")
            data = event.get("data", {})
            logger.trace(f"Stream event: {event_type}")

            # on_chat_model_stream - real-time token streaming (preferred)
            if event_type == "on_chat_model_stream":
                self._got_chat_model_stream = True
                chunk = data.get("chunk")
                if isinstance(chunk, AIMessageChunk):
                    async for streaming_event in self._handle_chunk(chunk):
                        yield streaming_event

            # on_chain_stream - complete messages (fallback if no chat_model_stream)
            elif event_type == "on_chain_stream":
                if not self._got_chat_model_stream:
                    ai_message = self._extract_ai_message(data.get("chunk", {}))
                    if ai_message and not self._is_duplicate(ai_message):
                        async for streaming_event in self._handle_message(ai_message):
                            yield streaming_event
                        self._final_message = ai_message

            # on_chat_model_end - usage metadata from the model
            elif event_type == "on_chat_model_end":
                output = data.get("output")
                if isinstance(output, (AIMessage, AIMessageChunk)):
                    self._final_message = output
                    async for streaming_event in self._emit_usage_if_available(output):
                        yield streaming_event

            # on_chain_end - final state
            elif event_type == "on_chain_end":
                output = data.get("output", {})
                if isinstance(output, dict) and "messages" in output:
                    for msg in output["messages"]:
                        if isinstance(msg, (AIMessage, AIMessageChunk)):
                            if self._final_message is None:
                                self._final_message = msg
                            async for streaming_event in self._emit_usage_if_available(msg):
                                yield streaming_event
                            break

            # on_tool_end - tool execution completed
            elif event_type == "on_tool_end":
                output = data.get("output")
                if output is not None:
                    tool_call_id = getattr(output, "tool_call_id", None)
                    content = getattr(output, "content", str(output))
                    if tool_call_id:
                        async for streaming_event in self.content_handler.handle_tool_response(
                            tool_call_id, content if isinstance(content, str) else str(content)
                        ):
                            yield streaming_event

        # End any active thinking session
        async for event in self.content_handler.end_final_thinking_session_if_needed():
            yield event

        # Emit final COMPLETE event
        if self._final_message or self.state_manager.current_message_id:
            yield StreamingEvent(
                event_type=EventType.COMPLETE,
                message=self._final_message,
                blocks=self.block_manager.get_block_ids(),
                message_id=self.state_manager.current_message_id,
            )

    def _is_duplicate(self, message: AIMessageType) -> bool:
        msg_id = getattr(message, "id", None)
        if not msg_id:
            return False
        if msg_id in self._processed_message_ids:
            return True
        self._processed_message_ids.add(msg_id)
        return False

    def _extract_ai_message(self, chunk: dict) -> Optional[AIMessageType]:
        if "messages" in chunk:
            for msg in chunk["messages"]:
                if isinstance(msg, (AIMessage, AIMessageChunk)):
                    return msg
        if "model" in chunk and isinstance(chunk["model"], dict):
            if "messages" in chunk["model"]:
                for msg in chunk["model"]["messages"]:
                    if isinstance(msg, (AIMessage, AIMessageChunk)):
                        return msg
        return None

    async def _handle_chunk(self, chunk: AIMessageChunk) -> AsyncGenerator[StreamingEvent, None]:
        """Handle streaming chunk - real-time content."""
        content = chunk.content

        if isinstance(content, str) and content:
            async for event in self.content_handler.handle_regular_content(content):
                yield event
            self.state_manager.mark_text_content_received()

        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    block_type = block.get("type")
                    if block_type == "text":
                        text = block.get("text", "")
                        if text:
                            async for event in self.content_handler.handle_regular_content(text):
                                yield event
                            self.state_manager.mark_text_content_received()
                    elif block_type in ("reasoning", "thinking"):
                        reasoning = block.get("reasoning", "") or block.get("thinking", "")
                        if reasoning:
                            async for event in self.content_handler.handle_reasoning_content(reasoning):
                                yield event
                elif isinstance(block, str) and block:
                    async for event in self.content_handler.handle_regular_content(block):
                        yield event
                    self.state_manager.mark_text_content_received()

        if hasattr(chunk, "tool_calls") and chunk.tool_calls:
            for tool_call in chunk.tool_calls:
                tool_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", None)
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                tool_args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                if tool_id and tool_name:
                    async for event in self.content_handler.handle_tool_use(tool_id, tool_name, tool_args):
                        yield event

    async def _handle_message(self, message: AIMessageType) -> AsyncGenerator[StreamingEvent, None]:
        """Handle complete message (from on_chain_stream fallback)."""
        content = message.content

        if isinstance(content, str) and content:
            async for event in self.content_handler.handle_regular_content(content):
                yield event
            self.state_manager.mark_text_content_received()

        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    block_type = block.get("type")
                    if block_type == "text":
                        async for event in self.content_handler.handle_regular_content(block.get("text", "")):
                            yield event
                        self.state_manager.mark_text_content_received()
                    elif block_type in ("reasoning", "thinking"):
                        reasoning = block.get("reasoning", "") or block.get("thinking", "")
                        async for event in self.content_handler.handle_reasoning_content(reasoning):
                            yield event
                elif isinstance(block, str) and block:
                    async for event in self.content_handler.handle_regular_content(block):
                        yield event
                    self.state_manager.mark_text_content_received()

        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", None)
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                tool_args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                if tool_id and tool_name:
                    async for event in self.content_handler.handle_tool_use(tool_id, tool_name, tool_args):
                        yield event

    async def _emit_usage_if_available(self, message: AIMessageType) -> AsyncGenerator[StreamingEvent, None]:
        """Emit usage metadata if available on message."""
        if hasattr(message, "usage_metadata") and message.usage_metadata:
            yield StreamingEvent(
                event_type=EventType.USAGE_METADATA,
                message_id=self.state_manager.current_message_id,
                usage_metadata=TokenUsage.from_langchain(message.usage_metadata),
            )


__all__ = ["StreamingEventHandler"]
