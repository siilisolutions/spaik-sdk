from typing import Any, Dict, Optional

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class OpenAIModelFactory(BaseModelFactory):
    MODELS = ModelRegistry.get_by_family(LLMFamilies.OPENAI)

    def supports_model(self, model: LLMModel) -> bool:
        return model in OpenAIModelFactory.MODELS

    def supports_model_config(self, config: LLMConfig) -> bool:
        # First check basic model support
        if not self.supports_model(config.model):
            return False
        if config.reasoning and not config.model.reasoning:
            # let's not fail here, but we should log a warning
            logger.warning(f"Model {config.model} does not support reasoning")
        return True

    def get_cache_control(self, config: LLMConfig) -> Optional[Dict[str, Any]]:
        if config.model.prompt_caching:
            return {"type": "permanent"}
        return None

    def get_model_specific_config(self, config: LLMConfig) -> Dict[str, Any]:
        model_config: Dict[str, Any] = {"model": config.model.name, "streaming": config.streaming}
        model_kwargs: Dict[str, Any] = {}

        if config.tool_usage:
            model_kwargs["parallel_tool_calls"] = True

        # Handle reasoning configuration based on user preference (config.reasoning)
        # and model capability (config.model.reasoning)
        if config.model.reasoning:
            # Model supports reasoning - check user preference
            model_config["use_responses_api"] = True

            if config.reasoning:
                # User wants reasoning enabled - use configured effort
                if config.reasoning_summary:
                    model_kwargs["reasoning"] = {"effort": config.reasoning_effort, "summary": config.reasoning_summary}
            else:
                # User wants reasoning disabled - use model's minimum effort level
                model_kwargs["reasoning"] = {"effort": config.model.reasoning_min_effort}
        else:
            # Model doesn't support reasoning
            model_config["temperature"] = config.temperature

        if model_kwargs:
            model_config["model_kwargs"] = model_kwargs

        return model_config
