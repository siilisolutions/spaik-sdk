import copy
import json
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from spaik_sdk.thread.models import BlockAddedEvent, BlockFullyAddedEvent, MessageAddedEvent, MessageBlock, MessageBlockType, ThreadMessage
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
        return f'<custom_tool_call tool="{block.tool_name}" id="{block.tool_call_id}"/>'


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
    def test_add_message_block_preserves_tool_response_when_replacing_existing_tool_block(self):
        thread = ThreadContainer(system_prompt="system prompt")
        message = make_message(
            "message-1",
            True,
            MessageBlock(
                id="block-1",
                streaming=False,
                type=MessageBlockType.TOOL_USE,
                tool_name="generate_image",
                tool_call_id="call-1",
                tool_call_args={},
                tool_call_response="file-123",
            ),
        )
        thread.add_message(message)

        emitted_events: list[BlockAddedEvent] = []
        thread.subscribe(lambda event: emitted_events.append(copy.deepcopy(event)) if isinstance(event, BlockAddedEvent) else None)

        thread.add_message_block(
            "message-1",
            MessageBlock(
                id="block-1",
                streaming=True,
                type=MessageBlockType.TOOL_USE,
                tool_name="generate_image",
                tool_call_id="call-1",
                tool_call_args={"prompt": "balloon"},
            ),
        )

        block = thread.messages[0].blocks[0]
        assert block.tool_call_args == {"prompt": "balloon"}
        assert block.tool_call_response == "file-123"
        assert emitted_events[-1].get_event_data() == {
            "message_id": "message-1",
            "block": {
                "id": "block-1",
                "streaming": True,
                "content": None,
                "tool_provider_id": None,
                "tool_call_id": "call-1",
                "tool_call_args": {"prompt": "balloon"},
                "tool_name": "generate_image",
                "tool_call_response": "file-123",
                "tool_call_error": None,
                "type": "tool_use",
            },
        }

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

    def test_thread_events_strip_live_tool_provider_references(self):
        provider = DetailedHistoryToolProvider()
        thread = ThreadContainer(system_prompt="system prompt")
        events = []
        thread.subscribe(events.append)

        initial_message = make_message(
            "message-1",
            True,
            MessageBlock(
                id="block-1",
                streaming=False,
                type=MessageBlockType.TOOL_USE,
                tool_provider_id=provider.get_provider_id(),
                tool_provider=provider,
                tool_name="search_docs",
                tool_call_id="call-1",
            ),
        )
        thread.add_message(initial_message)

        assert isinstance(events[0], MessageAddedEvent)
        assert events[0].message.blocks[0].tool_provider is None
        assert initial_message.blocks[0].tool_provider is provider

        thread.add_message(make_message("message-2", True, MessageBlock(id="block-2", streaming=False, type=MessageBlockType.PLAIN)))
        thread.add_message_block(
            "message-2",
            MessageBlock(
                id="block-3",
                streaming=True,
                type=MessageBlockType.TOOL_USE,
                tool_provider_id=provider.get_provider_id(),
                tool_provider=provider,
                tool_name="search_docs",
                tool_call_id="call-2",
            ),
        )

        block_added_event = next(event for event in events if isinstance(event, BlockAddedEvent) and event.block_id == "block-3")
        assert block_added_event.block.tool_provider is None

        thread.finalize_streaming_blocks("message-2", ["block-3"])

        block_fully_added_event = next(event for event in events if isinstance(event, BlockFullyAddedEvent) and event.block_id == "block-3")
        assert block_fully_added_event.block.tool_provider is None

    def test_bind_tool_providers_rebinds_new_provider_instance_after_serializable_copy(self):
        original_provider = DetailedHistoryToolProvider()
        thread = ThreadContainer(system_prompt="system prompt")
        thread.add_message(
            make_message(
                "message-1",
                True,
                MessageBlock(
                    id="block-1",
                    streaming=False,
                    type=MessageBlockType.TOOL_USE,
                    tool_provider_id=original_provider.get_provider_id(),
                    tool_provider=original_provider,
                    tool_name="search_docs",
                    tool_call_id="call-1",
                ),
            )
        )

        reloaded_thread = thread.create_serializable_copy()
        reloaded_block = reloaded_thread.messages[0].blocks[0]

        assert reloaded_block.tool_provider is None
        assert reloaded_block.tool_provider_id == original_provider.get_provider_id()

        rebound_provider = DetailedHistoryToolProvider()
        reloaded_thread.bind_tool_providers([rebound_provider])

        assert reloaded_block.tool_provider is rebound_provider
        assert reloaded_block.tool_provider is not original_provider
