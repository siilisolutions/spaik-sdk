from typing import Any, Dict, Optional

from siili_ai_sdk.models.factories.base_model_factory import BaseModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_families import LLMFamilies
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class OllamaModelFactory(BaseModelFactory):
    # Models are dynamically created by users with LLMModel(family="ollama", name="...")
    # So we start with an empty registry and let users add models as needed
    MODELS = ModelRegistry.get_by_family(LLMFamilies.OLLAMA)

    def supports_model(self, model: LLMModel) -> bool:
        return model.family == "ollama"

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        # Ollama doesn't support prompt caching in the same way as cloud providers
        return None

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {
            "model": config.model.name,
            "temperature": config.temperature,
        }

        # Enable streaming if requested
        if config.streaming:
            model_config["streaming"] = True

        # Handle reasoning configuration for models that support it (like deepseek-r1)
        # reasoning=True should separate <think> content to additional_kwargs['reasoning_content']
        # reasoning=None/False leaves <think> tags in main content
        if config.reasoning is not None:
            model_config["reasoning"] = config.reasoning

        return model_config
