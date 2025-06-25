import re
from enum import Enum
from typing import Dict, Type, TypeVar


class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    AZURE_AI_FOUNDRY = "azure_ai_foundry"
    OPENAI_DIRECT = "openai"
    GOOGLE = "google"

    @classmethod
    def from_name(cls, name: str) -> "ProviderType":
        return _find_enum_by_name(cls, name, PROVIDER_ALIASES)

    @classmethod
    def from_model_name(cls, model_name: str) -> "ProviderType":
        if model_name.startswith("claude"):
            return cls.ANTHROPIC
        elif model_name.startswith("gemini"):
            return cls.GOOGLE
        elif model_name.startswith("gpt") or model_name.startswith("o3") or model_name.startswith("o4"):
            return cls.OPENAI_DIRECT
        else:
            raise ValueError(f"Cant determine provider type from model name: {model_name}")


PROVIDER_ALIASES = {
    "claude": ProviderType.ANTHROPIC,
    "azure": ProviderType.AZURE_AI_FOUNDRY,
    "foundry": ProviderType.AZURE_AI_FOUNDRY,
    "openai": ProviderType.OPENAI_DIRECT,
    "google": ProviderType.GOOGLE,
    "gemini": ProviderType.GOOGLE,
}


T = TypeVar("T", bound=Enum)


def _normalize_name(name: str) -> str:
    """Normalize name by keeping only alphanumeric characters and converting to lowercase."""
    return re.sub(r"[^a-zA-Z0-9]", "", name.lower())


def _find_enum_by_name(enum_cls: Type[T], name: str, aliases: Dict[str, T]) -> T:
    """Shared logic for finding enum members by name with alias support."""
    # Check for exact match in aliases first (case-insensitive, ignoring non-alphanumeric)
    normalized_name = _normalize_name(name)
    for alias_key, alias_value in aliases.items():
        if _normalize_name(alias_key) == normalized_name:
            return alias_value

    # Check for exact match in enum values
    for item in enum_cls:
        if item.value == name:
            return item

    # Check for starts-with matches in enum values
    matches = []
    for item in enum_cls:
        if item.value.startswith(name):
            matches.append(item)

    if len(matches) == 0:
        raise ValueError(f"No {enum_cls.__name__} found starting with '{name}'")
    elif len(matches) == 1:
        return matches[0]
    else:
        match_names = [m.value for m in matches]
        raise ValueError(f"Ambiguous {enum_cls.__name__} name '{name}'. Could match: {', '.join(match_names)}")
