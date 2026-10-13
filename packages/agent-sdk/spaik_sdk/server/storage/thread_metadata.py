from dataclasses import dataclass

from spaik_sdk.thread.thread_container import ThreadContainer


@dataclass
class ThreadMetadata:
    thread_id: str
    title: str
    message_count: int
    last_activity_time: int
    created_at: int
    author_id: str
    type: str

    @classmethod
    def from_thread_container(cls, thread: ThreadContainer, thread_type: str = "chat") -> "ThreadMetadata":
        """Create ThreadMetadata from a ThreadContainer"""

        from spaik_sdk.thread.thread_container import message_text

        first = next((m for m in thread.messages if m.role == "user"), None)
        title = message_text(first)[:50] if first else "New Thread"
        return cls(
            thread_id=thread.thread_id,
            title=title,
            message_count=len(thread.messages),
            last_activity_time=thread.get_last_activity_time(),
            created_at=thread.envelope.created_at,
            author_id=thread.owner_id,
            type=thread_type,
        )
