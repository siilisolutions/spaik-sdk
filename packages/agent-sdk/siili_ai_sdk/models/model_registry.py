import re
from typing import Dict, Set

from siili_ai_sdk.models.llm_families import LLMFamilies
from siili_ai_sdk.models.llm_model import LLMModel


class ModelRegistry:
    """Registry containing all built-in models with extensibility support."""

    # Anthropic models
    CLAUDE_3_7_SONNET_FEB_2025 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-3-7-sonnet-20250219", prompt_caching=True)
    CLAUDE_3_7_SONNET = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-3-7-sonnet-latest", prompt_caching=True)
    CLAUDE_4_SONNET = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-sonnet-4-20250514", prompt_caching=True)
    CLAUDE_4_OPUS = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-opus-4-20250514", prompt_caching=True)
    CLAUDE_4_1_OPUS = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-opus-4-1-20250805", prompt_caching=True)
    CLAUDE_4_SONNET_MAY_2025 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-sonnet-4-20250514", prompt_caching=True)
    CLAUDE_4_OPUS_MAY_2025 = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-opus-4-20250514", prompt_caching=True)
    CLAUDE_4_5_SONNET = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-sonnet-4-5-20250929", prompt_caching=True)
    CLAUDE_4_5_HAIKU = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-haiku-4-5-20251001", prompt_caching=True)
    CLAUDE_4_5_OPUS = LLMModel(family=LLMFamilies.ANTHROPIC, name="claude-opus-4-5-20251101", prompt_caching=True)

    # OpenAI models
    GPT_4_1 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4.1", reasoning=False, prompt_caching=True)
    GPT_4O = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4o", reasoning=False, prompt_caching=True)
    O4_MINI = LLMModel(family=LLMFamilies.OPENAI, name="o4-mini")
    O4_MINI_APRIL_2025 = LLMModel(family=LLMFamilies.OPENAI, name="o4-mini-2025-04-16")
    GPT_5 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5", reasoning=True, prompt_caching=True)
    GPT_5_MINI = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-mini", reasoning=True, prompt_caching=True)
    GPT_5_NANO = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-nano", reasoning=True, prompt_caching=True)
    GPT_5_1 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1", reasoning=True, prompt_caching=True)
    GPT_5_1_CODEX = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-codex", reasoning=True, prompt_caching=True)
    GPT_5_1_CODEX_MINI = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-codex-mini", reasoning=True, prompt_caching=True)
    GPT_5_1_CODEX_MAX = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-codex-max", reasoning=True, prompt_caching=True)
    GPT_5_2 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.2", reasoning=True, prompt_caching=True)
    GPT_5_2_PRO = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.2-pro", reasoning=True, prompt_caching=True)

    # Google models
    GEMINI_2_5_FLASH = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-flash", prompt_caching=True)
    GEMINI_2_5_PRO = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-pro", prompt_caching=True)
    GEMINI_2_5_FLASH_MAY_2025 = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-flash", prompt_caching=True)
    GEMINI_2_5_PRO_MAY_2025 = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-pro", prompt_caching=True)
    GEMINI_3_FLASH = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-3-flash-preview", prompt_caching=True)
    GEMINI_3_PRO = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-3-pro-preview", prompt_caching=True)

    # Registry for custom models
    _custom_models: Set[LLMModel] = set()

    @classmethod
    def register_custom(cls, model: LLMModel) -> LLMModel:
        """Register a custom model."""
        cls._custom_models.add(model)
        return model

    @classmethod
    def get_all_built_in(cls) -> Set[LLMModel]:
        """Get all built-in models."""
        built_ins = set()
        for attr_name in dir(cls):
            if not attr_name.startswith("_") and not callable(getattr(cls, attr_name)):
                attr = getattr(cls, attr_name)
                if isinstance(attr, LLMModel):
                    built_ins.add(attr)
        return built_ins

    @classmethod
    def get_all(cls) -> Set[LLMModel]:
        """Get all models (built-in + custom)."""
        return cls.get_all_built_in().union(cls._custom_models)

    @classmethod
    def get_by_family(cls, family: str) -> Set[LLMModel]:
        """Get all models for a specific family."""
        return {model for model in cls.get_all() if model.family == family}

    @classmethod
    def from_name(cls, name: str) -> LLMModel:
        """Find model by name with alias support."""
        return _find_model_by_name(name, cls._get_aliases())

    @classmethod
    def _get_aliases(cls) -> Dict[str, LLMModel]:
        """Get aliases mapping."""
        return {
            "sonnet": cls.CLAUDE_4_SONNET,
            "sonnet 3.7": cls.CLAUDE_3_7_SONNET,
            "sonnet 4.5": cls.CLAUDE_4_5_SONNET,
            "haiku": cls.CLAUDE_4_5_HAIKU,
            "haiku 4.5": cls.CLAUDE_4_5_HAIKU,
            "opus": cls.CLAUDE_4_5_OPUS,
            "opus 4.1": cls.CLAUDE_4_1_OPUS,
            "opus 4.5": cls.CLAUDE_4_5_OPUS,
            "claude 4.1 opus": cls.CLAUDE_4_1_OPUS,
            "claude opus 4.1": cls.CLAUDE_4_1_OPUS,
            "claude 4.5 opus": cls.CLAUDE_4_5_OPUS,
            "claude opus 4.5": cls.CLAUDE_4_5_OPUS,
            "claude": cls.CLAUDE_4_SONNET,
            "claude 3.7 sonnet": cls.CLAUDE_3_7_SONNET,
            "claude 4 sonnet": cls.CLAUDE_4_SONNET,
            "claude 4.5 sonnet": cls.CLAUDE_4_5_SONNET,
            "claude 4.5 haiku": cls.CLAUDE_4_5_HAIKU,
            "claude 4 opus": cls.CLAUDE_4_OPUS,
            "o4 mini": cls.O4_MINI,
            "o4 mini 2025-04-16": cls.O4_MINI_APRIL_2025,
            "gpt 4.1": cls.GPT_4_1,
            "gpt 4o": cls.GPT_4O,
            "gpt 5": cls.GPT_5,
            "gpt 5 mini": cls.GPT_5_MINI,
            "gpt 5 nano": cls.GPT_5_NANO,
            "gpt 5.1": cls.GPT_5_1,
            "gpt 5.1 codex": cls.GPT_5_1_CODEX,
            "gpt 5.1 codex mini": cls.GPT_5_1_CODEX_MINI,
            "gpt 5.1 codex max": cls.GPT_5_1_CODEX_MAX,
            "gpt 5.2": cls.GPT_5_2,
            "gpt 5.2 pro": cls.GPT_5_2_PRO,
            "gemini 2.5 flash": cls.GEMINI_2_5_FLASH,
            "gemini 2.5 pro": cls.GEMINI_2_5_PRO,
            "gemini 3 flash": cls.GEMINI_3_FLASH,
            "gemini 3.0 flash": cls.GEMINI_3_FLASH,
            "gemini 3 pro": cls.GEMINI_3_PRO,
            "gemini 3.0 pro": cls.GEMINI_3_PRO,
        }


def _normalize_name(name: str) -> str:
    """Normalize name by keeping only alphanumeric characters and converting to lowercase."""
    return re.sub(r"[^a-zA-Z0-9]", "", name.lower())


def _find_model_by_name(name: str, aliases: Dict[str, LLMModel]) -> LLMModel:
    """Find model by name with alias support."""
    # Check for exact match in aliases first (case-insensitive, ignoring non-alphanumeric)
    normalized_name = _normalize_name(name)
    for alias_key, alias_value in aliases.items():
        if _normalize_name(alias_key) == normalized_name:
            return alias_value

    # Check for exact match in all models
    all_models = ModelRegistry.get_all()
    for model in all_models:
        if model.name == name:
            return model

    # Check for starts-with matches in all models
    matches = []
    for model in all_models:
        if model.name.startswith(name):
            matches.append(model)

    if len(matches) == 0:
        raise ValueError(f"No LLMModel found starting with '{name}'")
    elif len(matches) == 1:
        return matches[0]
    else:
        match_names = [m.name for m in matches]
        raise ValueError(f"Ambiguous LLMModel name '{name}'. Could match: {', '.join(match_names)}")
