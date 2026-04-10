from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from spaik_sdk.server.job_processor.thread_job_processor import ThreadJobProcessor
from spaik_sdk.server.queue.agent_job_queue import AgentJob


def _make_job(thread_id: str = "thread-1") -> AgentJob:
    job = MagicMock(spec=AgentJob)
    job.id = thread_id
    return job


def _stream_factory(*chunks: Dict[str, Any], checkpoint_on: list[int] | None = None):
    """
    Returns a mock response_generator whose stream_response yields the given chunks.
    If checkpoint_on is provided, the on_checkpoint callback is called before
    yielding the chunk at those indices (simulating what AgentResponseGenerator does).
    """

    async def stream_response(thread, cancellation_handle=None, on_checkpoint=None):
        for i, chunk in enumerate(chunks):
            if checkpoint_on and i in checkpoint_on and on_checkpoint:
                await on_checkpoint()
            yield chunk

    generator = MagicMock()
    generator.stream_response = stream_response
    return generator


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_thread_called_on_clean_completion():
    thread_container = MagicMock()
    thread_service = AsyncMock()
    thread_service.get_thread.return_value = thread_container

    generator = _stream_factory({"event_type": "text"})
    sut = ThreadJobProcessor(thread_service, generator)

    chunks = [c async for c in sut.process_job(_make_job(), cancellation_handle=None)]

    thread_service.update_thread.assert_awaited_once_with(thread_container)
    assert len(chunks) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_thread_called_on_each_checkpoint_and_at_end():
    thread_container = MagicMock()
    thread_service = AsyncMock()
    thread_service.get_thread.return_value = thread_container

    # Two chunks; checkpoint fires before chunk 0 and chunk 1
    generator = _stream_factory(
        {"event_type": "tool_response"},
        {"event_type": "message_fully_added"},
        checkpoint_on=[0, 1],
    )
    sut = ThreadJobProcessor(thread_service, generator)

    [c async for c in sut.process_job(_make_job(), cancellation_handle=None)]

    # 2 checkpoints + 1 final = 3 calls
    assert thread_service.update_thread.await_count == 3
    thread_service.update_thread.assert_awaited_with(thread_container)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_on_complete_called_after_stream():
    thread_container = MagicMock()
    thread_service = AsyncMock()
    thread_service.get_thread.return_value = thread_container

    generator = _stream_factory({"event_type": "text"})
    sut = ThreadJobProcessor(thread_service, generator)
    on_complete = MagicMock()

    [c async for c in sut.process_job(_make_job(), cancellation_handle=None, on_complete=on_complete)]

    on_complete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_raises_404_when_thread_not_found():
    thread_service = AsyncMock()
    thread_service.get_thread.return_value = None
    generator = MagicMock()
    sut = ThreadJobProcessor(thread_service, generator)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        [c async for c in sut.process_job(_make_job(), cancellation_handle=None)]

    assert exc_info.value.status_code == 404
