from typing import Any, Dict, Optional

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry


class GoogleModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.GOOGLE)
    GEMINI_3_MODELS_WITHOUT_MINIMAL_THINKING = {
        ModelRegistry.GEMINI_3_PRO,
        ModelRegistry.GEMINI_3_1_PRO,
    }

    def supports_model(self, model: LLMModel) -> bool:
        return model in GoogleModelFactory.MODELS

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        return {"type": "permanent"}

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {"model": config.model.name, "temperature": config.temperature}

        if config.model.name.startswith("gemini-3"):
            if config.reasoning:
                model_config["thinking_level"] = "high"
            elif config.model in self.GEMINI_3_MODELS_WITHOUT_MINIMAL_THINKING:
                model_config["thinking_level"] = "low"
            else:
                model_config["thinking_level"] = "minimal"
        else:
            model_config["thinking_budget"] = config.reasoning_budget_tokens if config.reasoning else 0

        model_config["include_thoughts"] = config.reasoning

        # Handle streaming - Google models use disable_streaming instead of streaming
        if not config.streaming:
            model_config["disable_streaming"] = True

        return model_config
