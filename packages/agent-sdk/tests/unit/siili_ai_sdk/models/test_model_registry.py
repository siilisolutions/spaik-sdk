import pytest

from siili_ai_sdk.models.llm_families import LLMFamilies
from siili_ai_sdk.models.model_registry import ModelRegistry


@pytest.mark.unit
class TestModelRegistry:
    @pytest.mark.parametrize(
        "alias,expected_model_name",
        [
            ("opus 4.5", "claude-opus-4-5-20251101"),
            ("claude opus 4.5", "claude-opus-4-5-20251101"),
            ("claude 4.5 opus", "claude-opus-4-5-20251101"),
            ("gpt 5.1", "gpt-5.1"),
            ("gpt 5.1 codex", "gpt-5.1-codex"),
            ("gpt 5.1 codex mini", "gpt-5.1-codex-mini"),
            ("gpt 5.1 codex max", "gpt-5.1-codex-max"),
            ("gpt 5.2", "gpt-5.2"),
            ("gpt 5.2 pro", "gpt-5.2-pro"),
            ("gemini 3 flash", "gemini-3-flash-preview"),
            ("gemini 3.0 flash", "gemini-3-flash-preview"),
            ("gemini 3 pro", "gemini-3-pro-preview"),
            ("gemini 3.0 pro", "gemini-3-pro-preview"),
        ],
    )
    def test_from_name_alias_lookup_new_models(self, alias: str, expected_model_name: str):
        model = ModelRegistry.from_name(alias)
        assert model.name == expected_model_name

    @pytest.mark.parametrize(
        "model_name",
        [
            "claude-opus-4-5-20251101",
            "gpt-5.1",
            "gpt-5.1-codex",
            "gpt-5.1-codex-mini",
            "gpt-5.1-codex-max",
            "gpt-5.2",
            "gpt-5.2-pro",
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
        ],
    )
    def test_from_name_exact_model_name(self, model_name: str):
        model = ModelRegistry.from_name(model_name)
        assert model.name == model_name

    def test_gpt_5_1_codex_variants_have_reasoning_enabled(self):
        assert ModelRegistry.GPT_5_1_CODEX.reasoning is True
        assert ModelRegistry.GPT_5_1_CODEX_MINI.reasoning is True
        assert ModelRegistry.GPT_5_1_CODEX_MAX.reasoning is True

    def test_gemini_3_models_use_google_family(self):
        assert ModelRegistry.GEMINI_3_FLASH.family == LLMFamilies.GOOGLE
        assert ModelRegistry.GEMINI_3_PRO.family == LLMFamilies.GOOGLE

    def test_claude_4_5_opus_uses_anthropic_family(self):
        assert ModelRegistry.CLAUDE_4_5_OPUS.family == LLMFamilies.ANTHROPIC

    def test_ambiguous_model_name_raises_error(self):
        with pytest.raises(ValueError, match="Ambiguous"):
            ModelRegistry.from_name("gpt-5.1-codex-m")

    def test_nonexistent_model_raises_error(self):
        with pytest.raises(ValueError, match="No LLMModel found"):
            ModelRegistry.from_name("nonexistent-model-xyz")

    def test_new_models_included_in_get_all(self):
        all_models = ModelRegistry.get_all()
        model_names = {m.name for m in all_models}
        assert "claude-opus-4-5-20251101" in model_names
        assert "gpt-5.1" in model_names
        assert "gpt-5.2" in model_names
        assert "gemini-3-flash-preview" in model_names
        assert "gemini-3-pro-preview" in model_names
