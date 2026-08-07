from typing import Any, Dict, Optional

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry

ADAPTIVE_THINKING_MODELS: frozenset[str] = frozenset(
    {
        "claude-opus-4-8",
        "claude-fable-5",
        "claude-opus-5",
        "claude-sonnet-5",
    }
)

THINKING_CANNOT_DISABLE_MODELS: frozenset[str] = frozenset({"claude-fable-5"})


class AnthropicModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.ANTHROPIC)

    def supports_model(self, model: LLMModel) -> bool:
        return model in AnthropicModelFactory.MODELS

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        return {"type": "ephemeral"}

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {
            "model_name": config.model.name,
            "streaming": config.streaming,
            "max_tokens": config.max_output_tokens if config.max_output_tokens is not None else 8192,
        }

        if config.model.name in ADAPTIVE_THINKING_MODELS:
            if config.structured_response:
                return model_config
            if not config.reasoning:
                if config.model.name in THINKING_CANNOT_DISABLE_MODELS:
                    raise ValueError(f"Model {config.model.name} does not support disabling thinking")
                if config.model == ModelRegistry.CLAUDE_OPUS_5 and config.reasoning_effort in {"xhigh", "max"}:
                    raise ValueError(
                        f"Model {config.model.name} does not support disabling thinking with effort {config.reasoning_effort}"
                    )
                model_config["thinking"] = {"type": "disabled"}
            else:
                model_config["thinking"] = {"type": "adaptive"}
                model_config["output_config"] = {"effort": config.reasoning_effort}
            return model_config

        allow_reasoning = config.reasoning and config.model.reasoning and not config.structured_response
        if allow_reasoning:
            model_config["thinking"] = {"type": "enabled", "budget_tokens": config.reasoning_budget_tokens}
        elif config.model == ModelRegistry.CLAUDE_4_7_OPUS:
            model_config["top_p"] = 0.99
        else:
            model_config["temperature"] = config.temperature

        return model_config
