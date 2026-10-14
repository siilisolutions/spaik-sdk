import pytest

from spaik_sdk.models.family_settings import family_kwargs
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel

pytestmark = pytest.mark.unit


def kwargs_for(model: LLMModel, **config) -> dict:
    return family_kwargs(model, LLMConfig(model=model, **config))


def test_gemini_3_without_reasoning_uses_minimal_thinking():
    assert kwargs_for(LLMModel(family="google", name="gemini-3.8-flash"), reasoning=False) == {"thinking_level": "minimal"}


def test_gemini_3_minimum_follows_model_setting():
    pro = LLMModel(family="google", name="gemini-3.9-pro", reasoning_min_effort="low")
    assert kwargs_for(pro, reasoning=False) == {"thinking_level": "low"}
    assert kwargs_for(pro) == {"thinking_level": "high"}


def test_older_gemini_uses_thinking_budget():
    assert kwargs_for(LLMModel(family="google", name="gemini-2.5-flash"), reasoning=False) == {
        "thinking_budget": 0,
        "include_thoughts": False,
    }


def test_new_claude_generation_gets_adaptive_thinking():
    assert kwargs_for(LLMModel(family="anthropic", name="claude-opus-6-0"))["thinking"] == {"type": "adaptive"}


def test_older_claude_reasoning_uses_budget():
    result = kwargs_for(LLMModel(family="anthropic", name="claude-sonnet-4-5"), reasoning_budget_tokens=2048)
    assert result["thinking"] == {"type": "enabled", "budget_tokens": 2048}


def test_model_requiring_thinking_rejects_reasoning_off():
    with pytest.raises(ValueError, match="requires adaptive thinking"):
        kwargs_for(LLMModel(family="anthropic", name="claude-opus-5-5"), reasoning=False)


def test_openai_reasoning_off_uses_minimum_effort():
    result = kwargs_for(LLMModel(family="openai", name="gpt-6-astra", reasoning_min_effort="low"), reasoning=False)
    assert result["reasoning"]["effort"] == "low"


def test_ollama_reasoning_flag_is_passed():
    assert kwargs_for(LLMModel(family="ollama", name="deepseek-r1"), reasoning=False) == {"reasoning": False}
    assert kwargs_for(LLMModel(family="ollama", name="llama3", reasoning=False)) == {}


def test_unknown_family_has_no_settings():
    assert kwargs_for(LLMModel(family="cohere", name="command-a")) == {}
