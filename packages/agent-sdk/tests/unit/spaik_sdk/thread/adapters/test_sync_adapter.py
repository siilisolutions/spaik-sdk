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
        # A sibling task running alongside the wait must get CPU time *during*
        # the poll, not only after it returns.
        container = _streaming_container()
        adapter = SyncAdapter(container)

        ticks = 0
        adapter_done = False

        async def tick():
            nonlocal ticks
            while not adapter_done:
                ticks += 1
                await asyncio.sleep(0.005)

        tick_task = asyncio.create_task(tick())
        await adapter.wait_for_completion_async(timeout=0.2)
        adapter_done = True
        await tick_task

        # With the bug the sibling was starved for the full 0.2s and reported 0
        # ticks. With the fix it runs every ~5ms, so expect well over 10.
        assert ticks > 10

    async def test_returns_promptly_once_streaming_ends(self):
        container = _streaming_container()
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
