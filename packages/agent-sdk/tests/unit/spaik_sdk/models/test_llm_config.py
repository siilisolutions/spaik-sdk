from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.base_provider import BaseProvider

pytestmark = pytest.mark.unit

SETTINGS = ("thinking", "model_kwargs", "max_tokens", "temperature", "reasoning", "use_responses_api", "disable_streaming")


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")


def settings(config: LLMConfig) -> dict[str, Any]:
    model = config.get_model_wrapper().get_langchain_model()
    return {key: getattr(model, key, None) for key in SETTINGS}


def test_preset_custom_model_and_string_id_build_the_same_model():
    preset = settings(LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5_5))
    assert preset["thinking"] == {"type": "adaptive"}
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


def test_streaming_off_disables_streaming():
    assert settings(LLMConfig(model=ModelRegistry.GPT_4_1, streaming=False))["disable_streaming"] is True


def test_structured_response_uses_minimum_thinking_unless_model_requires_it():
    sonnet = LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5_5).as_structured_response_config()
    assert settings(sonnet)["thinking"] == {"type": "between_tools"}
    opus = LLMConfig(model=ModelRegistry.CLAUDE_OPUS_5_5).as_structured_response_config()
    assert settings(opus)["thinking"] == {"type": "adaptive"}


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
