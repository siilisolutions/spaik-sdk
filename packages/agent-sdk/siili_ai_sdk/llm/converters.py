import base64
from typing import Any, Dict, List, Optional, Union, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from siili_ai_sdk.attachments.models import Attachment
from siili_ai_sdk.attachments.provider_support import is_supported_by_provider
from siili_ai_sdk.attachments.storage.base_file_storage import BaseFileStorage
from siili_ai_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


def convert_thread_message_to_langchain(
    thread_message: ThreadMessage,
    include_author_name: bool = False,
) -> BaseMessage:
    processed_blocks = [_process_message_block(block) for block in thread_message.blocks]
    content = "\n".join(filter(None, processed_blocks))
    author_prefix = f"{'[' + thread_message.author_name + ']: ' if include_author_name else ''}"
    if thread_message.ai:
        return AIMessage(content=f"{author_prefix}{content}")
    else:
        return HumanMessage(content=f"{author_prefix}{content}")


async def convert_thread_message_to_langchain_multimodal(
    thread_message: ThreadMessage,
    file_storage: BaseFileStorage,
    provider_family: str = "openai",
    include_author_name: bool = False,
) -> BaseMessage:
    processed_blocks = [_process_message_block(block) for block in thread_message.blocks]
    text_content = "\n".join(filter(None, processed_blocks))
    author_prefix = f"{'[' + thread_message.author_name + ']: ' if include_author_name else ''}"

    if thread_message.ai:
        return AIMessage(content=f"{author_prefix}{text_content}")

    if not thread_message.attachments:
        return HumanMessage(content=f"{author_prefix}{text_content}")

    content_parts: List[Dict[str, Any]] = []

    if text_content:
        content_parts.append({"type": "text", "text": f"{author_prefix}{text_content}"})

    for attachment in thread_message.attachments:
        # Check if MIME type is supported by the provider
        if not is_supported_by_provider(attachment.mime_type, provider_family):
            logger.warning(f"Skipping unsupported attachment type {attachment.mime_type} for provider {provider_family}")
            filename = attachment.filename or "unnamed file"
            fallback_msg = (
                f"[SYSTEM: The user attempted to attach a file '{filename}' of type '{attachment.mime_type}', "
                f"but this file type is not supported by the current AI model. "
                f"Please inform the user that you cannot process this file type "
                f"and suggest supported alternatives like images (PNG, JPEG, GIF, WEBP) or PDF documents.]"
            )
            content_parts.append({"type": "text", "text": fallback_msg})
            continue

        attachment_content = await _convert_attachment_to_content_part(attachment, file_storage)
        if attachment_content:
            content_parts.append(attachment_content)

    if not content_parts:
        return HumanMessage(content="")

    return HumanMessage(content=cast(List[Union[str, Dict[str, Any]]], content_parts))


async def _convert_attachment_to_content_part(
    attachment: Attachment,
    file_storage: BaseFileStorage,
) -> Optional[Dict[str, Any]]:
    try:
        data, metadata = await file_storage.retrieve(attachment.file_id)
    except FileNotFoundError:
        return None

    mime_type = attachment.mime_type
    b64_data = base64.b64encode(data).decode("utf-8")

    if mime_type.startswith("image/"):
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
        }
    elif mime_type == "application/pdf":
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
        }
    elif mime_type.startswith("audio/"):
        return {
            "type": "input_audio",
            "input_audio": {"data": b64_data, "format": _get_audio_format(mime_type)},
        }
    elif mime_type.startswith("video/"):
        return {
            "type": "video_url",
            "video_url": {"url": f"data:{mime_type};base64,{b64_data}"},
        }
    else:
        return {
            "type": "file",
            "file": {"data": b64_data, "mime_type": mime_type},
        }


def _get_audio_format(mime_type: str) -> str:
    format_map = {
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "audio/ogg": "ogg",
        "audio/webm": "webm",
    }
    return format_map.get(mime_type, "wav")


def _process_message_block(block: MessageBlock) -> str:
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
        return block.content or ""
