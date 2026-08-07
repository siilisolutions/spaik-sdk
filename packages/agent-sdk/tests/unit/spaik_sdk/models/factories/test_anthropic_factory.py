import pytest

from spaik_sdk.models.factories.anthropic_factory import AnthropicModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.model_registry import ModelRegistry


@pytest.mark.unit
class TestAnthropicModelFactory:
    def test_reasoning_model_sets_thinking_config(self):
        config = LLMConfig(model=ModelRegistry.CLAUDE_4_6_SONNET, reasoning=True, reasoning_budget_tokens=2048)

        model_config = AnthropicModelFactory().get_model_specific_config(config)

        assert model_config["thinking"] == {"type": "enabled", "budget_tokens": 2048}
        assert "temperature" not in model_config

    def test_claude_opus_4_7_uses_required_top_p_without_thinking_or_temperature(self):
        config = LLMConfig(model=ModelRegistry.CLAUDE_4_7_OPUS, reasoning=True, temperature=0.7)

        model_config = AnthropicModelFactory().get_model_specific_config(config)

        assert model_config["top_p"] == 0.99
        assert "thinking" not in model_config
        assert "temperature" not in model_config

    def test_adaptive_thinking_model_uses_adaptive_when_reasoning_enabled(self):
        config = LLMConfig(model=ModelRegistry.CLAUDE_OPUS_5, reasoning=True)

        model_config = AnthropicModelFactory().get_model_specific_config(config)

        assert model_config["thinking"] == {"type": "adaptive"}
        assert "temperature" not in model_config

    def test_adaptive_thinking_model_uses_disabled_when_reasoning_disabled(self):
        config = LLMConfig(model=ModelRegistry.CLAUDE_SONNET_5, reasoning=False)

        model_config = AnthropicModelFactory().get_model_specific_config(config)

        assert model_config["thinking"] == {"type": "disabled"}
        assert "temperature" not in model_config

    def test_fable_5_rejects_disabled_reasoning(self):
        config = LLMConfig(model=ModelRegistry.CLAUDE_FABLE_5, reasoning=False)

        with pytest.raises(ValueError, match="does not support disabling thinking"):
            AnthropicModelFactory().get_model_specific_config(config)
