from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.base_provider import BaseProvider

pytestmark = pytest.mark.unit

SETTINGS = ("thinking", "output_config", "max_tokens", "temperature", "reasoning", "use_responses_api", "disable_streaming")


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")


def settings(config: LLMConfig) -> dict[str, Any]:
    model = config.get_model_wrapper().get_langchain_model()
    return {key: getattr(model, key, None) for key in SETTINGS}


def test_preset_custom_model_and_string_id_build_the_same_model():
    preset = settings(LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5_5))
    assert preset["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert preset["max_tokens"] == 8192
    assert settings(LLMConfig(model=LLMModel(family="anthropic", name="claude-sonnet-5-5"))) == preset
    assert settings(LLMConfig(model="claude-sonnet-5-5", provider_type="anthropic")) == preset


def test_string_matching_a_preset_infers_its_provider():
    assert LLMConfig(model="gpt-6.1-sol").provider_name == "openai"


def test_unknown_string_id_uses_provider_defaults():
    built = settings(LLMConfig(model="claude-next-experimental", provider_type="anthropic"))
    assert built["thinking"] is None
    assert built["temperature"] is None


def test_temperature_is_sent_only_when_set():
    assert settings(LLMConfig(model=ModelRegistry.GPT_4_1))["temperature"] is None
    assert settings(LLMConfig(model=ModelRegistry.GPT_4_1, temperature=0.9))["temperature"] == 0.9


def test_older_model_generation_is_configured_through_provider_kwargs():
    budget = {"type": "enabled", "budget_tokens": 2048}
    older = LLMModel(family="anthropic", name="claude-sonnet-4-5")
    built = settings(LLMConfig(model=older, provider_kwargs={"thinking": budget, "output_config": None}))
    assert built["thinking"] == budget
    assert built["output_config"] is None


def test_streaming_off_disables_streaming():
    assert settings(LLMConfig(model=ModelRegistry.GPT_4_1, streaming=False))["disable_streaming"] is True


def test_structured_response_defaults_to_minimum_reasoning():
    sonnet = LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5_5).as_structured_response_config()
    assert settings(sonnet)["thinking"] == {"type": "between_tools"}
    opus = settings(LLMConfig(model=ModelRegistry.CLAUDE_OPUS_5_5).as_structured_response_config())
    assert opus["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert opus["output_config"] == {"effort": "low"}
    gpt = settings(LLMConfig(model=ModelRegistry.GPT_6_1_SOL).as_structured_response_config())
    assert gpt["reasoning"]["effort"] == "low"


def test_structured_reasoning_effort_is_configurable():
    configured = LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5_5, structured_reasoning_effort="medium")
    built = settings(configured.as_structured_response_config())
    assert built["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert built["output_config"] == {"effort": "medium"}
    per_call = settings(configured.as_structured_response_config(reasoning_effort="high"))
    assert per_call["output_config"] == {"effort": "high"}
    gpt = LLMConfig(model=ModelRegistry.GPT_6_1_SOL).as_structured_response_config(reasoning_effort="high")
    assert settings(gpt)["reasoning"]["effort"] == "high"


def test_provider_kwargs_override_family_settings():
    config = LLMConfig(model=ModelRegistry.CLAUDE_HAIKU_5_5, provider_kwargs={"max_tokens": 100, "thinking": {"type": "disabled"}})
    built = settings(config)
    assert built["max_tokens"] == 100
    assert built["thinking"] == {"type": "disabled"}


def test_known_provider_never_uses_langchain_router():
    with patch("spaik_sdk.models.llm_config.init_chat_model") as router:
        LLMConfig(model="any-new-model", provider_type="openai").get_model_wrapper()
    router.assert_not_called()


def test_explicit_provider_builds_the_model():
    chat_model = MagicMock(spec=BaseChatModel)
    provider = MagicMock(spec=BaseProvider)
    provider.get_model_config.return_value = {"api_key": "from-provider"}
    provider.create_langchain_model.return_value = chat_model
    config = LLMConfig(model="deployment-name", provider=provider, provider_kwargs={"timeout": 5})
    assert config.get_model_wrapper().get_langchain_model() is chat_model
    provider.create_langchain_model.assert_called_once_with(config, {"api_key": "from-provider", "timeout": 5, "model": "deployment-name"})


def test_unknown_string_without_provider_is_rejected():
    with pytest.raises(ValueError, match="explicit provider_type"):
        LLMConfig(model="unknown-model").get_model_wrapper()
