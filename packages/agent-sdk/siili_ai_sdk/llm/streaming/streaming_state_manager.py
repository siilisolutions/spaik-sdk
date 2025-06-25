from typing import Optional

from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class StreamingStateManager:
    """Manages state for streaming operations."""

    def __init__(self):
        self.current_message_id: Optional[str] = None
        self.streaming_started = False

        # Track mid-response thinking state
        self.last_block_type = None
        self.has_text_content = False
        self.reasoning_blocks_created = 0  # Track how many reasoning blocks we've created
        self.in_thinking_session = False  # Track if we're currently in a thinking session

    def reset(self):
        """Reset all state for new stream."""
        self.current_message_id = None
        self.streaming_started = False
        self.last_block_type = None
        self.has_text_content = False
        self.reasoning_blocks_created = 0
        self.in_thinking_session = False

    def start_thinking_session(self):
        """Mark the start of a thinking session."""
        if not self.in_thinking_session:
            logger.debug("🧠 Starting thinking session")
            self.in_thinking_session = True

    def end_thinking_session(self):
        """Mark the end of a thinking session."""
        if self.in_thinking_session:
            logger.debug("Ending thinking session - got text content")
            self.in_thinking_session = False

    def increment_reasoning_blocks(self):
        """Increment the count of reasoning blocks created."""
        self.reasoning_blocks_created += 1
        logger.debug(f"Created reasoning block #{self.reasoning_blocks_created}")

    def should_create_new_thinking_session(self, reasoning_content: bool, current_block_type: str) -> bool:
        """Determine if we should create a new thinking session (mid-response thinking)."""
        return reasoning_content and self.has_text_content and self.last_block_type == "text" and current_block_type == "thinking"

    def update_block_type(self, block_type: str):
        """Update the last block type."""
        if block_type:
            self.last_block_type = block_type

    def mark_text_content_received(self):
        """Mark that we've received text content."""
        self.has_text_content = True
