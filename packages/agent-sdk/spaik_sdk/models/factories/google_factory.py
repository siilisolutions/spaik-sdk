from typing import Any, Dict, Optional

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry


class GoogleModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.GOOGLE)

    def supports_model(self, model: LLMModel) -> bool:
        return model in GoogleModelFactory.MODELS

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        return {"type": "permanent"}

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {"model": config.model.name, "temperature": config.temperature}

        if config.reasoning:
            model_config["thinking_budget"] = config.reasoning_budget_tokens
            model_config["include_thoughts"] = True
        else:
            # Gemini models have thinking enabled by default, so we must explicitly
            # set thinking_budget=0 to disable it (omitting the parameter doesn't work)
            model_config["thinking_budget"] = 0
            model_config["include_thoughts"] = False

        # Handle streaming - Google models use disable_streaming instead of streaming
        if not config.streaming:
            model_config["disable_streaming"] = True

        return model_config
