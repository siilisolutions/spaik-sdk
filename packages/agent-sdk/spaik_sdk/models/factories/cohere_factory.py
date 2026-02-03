from typing import Any, Dict

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry


class CohereModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.COHERE)

    def supports_model(self, model: LLMModel) -> bool:
        return model in CohereModelFactory.MODELS

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {
            "model": config.model.name,
            "temperature": config.temperature,
        }
        return model_config
