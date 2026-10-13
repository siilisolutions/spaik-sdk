"""Versioned JSON storage for local development; never unpickles legacy data."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import quote

from ag_ui.core import Message

from spaik_sdk.server.storage.base_thread_repository import BaseThreadRepository
from spaik_sdk.server.storage.thread_filter import ThreadFilter
from spaik_sdk.server.storage.thread_metadata import ThreadMetadata
from spaik_sdk.thread.thread_container import ThreadContainer


class LocalFileThreadRepository(BaseThreadRepository):
    def __init__(self, data_dir: str = "data-v1"):
        self.threads_dir = Path(data_dir) / "threads"
        self.threads_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, thread_id: str) -> Path:
        if not thread_id:
            raise ValueError("Thread ID cannot be empty")
        return self.threads_dir / f"{quote(thread_id, safe='')}.json"

    async def save_thread(self, thread_container: ThreadContainer) -> None:
        def save():
            path = self._path(thread_container.thread_id)
            with tempfile.NamedTemporaryFile(mode="w", dir=self.threads_dir, delete=False, encoding="utf-8") as file:
                temporary = Path(file.name)
                try:
                    json.dump(thread_container.to_dict(), file, ensure_ascii=False)
                    file.flush()
                    os.fsync(file.fileno())
                    file.close()
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)

        await asyncio.to_thread(save)

    async def load_thread(self, thread_id: str) -> ThreadContainer | None:
        path = self._path(thread_id)
        if not path.exists():
            return None
        data = await asyncio.to_thread(path.read_text, encoding="utf-8")
        thread = ThreadContainer.from_dict(json.loads(data))
        if thread.thread_id != thread_id:
            raise ValueError("Stored thread ID does not match its filename")
        return thread

    async def thread_exists(self, thread_id: str) -> bool:
        return self._path(thread_id).exists()

    async def delete_thread(self, thread_id: str) -> bool:
        path = self._path(thread_id)
        if not path.exists():
            return False
        await asyncio.to_thread(path.unlink)
        return True

    async def list_threads(self, filter: ThreadFilter) -> list[ThreadMetadata]:
        result = []
        for path in self.threads_dir.glob("*.json"):
            thread = ThreadContainer.from_dict(json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8")))
            metadata = ThreadMetadata.from_thread_container(thread)
            if filter.matches(metadata):
                result.append(metadata)
        return sorted(result, key=lambda m: m.last_activity_time, reverse=True)

    async def get_message(self, thread_id: str, message_id: str) -> Message | None:
        thread = await self.load_thread(thread_id)
        return next((m for m in thread.messages if m.id == message_id), None) if thread else None

    async def upsert_message(self, thread_id: str, message: Message) -> None:
        thread = await self.load_thread(thread_id)
        if thread is None:
            raise ValueError("Thread not found")
        thread.messages = [m for m in thread.messages if m.id != message.id] + [message]
        await self.save_thread(thread)

    async def delete_message(self, thread_id: str, message_id: str) -> None:
        thread = await self.load_thread(thread_id)
        if thread:
            thread.messages = [m for m in thread.messages if m.id != message_id]
            await self.save_thread(thread)
