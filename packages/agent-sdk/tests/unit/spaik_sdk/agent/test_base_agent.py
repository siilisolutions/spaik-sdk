from unittest.mock import MagicMock

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

from spaik_sdk import BaseAgent, LLMConfig
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.base_provider import BaseProvider

pytestmark = pytest.mark.unit


class Answer(BaseModel):
    city: str


class StructuredModel(FakeListChatModel):
    def with_structured_output(self, schema, **kwargs):
        raw = AIMessage(content='{"city":"Helsinki"}', id="raw")
        return RunnableLambda(lambda prompt: {"parsed": Answer(city="Helsinki"), "raw": raw, "parsing_error": None})


@pytest.mark.parametrize("effort,expected", [(None, {"type": "between_tools"}), ("high", {"type": "adaptive", "display": "summarized"})])
async def test_structured_response_effort_reaches_the_model(effort, expected):
    provider = MagicMock(spec=BaseProvider)
    provider.get_model_config.return_value = {}
    provider.create_langchain_model.return_value = StructuredModel(responses=["unused"])
    agent = BaseAgent(system_prompt="test", llm_config=LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5_5, provider=provider))
    result = await agent.get_structured_response_async("Capital of Finland?", Answer, reasoning_effort=effort)
    assert result.city == "Helsinki"
    kwargs = provider.create_langchain_model.call_args.args[1]
    assert kwargs["thinking"] == expected
    assert kwargs.get("output_config", {}).get("effort") == effort
