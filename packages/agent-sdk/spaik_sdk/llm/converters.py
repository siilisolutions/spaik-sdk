import base64
from typing import Any, Dict, Optional

from spaik_sdk.attachments.models import Attachment
from spaik_sdk.attachments.storage.base_file_storage import BaseFileStorage


async def attachment_content(
    attachment: Attachment,
    file_storage: BaseFileStorage,
    provider_family: str = "openai",
) -> Optional[Dict[str, Any]]:
    try:
        data, metadata = await file_storage.retrieve(attachment.file_id)
    except FileNotFoundError:
        return None

    mime_type = attachment.mime_type
    b64_data = base64.b64encode(data).decode("utf-8")

    if mime_type.startswith("image/"):
        if provider_family == "anthropic":
            return {
                "type": "image",
                "source": {"type": "base64", "media_type": mime_type, "data": b64_data},
            }
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
        }
    elif mime_type == "application/pdf":
        if provider_family == "anthropic":
            return {
                "type": "document",
                "source": {"type": "base64", "media_type": mime_type, "data": b64_data},
            }
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
