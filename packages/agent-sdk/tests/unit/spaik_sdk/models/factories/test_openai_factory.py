"""Unit tests for OpenAIModelFactory reasoning configuration."""

import pytest

from spaik_sdk.models.factories.openai_factory import OpenAIModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.model_registry import ModelRegistry


@pytest.mark.unit
class TestOpenAIModelFactoryReasoning:
    """Tests for OpenAIModelFactory reasoning configuration."""

    @pytest.fixture
    def factory(self):
        return OpenAIModelFactory()

    # Test that factory checks config.reasoning (user preference), not config.model.reasoning (capability)

    def test_checks_user_reasoning_preference_not_model_capability(self, factory):
        """Factory checks config.reasoning (user preference), not config.model.reasoning (capability)."""
        # Use a reasoning-capable model (GPT-5.1) but set reasoning=False
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1,
            reasoning=False,  # User wants reasoning disabled
        )

        # The model supports reasoning (config.model.reasoning=True)
        assert config.model.reasoning is True

        model_config = factory.get_model_specific_config(config)

        # Should still use Responses API (model supports it)
        assert model_config["use_responses_api"] is True
        # But reasoning should be disabled per user preference
        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    # Tests for GPT-5.1+ models (support effort='none' for full disable)

    def test_reasoning_false_gpt_5_1_sets_effort_none(self, factory):
        """When reasoning=False on GPT-5.1 model, reasoning effort is 'none'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    def test_reasoning_false_gpt_5_1_codex_sets_effort_none(self, factory):
        """When reasoning=False on GPT-5.1-codex model, reasoning effort is 'none'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1_CODEX,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    def test_reasoning_false_gpt_5_1_codex_mini_sets_effort_none(self, factory):
        """When reasoning=False on GPT-5.1-codex-mini model, reasoning effort is 'none'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1_CODEX_MINI,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    def test_reasoning_false_gpt_5_1_codex_max_sets_effort_none(self, factory):
        """When reasoning=False on GPT-5.1-codex-max model, reasoning effort is 'none'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1_CODEX_MAX,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    def test_reasoning_false_gpt_5_2_sets_effort_none(self, factory):
        """When reasoning=False on GPT-5.2 model, reasoning effort is 'none'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_2,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    def test_reasoning_false_gpt_5_2_pro_sets_effort_none(self, factory):
        """When reasoning=False on GPT-5.2-pro model, reasoning effort is 'none'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_2_PRO,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "none"

    # Tests for GPT-5 base models (only support effort='minimal')

    def test_reasoning_false_gpt_5_sets_effort_minimal(self, factory):
        """When reasoning=False on GPT-5 model, reasoning effort is 'minimal'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "minimal"

    def test_reasoning_false_gpt_5_mini_sets_effort_minimal(self, factory):
        """When reasoning=False on GPT-5-mini model, reasoning effort is 'minimal'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_MINI,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "minimal"

    def test_reasoning_false_gpt_5_nano_sets_effort_minimal(self, factory):
        """When reasoning=False on GPT-5-nano model, reasoning effort is 'minimal'."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_NANO,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == "minimal"

    # Tests for reasoning=True (existing behavior preserved)

    def test_reasoning_true_preserves_existing_behavior(self, factory):
        """When reasoning=True, existing behavior is preserved (Responses API enabled, configurable effort)."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1,
            reasoning=True,
            reasoning_effort="high",
            reasoning_summary="detailed",
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["use_responses_api"] is True
        assert model_config["model_kwargs"]["reasoning"]["effort"] == "high"
        assert model_config["model_kwargs"]["reasoning"]["summary"] == "detailed"

    @pytest.mark.parametrize(
        "model",
        [
            ModelRegistry.GPT_5,
            ModelRegistry.GPT_5_MINI,
            ModelRegistry.GPT_5_NANO,
            ModelRegistry.GPT_5_1,
            ModelRegistry.GPT_5_1_CODEX,
            ModelRegistry.GPT_5_1_CODEX_MINI,
            ModelRegistry.GPT_5_1_CODEX_MAX,
            ModelRegistry.GPT_5_2,
            ModelRegistry.GPT_5_2_PRO,
        ],
    )
    def test_reasoning_true_enables_responses_api_for_all_reasoning_models(self, factory, model):
        """When reasoning=True on reasoning-capable models, Responses API is enabled."""
        config = LLMConfig(
            model=model,
            reasoning=True,
            reasoning_effort="medium",
            reasoning_summary="auto",
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["use_responses_api"] is True

    # Test for non-reasoning models

    def test_non_reasoning_model_uses_temperature(self, factory):
        """Non-reasoning models use temperature instead of reasoning config."""
        config = LLMConfig(
            model=ModelRegistry.GPT_4_1,  # Non-reasoning model
            reasoning=True,  # User preference doesn't matter for non-reasoning models
            temperature=0.7,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["temperature"] == 0.7
        assert "use_responses_api" not in model_config
        assert "reasoning" not in model_config.get("model_kwargs", {})


@pytest.mark.unit
class TestOpenAIModelFactoryParameterized:
    """Parametrized tests for comprehensive model coverage."""

    @pytest.fixture
    def factory(self):
        return OpenAIModelFactory()

    @pytest.mark.parametrize(
        "model,expected_effort",
        [
            # GPT-5.1+ models -> effort='none'
            (ModelRegistry.GPT_5_1, "none"),
            (ModelRegistry.GPT_5_1_CODEX, "none"),
            (ModelRegistry.GPT_5_1_CODEX_MINI, "none"),
            (ModelRegistry.GPT_5_1_CODEX_MAX, "none"),
            (ModelRegistry.GPT_5_2, "none"),
            (ModelRegistry.GPT_5_2_PRO, "none"),
            # GPT-5 base models -> effort='minimal'
            (ModelRegistry.GPT_5, "minimal"),
            (ModelRegistry.GPT_5_MINI, "minimal"),
            (ModelRegistry.GPT_5_NANO, "minimal"),
        ],
    )
    def test_reasoning_false_sets_correct_effort_for_model(self, factory, model, expected_effort):
        """When reasoning=False, the correct effort level is set based on model version."""
        config = LLMConfig(
            model=model,
            reasoning=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["reasoning"]["effort"] == expected_effort


@pytest.mark.unit
class TestOpenAIModelFactoryParallelToolCalls:
    """Tests for parallel_tool_calls handling (#44)."""

    @pytest.fixture
    def factory(self):
        return OpenAIModelFactory()

    def test_no_parallel_tool_calls_when_tool_usage_disabled(self, factory):
        """parallel_tool_calls must not appear when tool_usage is False."""
        config = LLMConfig(
            model=ModelRegistry.GPT_4_1,
            tool_usage=False,
        )

        model_config = factory.get_model_specific_config(config)

        assert "parallel_tool_calls" not in model_config.get("model_kwargs", {})

    def test_parallel_tool_calls_present_when_tool_usage_enabled(self, factory):
        """parallel_tool_calls should be set when tool_usage is True."""
        config = LLMConfig(
            model=ModelRegistry.GPT_4_1,
            tool_usage=True,
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["parallel_tool_calls"] is True

    def test_structured_response_config_disables_tool_usage(self):
        """as_structured_response_config should set tool_usage=False so parallel_tool_calls is not sent."""
        config = LLMConfig(
            model=ModelRegistry.GPT_4_1,
            tool_usage=True,
        )

        structured_config = config.as_structured_response_config()

        assert structured_config.structured_response is True
        assert structured_config.tool_usage is False

    def test_parallel_tool_calls_preserved_with_reasoning(self, factory):
        """parallel_tool_calls must not be overwritten when reasoning config is also set."""
        config = LLMConfig(
            model=ModelRegistry.GPT_5_1,
            tool_usage=True,
            reasoning=True,
            reasoning_effort="high",
            reasoning_summary="detailed",
        )

        model_config = factory.get_model_specific_config(config)

        assert model_config["model_kwargs"]["parallel_tool_calls"] is True
        assert model_config["model_kwargs"]["reasoning"]["effort"] == "high"
