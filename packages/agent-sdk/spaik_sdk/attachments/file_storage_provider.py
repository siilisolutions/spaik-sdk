from typing import Optional

from spaik_sdk.attachments.storage.base_file_storage import BaseFileStorage
from spaik_sdk.attachments.storage.impl.local_file_storage import LocalFileStorage

_file_storage: Optional[BaseFileStorage] = None


def get_file_storage() -> Optional[BaseFileStorage]:
    return _file_storage


def set_file_storage(storage: BaseFileStorage) -> None:
    global _file_storage
    _file_storage = storage


def get_or_create_file_storage() -> BaseFileStorage:
    global _file_storage
    if _file_storage is None:
        _file_storage = LocalFileStorage()
    return _file_storage


def reset_file_storage() -> None:
    global _file_storage
    _file_storage = None
