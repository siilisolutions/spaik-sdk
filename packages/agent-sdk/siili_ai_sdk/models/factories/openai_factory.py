from typing import Any, Dict, Optional

from siili_ai_sdk.models.factories.base_model_factory import BaseModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_families import LLMFamilies
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.utils.init_logger import init_logger

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
        # Add parallel tool calls if tool usage is enabled
        if config.tool_usage:
            model_config["model_kwargs"] = {"parallel_tool_calls": True}

        # Add model-specific configurations for reasoning models
        if config.model.reasoning:
            # Enable Responses API for reasoning models
            model_config["use_responses_api"] = True

            # Configure reasoning through model_kwargs as per LangChain docs
            if config.reasoning_summary:
                model_config["model_kwargs"] = {"reasoning": {"effort": config.reasoning_effort, "summary": config.reasoning_summary}}
        else:
            model_config["temperature"] = config.temperature

        return model_config
