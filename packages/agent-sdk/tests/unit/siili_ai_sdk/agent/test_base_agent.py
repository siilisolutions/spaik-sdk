import time
from typing import List, Optional

import pytest
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool
from pydantic import BaseModel

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
from siili_ai_sdk.llm.cost.builtin_cost_provider import BuiltinCostProvider
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.recording.conditional_recorder import ConditionalRecorder
from siili_ai_sdk.recording.impl.local_recorder import LocalRecorder
from siili_ai_sdk.thread.models import MessageAddedEvent, MessageBlockType
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
    def __init__(
        self,
        recording_name: str,
        delay: float = 0.001,
        system_prompt: str = "You're an an agent used in unit testing. Be very concise in your responses.",
        **kwargs,
    ):
        super().__init__(
            system_prompt=system_prompt,
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


def assert_consumption_equals(actual_consumption: TokenUsage, expected_consumption: TokenUsage):
    """Helper function to assert consumption data matches expected values exactly."""
    # Collect all token mismatches
    mismatches = []

    # Check each field individually
    if actual_consumption.input_tokens != expected_consumption.input_tokens:
        mismatches.append(f"input_tokens: expected {expected_consumption.input_tokens}, got {actual_consumption.input_tokens}")

    if actual_consumption.output_tokens != expected_consumption.output_tokens:
        mismatches.append(f"output_tokens: expected {expected_consumption.output_tokens}, got {actual_consumption.output_tokens}")

    if actual_consumption.total_tokens != expected_consumption.total_tokens:
        mismatches.append(f"total_tokens: expected {expected_consumption.total_tokens}, got {actual_consumption.total_tokens}")

    if actual_consumption.reasoning_tokens != expected_consumption.reasoning_tokens:
        mismatches.append(f"reasoning_tokens: expected {expected_consumption.reasoning_tokens}, got {actual_consumption.reasoning_tokens}")

    if actual_consumption.cache_creation_tokens != expected_consumption.cache_creation_tokens:
        mismatches.append(
            f"cache_creation_tokens: expected {expected_consumption.cache_creation_tokens}, got {actual_consumption.cache_creation_tokens}"
        )

    if actual_consumption.cache_read_tokens != expected_consumption.cache_read_tokens:
        mismatches.append(
            f"cache_read_tokens: expected {expected_consumption.cache_read_tokens}, got {actual_consumption.cache_read_tokens}"
        )

    # If there are any mismatches, raise a detailed error
    if mismatches:
        error_msg = "Consumption token mismatches:\n" + "\n".join(f"  - {mismatch}" for mismatch in mismatches)
        error_msg += f"\n\nExpected: {expected_consumption}"
        error_msg += f"\nActual:   {actual_consumption}"
        raise AssertionError(error_msg)


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
            ModelRegistry.CLAUDE_4_5_SONNET,
            ModelRegistry.CLAUDE_4_5_HAIKU,
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
            ModelRegistry.CLAUDE_4_5_SONNET,
            ModelRegistry.CLAUDE_4_5_HAIKU,
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
        events = []
        counts = {}
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

        events = []
        counts = {}
        async for event in agent.get_event_stream("derp'"):
            events.append(event)
            if event.get_event_type() == "MessageAdded":
                message_event = event if isinstance(event, MessageAddedEvent) else None
                if message_event:
                    logger.info(f"message: {message_event.message}")
            counts[event.get_event_type()] = counts.get(event.get_event_type(), 0) + 1
        logger.info(f"counts: {counts}")
        assert counts["MessageAdded"] == 1
        assert counts["BlockAdded"] == 5
        assert counts["BlockFullyAdded"] == 5
        assert counts["ToolCallStarted"] == 2
        assert counts["ToolResponseReceived"] == 2

    def test_consumption_tracking(self):
        """Test that consumption metadata is properly tracked and stored with exact values."""
        agent = ConcreteTestAgent(
            recording_name="test_consumption_tracking",
            llm_model=ModelRegistry.CLAUDE_4_SONNET,
            system_prompt=f"""
            You're an an agent used in unit testing
            (in particular cost estimates). Ignore the following
            garbage {"foobar" * 1000}""",
        )

        # Send first message
        agent.get_response("Hello, how are you?")

        # TODO: prompt caching doesnt seem to be working - these will break once thats fixed
        # Expected consumption after first message (made-up exact figures)
        expected_first_message = TokenUsage(
            input_tokens=3070,
            output_tokens=84,
            total_tokens=3154,
            reasoning_tokens=0,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )

        # Check consumption after first message
        total_consumption_1 = agent.thread_container.get_total_consumption()
        assert_consumption_equals(total_consumption_1, expected_first_message)

        # Send second message
        agent.get_response("Tell me a short joke.")

        # Expected total consumption after both messages (made-up exact figures)
        expected_total_consumption = TokenUsage(
            input_tokens=6174,
            output_tokens=144,
            total_tokens=6318,
            reasoning_tokens=0,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )

        # Check total consumption after second message
        total_consumption_2 = agent.thread_container.get_total_consumption()
        assert_consumption_equals(total_consumption_2, expected_total_consumption)

        cost = BuiltinCostProvider().get_cost_estimate(ModelRegistry.CLAUDE_4_SONNET, total_consumption_2)
        assert cost.cost == 0.020682
