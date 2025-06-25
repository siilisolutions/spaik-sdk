"""
Streaming block adapter that yields blocks as they appear
"""

import asyncio
from typing import AsyncGenerator

from siili_ai_sdk.thread.models import BlockAddedEvent, MessageBlock, ThreadEvent
from siili_ai_sdk.thread.thread_container import ThreadContainer


class StreamingBlockAdapter:
    """Adapter that streams blocks as they are created until streaming ends"""

    def __init__(self, container: ThreadContainer):
        self.container = container
        self._block_queue: asyncio.Queue[MessageBlock] = asyncio.Queue()
        self._streaming_ended = False

        # Subscribe to events
        self.container.subscribe(self._handle_event)

    def _handle_event(self, event: ThreadEvent):
        """Handle ThreadContainer events"""
        if isinstance(event, BlockAddedEvent):
            # Queue the new block
            asyncio.create_task(self._queue_block(event.block))

    async def _queue_block(self, block: MessageBlock):
        """Add block to queue"""
        await self._block_queue.put(block)

    async def stream_blocks(self) -> AsyncGenerator[MessageBlock, None]:
        """
        Async generator that yields blocks as they are created.
        Ends when streaming is no longer active.
        """
        try:
            while True:
                # Check if streaming is still active
                if not self.container.is_streaming_active() and self._block_queue.empty():
                    break

                try:
                    # Wait for next block with timeout to check streaming status periodically
                    block = await asyncio.wait_for(self._block_queue.get(), timeout=0.1)
                    yield block
                except asyncio.TimeoutError:
                    # Continue loop to check streaming status
                    continue

        finally:
            self.cleanup()

    def cleanup(self):
        """Unsubscribe from events"""
        self.container.unsubscribe(self._handle_event)
