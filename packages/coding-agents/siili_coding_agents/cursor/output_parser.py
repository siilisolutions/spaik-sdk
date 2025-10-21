import json
import uuid
from typing import List

from siili_ai_sdk import MessageBlock, MessageBlockType


def _text_block(text: str, streaming: bool) -> MessageBlock:
    return MessageBlock(
        id=str(uuid.uuid4()),
        streaming=streaming,
        type=MessageBlockType.PLAIN,
        content=text,
    )


def parse_stream_line(line: str) -> List[MessageBlock]:
    """Parse a single line from stream-json output into MessageBlocks.

    Returns zero or more MessageBlocks depending on the event type.
    Falls back to returning the raw line as a text block if JSON parsing fails.
    """
    if not line.strip():
        return []

    try:
        event = json.loads(line)
    except Exception:
        return [_text_block(line, streaming=True)]

    blocks: List[MessageBlock] = []
    event_type = event.get("type")

    if event_type == "assistant":
        message = event.get("message", {})
        for block in message.get("content", []) or []:
            if block.get("type") == "text" and block.get("text"):
                blocks.append(_text_block(block.get("text"), streaming=True))

    elif event_type == "tool_call":
        tool_call = event.get("tool_call") or {}
        if isinstance(tool_call, dict) and tool_call:
            tool_name = next(iter(tool_call.keys()))
            tool_entry = tool_call.get(tool_name) or {}
            args = tool_entry.get("args")
            call_id = event.get("call_id") or tool_entry.get("toolCallId")
            blocks.append(
                MessageBlock(
                    id=str(uuid.uuid4()),
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_name=str(tool_name),
                    tool_call_id=str(call_id) if call_id else None,
                    tool_call_args=args,
                )
            )

    elif event_type == "result":
        result_text = event.get("result")
        if result_text:
            blocks.append(_text_block(result_text, streaming=False))

    # Ignore system/user/status events for now
    return blocks


def parse_json_output(raw: str) -> List[MessageBlock]:
    """Parse the final JSON payload output into MessageBlocks.

    Expected to be a single JSON object with possible fields like
    { message: { role: 'assistant', content: [ {type: 'text', text: ...}, ... ] }, result: ... }
    Falls back to emitting the raw payload as text if parsing fails.
    """
    if not raw:
        return []

    try:
        payload = json.loads(raw)
    except Exception:
        return [_text_block(raw, streaming=False)]

    blocks: List[MessageBlock] = []
    if isinstance(payload, dict):
        message = payload.get("message") or {}
        if message.get("role") == "assistant":
            for block in message.get("content", []) or []:
                if block.get("type") == "text" and block.get("text"):
                    blocks.append(_text_block(block.get("text"), streaming=False))

        result_text = payload.get("result")
        if result_text:
            blocks.append(_text_block(result_text, streaming=False))

    else:
        blocks.append(_text_block(raw, streaming=False))

    return blocks


