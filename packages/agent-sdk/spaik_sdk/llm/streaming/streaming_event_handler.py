import json
from typing import Any, AsyncGenerator, Optional, Union, cast

from langchain_core.messages import AIMessage, AIMessageChunk

from spaik_sdk.llm.consumption.token_usage import TokenUsage
from spaik_sdk.llm.streaming.block_manager import BlockManager
from spaik_sdk.llm.streaming.models import EventType, StreamingEvent
from spaik_sdk.llm.streaming.streaming_content_handler import StreamingContentHandler
from spaik_sdk.llm.streaming.streaming_state_manager import StreamingStateManager
from spaik_sdk.recording.base_recorder import BaseRecorder
from spaik_sdk.utils.init_logger import init_logger

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
        self._processed_tool_ids: set[str] = set()
        self._tool_args_by_id: dict[str, dict] = {}
        self._final_message: Optional[AIMessageType] = None
        self._got_chat_model_stream: bool = False

    def reset(self) -> None:
        self.block_manager.reset()
        self.state_manager.reset()
        self._processed_message_ids.clear()
        self._processed_tool_ids.clear()
        self._tool_args_by_id.clear()
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
                    async for streaming_event in self._handle_ai_message(chunk):
                        yield streaming_event

            # on_chain_stream - complete messages (fallback if no chat_model_stream)
            elif event_type == "on_chain_stream":
                if not self._got_chat_model_stream:
                    ai_message = self._extract_ai_message(data.get("chunk", {}))
                    if ai_message and not self._is_duplicate(ai_message):
                        async for streaming_event in self._handle_ai_message(ai_message):
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

                            if self._got_chat_model_stream:
                                for tool_id, tool_name, tool_args in self._collect_final_tool_calls(msg).values():
                                    if tool_id not in self._processed_tool_ids:
                                        self._processed_tool_ids.add(tool_id)
                                        self._tool_args_by_id[tool_id] = tool_args
                                        async for streaming_event in self.content_handler.handle_tool_use(tool_id, tool_name, tool_args):
                                            yield streaming_event
                                    else:
                                        streamed_args = self._tool_args_by_id.get(tool_id, {})
                                        if not streamed_args and tool_args:
                                            self._tool_args_by_id[tool_id] = tool_args
                                            async for streaming_event in self.content_handler.handle_tool_use(
                                                tool_id, tool_name, tool_args
                                            ):
                                                yield streaming_event

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

    async def _handle_ai_message(self, message: AIMessageType) -> AsyncGenerator[StreamingEvent, None]:
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
                tool_details = self._extract_tool_call(tool_call)
                if tool_details is None:
                    continue

                tool_id, tool_name, tool_args = tool_details
                self._processed_tool_ids.add(tool_id)
                self._tool_args_by_id[tool_id] = tool_args
                async for event in self.content_handler.handle_tool_use(tool_id, tool_name, tool_args):
                    yield event

    def _collect_final_tool_calls(self, message: AIMessageType) -> dict[str, tuple[str, str, dict]]:
        final_tool_calls = {
            tool_id: (tool_id, tool_name, tool_args)
            for tool_call in getattr(message, "tool_calls", []) or []
            if (tool_details := self._extract_tool_call(tool_call)) is not None
            for tool_id, tool_name, tool_args in [tool_details]
        }

        content = getattr(message, "content", None)
        if not isinstance(content, list):
            return final_tool_calls

        for block in content:
            tool_details = self._extract_tool_call_from_content_block(block)
            if tool_details is None:
                continue

            tool_id, tool_name, tool_args = tool_details
            existing_tool_call = final_tool_calls.get(tool_id)
            if existing_tool_call is None or (not existing_tool_call[2] and tool_args):
                final_tool_calls[tool_id] = (tool_id, tool_name, tool_args)

        return final_tool_calls

    def _extract_tool_call(self, tool_call) -> Optional[tuple[str, str, dict]]:
        tool_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", None)
        tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
        tool_args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
        if not tool_id or not tool_name:
            return None
        return tool_id, tool_name, tool_args if isinstance(tool_args, dict) else {}

    def _extract_tool_call_from_content_block(self, block: object) -> Optional[tuple[str, str, dict]]:
        if not isinstance(block, dict):
            return None

        block_dict = cast(dict[str, Any], block)
        if block_dict.get("type") == "tool_use":
            tool_id = block_dict.get("id") or block_dict.get("tool_use_id")
            tool_name = block_dict.get("name")
            tool_args = block_dict.get("input", block_dict.get("args", {}))
        elif block_dict.get("type") == "function_call":
            tool_id = block_dict.get("call_id") or block_dict.get("id")
            tool_name = block_dict.get("name")
            tool_args = block_dict.get("arguments", block_dict.get("args", {}))
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}
        else:
            return None

        if not tool_id or not tool_name or not isinstance(tool_args, dict):
            return None

        return tool_id, tool_name, tool_args

    async def _emit_usage_if_available(self, message: AIMessageType) -> AsyncGenerator[StreamingEvent, None]:
        """Emit usage metadata if available on message."""
        if hasattr(message, "usage_metadata") and message.usage_metadata:
            yield StreamingEvent(
                event_type=EventType.USAGE_METADATA,
                message_id=self.state_manager.current_message_id,
                usage_metadata=TokenUsage.from_langchain(message.usage_metadata),
            )


__all__ = ["StreamingEventHandler"]
