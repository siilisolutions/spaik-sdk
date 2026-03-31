import json
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from spaik_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from spaik_sdk.thread.thread_container import ThreadContainer
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


def make_message(message_id: str, ai: bool, block: MessageBlock) -> ThreadMessage:
    author_id = "assistant" if ai else "user"
    return ThreadMessage(
        id=message_id,
        ai=ai,
        author_id=author_id,
        author_name=author_id,
        timestamp=int(time.time() * 1000),
        blocks=[block],
    )


@pytest.mark.unit
class TestThreadContainer:
    def test_get_langchain_messages_preserves_tool_history_across_turns(self):
        provider = DetailedHistoryToolProvider()
        thread = ThreadContainer(system_prompt="system prompt")
        thread.add_message(
            make_message(
                "message-1",
                False,
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.PLAIN,
                    content="Use the search tool",
                ),
            )
        )
        thread.add_message(
            make_message(
                "message-2",
                True,
                MessageBlock(
                    id="block-2",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_name="search_docs",
                    tool_call_id="call-1",
                    tool_call_args={"query": "tool history"},
                    tool_call_response="Found matching documents",
                ),
            )
        )
        thread.add_message(
            make_message(
                "message-3",
                False,
                MessageBlock(
                    id="block-3",
                    streaming=False,
                    type=MessageBlockType.PLAIN,
                    content="Continue from that result",
                ),
            )
        )
        thread.bind_tool_providers([provider])

        messages = thread.get_langchain_messages()

        assert len(messages) == 4
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert isinstance(messages[2], AIMessage)
        assert isinstance(messages[3], HumanMessage)
        assert messages[1].content == "Use the search tool"
        assert messages[3].content == "Continue from that result"
        assert parse_tool_call_payload(messages[2].content) == {
            "args": {"query": "tool history"},
            "response": "Found matching documents",
            "tool": "search_docs",
            "tool_call_id": "call-1",
        }

    def test_get_langchain_messages_uses_provider_tool_history_override(self):
        provider = CustomHistoryToolProvider()
        thread = ThreadContainer(system_prompt="system prompt")
        thread.add_message(
            make_message(
                "message-1",
                True,
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_name="search_docs",
                    tool_call_id="call-1",
                ),
            )
        )
        thread.bind_tool_providers([provider])

        messages = thread.get_langchain_messages()

        assert messages[1].content == '<custom_tool_call tool="search_docs" id="call-1"/>'

    def test_get_langchain_messages_keeps_tool_name_for_provider_disabled_history_details(self):
        provider = HiddenHistoryToolProvider()
        thread = ThreadContainer(system_prompt="system prompt")
        thread.add_message(
            make_message(
                "message-1",
                True,
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_name="search_docs",
                    tool_call_id="call-1",
                ),
            )
        )
        thread.bind_tool_providers([provider])

        messages = thread.get_langchain_messages()

        assert messages[1].content == '<tool_call tool="search_docs"/>'

    @pytest.mark.asyncio
    async def test_get_langchain_messages_multimodal_uses_provider_tool_history_override(self):
        provider = CustomHistoryToolProvider()
        thread = ThreadContainer(system_prompt="system prompt")
        thread.add_message(
            make_message(
                "message-1",
                True,
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=provider.get_provider_id(),
                    tool_name="search_docs",
                    tool_call_id="call-1",
                ),
            )
        )
        thread.bind_tool_providers([provider])

        messages = await thread.get_langchain_messages_multimodal(
            file_storage=MagicMock(),
        )

        assert messages[1].content == '<custom_tool_call tool="search_docs" id="call-1"/>'
