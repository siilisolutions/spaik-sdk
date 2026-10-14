"""Optional convenience presets. Model construction never requires registry membership;
a string ID that matches a preset picks up its settings."""

import re

from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel


class ModelRegistry:
    CLAUDE_FABLE_5_1 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-fable-5-1", prompt_caching=True)
    CLAUDE_OPUS_5_5 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-opus-5-5", prompt_caching=True)
    CLAUDE_SONNET_5_5 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-sonnet-5-5", prompt_caching=True)
    CLAUDE_HAIKU_5_5 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-haiku-5-5", prompt_caching=True)
    GPT_6_ASTRA = LLMModel(family=LLMFamilies.OPENAI, name="gpt-6-astra", reasoning_min_effort="low", prompt_caching=True)
    GPT_6_1_SOL = LLMModel(family=LLMFamilies.OPENAI, name="gpt-6.1-sol", reasoning_min_effort="low", prompt_caching=True)
    GPT_6_LUNA = LLMModel(family=LLMFamilies.OPENAI, name="gpt-6-luna", prompt_caching=True)
    GEMINI_3_8_FLASH = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-3.8-flash", prompt_caching=True)
    GPT_4_1 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4.1", reasoning=False, prompt_caching=True)
    GPT_4O = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4o", reasoning=False, prompt_caching=True)
    GPT_5_6_SOL = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.6-sol", reasoning=True, prompt_caching=True)
    GPT_5_6_TERRA = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.6-terra", reasoning=True, prompt_caching=True)
    GPT_5_6_LUNA = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.6-luna", reasoning=True, prompt_caching=True)
    GEMINI_3_5_FLASH_LITE = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-3.5-flash-lite", prompt_caching=True)
    DEEPSEEK_V3_2 = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-V3.2")
    MISTRAL_LARGE_3 = LLMModel(family=LLMFamilies.MISTRAL, name="Mistral-Large-3", reasoning=False)
    LLAMA_4_MAVERICK = LLMModel(family=LLMFamilies.META, name="Llama-4-Maverick-17B-128E-Instruct-FP8", reasoning=False)
    COHERE_COMMAND_A = LLMModel(family=LLMFamilies.COHERE, name="Cohere-command-a", reasoning=False)
    GROK_4 = LLMModel(family=LLMFamilies.XAI, name="grok-4")
    KIMI_K2_THINKING = LLMModel(family=LLMFamilies.MOONSHOT, name="Kimi-K2-Thinking")

    @classmethod
    def get_all(cls) -> set[LLMModel]:
        return {value for value in vars(cls).values() if isinstance(value, LLMModel)}

    @classmethod
    def get_by_family(cls, family: str) -> set[LLMModel]:
        return {model for model in cls.get_all() if model.family == family}

    @classmethod
    def by_id(cls, model_id: str) -> LLMModel | None:
        return next((model for model in cls.get_all() if model.name == model_id), None)

    @classmethod
    def from_name(cls, name: str) -> LLMModel:
        aliases = {
            "sonnet": cls.CLAUDE_SONNET_5_5,
            "claude": cls.CLAUDE_SONNET_5_5,
            "opus": cls.CLAUDE_OPUS_5_5,
            "haiku": cls.CLAUDE_HAIKU_5_5,
            "fable": cls.CLAUDE_FABLE_5_1,
            "gpt": cls.GPT_6_1_SOL,
            "gemini flash": cls.GEMINI_3_8_FLASH,
        }
        normalized = re.sub(r"[^a-z0-9]", "", name.lower())
        choices = {
            **{key: value for key, value in vars(cls).items() if isinstance(value, LLMModel)},
            **{model.name: model for model in cls.get_all()},
            **aliases,
        }
        for key, value in choices.items():
            if re.sub(r"[^a-z0-9]", "", key.lower()) == normalized:
                return value
        raise ValueError(f"No preset named {name!r}; pass the model ID with an explicit provider")
