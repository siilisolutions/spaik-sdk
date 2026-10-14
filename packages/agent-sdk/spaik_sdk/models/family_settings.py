"""Per-family model settings, applied to any LLMModel whatever provider hosts it."""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel

if TYPE_CHECKING:
    from spaik_sdk.models.llm_config import LLMConfig

ADAPTIVE_THINKING = re.compile(r"^claude-(opus|fable|sonnet|haiku)-([5-9]|\d{2,})")
REQUIRES_THINKING = {"claude-opus-5-5", "claude-fable-5-1"}
BETWEEN_TOOLS_MINIMUM = {"claude-sonnet-5-5"}


def _anthropic(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    kwargs: dict[str, Any] = {"max_tokens": config.max_output_tokens or 8192}
    if not model.reasoning:
        return kwargs
    thinking = config.reasoning and not config.structured_response
    if ADAPTIVE_THINKING.match(model.name):
        if not thinking and model.name in REQUIRES_THINKING:
            if not config.reasoning:
                raise ValueError(f"{model.name} requires adaptive thinking")
            thinking = True
        minimum = "between_tools" if model.name in BETWEEN_TOOLS_MINIMUM else "disabled"
        kwargs["thinking"] = {"type": "adaptive" if thinking else minimum}
        if thinking:
            kwargs["model_kwargs"] = {"output_config": {"effort": config.reasoning_effort}}
    elif thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": config.reasoning_budget_tokens}
    return kwargs


def _openai(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    if not model.reasoning:
        return {}
    effort = config.reasoning_effort if config.reasoning else model.reasoning_min_effort
    return {"use_responses_api": True, "reasoning": {"effort": effort, "summary": config.reasoning_summary}}


def _google(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    if not model.reasoning:
        return {}
    if model.name.startswith("gemini-3"):
        minimum = model.reasoning_min_effort if model.reasoning_min_effort != "none" else "minimal"
        return {"thinking_level": "high" if config.reasoning else minimum}
    return {"thinking_budget": config.reasoning_budget_tokens if config.reasoning else 0, "include_thoughts": config.reasoning}


def _ollama(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    return {"reasoning": config.reasoning} if model.reasoning else {}


FAMILY_SETTINGS: dict[str, Callable[[LLMModel, "LLMConfig"], dict[str, Any]]] = {
    LLMFamilies.ANTHROPIC: _anthropic,
    LLMFamilies.OPENAI: _openai,
    LLMFamilies.GOOGLE: _google,
    LLMFamilies.OLLAMA: _ollama,
}


def family_kwargs(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    settings = FAMILY_SETTINGS.get(model.family)
    return settings(model, config) if settings else {}
