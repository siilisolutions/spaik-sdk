import time
from typing import List, Optional

import pytest
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool
from pydantic import BaseModel

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.recording.conditional_recorder import ConditionalRecorder
from siili_ai_sdk.recording.impl.local_recorder import LocalRecorder
from siili_ai_sdk.thread.models import MessageBlockType
from siili_ai_sdk.tools.tool_provider import ToolProvider
from siili_ai_sdk.utils.init_logger import init_logger

load_dotenv()
logger = init_logger(__name__)


def create_recorder(recording_name: str, delay: float = 0.001) -> ConditionalRecorder:
    return LocalRecorder.create_conditional_recorder(
        recording_name=recording_name,
        recordings_dir="tests/data/recordings",
        delay=delay,
    )


class ConcreteTestAgent(BaseAgent):
    def __init__(self, recording_name: str, delay: float = 0.001, **kwargs):
        super().__init__(
            system_prompt="You're an an agent used in unit testing. Be very concise in your responses.",
            recorder=create_recorder(recording_name, delay),
            **kwargs,
        )


class TestToolProvider(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def get_secret_greeting() -> str:
            """Returns the users secret greeting."""
            return "kikkelis kokkelis"

        return [get_secret_greeting]


class DelayCancellationHandle(CancellationHandle):
    def __init__(self, delay: float = 2):
        self.delay = delay
        self.start_time = time.time()

    async def is_cancelled(self) -> bool:
        return time.time() - self.start_time > self.delay


class ToolCallTestAgent(BaseAgent):
    def __init__(self, recording_name: str, **kwargs):
        super().__init__(
            system_prompt="Be very concise in your responses. Always use your tool to get the secret greeting.",
            recorder=create_recorder(recording_name),
            **kwargs,
        )

    def get_tool_providers(self) -> List[ToolProvider]:
        return [TestToolProvider()]


@pytest.mark.unit
class TestBaseAgent:
    """Unit tests for BaseAgent class."""

    def test_get_response_text(self):
        """Test basic agent instantiation."""
        agent = ConcreteTestAgent(recording_name="test_get_response_text")
        assert agent.get_response_text("Hello, how are you?")[0:6] == "Hello!"

    def test_get_structured_response(self):
        agent = ConcreteTestAgent(recording_name="test_get_structured_response")

        class TestResponse(BaseModel):
            message: str
            random_number: int

        response = agent.get_structured_response("Hi give me a random number from 0-1000", TestResponse)
        assert response.message == "Here's a random number between 0-1000 for you!"
        assert response.random_number == 742

    @pytest.mark.parametrize(
        "model",
        [
            ModelRegistry.CLAUDE_4_SONNET,
            ModelRegistry.CLAUDE_3_7_SONNET,
            ModelRegistry.GPT_4_1,
            ModelRegistry.O4_MINI,
            ModelRegistry.GEMINI_2_5_FLASH,
        ],
    )
    def test_get_response_text_with_different_models(self, model):
        """Test basic agent response with different LLM models."""
        agent = ConcreteTestAgent(
            recording_name=f"test_get_response_text_{model.name.lower()}",
            llm_model=model,
        )
        response = agent.get_response_text("Hello, how are you?")
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.parametrize(
        "model",
        [
            ModelRegistry.CLAUDE_4_SONNET,
            ModelRegistry.CLAUDE_3_7_SONNET,
            ModelRegistry.GPT_4_1,
            ModelRegistry.O4_MINI,
            ModelRegistry.GEMINI_2_5_FLASH,
            ModelRegistry.CLAUDE_4_1_OPUS,
            ModelRegistry.GPT_5,
        ],
    )
    def test_get_response_with_tool_call(self, model):
        """Test basic agent response with tool call."""
        agent = ToolCallTestAgent(
            recording_name=f"test_get_response_with_tool_call_{model.name.lower()}",
            llm_model=model,
        )
        reasoning = []
        response_text = []
        tool_calls = []
        response = agent.get_response("What is my secret greeting?")
        for block in response.blocks:
            if block.type == MessageBlockType.REASONING and block.content is not None:
                reasoning.append(block.content)
            elif block.type == MessageBlockType.PLAIN and block.content is not None:
                response_text.append(block.content)
            elif block.type == MessageBlockType.TOOL_USE:
                tool_calls.append(block)

        for content in reasoning:
            logger.info(f"reasoning: {content}")
        for content in response_text:
            logger.info(f"response: {content}")
        for block in tool_calls:
            logger.info(f"tool_calls: {block}")
        logger.info(f"model: {model}")
        assert "kikkelis kokkelis" in " ".join(response_text).lower()
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "get_secret_greeting"
        if model.reasoning:
            assert len(reasoning[0]) > 0

    def test_get_response_text_with_cancellation(self):
        """Test basic agent instantiation."""
        recording_name = "test_get_response_text_with_cancellation"

        cancellation_handle: Optional[CancellationHandle] = DelayCancellationHandle(delay=0.2)
        # If we are recording, we dont want to cancel as that prevents getting the full response
        tmp_recorder = create_recorder(recording_name)

        if tmp_recorder.get_playback() is None:
            cancellation_handle = None

        agent = ConcreteTestAgent(recording_name=recording_name, cancellation_handle=cancellation_handle, delay=0.01)
        response = agent.get_response("write me a poem about cats where each word starts with a, 2nd with b etc until z'")
        logger.info(f"response: {response}")
        logger.info(f"thread_container: {agent.thread_container.streaming_content}")
        assert len(response.blocks) == 1
        assert len(response.blocks[0].content or "") > 10

    @pytest.mark.asyncio
    async def test_mystery_streaming_issue(self):
        agent = ConcreteTestAgent(
            recording_name="test_mystery_streaming_issue",
        )
        events=[]
        counts={}
        async for event in agent.get_event_stream("derp'"):
            events.append(event)
            counts[event.get_event_type()] = counts.get(event.get_event_type(), 0) + 1
        logger.info(f"counts: {counts}")
        assert counts["MessageAdded"] == 1
        assert counts["BlockAdded"] == 4
        assert counts["BlockFullyAdded"] == 4
        assert counts["ToolCallStarted"] == 2
        assert counts["ToolResponseReceived"] == 2

        # weird stuff going on on second run

        events=[]
        counts={}
        async for event in agent.get_event_stream("derp'"):
            events.append(event)
            if event.get_event_type() == "MessageAdded":
                logger.info(f"message: {event.message}")
            counts[event.get_event_type()] = counts.get(event.get_event_type(), 0) + 1
        logger.info(f"counts: {counts}")
        assert counts["MessageAdded"] == 1
        assert counts["BlockAdded"] == 5
        assert counts["BlockFullyAdded"] == 5
        assert counts["ToolCallStarted"] == 2
        assert counts["ToolResponseReceived"] == 2

        

