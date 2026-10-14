import json

import pytest
from ag_ui.core import AssistantMessage, ToolMessage

from spaik_sdk.thread.migration import is_legacy_thread, load_thread_data
from spaik_sdk.thread.thread_container import ThreadContainer

pytestmark = pytest.mark.unit


def block(block_id: str, block_type: str, **fields) -> dict:
    return {
        "id": block_id,
        "streaming": False,
        "content": None,
        "tool_provider_id": None,
        "tool_call_id": None,
        "tool_call_args": None,
        "tool_name": None,
        "tool_call_response": None,
        "tool_call_error": None,
        "type": block_type,
        **fields,
    }


def legacy_row(include_user: bool = True) -> dict:
    user = {
        "id": "m1",
        "ai": False,
        "author_id": "alice",
        "author_name": "Alice",
        "timestamp": 1000,
        "blocks": [block("b1", "plain", content="What is the weather?")],
        "attachments": [{"file_id": "f1", "mime_type": "image/png", "filename": "map.png"}],
    }
    assistant = {
        "id": "m2",
        "ai": True,
        "author_id": "agent",
        "author_name": "Agent",
        "timestamp": 2000,
        "blocks": [
            block("b2", "reasoning", content="Check the tool."),
            block(
                "b3",
                "tool_use",
                tool_provider_id="weather",
                tool_call_id="call-1",
                tool_call_args={"city": "Helsinki"},
                tool_name="get_weather",
                tool_call_response="Sunny",
            ),
            block("b4", "plain", content="It is sunny."),
        ],
        "consumption_metadata": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    }
    messages = [user, assistant] if include_user else [assistant]
    return {"id": "t1", "system_prompt": "private", "last_activity_time": 3000, "messages": messages}


def test_legacy_row_converts_in_memory():
    data = legacy_row()
    thread = load_thread_data(json.loads(json.dumps(data)))
    assert thread.owner_id == "alice"
    assert [m.id for m in thread.messages] == ["m1", "b2", "m2", "b3:result"]
    assistant = thread.messages[2]
    assert isinstance(assistant, AssistantMessage)
    assert assistant.content == "It is sunny."
    assert assistant.tool_calls is not None
    assert json.loads(assistant.tool_calls[0].function.arguments) == {"city": "Helsinki"}
    result = thread.messages[3]
    assert isinstance(result, ToolMessage)
    assert result.content == "Sunny"
    assert thread.envelope.message_metadata["m1"]["attachments"][0]["file_id"] == "f1"
    assert thread.envelope.message_metadata["m2"]["timestamp"] == 2000
    assert thread.envelope.replay["m2"]["tool_providers"] == {"call-1": "weather"}
    assert thread.envelope.invocations[0].usage == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    assert thread.system_prompt == "private"
    assert (thread.envelope.created_at, thread.envelope.last_activity_time) == (1000, 3000)
    assert data == legacy_row()


def test_fallback_owner_is_used_only_without_a_user_message():
    assert load_thread_data(legacy_row(), fallback_owner="bob").owner_id == "alice"
    assert load_thread_data(legacy_row(include_user=False), fallback_owner="bob").owner_id == "bob"
    with pytest.raises(ValueError, match="fallback owner"):
        load_thread_data(legacy_row(include_user=False))


def test_converted_thread_reloads_as_current_format():
    stored = load_thread_data(legacy_row()).to_dict()
    assert not is_legacy_thread(stored)
    assert load_thread_data(stored).envelope == load_thread_data(legacy_row()).envelope


def test_current_format_loads_unchanged():
    thread = ThreadContainer(system_prompt="hi", owner_id="carol")
    assert load_thread_data(thread.to_dict()).envelope == thread.envelope


def test_from_dict_points_legacy_data_to_loader():
    with pytest.raises(ValueError, match="load_thread_data"):
        ThreadContainer.from_dict(legacy_row())
