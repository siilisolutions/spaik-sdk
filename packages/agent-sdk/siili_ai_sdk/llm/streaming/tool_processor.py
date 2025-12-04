from typing import Any, AsyncGenerator

from siili_ai_sdk.llm.streaming.block_manager import BlockManager
from siili_ai_sdk.llm.streaming.models import EventType, StreamingEvent
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ToolProcessor:
    """Handles processing of tool calls and responses from final outputs."""

    def __init__(self, state_manager=None):
        self.state_manager = state_manager

    async def process_final_output_tool_calls(
        self, data: Any, message_id: str, block_manager: BlockManager
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Process tool calls from the final output message (for OpenAI and similar models)."""
        if "output" in data and hasattr(data["output"], "tool_calls") and data["output"].tool_calls:
            logger.debug(f"🔧 Processing {len(data['output'].tool_calls)} tool calls from final output (OpenAI-style)")
            for tool_call in data["output"].tool_calls:
                tool_call_id = tool_call.get("id")
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

                if tool_call_id and tool_name and message_id:
                    logger.debug(f"🔧 Found tool call in final message: {tool_name} (id: {tool_call_id})")

                    # Create tool use block for this tool call
                    async for streaming_event in block_manager.ensure_tool_use_block(message_id, tool_call_id, tool_name, tool_args):
                        yield streaming_event

                    # Emit tool use event
                    yield StreamingEvent(
                        event_type=EventType.TOOL_USE,
                        block_id=block_manager.get_tool_use_block_id(tool_call_id),
                        message_id=message_id,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        tool_args=tool_args,
                    )

    async def process_tool_responses(self, data: Any, message_id: str, block_manager: BlockManager) -> AsyncGenerator[StreamingEvent, None]:
        """Process ToolMessage objects from conversation history and generate tool responses."""
        if "input" in data and "messages" in data["input"]:
            all_messages = data["input"]["messages"][-1]  # Get the latest conversation state
            for message_batch in all_messages:
                for msg in message_batch if isinstance(message_batch, list) else [message_batch]:
                    # Import ToolMessage here to avoid circular imports
                    from langchain_core.messages import ToolMessage

                    if isinstance(msg, ToolMessage):
                        logger.debug(f"🔧 Processing tool response: {msg.tool_call_id}")
                        # Emit tool response event
                        tool_response_content = msg.content
                        if isinstance(tool_response_content, list):
                            # Convert list content to string
                            content_parts = []
                            for item in tool_response_content:
                                if isinstance(item, dict):
                                    content_parts.append(item.get("text", str(item)))
                                else:
                                    content_parts.append(str(item))
                            tool_response_content = "\n".join(content_parts)
                        elif not isinstance(tool_response_content, str):
                            tool_response_content = str(tool_response_content)

                        # Get the tool use block for this tool call
                        block_id = block_manager.get_tool_use_block_id(msg.tool_call_id)

                        # For OpenAI models, tool responses may come before blocks are created
                        # If no block exists, create one retroactively (this is expected behavior)
                        if not block_id and message_id:
                            logger.debug(f"🔧 Creating tool use block for {msg.tool_call_id} (OpenAI-style retroactive creation)")
                            # Create tool use block retroactively (we might not have the tool name/args)
                            async for streaming_event in block_manager.ensure_tool_use_block(
                                message_id, msg.tool_call_id, getattr(msg, "name", None) or "unknown_tool", {}
                            ):
                                yield streaming_event
                            block_id = block_manager.get_tool_use_block_id(msg.tool_call_id)

                        if block_id:
                            yield StreamingEvent(
                                event_type=EventType.TOOL_RESPONSE,
                                content=tool_response_content,
                                block_id=block_id,
                                message_id=message_id,
                                tool_call_id=msg.tool_call_id,
                            )
                        else:
                            logger.warning(f"🔧 No block_id found for tool_call_id: {msg.tool_call_id}")
