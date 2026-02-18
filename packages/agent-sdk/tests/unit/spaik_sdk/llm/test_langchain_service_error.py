from unittest.mock import MagicMock, patch

import pytest

from spaik_sdk.llm.langchain_service import LangChainService
from spaik_sdk.thread.models import ErrorEvent


def make_service_with_mocks() -> LangChainService:
    mock_config = MagicMock()
    mock_thread = MagicMock()
    mock_thread.thread_id = "test-thread"
    return LangChainService(
        llm_config=mock_config,
        thread_container=mock_thread,
        assistant_name="test-assistant",
        assistant_id="test-id",
    )


@pytest.mark.unit
class TestLangChainServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_execute_stream_tokens_yields_error_event_on_exception(self):
        service = make_service_with_mocks()

        test_error = RuntimeError("model exploded")

        async def failing_stream(*args, **kwargs):
            raise test_error
            yield  # noqa: F841 - makes this an async generator

        with patch.object(service, "_execute_stream_tokens_direct", side_effect=failing_stream):
            with patch.object(service, "_handle_error", return_value={"error": "model exploded"}) as mock_handle:
                events = []
                async for event in service.execute_stream_tokens("hello"):
                    events.append(event)

                mock_handle.assert_called_once_with(test_error)

                assert len(events) == 1
                assert isinstance(events[0], ErrorEvent)
                assert events[0].error_message == "model exploded"

    @pytest.mark.asyncio
    async def test_error_event_has_unknown_type_by_default(self):
        service = make_service_with_mocks()

        async def failing_stream(*args, **kwargs):
            raise ValueError("bad input")
            yield  # noqa: F841

        with patch.object(service, "_execute_stream_tokens_direct", side_effect=failing_stream):
            with patch.object(service, "_handle_error", return_value={"error": "bad input"}):
                events = []
                async for event in service.execute_stream_tokens("hello"):
                    events.append(event)

                assert events[0].error_type == "unknown"
