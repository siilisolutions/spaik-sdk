from pathlib import Path
from typing import List, Optional, Union

from siili_ai_sdk.attachments.mime_types import guess_mime_type
from siili_ai_sdk.attachments.models import Attachment
from siili_ai_sdk.attachments.storage.base_file_storage import BaseFileStorage


class AttachmentBuilder:
    def __init__(self, file_storage: BaseFileStorage):
        self.file_storage = file_storage

    async def from_path(
        self,
        path: Union[str, Path],
        owner_id: str = "system",
        mime_type: Optional[str] = None,
    ) -> Attachment:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if mime_type is None:
            mime_type = guess_mime_type(path)
            if mime_type is None:
                raise ValueError(f"Could not determine MIME type for: {path}")

        with open(path, "rb") as f:
            data = f.read()

        metadata = await self.file_storage.store(
            data=data,
            mime_type=mime_type,
            owner_id=owner_id,
            filename=path.name,
        )

        return metadata.to_attachment()

    async def from_paths(
        self,
        paths: List[Union[str, Path]],
        owner_id: str = "system",
    ) -> List[Attachment]:
        return [await self.from_path(p, owner_id=owner_id) for p in paths]

    async def from_bytes(
        self,
        data: bytes,
        mime_type: str,
        owner_id: str = "system",
        filename: Optional[str] = None,
    ) -> Attachment:
        metadata = await self.file_storage.store(
            data=data,
            mime_type=mime_type,
            owner_id=owner_id,
            filename=filename,
        )
        return metadata.to_attachment()
