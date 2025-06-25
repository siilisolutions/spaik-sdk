from typing import Any, Dict, Optional

from siili_ai_sdk.models.factories.base_model_factory import BaseModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_families import LLMFamilies
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.model_registry import ModelRegistry


class AnthropicModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.ANTHROPIC)

    def supports_model(self, model: LLMModel) -> bool:
        return model in AnthropicModelFactory.MODELS

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        return {"type": "ephemeral"}

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        allow_reasoning = config.reasoning and not config.structured_response
        model_config: Dict[str, Any] = {
            "model_name": config.model.name,
            "streaming": config.streaming,
            "max_tokens": config.max_output_tokens,
        }

        # Handle thinking mode via model_kwargs for LangChain compatibility
        if allow_reasoning:
            model_config["thinking"] = {"type": "enabled", "budget_tokens": config.reasoning_budget_tokens}
        else:
            model_config["temperature"] = config.temperature

        return model_config
