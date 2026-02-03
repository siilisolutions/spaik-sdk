from typing import Any, Dict, Optional

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry


class MistralModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.MISTRAL)

    def supports_model(self, model: LLMModel) -> bool:
        return model in MistralModelFactory.MODELS

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        return None

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {
            "model": config.model.name,
            "temperature": config.temperature,
        }
        if config.max_output_tokens is not None:
            model_config["max_tokens"] = config.max_output_tokens
        return model_config
