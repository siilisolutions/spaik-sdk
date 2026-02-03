import re
from typing import Dict, Set

from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel


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
    GPT_4_1_MINI = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4.1-mini", reasoning=False, prompt_caching=True)
    GPT_4_1_NANO = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4.1-nano", reasoning=False, prompt_caching=True)
    GPT_4O = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4o", reasoning=False, prompt_caching=True)
    GPT_4O_MINI = LLMModel(family=LLMFamilies.OPENAI, name="gpt-4o-mini", reasoning=False, prompt_caching=True)
    O1 = LLMModel(family=LLMFamilies.OPENAI, name="o1")
    O1_MINI = LLMModel(family=LLMFamilies.OPENAI, name="o1-mini")
    O3 = LLMModel(family=LLMFamilies.OPENAI, name="o3")
    O3_MINI = LLMModel(family=LLMFamilies.OPENAI, name="o3-mini")
    O3_PRO = LLMModel(family=LLMFamilies.OPENAI, name="o3-pro")
    O4_MINI = LLMModel(family=LLMFamilies.OPENAI, name="o4-mini")
    O4_MINI_APRIL_2025 = LLMModel(family=LLMFamilies.OPENAI, name="o4-mini-2025-04-16")
    CODEX_MINI = LLMModel(family=LLMFamilies.OPENAI, name="codex-mini")
    GPT_5 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5", reasoning=True, reasoning_min_effort="minimal", prompt_caching=True)
    GPT_5_MINI = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-mini", reasoning=True, reasoning_min_effort="minimal", prompt_caching=True)
    GPT_5_NANO = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-nano", reasoning=True, reasoning_min_effort="minimal", prompt_caching=True)
    GPT_5_CHAT = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-chat", reasoning=False, prompt_caching=True)
    GPT_5_CODEX = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-codex", reasoning=True, prompt_caching=True)
    GPT_5_PRO = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5-pro", reasoning=True, prompt_caching=True)
    GPT_5_1 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1", reasoning=True, prompt_caching=True)
    GPT_5_1_CHAT = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-chat", reasoning=True, prompt_caching=True)
    GPT_5_1_CODEX = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-codex", reasoning=True, prompt_caching=True)
    GPT_5_1_CODEX_MINI = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-codex-mini", reasoning=True, prompt_caching=True)
    GPT_5_1_CODEX_MAX = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.1-codex-max", reasoning=True, prompt_caching=True)
    GPT_5_2 = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.2", reasoning=True, prompt_caching=True)
    GPT_5_2_CHAT = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.2-chat", reasoning=False, prompt_caching=True)
    GPT_5_2_CODEX = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.2-codex", reasoning=True, prompt_caching=True)
    GPT_5_2_PRO = LLMModel(family=LLMFamilies.OPENAI, name="gpt-5.2-pro", reasoning=True, prompt_caching=True)

    # Google models
    GEMINI_2_5_FLASH = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-flash", prompt_caching=True)
    GEMINI_2_5_PRO = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-pro", prompt_caching=True)
    GEMINI_2_5_FLASH_MAY_2025 = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-flash", prompt_caching=True)
    GEMINI_2_5_PRO_MAY_2025 = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-2.5-pro", prompt_caching=True)
    GEMINI_3_FLASH = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-3-flash-preview", prompt_caching=True)
    GEMINI_3_PRO = LLMModel(family=LLMFamilies.GOOGLE, name="gemini-3-pro-preview", prompt_caching=True)

    # DeepSeek models
    DEEPSEEK_V3 = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-V3-0324")
    DEEPSEEK_V3_1 = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-V3.1")
    DEEPSEEK_V3_2 = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-V3.2")
    DEEPSEEK_V3_2_SPECIALE = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-V3.2-Speciale")
    DEEPSEEK_R1 = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-R1")
    DEEPSEEK_R1_0528 = LLMModel(family=LLMFamilies.DEEPSEEK, name="DeepSeek-R1-0528")

    # Mistral models
    MISTRAL_LARGE_3 = LLMModel(family=LLMFamilies.MISTRAL, name="Mistral-Large-3", reasoning=False)

    # Meta Llama models
    LLAMA_4_MAVERICK = LLMModel(family=LLMFamilies.META, name="Llama-4-Maverick-17B-128E-Instruct-FP8", reasoning=False)
    LLAMA_3_3_70B = LLMModel(family=LLMFamilies.META, name="Llama-3.3-70B-Instruct", reasoning=False)

    # Cohere models
    COHERE_COMMAND_A = LLMModel(family=LLMFamilies.COHERE, name="Cohere-command-a", reasoning=False)

    # xAI Grok models
    GROK_3 = LLMModel(family=LLMFamilies.XAI, name="grok-3")
    GROK_3_MINI = LLMModel(family=LLMFamilies.XAI, name="grok-3-mini")
    GROK_4 = LLMModel(family=LLMFamilies.XAI, name="grok-4")
    GROK_4_FAST_REASONING = LLMModel(family=LLMFamilies.XAI, name="grok-4-fast-reasoning")
    GROK_4_FAST_NON_REASONING = LLMModel(family=LLMFamilies.XAI, name="grok-4-fast-non-reasoning", reasoning=False)
    GROK_CODE_FAST_1 = LLMModel(family=LLMFamilies.XAI, name="grok-code-fast-1")

    # Moonshot AI models
    KIMI_K2_THINKING = LLMModel(family=LLMFamilies.MOONSHOT, name="Kimi-K2-Thinking")

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
            # Claude aliases
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
            # OpenAI aliases
            "o1": cls.O1,
            "o1 mini": cls.O1_MINI,
            "o3": cls.O3,
            "o3 mini": cls.O3_MINI,
            "o3 pro": cls.O3_PRO,
            "o4 mini": cls.O4_MINI,
            "o4 mini 2025-04-16": cls.O4_MINI_APRIL_2025,
            "codex mini": cls.CODEX_MINI,
            "gpt 4.1": cls.GPT_4_1,
            "gpt 4.1 mini": cls.GPT_4_1_MINI,
            "gpt 4.1 nano": cls.GPT_4_1_NANO,
            "gpt 4o": cls.GPT_4O,
            "gpt 4o mini": cls.GPT_4O_MINI,
            "gpt 5": cls.GPT_5,
            "gpt 5 mini": cls.GPT_5_MINI,
            "gpt 5 nano": cls.GPT_5_NANO,
            "gpt 5 chat": cls.GPT_5_CHAT,
            "gpt 5 codex": cls.GPT_5_CODEX,
            "gpt 5 pro": cls.GPT_5_PRO,
            "gpt 5.1": cls.GPT_5_1,
            "gpt 5.1 chat": cls.GPT_5_1_CHAT,
            "gpt 5.1 codex": cls.GPT_5_1_CODEX,
            "gpt 5.1 codex mini": cls.GPT_5_1_CODEX_MINI,
            "gpt 5.1 codex max": cls.GPT_5_1_CODEX_MAX,
            "gpt 5.2": cls.GPT_5_2,
            "gpt 5.2 chat": cls.GPT_5_2_CHAT,
            "gpt 5.2 codex": cls.GPT_5_2_CODEX,
            "gpt 5.2 pro": cls.GPT_5_2_PRO,
            # Gemini aliases
            "gemini 2.5 flash": cls.GEMINI_2_5_FLASH,
            "gemini 2.5 pro": cls.GEMINI_2_5_PRO,
            "gemini 3 flash": cls.GEMINI_3_FLASH,
            "gemini 3.0 flash": cls.GEMINI_3_FLASH,
            "gemini 3 pro": cls.GEMINI_3_PRO,
            "gemini 3.0 pro": cls.GEMINI_3_PRO,
            # DeepSeek aliases
            "deepseek": cls.DEEPSEEK_V3_2,
            "deepseek v3": cls.DEEPSEEK_V3,
            "deepseek v3.1": cls.DEEPSEEK_V3_1,
            "deepseek v3.2": cls.DEEPSEEK_V3_2,
            "deepseek v3.2 speciale": cls.DEEPSEEK_V3_2_SPECIALE,
            "deepseek r1": cls.DEEPSEEK_R1,
            # Mistral aliases
            "mistral": cls.MISTRAL_LARGE_3,
            "mistral large": cls.MISTRAL_LARGE_3,
            "mistral large 3": cls.MISTRAL_LARGE_3,
            # Meta Llama aliases
            "llama": cls.LLAMA_3_3_70B,
            "llama 3.3": cls.LLAMA_3_3_70B,
            "llama 3.3 70b": cls.LLAMA_3_3_70B,
            "llama 4": cls.LLAMA_4_MAVERICK,
            "llama 4 maverick": cls.LLAMA_4_MAVERICK,
            # Cohere aliases
            "cohere": cls.COHERE_COMMAND_A,
            "cohere command": cls.COHERE_COMMAND_A,
            "command a": cls.COHERE_COMMAND_A,
            # xAI Grok aliases
            "grok": cls.GROK_4,
            "grok 3": cls.GROK_3,
            "grok 3 mini": cls.GROK_3_MINI,
            "grok 4": cls.GROK_4,
            "grok 4 fast": cls.GROK_4_FAST_REASONING,
            "grok code": cls.GROK_CODE_FAST_1,
            # Moonshot aliases
            "kimi": cls.KIMI_K2_THINKING,
            "kimi k2": cls.KIMI_K2_THINKING,
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
