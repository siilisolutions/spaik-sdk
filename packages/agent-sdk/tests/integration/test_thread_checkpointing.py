"""
Integration test for thread checkpointing.

Verifies that the thread is persisted to storage after each tool call
(mid-run), not only on clean completion.
"""

import time
import uuid
from typing import List

import pytest
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.recording.impl.local_recorder import LocalRecorder
from spaik_sdk.server.job_processor.thread_job_processor import ThreadJobProcessor
from spaik_sdk.server.queue.agent_job_queue import AgentJob, JobType
from spaik_sdk.server.response.simple_agent_response_generator import SimpleAgentResponseGenerator
from spaik_sdk.server.services.thread_service import ThreadService
from spaik_sdk.server.storage.impl.in_memory_thread_repository import InMemoryThreadRepository
from spaik_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from spaik_sdk.thread.thread_container import ThreadContainer
from spaik_sdk.tools.tool_provider import ToolProvider

load_dotenv()


class GreetingToolProvider(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def get_secret_greeting() -> str:
            """Returns the users secret greeting."""
            return "kikkelis kokkelis"

        return [get_secret_greeting]


class CheckpointTestAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="Be very concise. Always use your tool to get the secret greeting.",
            llm_model=ModelRegistry.CLAUDE_4_SONNET,
            recorder=LocalRecorder.create_conditional_recorder(
                recording_name="test_get_response_with_tool_call_claude-sonnet-4-20250514",
                recordings_dir="tests/data/recordings",
                delay=0.001,
            ),
        )

    def get_tool_providers(self) -> List[ToolProvider]:
        return [GreetingToolProvider()]


def _make_user_message(content: str) -> ThreadMessage:
    return ThreadMessage(
        id=str(uuid.uuid4()),
        ai=False,
        author_id="user",
        author_name="User",
        timestamp=int(time.time() * 1000),
        blocks=[MessageBlock(id=str(uuid.uuid4()), streaming=False, type=MessageBlockType.PLAIN, content=content)],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_checkpoint_fires_during_tool_call_run():
    """
    With a tool-calling agent, save_thread must be called more than once:
    at minimum once for the tool response checkpoint and once for the final save.
    """
    repository = InMemoryThreadRepository()
    thread_service = ThreadService(repository)

    thread = ThreadContainer(system_prompt="Be very concise. Always use your tool to get the secret greeting.")
    thread.add_message(_make_user_message("What is my secret greeting?"))
    await repository.save_thread(thread)

    agent = CheckpointTestAgent()
    generator = SimpleAgentResponseGenerator(agent)
    processor = ThreadJobProcessor(thread_service, generator)

    job = AgentJob(id=thread.thread_id, job_type=JobType.THREAD_MESSAGE)

    save_calls: list[ThreadContainer] = []
    original_save = repository.save_thread

    async def spy_save(tc: ThreadContainer) -> None:
        save_calls.append(tc)
        await original_save(tc)

    repository.save_thread = spy_save  # type: ignore[method-assign]

    [chunk async for chunk in processor.process_job(job, cancellation_handle=None)]

    # At minimum: one checkpoint (after tool response) + one final save
    assert len(save_calls) >= 2, f"Expected at least 2 save_thread calls (checkpoint + final), got {len(save_calls)}"

    # The thread in storage should now contain the assistant reply
    saved = await repository.load_thread(thread.thread_id)
    assert saved is not None
    ai_messages = [m for m in saved.messages if m.ai]
    assert len(ai_messages) >= 1
