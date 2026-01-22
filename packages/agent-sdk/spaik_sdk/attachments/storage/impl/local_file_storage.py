import json
import uuid
from pathlib import Path
from typing import Optional

from spaik_sdk.attachments.models import FileMetadata
from spaik_sdk.attachments.storage.base_file_storage import BaseFileStorage


class LocalFileStorage(BaseFileStorage):
    def __init__(self, data_dir: str = "data/files"):
        self.data_dir = Path(data_dir)
        self.files_dir = self.data_dir / "content"
        self.metadata_dir = self.data_dir / "metadata"

        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, file_id: str) -> Path:
        return self.files_dir / file_id

    def _metadata_path(self, file_id: str) -> Path:
        return self.metadata_dir / f"{file_id}.json"

    def _save_metadata(self, metadata: FileMetadata) -> None:
        with open(self._metadata_path(metadata.file_id), "w") as f:
            json.dump(metadata.to_dict(), f)

    def _load_metadata(self, file_id: str) -> Optional[FileMetadata]:
        metadata_path = self._metadata_path(file_id)
        if not metadata_path.exists():
            return None
        try:
            with open(metadata_path, "r") as f:
                return FileMetadata.from_dict(json.load(f))
        except (json.JSONDecodeError, KeyError):
            return None

    async def store(
        self,
        data: bytes,
        mime_type: str,
        owner_id: str,
        filename: Optional[str] = None,
    ) -> FileMetadata:
        file_id = str(uuid.uuid4())

        file_path = self._file_path(file_id)
        with open(file_path, "wb") as f:
            f.write(data)

        metadata = FileMetadata(
            file_id=file_id,
            mime_type=mime_type,
            owner_id=owner_id,
            size_bytes=len(data),
            filename=filename,
        )
        self._save_metadata(metadata)

        return metadata

    async def retrieve(self, file_id: str) -> tuple[bytes, FileMetadata]:
        metadata = await self.get_metadata(file_id)
        if metadata is None:
            raise FileNotFoundError(f"File not found: {file_id}")

        file_path = self._file_path(file_id)
        if not file_path.exists():
            raise FileNotFoundError(f"File content not found: {file_id}")

        with open(file_path, "rb") as f:
            data = f.read()

        return data, metadata

    async def get_metadata(self, file_id: str) -> Optional[FileMetadata]:
        return self._load_metadata(file_id)

    async def delete(self, file_id: str) -> bool:
        file_path = self._file_path(file_id)
        metadata_path = self._metadata_path(file_id)

        deleted = False
        if file_path.exists():
            file_path.unlink()
            deleted = True
        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

    async def exists(self, file_id: str) -> bool:
        return self._file_path(file_id).exists() and self._metadata_path(file_id).exists()

    def clear_all(self) -> None:
        for file_path in self.files_dir.glob("*"):
            file_path.unlink()
        for metadata_path in self.metadata_dir.glob("*.json"):
            metadata_path.unlink()
