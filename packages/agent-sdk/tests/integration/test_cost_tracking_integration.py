"""Integration test for cost tracking in streaming events."""

import pytest

from siili_ai_sdk.llm.streaming.models import EventType
from siili_ai_sdk.llm.streaming.streaming_event_handler import StreamingEventHandler


@pytest.mark.integration
class TestCostTrackingIntegration:
    """Test cost tracking integration with streaming event handler."""

    def test_cost_tracking_with_openai_style_data(self):
        """Test cost tracking with OpenAI-style usage metadata."""
        handler = StreamingEventHandler()

        # Mock OpenAI on_chat_model_end event data
        class MockUsageMetadata:
            input_tokens = 100
            output_tokens = 50
            total_tokens = 150

        class MockOutput:
            usage_metadata = MockUsageMetadata()
            response_metadata = {"model_name": "gpt-4o"}

        data = {"metadata": {"ls_provider": "openai", "ls_model_name": "gpt-4o"}, "output": MockOutput()}

        # Process the stream end event
        events = []

        async def collect_events():
            async for event in handler._handle_stream_end(data):
                events.append(event)

        # Run the async generator
        import asyncio

        asyncio.run(collect_events())

        # Verify we got a usage metadata event
        usage_events = [e for e in events if e.event_type == EventType.USAGE_METADATA]
        assert len(usage_events) == 1

        usage_event = usage_events[0]
        assert usage_event.usage_metadata is not None
        assert usage_event.usage_metadata["token_usage"]["input_tokens"] == 100
        assert usage_event.usage_metadata["token_usage"]["output_tokens"] == 50
        assert usage_event.usage_metadata["token_usage"]["total_tokens"] == 150

    def test_cost_tracking_with_google_style_data(self):
        """Test cost tracking with Google-style usage metadata including reasoning tokens."""
        handler = StreamingEventHandler()

        # Mock Google on_chat_model_end event data
        class MockOutputTokenDetails:
            reasoning = 25

        class MockUsageMetadata:
            input_tokens = 53
            output_tokens = 11
            total_tokens = 110
            output_token_details = MockOutputTokenDetails()

        class MockOutput:
            usage_metadata = MockUsageMetadata()
            response_metadata = {"model_name": "gemini-2.5-flash-preview-05-20"}

        data = {"metadata": {"ls_provider": "google_genai", "ls_model_name": "gemini-2.5-flash-preview-05-20"}, "output": MockOutput()}

        # Process the stream end event
        events = []

        async def collect_events():
            async for event in handler._handle_stream_end(data):
                events.append(event)

        # Run the async generator
        import asyncio

        asyncio.run(collect_events())

        # Verify we got a usage metadata event with reasoning tokens
        usage_events = [e for e in events if e.event_type == EventType.USAGE_METADATA]
        assert len(usage_events) == 1

        usage_event = usage_events[0]
        assert usage_event.usage_metadata is not None
        assert usage_event.usage_metadata["token_usage"]["reasoning_tokens"] == 25

    def test_cost_tracking_fallback_without_usage_metadata(self):
        """Test cost tracking fallback when usage_metadata is not available."""
        handler = StreamingEventHandler()

        # Mock GPT-4.1 style data (no usage_metadata)
        class MockResponseMetadata:
            model_name = "gpt-4.1-2025-04-14"
            finish_reason = "stop"

        class MockOutput:
            usage_metadata = None
            response_metadata = MockResponseMetadata()
            content = "This is a test response from GPT-4.1"

        data = {"metadata": {"ls_provider": "openai", "ls_model_name": "gpt-4.1"}, "output": MockOutput()}

        # Process the stream end event
        events = []

        async def collect_events():
            async for event in handler._handle_stream_end(data):
                events.append(event)

        # Run the async generator
        import asyncio

        asyncio.run(collect_events())

        # Verify we still got a usage metadata event with estimation
        usage_events = [e for e in events if e.event_type == EventType.USAGE_METADATA]
        assert len(usage_events) == 1

        usage_event = usage_events[0]
        assert usage_event.usage_metadata is not None
        assert usage_event.usage_metadata["token_usage"]["output_tokens"] > 0  # Estimated
        assert usage_event.usage_metadata["metadata"]["estimation_method"] == "content_length"
