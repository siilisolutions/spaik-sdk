from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from spaik_sdk.server.response.agent_response_generator import AgentResponseGenerator
from spaik_sdk.thread.models import (
    BlockAddedEvent,
    MessageBlock,
    MessageBlockType,
    MessageFullyAddedEvent,
    StreamingUpdatedEvent,
    ThreadEvent,
    ThreadMessage,
    ToolResponseReceivedEvent,
)


def _make_block(block_id: str = "b1") -> MessageBlock:
    return MessageBlock(id=block_id, streaming=False, type=MessageBlockType.PLAIN, content="hi")


def _make_message(msg_id: str = "m1") -> ThreadMessage:
    return ThreadMessage(id=msg_id, ai=True, author_id="agent", author_name="Agent", timestamp=0, blocks=[])


def _make_generator_factory(*events: ThreadEvent) -> Any:
    async def call_agent(agent: Any) -> AsyncGenerator[ThreadEvent, None]:
        for event in events:
            yield event

    return call_agent


def _make_sut(*events: ThreadEvent) -> tuple[AgentResponseGenerator, AsyncMock]:
    agent = MagicMock()
    agent.set_thread_container = MagicMock()
    agent.set_cancellation_handle = MagicMock()
    call_agent = _make_generator_factory(*events)
    return AgentResponseGenerator(agent, call_agent), agent


def _make_thread() -> MagicMock:
    thread = MagicMock()
    thread.thread_id = "thread-1"
    return thread


@pytest.mark.unit
@pytest.mark.asyncio
async def test_on_checkpoint_called_after_tool_response():
    tool_event = ToolResponseReceivedEvent(tool_call_id="tc1", response="done", block_id="b1")
    sut, _ = _make_sut(tool_event)
    checkpoint = AsyncMock()

    chunks = [c async for c in sut.stream_response(_make_thread(), on_checkpoint=checkpoint)]

    checkpoint.assert_awaited_once()
    assert len(chunks) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_on_checkpoint_called_after_message_fully_added():
    msg_event = MessageFullyAddedEvent(message=_make_message())
    sut, _ = _make_sut(msg_event)
    checkpoint = AsyncMock()

    chunks = [c async for c in sut.stream_response(_make_thread(), on_checkpoint=checkpoint)]

    checkpoint.assert_awaited_once()
    assert len(chunks) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_on_checkpoint_not_called_for_other_events():
    block = _make_block()
    streaming_event = StreamingUpdatedEvent(block_id="b1", content="x", total_content="x")
    block_event = BlockAddedEvent(message_id="m1", block_id="b1", block=block)
    sut, _ = _make_sut(streaming_event, block_event)
    checkpoint = AsyncMock()

    [c async for c in sut.stream_response(_make_thread(), on_checkpoint=checkpoint)]

    checkpoint.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_on_checkpoint_called_once_per_checkpoint_event():
    tool_event = ToolResponseReceivedEvent(tool_call_id="tc1", response="r1", block_id="b1")
    msg_event = MessageFullyAddedEvent(message=_make_message())
    sut, _ = _make_sut(tool_event, msg_event)
    checkpoint = AsyncMock()

    [c async for c in sut.stream_response(_make_thread(), on_checkpoint=checkpoint)]

    assert checkpoint.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_on_checkpoint_does_not_raise():
    tool_event = ToolResponseReceivedEvent(tool_call_id="tc1", response="r1", block_id="b1")
    sut, _ = _make_sut(tool_event)

    chunks = [c async for c in sut.stream_response(_make_thread(), on_checkpoint=None)]

    assert len(chunks) == 1
