import json

import pytest

from spaik_sdk.thread.models import ErrorEvent


@pytest.mark.unit
class TestErrorEvent:
    def test_is_publishable(self):
        event = ErrorEvent(error_message="rate limit exceeded")
        assert event.is_publishable() is True

    def test_event_type_strips_event_suffix(self):
        event = ErrorEvent(error_message="something broke")
        assert event.get_event_type() == "Error"

    def test_event_data_contains_only_error_fields(self):
        event = ErrorEvent(error_message="bad request", error_type="rate_limit")
        data = event.get_event_data()
        assert data == {"error_message": "bad request", "error_type": "rate_limit"}

    def test_default_error_type_is_unknown(self):
        event = ErrorEvent(error_message="oops")
        data = event.get_event_data()
        assert data is not None
        assert data["error_type"] == "unknown"

    def test_dump_json_produces_valid_event_structure(self):
        event = ErrorEvent(error_message="test error", error_type="stream_error")
        raw = event.dump_json("thread-123")
        parsed = json.loads(raw)

        assert parsed["thread_id"] == "thread-123"
        assert parsed["event_type"] == "Error"
        assert parsed["data"]["error_message"] == "test error"
        assert parsed["data"]["error_type"] == "stream_error"
        assert "timestamp" in parsed
