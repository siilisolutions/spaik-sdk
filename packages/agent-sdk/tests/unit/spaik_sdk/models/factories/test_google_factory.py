"""Unit tests for GoogleModelFactory reasoning configuration."""

import pytest

from spaik_sdk.models.factories.google_factory import GoogleModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.model_registry import ModelRegistry


@pytest.mark.unit
class TestGoogleModelFactoryReasoning:
    """Tests for GoogleModelFactory reasoning configuration."""

    @pytest.fixture
    def factory(self):
        return GoogleModelFactory()

    @pytest.fixture
    def gemini_model(self):
        return ModelRegistry.GEMINI_2_5_FLASH

    def test_reasoning_true_sets_thinking_budget(self, factory, gemini_model):
        """When config.reasoning is True, thinking_budget is set to configured value."""
        config = LLMConfig(
            model=gemini_model,
            reasoning=True,
            reasoning_budget_tokens=8192,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["thinking_budget"] == 8192

    def test_reasoning_true_sets_include_thoughts(self, factory, gemini_model):
        """When config.reasoning is True, include_thoughts is set to True."""
        config = LLMConfig(
            model=gemini_model,
            reasoning=True,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["include_thoughts"] is True

    def test_reasoning_false_sets_thinking_budget_to_zero(self, factory, gemini_model):
        """When config.reasoning is False, thinking_budget is explicitly set to 0."""
        config = LLMConfig(
            model=gemini_model,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["thinking_budget"] == 0

    def test_reasoning_false_sets_include_thoughts_to_false(self, factory, gemini_model):
        """When config.reasoning is False, include_thoughts is set to False."""
        config = LLMConfig(
            model=gemini_model,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["include_thoughts"] is False

    @pytest.mark.parametrize(
        "model",
        [
            ModelRegistry.GEMINI_2_5_FLASH,
            ModelRegistry.GEMINI_2_5_PRO,
            ModelRegistry.GEMINI_3_FLASH,
            ModelRegistry.GEMINI_3_PRO,
        ],
    )
    def test_reasoning_false_works_for_all_gemini_models(self, factory, model):
        """When reasoning is False, all Gemini models get thinking_budget=0."""
        config = LLMConfig(
            model=model,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["thinking_budget"] == 0
        assert model_config["include_thoughts"] is False

    @pytest.mark.parametrize(
        "model",
        [
            ModelRegistry.GEMINI_2_5_FLASH,
            ModelRegistry.GEMINI_2_5_PRO,
            ModelRegistry.GEMINI_3_FLASH,
            ModelRegistry.GEMINI_3_PRO,
        ],
    )
    def test_reasoning_true_works_for_all_gemini_models(self, factory, model):
        """When reasoning is True, all Gemini models get the configured budget."""
        budget = 4096
        config = LLMConfig(
            model=model,
            reasoning=True,
            reasoning_budget_tokens=budget,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["thinking_budget"] == budget
        assert model_config["include_thoughts"] is True

    def test_config_includes_model_name(self, factory, gemini_model):
        """Model config always includes the model name."""
        config_false = LLMConfig(model=gemini_model, reasoning=False)
        config_true = LLMConfig(model=gemini_model, reasoning=True)

        model_config_false = factory.get_model_specific_config(config_false)
        model_config_true = factory.get_model_specific_config(config_true)

        assert model_config_false["model"] == gemini_model.name
        assert model_config_true["model"] == gemini_model.name

    def test_config_includes_temperature(self, factory, gemini_model):
        """Model config always includes temperature."""
        config = LLMConfig(model=gemini_model, reasoning=False, temperature=0.7)

        model_config = factory.get_model_specific_config(config)

        assert model_config["temperature"] == 0.7

    def test_streaming_disabled_adds_disable_streaming_flag(self, factory, gemini_model):
        """When streaming is False, disable_streaming is set to True."""
        config = LLMConfig(model=gemini_model, streaming=False)

        model_config = factory.get_model_specific_config(config)

        assert model_config["disable_streaming"] is True

    def test_streaming_enabled_no_disable_streaming_flag(self, factory, gemini_model):
        """When streaming is True, disable_streaming is not in config."""
        config = LLMConfig(model=gemini_model, streaming=True)

        model_config = factory.get_model_specific_config(config)

        assert "disable_streaming" not in model_config
