from typing import AsyncGenerator

import pytest

from spaik_sdk.llm.message_handler import MessageHandler
from spaik_sdk.llm.streaming.models import EventType, StreamingEvent
from spaik_sdk.thread.models import MessageBlockType
from spaik_sdk.thread.thread_container import ThreadContainer
from spaik_sdk.tools.tool_provider import BaseTool, ToolProvider


async def fake_stream() -> AsyncGenerator[dict, None]:
    if False:
        yield {}


class SearchToolProvider(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        return []


@pytest.mark.unit
class TestMessageHandler:
    @pytest.mark.asyncio
    async def test_process_agent_token_stream_persists_tool_provider_id_on_block_creation(self):
        thread = ThreadContainer(system_prompt="system prompt")
        provider = SearchToolProvider()
        handler = MessageHandler(
            thread,
            assistant_name="assistant",
            assistant_id="assistant",
            tool_provider_resolver=lambda tool_name: provider if tool_name == "search_docs" else None,
        )

        async def process_stream(_agent_stream):
            yield StreamingEvent(
                event_type=EventType.MESSAGE_START,
                message_id="message-1",
            )
            yield StreamingEvent(
                event_type=EventType.BLOCK_START,
                message_id="message-1",
                block_id="block-1",
                block_type=MessageBlockType.TOOL_USE,
                tool_name="search_docs",
                tool_call_id="call-1",
                tool_args={"query": "history"},
            )

        handler.streaming_handler.process_stream = process_stream  # type: ignore[method-assign]

        async for _ in handler.process_agent_token_stream(fake_stream()):
            pass

        block = thread.messages[0].blocks[0]
        assert block.tool_provider is provider
        assert block.tool_provider_id == provider.get_provider_id()
        assert block.tool_name == "search_docs"
        assert block.tool_call_id == "call-1"
