import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Attachment:
    file_id: str
    mime_type: str
    filename: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.file_id,
            "mime_type": self.mime_type,
            "filename": self.filename,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        return cls(
            file_id=data["file_id"],
            mime_type=data["mime_type"],
            filename=data.get("filename"),
        )


@dataclass
class FileMetadata:
    file_id: str
    mime_type: str
    owner_id: str
    size_bytes: int
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    filename: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.file_id,
            "mime_type": self.mime_type,
            "filename": self.filename,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        return cls(
            file_id=data["file_id"],
            mime_type=data["mime_type"],
            filename=data.get("filename"),
            owner_id=data["owner_id"],
            created_at=data["created_at"],
            size_bytes=data["size_bytes"],
        )

    def to_attachment(self) -> Attachment:
        return Attachment(
            file_id=self.file_id,
            mime_type=self.mime_type,
            filename=self.filename,
        )
