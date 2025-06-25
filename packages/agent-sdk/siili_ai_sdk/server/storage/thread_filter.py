from dataclasses import dataclass
from typing import List, Optional, Set

from siili_ai_sdk.server.storage.thread_metadata import ThreadMetadata


@dataclass
class ThreadFilter:
    """Filter for thread metadata with fluent builder interface"""

    thread_ids: Optional[Set[str]] = None
    author_ids: Optional[Set[str]] = None
    types: Optional[Set[str]] = None
    title_contains: Optional[str] = None
    min_message_count: Optional[int] = None
    max_message_count: Optional[int] = None
    min_last_activity: Optional[int] = None
    max_last_activity: Optional[int] = None
    min_created_at: Optional[int] = None
    max_created_at: Optional[int] = None

    @classmethod
    def builder(cls) -> "ThreadFilterBuilder":
        """Create a new filter builder"""
        return ThreadFilterBuilder()

    def matches(self, metadata: ThreadMetadata) -> bool:
        """Check if thread metadata matches all filter criteria"""

        if self.thread_ids is not None and metadata.thread_id not in self.thread_ids:
            return False

        if self.author_ids is not None and metadata.author_id not in self.author_ids:
            return False

        if self.types is not None and metadata.type not in self.types:
            return False

        if self.title_contains is not None and self.title_contains.lower() not in metadata.title.lower():
            return False

        if self.min_message_count is not None and metadata.message_count < self.min_message_count:
            return False

        if self.max_message_count is not None and metadata.message_count > self.max_message_count:
            return False

        if self.min_last_activity is not None and metadata.last_activity_time < self.min_last_activity:
            return False

        if self.max_last_activity is not None and metadata.last_activity_time > self.max_last_activity:
            return False

        if self.min_created_at is not None and metadata.created_at < self.min_created_at:
            return False

        if self.max_created_at is not None and metadata.created_at > self.max_created_at:
            return False

        return True


class ThreadFilterBuilder:
    """Fluent builder for ThreadFilter"""

    def __init__(self):
        self._filter = ThreadFilter()

    def with_thread_id(self, thread_id: str) -> "ThreadFilterBuilder":
        """Filter by specific thread ID"""
        if self._filter.thread_ids is None:
            self._filter.thread_ids = set()
        self._filter.thread_ids.add(thread_id)
        return self

    def with_thread_ids(self, thread_ids: List[str]) -> "ThreadFilterBuilder":
        """Filter by multiple thread IDs"""
        if self._filter.thread_ids is None:
            self._filter.thread_ids = set()
        self._filter.thread_ids.update(thread_ids)
        return self

    def with_author_id(self, author_id: str) -> "ThreadFilterBuilder":
        """Filter by specific author ID"""
        if self._filter.author_ids is None:
            self._filter.author_ids = set()
        self._filter.author_ids.add(author_id)
        return self

    def with_author_ids(self, author_ids: List[str]) -> "ThreadFilterBuilder":
        """Filter by multiple author IDs"""
        if self._filter.author_ids is None:
            self._filter.author_ids = set()
        self._filter.author_ids.update(author_ids)
        return self

    def with_type(self, thread_type: str) -> "ThreadFilterBuilder":
        """Filter by specific thread type"""
        if self._filter.types is None:
            self._filter.types = set()
        self._filter.types.add(thread_type)
        return self

    def with_types(self, thread_types: List[str]) -> "ThreadFilterBuilder":
        """Filter by multiple thread types"""
        if self._filter.types is None:
            self._filter.types = set()
        self._filter.types.update(thread_types)
        return self

    def with_title_containing(self, text: str) -> "ThreadFilterBuilder":
        """Filter by title containing text (case insensitive)"""
        self._filter.title_contains = text
        return self

    def with_min_messages(self, min_count: int) -> "ThreadFilterBuilder":
        """Filter threads with at least this many messages"""
        self._filter.min_message_count = min_count
        return self

    def with_max_messages(self, max_count: int) -> "ThreadFilterBuilder":
        """Filter threads with at most this many messages"""
        self._filter.max_message_count = max_count
        return self

    def with_message_count_range(self, min_count: int, max_count: int) -> "ThreadFilterBuilder":
        """Filter threads with message count in range [min_count, max_count]"""
        self._filter.min_message_count = min_count
        self._filter.max_message_count = max_count
        return self

    def with_activity_after(self, timestamp: int) -> "ThreadFilterBuilder":
        """Filter threads with last activity after timestamp (UTC millis)"""
        self._filter.min_last_activity = timestamp
        return self

    def with_activity_before(self, timestamp: int) -> "ThreadFilterBuilder":
        """Filter threads with last activity before timestamp (UTC millis)"""
        self._filter.max_last_activity = timestamp
        return self

    def with_activity_range(self, start: int, end: int) -> "ThreadFilterBuilder":
        """Filter threads with last activity in range [start, end] (UTC millis)"""
        self._filter.min_last_activity = start
        self._filter.max_last_activity = end
        return self

    def with_created_after(self, timestamp: int) -> "ThreadFilterBuilder":
        """Filter threads created after timestamp (UTC millis)"""
        self._filter.min_created_at = timestamp
        return self

    def with_created_before(self, timestamp: int) -> "ThreadFilterBuilder":
        """Filter threads created before timestamp (UTC millis)"""
        self._filter.max_created_at = timestamp
        return self

    def with_created_range(self, start: int, end: int) -> "ThreadFilterBuilder":
        """Filter threads created in range [start, end] (UTC millis)"""
        self._filter.min_created_at = start
        self._filter.max_created_at = end
        return self

    def build(self) -> ThreadFilter:
        """Build the final filter"""
        return self._filter
