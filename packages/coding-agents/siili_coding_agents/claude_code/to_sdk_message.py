import uuid
from typing import List

from claude_code_sdk import (
    AssistantMessage,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from siili_ai_sdk import MessageBlock, MessageBlockType, ThreadMessage


def to_sdk_message(message: Message) -> ThreadMessage:
    raise Exception(message)
    #return ThreadMessage()


def to_sdk_message_blocks(message: Message) -> List[MessageBlock]:
    if isinstance(message, SystemMessage):
        return []
    ret: List[MessageBlock] = []
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                ret.append(MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.PLAIN,
                    content=block.text))
            elif isinstance(block, ToolUseBlock):
                ret.append(MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_call_id=block.id,
                    tool_name=block.name,
                    tool_call_args=block.input,
                    ))
            elif isinstance(block, ThinkingBlock):
                ret.append(MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.REASONING,
                    content=block.thinking))
            else:
                raise Exception(block)
    elif isinstance(message, ResultMessage):
        ret.append(MessageBlock(
            id=str(uuid.uuid4()),
            streaming=False,
            type=MessageBlockType.PLAIN,
            content=message.result))
    elif isinstance(message, UserMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                ret.append(MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.PLAIN,
                    content=block.text))
            elif isinstance(block, ToolResultBlock):
                content_str = str(block.content) if block.content else None
                ret.append(MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_call_id=block.tool_use_id,
                    tool_call_response=content_str if not block.is_error else None,
                    tool_call_error=content_str if block.is_error else None,
                    ))
            else:
                raise Exception(block)


    else:
        raise Exception(message)
    return ret
    #return [MessageBlock()]
