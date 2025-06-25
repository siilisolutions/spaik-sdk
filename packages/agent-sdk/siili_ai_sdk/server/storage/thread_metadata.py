from dataclasses import dataclass

from siili_ai_sdk.thread.thread_container import ThreadContainer


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

        # Extract title from first user message or fallback to system prompt
        title = "New Thread"
        first_user_message = None

        # Find first non-AI message for title and author
        for msg in thread.messages:
            if not msg.ai:
                first_user_message = msg
                content = msg.get_text_content().strip()
                if content:
                    # Use first 50 chars as title
                    title = content[:50] + ("..." if len(content) > 50 else "")
                break

        # Fallback to system prompt for title if no user message
        if title == "New Thread" and thread.system_prompt:
            prompt_preview = thread.system_prompt[:50]
            title = f"System: {prompt_preview}" + ("..." if len(thread.system_prompt) > 50 else "")

        # Extract author_id from first user message or default
        author_id = first_user_message.author_id if first_user_message else "unknown"

        # Use first message timestamp as created_at, or current time if no messages
        created_at = thread.messages[0].timestamp if thread.messages else thread.get_last_activity_time()

        return cls(
            thread_id=thread.thread_id,
            title=title,
            message_count=len(thread.messages),
            last_activity_time=thread.get_last_activity_time(),
            created_at=created_at,
            author_id=author_id,
            type=thread_type,
        )
