import asyncio
import time

import pytest

from spaik_sdk.thread.adapters.sync_adapter import SyncAdapter
from spaik_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from spaik_sdk.thread.thread_container import ThreadContainer


def _streaming_container() -> ThreadContainer:
    # Keeps the adapter in its polling loop (no early return).
    container = ThreadContainer()
    container.messages.append(
        ThreadMessage(
            id="m-1",
            ai=True,
            author_id="assistant",
            author_name="assistant",
            timestamp=0,
            blocks=[MessageBlock(id="b-1", streaming=True, type=MessageBlockType.PLAIN, content="")],
        )
    )
    assert container.is_streaming_active() is True
    return container


@pytest.mark.unit
class TestSyncAdapterWaitForCompletion:
    async def test_yields_to_event_loop_while_waiting(self):
        # Regression for #61: the polling loop used to seize the event loop.
        container = _streaming_container()
        adapter = SyncAdapter(container)

        ticks = 0

        async def tick():
            nonlocal ticks
            while ticks < 3:
                ticks += 1
                await asyncio.sleep(0.01)

        start = time.time()
        await asyncio.wait_for(
            asyncio.gather(adapter.wait_for_completion_async(timeout=0.2), tick()),
            timeout=1.0,
        )
        elapsed = time.time() - start

        assert ticks == 3
        assert elapsed < 0.5

    async def test_returns_promptly_once_streaming_ends(self):
        container = ThreadContainer()
        adapter = SyncAdapter(container)

        async def end_streaming_soon():
            await asyncio.sleep(0.05)
            adapter._streaming_ended = True

        start = time.time()
        await asyncio.gather(
            adapter.wait_for_completion_async(timeout=5.0),
            end_streaming_soon(),
        )
        elapsed = time.time() - start

        assert elapsed < 1.0
