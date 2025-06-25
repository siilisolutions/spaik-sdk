"""
Simple synchronous adapter for ThreadContainer
"""

import asyncio
import time
from typing import Optional

from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.thread.models import StreamingEndedEvent, ThreadEvent, ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer


class SyncAdapter:
    """Simple adapter that synchronously waits for streaming to end and returns final message"""

    def __init__(self, container: ThreadContainer, cancellation_handle: Optional[CancellationHandle] = None):
        self.container = container
        self._streaming_ended = False
        self.cancellation_handle = cancellation_handle

        # Subscribe to events
        self.container.subscribe(self._handle_event)

    def run(self, response_stream, timeout: float = 30.0) -> "SyncAdapter":
        """Run the adapter with an async generator stream - handles everything internally"""
        asyncio.run(self.run_async(response_stream, timeout))
        return self

    async def run_async(self, response_stream, timeout: float = 30.0) -> Optional[ThreadMessage]:
        """Async version of run that consumes the stream and waits for completion"""
        try:
            # Consume the response stream
            async for token_data in response_stream:
                # Stream processing happens automatically via events
                pass

            # Wait for streaming to complete
            return await self.wait_for_completion_async(timeout)

        finally:
            pass  # Could add cleanup here if needed

    def _handle_event(self, event: ThreadEvent):
        """Handle ThreadContainer events"""
        if isinstance(event, StreamingEndedEvent):
            self._streaming_ended = True

    def wait_for_completion(self, timeout: float = 30.0) -> Optional[ThreadMessage]:
        """Wait for streaming to complete and return the latest AI message"""
        return asyncio.run(self.wait_for_completion_async(timeout))

    async def wait_for_completion_async(self, timeout: float = 30.0) -> Optional[ThreadMessage]:
        """Async version of wait_for_completion"""
        start_time = time.time()

        # Wait for streaming to end
        while time.time() - start_time < timeout:
            if self._streaming_ended or not self.container.is_streaming_active():
                # Give it a moment to finalize
                await asyncio.sleep(0.1)
                return self.container.get_latest_ai_message()

        # Timeout - return what we have
        return self.container.get_latest_ai_message()

    def get_final_response(self) -> str:
        """Get the final text response"""
        message = self.wait_for_completion()
        if message:
            return self.container.get_final_text_content()
        return ""

    def cleanup(self):
        """Unsubscribe from events"""
        self.container.unsubscribe(self._handle_event)
