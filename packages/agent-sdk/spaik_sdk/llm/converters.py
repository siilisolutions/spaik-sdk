"""Translate AG-UI/local attachment sources into LangChain standard content blocks."""

import base64
from typing import Any

from spaik_sdk.attachments.models import Attachment
from spaik_sdk.attachments.storage.base_file_storage import BaseFileStorage


def message_content(content) -> str | list[str | dict[str, Any]]:
    if isinstance(content, str):
        return content
    blocks: list[str | dict[str, Any]] = []
    for part in content:
        if part.type == "text":
            blocks.append({"type": "text", "text": part.text})
            continue
        source = part.source
        block = {"type": "file" if part.type == "document" else part.type}
        block[{"data": "base64", "url": "url", "file": "file_id"}[source.type]] = source.value
        if source.mime_type:
            block["mime_type"] = source.mime_type
        if part.type == "document":
            metadata = part.metadata if isinstance(part.metadata, dict) else {}
            block["filename"] = metadata.get("filename", "attachment.pdf")
        blocks.append(block)
    return blocks


async def attachment_content(attachment: Attachment, storage: BaseFileStorage) -> dict[str, Any]:
    data, metadata = await storage.retrieve(attachment.file_id)
    kind = metadata.mime_type.split("/", 1)[0]
    return {
        "type": kind if kind in {"image", "audio", "video"} else "file",
        "base64": base64.b64encode(data).decode("ascii"),
        "mime_type": metadata.mime_type,
        "filename": metadata.filename or "attachment.pdf",
    }
