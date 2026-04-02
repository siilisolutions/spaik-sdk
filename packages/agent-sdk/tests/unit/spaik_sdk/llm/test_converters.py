import json
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from spaik_sdk.llm.converters import convert_thread_message_to_langchain, convert_thread_message_to_langchain_multimodal
from spaik_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from spaik_sdk.tools.tool_provider import BaseTool, ToolProvider


def parse_tool_call_payload(content: str | list[str | dict[str, Any]]) -> dict[str, Any]:
    prefix = "<tool_call>"
    suffix = "</tool_call>"
    assert isinstance(content, str)
    assert content.startswith(prefix)
    assert content.endswith(suffix)
    return json.loads(content[len(prefix) : -len(suffix)])


class CustomHistoryToolProvider(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        return []

    def render_tool_block_for_history(self, block: MessageBlock) -> str:
        return f"<custom_tool_call tool=\"{block.tool_name}\" id=\"{block.tool_call_id}\"/>"


class DetailedHistoryToolProvider(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        return []


class HiddenHistoryToolProvider(ToolProvider):
    def __init__(self):
        super().__init__(persist_tool_block_history=False)

    def get_tools(self) -> list[BaseTool]:
        return []


class LegacyHistoryToolProvider(ToolProvider):
    def __init__(self):
        pass

    def get_tools(self) -> list[BaseTool]:
        return []


@pytest.mark.unit
class TestConverters:
    def test_convert_thread_message_to_langchain_preserves_tool_block_details(self):
        provider = DetailedHistoryToolProvider()
        thread_message = ThreadMessage(
            id="message-1",
            ai=True,
            author_id="assistant",
            author_name="assistant",
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_provider=provider,
                    tool_name="search_docs",
                    tool_call_id="call-1",
                    tool_call_args={"query": "tool history"},
                    tool_call_response="Found matching documents",
                    tool_call_error="temporary warning",
                )
            ],
        )

        converted = convert_thread_message_to_langchain(thread_message)

        assert isinstance(converted, AIMessage)
        payload = parse_tool_call_payload(converted.content)
        assert payload == {
            "args": {"query": "tool history"},
            "error": "temporary warning",
            "response": "Found matching documents",
            "tool": "search_docs",
            "tool_call_id": "call-1",
        }

    def test_convert_thread_message_to_langchain_uses_provider_override(self):
        provider = CustomHistoryToolProvider()
        thread_message = ThreadMessage(
            id="message-1",
            ai=True,
            author_id="assistant",
            author_name="assistant",
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_provider=provider,
                    tool_name="search_docs",
                    tool_call_id="call-1",
                )
            ],
        )

        converted = convert_thread_message_to_langchain(thread_message)

        assert converted.content == '<custom_tool_call tool="search_docs" id="call-1"/>'

    def test_convert_thread_message_to_langchain_keeps_tool_name_when_provider_disables_history_details(self):
        provider = HiddenHistoryToolProvider()
        thread_message = ThreadMessage(
            id="message-1",
            ai=True,
            author_id="assistant",
            author_name="assistant",
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_provider=provider,
                    tool_name="search_docs",
                    tool_call_id="call-1",
                )
            ],
        )

        converted = convert_thread_message_to_langchain(thread_message)

        assert converted.content == '<tool_call tool="search_docs"/>'

    def test_convert_thread_message_to_langchain_handles_provider_without_base_init(self):
        provider = LegacyHistoryToolProvider()
        thread_message = ThreadMessage(
            id="message-1",
            ai=True,
            author_id="assistant",
            author_name="assistant",
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_provider=provider,
                    tool_name="search_docs",
                    tool_call_id="call-1",
                )
            ],
        )

        converted = convert_thread_message_to_langchain(thread_message)

        payload = parse_tool_call_payload(converted.content)
        assert payload == {"tool": "search_docs", "tool_call_id": "call-1"}

    @pytest.mark.asyncio
    async def test_convert_thread_message_to_langchain_multimodal_uses_tool_history_rendering(self):
        provider = CustomHistoryToolProvider()
        thread_message = ThreadMessage(
            id="message-1",
            ai=True,
            author_id="assistant",
            author_name="assistant",
            timestamp=int(time.time() * 1000),
            blocks=[
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_provider=provider,
                    tool_name="search_docs",
                    tool_call_id="call-1",
                )
            ],
        )

        converted = await convert_thread_message_to_langchain_multimodal(
            thread_message,
            file_storage=MagicMock(),
        )

        assert converted.content == '<custom_tool_call tool="search_docs" id="call-1"/>'
