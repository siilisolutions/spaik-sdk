from abc import ABC, abstractmethod
from typing import Optional

from spaik_sdk.attachments.models import FileMetadata


class BaseFileStorage(ABC):
    @abstractmethod
    async def store(
        self,
        data: bytes,
        mime_type: str,
        owner_id: str,
        filename: Optional[str] = None,
    ) -> FileMetadata:
        pass

    @abstractmethod
    async def retrieve(self, file_id: str) -> tuple[bytes, FileMetadata]:
        pass

    @abstractmethod
    async def get_metadata(self, file_id: str) -> Optional[FileMetadata]:
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        pass
