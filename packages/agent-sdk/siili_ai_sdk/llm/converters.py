from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from siili_ai_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage


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
