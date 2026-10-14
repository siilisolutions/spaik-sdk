"""Translate an LLMModel's reasoning fields into its family's current request shape.

Facts about individual models belong on their ModelRegistry presets, and this module never
checks model names. Models from older API generations take their settings via provider_kwargs.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel

if TYPE_CHECKING:
    from spaik_sdk.models.llm_config import LLMConfig

ANTHROPIC_THINKING_MODES = {"none": "disabled", "between_tools": "between_tools"}


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
    if effort is None and model.reasoning_min_effort in ANTHROPIC_THINKING_MODES:
        kwargs["thinking"] = {"type": ANTHROPIC_THINKING_MODES[model.reasoning_min_effort]}
        return kwargs
    kwargs["thinking"] = {"type": "adaptive", **({"display": "summarized"} if config.reasoning_summary else {})}
    kwargs["model_kwargs"] = {"output_config": {"effort": effort or model.reasoning_min_effort}}
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
    if effort is None:
        return {"thinking_level": model.reasoning_min_effort if model.reasoning_min_effort != "none" else "minimal"}
    return {"thinking_level": effort if config.structured_response else "high"}


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
