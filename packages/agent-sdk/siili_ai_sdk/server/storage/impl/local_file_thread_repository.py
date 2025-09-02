import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional

from siili_ai_sdk.server.storage.base_thread_repository import BaseThreadRepository
from siili_ai_sdk.server.storage.thread_filter import ThreadFilter
from siili_ai_sdk.server.storage.thread_metadata import ThreadMetadata
from siili_ai_sdk.thread.models import ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer


class LocalFileThreadRepository(BaseThreadRepository):
    """Local file-based implementation of thread repository for development"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.threads_dir = self.data_dir / "threads"
        self.metadata_file = self.data_dir / "metadata.json"

        # Create directories if they don't exist
        self.threads_dir.mkdir(parents=True, exist_ok=True)

        # Load metadata cache
        self._metadata_cache: Dict[str, ThreadMetadata] = {}
        self._load_metadata_cache()

    def _load_metadata_cache(self) -> None:
        """Load metadata from disk into memory cache"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    # Convert dict to ThreadMetadata objects
                    metadata_cache = {}
                    for thread_id, metadata_dict in data.items():
                        if isinstance(metadata_dict, dict):
                            # Create ThreadMetadata with explicit arguments to satisfy type checker
                            metadata_cache[thread_id] = ThreadMetadata(
                                thread_id=metadata_dict.get("thread_id", thread_id),
                                title=metadata_dict.get("title", "New Thread"),
                                message_count=metadata_dict.get("message_count", 0),
                                last_activity_time=metadata_dict.get("last_activity_time", 0),
                                created_at=metadata_dict.get("created_at", 0),
                                author_id=metadata_dict.get("author_id", "unknown"),
                                type=metadata_dict.get("type", "chat"),
                            )
                    self._metadata_cache = metadata_cache
            except (json.JSONDecodeError, TypeError, KeyError):
                # If metadata is corrupted, rebuild it
                self._rebuild_metadata_cache()

    def _save_metadata_cache(self) -> None:
        """Save metadata cache to disk"""
        data = {
            thread_id: {
                "thread_id": metadata.thread_id,
                "title": metadata.title,
                "message_count": metadata.message_count,
                "last_activity_time": metadata.last_activity_time,
                "created_at": metadata.created_at,
                "author_id": metadata.author_id,
                "type": metadata.type,
            }
            for thread_id, metadata in self._metadata_cache.items()
        }

        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def _rebuild_metadata_cache(self) -> None:
        """Rebuild metadata cache by reading all thread files"""
        self._metadata_cache.clear()

        for thread_file in self.threads_dir.glob("*.pkl"):
            thread_id = thread_file.stem
            try:
                thread = self._load_thread_from_file(thread_id)
                if thread:
                    metadata = ThreadMetadata.from_thread_container(thread)
                    self._metadata_cache[thread_id] = metadata
            except Exception:
                # Skip corrupted files
                continue

        self._save_metadata_cache()

    def _thread_file_path(self, thread_id: str) -> Path:
        """Get file path for a thread"""
        return self.threads_dir / f"{thread_id}.pkl"

    def _load_thread_from_file(self, thread_id: str) -> Optional[ThreadContainer]:
        """Load thread from pickle file"""
        file_path = self._thread_file_path(thread_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, EOFError, OSError):
            return None

    def _save_thread_to_file(self, thread: ThreadContainer) -> None:
        """Save thread to pickle file"""
        file_path = self._thread_file_path(thread.thread_id)

        # Create a serializable copy to avoid issues with non-picklable subscribers
        serializable_thread = thread.create_serializable_copy()

        with open(file_path, "wb") as f:
            pickle.dump(serializable_thread, f)

    async def save_thread(self, thread_container: ThreadContainer) -> None:
        """Save complete thread container to disk"""
        self._save_thread_to_file(thread_container)

        # Update metadata cache
        metadata = ThreadMetadata.from_thread_container(thread_container)
        self._metadata_cache[thread_container.thread_id] = metadata
        self._save_metadata_cache()

    async def load_thread(self, thread_id: str) -> Optional[ThreadContainer]:
        """Load thread container from disk"""
        return self._load_thread_from_file(thread_id)

    async def get_message(self, thread_id: str, message_id: str) -> Optional[ThreadMessage]:
        """Get message from disk"""
        thread = await self.load_thread(thread_id)
        if not thread:
            return None

        for message in thread.messages:
            if message.id == message_id:
                return message
        return None

    async def upsert_message(self, thread_id: str, message: ThreadMessage) -> None:
        """Upsert message to disk"""
        thread = await self.load_thread(thread_id)
        if not thread:
            return

        # Find existing message and replace, or add new one
        for i, existing_msg in enumerate(thread.messages):
            if existing_msg.id == message.id:
                thread.messages[i] = message
                break
        else:
            thread.messages.append(message)

        # Save updated thread
        await self.save_thread(thread)

    async def delete_message(self, thread_id: str, message_id: str) -> None:
        """Delete message from disk"""
        thread = await self.load_thread(thread_id)
        if not thread:
            return

        thread.messages = [msg for msg in thread.messages if msg.id != message_id]

        # Save updated thread
        await self.save_thread(thread)

    async def thread_exists(self, thread_id: str) -> bool:
        """Check if thread exists on disk"""
        return self._thread_file_path(thread_id).exists()

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete thread and all its messages from disk"""
        file_path = self._thread_file_path(thread_id)

        if file_path.exists():
            try:
                file_path.unlink()  # Delete file

                # Remove from metadata cache
                if thread_id in self._metadata_cache:
                    del self._metadata_cache[thread_id]
                    self._save_metadata_cache()

                return True
            except OSError:
                return False
        return False

    async def list_threads(self, filter: ThreadFilter) -> List[ThreadMetadata]:
        """List threads matching the filter from disk metadata"""
        result = []

        for metadata in self._metadata_cache.values():
            if filter.matches(metadata):
                result.append(metadata)

        # Sort by last activity time (most recent first)
        result.sort(key=lambda x: x.last_activity_time, reverse=True)
        return result

    def clear_all(self) -> None:
        """Clear all data from disk (useful for testing)"""
        # Remove all thread files
        for thread_file in self.threads_dir.glob("*.pkl"):
            thread_file.unlink()

        # Clear metadata
        self._metadata_cache.clear()
        if self.metadata_file.exists():
            self.metadata_file.unlink()

    def get_thread_count(self) -> int:
        """Get total number of threads stored"""
        return len(self._metadata_cache)

    def get_data_dir(self) -> Path:
        """Get the data directory path"""
        return self.data_dir
