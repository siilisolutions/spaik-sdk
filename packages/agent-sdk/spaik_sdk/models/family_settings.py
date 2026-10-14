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


def call_effort(config: "LLMConfig") -> str | None:
    """Reasoning effort for this call; None means the model's minimum.

    Structured responses default to the minimum unless structured_reasoning_effort is set.
    """
    if config.structured_response:
        return config.structured_reasoning_effort
    return config.reasoning_effort if config.reasoning else None


def _anthropic(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    kwargs: dict[str, Any] = {"max_tokens": config.max_output_tokens or 8192}
    if not model.reasoning:
        return kwargs
    effort = call_effort(config)
    if ADAPTIVE_THINKING.match(model.name):
        if effort is None and model.name in REQUIRES_THINKING:
            if not config.structured_response:
                raise ValueError(f"{model.name} requires adaptive thinking")
            effort = "low"
        if effort is None:
            kwargs["thinking"] = {"type": "between_tools" if model.name in BETWEEN_TOOLS_MINIMUM else "disabled"}
        else:
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["model_kwargs"] = {"output_config": {"effort": effort}}
    elif effort is not None:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": config.reasoning_budget_tokens}
    return kwargs


def _openai(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    if not model.reasoning:
        return {}
    effort = call_effort(config) or model.reasoning_min_effort
    return {"use_responses_api": True, "reasoning": {"effort": effort, "summary": config.reasoning_summary}}


def _google(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    if not model.reasoning:
        return {}
    effort = call_effort(config)
    if model.name.startswith("gemini-3"):
        if effort is None:
            level = model.reasoning_min_effort if model.reasoning_min_effort != "none" else "minimal"
        else:
            level = effort if config.structured_response else "high"
        return {"thinking_level": level}
    thinking = effort is not None
    return {"thinking_budget": config.reasoning_budget_tokens if thinking else 0, "include_thoughts": thinking}


def _ollama(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    return {"reasoning": call_effort(config) is not None} if model.reasoning else {}


FAMILY_SETTINGS: dict[str, Callable[[LLMModel, "LLMConfig"], dict[str, Any]]] = {
    LLMFamilies.ANTHROPIC: _anthropic,
    LLMFamilies.OPENAI: _openai,
    LLMFamilies.GOOGLE: _google,
    LLMFamilies.OLLAMA: _ollama,
}


def family_kwargs(model: LLMModel, config: "LLMConfig") -> dict[str, Any]:
    settings = FAMILY_SETTINGS.get(model.family)
    return settings(model, config) if settings else {}
