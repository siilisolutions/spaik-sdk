from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessageChunk

from siili_ai_sdk.llm.streaming.models import EventType
from siili_ai_sdk.llm.streaming.streaming_event_handler import StreamingEventHandler


def make_chat_model_stream_event(content: str, tool_calls: list | None = None) -> dict:
    chunk = AIMessageChunk(content=content, tool_calls=tool_calls or [])
    return {"event": "on_chat_model_stream", "data": {"chunk": chunk}}


def make_chain_stream_event(content: str) -> dict:
    chunk = AIMessageChunk(content=content)
    return {"event": "on_chain_stream", "data": {"chunk": {"messages": [chunk]}}}


def make_chain_end_event(content: str = "", usage_metadata: dict | None = None) -> dict:
    chunk = AIMessageChunk(content=content)
    if usage_metadata:
        chunk.usage_metadata = usage_metadata  # type: ignore[assignment]
    return {"event": "on_chain_end", "data": {"output": {"messages": [chunk]}}}


async def collect_events(handler: StreamingEventHandler, raw_events: list[dict]) -> list:
    async def mock_stream():
        for event in raw_events:
            yield event

    events = []
    async for event in handler.process_stream(mock_stream()):
        events.append(event)
    return events


@pytest.mark.unit
class TestStreamingEventHandler:
    @pytest.mark.asyncio
    async def test_emits_token_events_for_chat_model_stream(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event("Hello"),
            make_chat_model_stream_event(" world"),
            make_chat_model_stream_event("!"),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        token_events = [e for e in events if e.event_type == EventType.TOKEN]
        assert len(token_events) == 3
        assert token_events[0].content == "Hello"
        assert token_events[1].content == " world"
        assert token_events[2].content == "!"

    @pytest.mark.asyncio
    async def test_falls_back_to_chain_stream_when_no_chat_model_stream(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chain_stream_event("Complete response"),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        token_events = [e for e in events if e.event_type == EventType.TOKEN]
        assert len(token_events) == 1
        assert token_events[0].content == "Complete response"

    @pytest.mark.asyncio
    async def test_ignores_chain_stream_when_chat_model_stream_present(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event("Token 1"),
            make_chat_model_stream_event(" Token 2"),
            make_chain_stream_event("Should be ignored"),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        token_events = [e for e in events if e.event_type == EventType.TOKEN]
        contents = [e.content for e in token_events]
        assert "Token 1" in contents
        assert " Token 2" in contents
        assert "Should be ignored" not in contents

    @pytest.mark.asyncio
    async def test_emits_message_start_before_first_content(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event("Hello"),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        event_types = [e.event_type for e in events]
        message_start_idx = event_types.index(EventType.MESSAGE_START)
        token_idx = event_types.index(EventType.TOKEN)
        assert message_start_idx < token_idx

    @pytest.mark.asyncio
    async def test_emits_complete_event_at_end(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event("Hello"),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        assert events[-1].event_type == EventType.COMPLETE

    @pytest.mark.asyncio
    async def test_handles_empty_content_gracefully(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event(""),
            make_chat_model_stream_event("Hello"),
            make_chat_model_stream_event(""),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        token_events = [e for e in events if e.event_type == EventType.TOKEN]
        assert len(token_events) == 1
        assert token_events[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_extracts_usage_metadata(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event("Hello"),
            make_chain_end_event(usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}),
        ]

        events = await collect_events(handler, raw_events)

        usage_events = [e for e in events if e.event_type == EventType.USAGE_METADATA]
        assert len(usage_events) >= 1
        assert usage_events[0].usage_metadata.input_tokens == 10
        assert usage_events[0].usage_metadata.output_tokens == 5

    @pytest.mark.asyncio
    async def test_handles_reasoning_content_blocks(self):
        handler = StreamingEventHandler()
        chunk = AIMessageChunk(content=[{"type": "thinking", "thinking": "Let me think..."}])
        raw_events = [
            {"event": "on_chat_model_stream", "data": {"chunk": chunk}},
            make_chat_model_stream_event("Answer"),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        reasoning_events = [e for e in events if e.event_type == EventType.REASONING]
        token_events = [e for e in events if e.event_type == EventType.TOKEN]
        assert len(reasoning_events) == 1
        assert reasoning_events[0].content == "Let me think..."
        assert len(token_events) == 1
        assert token_events[0].content == "Answer"

    @pytest.mark.asyncio
    async def test_handles_tool_calls(self):
        handler = StreamingEventHandler()
        raw_events = [
            make_chat_model_stream_event("", tool_calls=[{"id": "call_123", "name": "get_weather", "args": {"city": "NYC"}}]),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        tool_events = [e for e in events if e.event_type == EventType.TOOL_USE]
        assert len(tool_events) == 1
        assert tool_events[0].tool_name == "get_weather"
        assert tool_events[0].tool_call_id == "call_123"

    @pytest.mark.asyncio
    async def test_records_events_when_recorder_provided(self):
        recorder = MagicMock()
        handler = StreamingEventHandler(recorder=recorder)
        raw_events = [
            make_chat_model_stream_event("Hello"),
            make_chain_end_event(),
        ]

        await collect_events(handler, raw_events)

        assert recorder.record_token.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_tool_response(self):
        handler = StreamingEventHandler()

        # Mock tool output object
        class MockToolOutput:
            tool_call_id = "call_123"
            content = "Weather in Paris: Sunny, 25°C"

        raw_events = [
            make_chat_model_stream_event("", tool_calls=[{"id": "call_123", "name": "get_weather", "args": {"city": "Paris"}}]),
            {"event": "on_tool_end", "data": {"output": MockToolOutput()}},
            make_chat_model_stream_event("The weather is sunny."),
            make_chain_end_event(),
        ]

        events = await collect_events(handler, raw_events)

        tool_use_events = [e for e in events if e.event_type == EventType.TOOL_USE]
        tool_response_events = [e for e in events if e.event_type == EventType.TOOL_RESPONSE]

        assert len(tool_use_events) == 1
        assert tool_use_events[0].tool_name == "get_weather"

        assert len(tool_response_events) == 1
        assert tool_response_events[0].content == "Weather in Paris: Sunny, 25°C"
        assert tool_response_events[0].tool_call_id == "call_123"
