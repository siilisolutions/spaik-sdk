import time
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from siili_ai_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage


def convert_langchain_to_thread_message(lc_message: BaseMessage, author_name: str, author_id: str) -> ThreadMessage:
    """Convert a LangChain BaseMessage to our ThreadMessage format."""
    message_id = str(uuid.uuid4())

    # Determine if it's AI message
    is_ai = isinstance(lc_message, (AIMessage, SystemMessage))

    # Extract content from the LangChain message
    content = ""
    if hasattr(lc_message, "content"):
        if isinstance(lc_message.content, str):
            content = lc_message.content
        elif isinstance(lc_message.content, list):
            # Handle content that's a list (e.g., multi-modal content)
            content_parts = []
            for item in lc_message.content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        content_parts.append(item.get("text", ""))
                    else:
                        content_parts.append(str(item))
                else:
                    content_parts.append(str(item))
            content = "\n".join(content_parts)
        else:
            content = str(lc_message.content)

    # Create message block
    block_id = str(uuid.uuid4())
    block = MessageBlock(
        id=block_id,
        streaming=False,
        type=MessageBlockType.PLAIN,
        content=content if content else None,
    )

    # Check if it has tool calls
    if hasattr(lc_message, "tool_calls") and lc_message.tool_calls:
        block.type = MessageBlockType.TOOL_USE
        if lc_message.tool_calls:
            tool_call = lc_message.tool_calls[0]
            block.tool_call_id = tool_call.get("id", str(uuid.uuid4()))
            block.tool_call_args = tool_call.get("args", {})
            block.tool_name = tool_call.get("name", "unknown")

    # Handle ToolMessage
    elif isinstance(lc_message, ToolMessage):
        # ToolMessage represents a tool response, so we don't create a new block
        # Instead, we should update the existing tool use block
        # For now, create a plain block - this will be handled by the message handler
        block.type = MessageBlockType.PLAIN

    thread_message = ThreadMessage(
        id=message_id, ai=is_ai, author_id=author_id, author_name=author_name, timestamp=int(time.time() * 1000), blocks=[block]
    )

    return thread_message


def convert_thread_message_to_langchain(thread_message: ThreadMessage, include_author_name: bool = False) -> BaseMessage:
    processed_blocks = [_process_message_block(block) for block in thread_message.blocks]
    content = "\n".join(filter(None, processed_blocks))  # Filter out None/empty strings
    author_prefix = f"{'[' + thread_message.author_name + ']: ' if include_author_name else ''}"
    if thread_message.ai:
        return AIMessage(content=f"{author_prefix}{content}")
    else:
        return HumanMessage(content=f"{author_prefix}{content}")


def _process_message_block(block: MessageBlock) -> str:
    """Process a message block based on its type."""
    if block.type == MessageBlockType.REASONING:
        return "<thinking/>"
    elif block.type == MessageBlockType.TOOL_USE:
        tool_name = block.tool_name or "unknown"
        return f'<tool_call tool="{tool_name}"/>'
    elif block.type == MessageBlockType.ERROR:
        content = block.content or "unknown error"
        return f'<error msg="{content}"/>'
    elif block.type == MessageBlockType.PLAIN:
        return block.content or ""
    else:
        # Fallback for unknown types
        return block.content or ""
