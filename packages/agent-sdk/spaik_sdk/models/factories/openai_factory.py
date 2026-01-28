from typing import Any, Dict, Optional

from spaik_sdk.models.factories.base_model_factory import BaseModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


def _supports_full_reasoning_disable(model_name: str) -> bool:
    """Check if the model supports reasoning.effort = 'none' for full disable.

    GPT-5.1 and later models (including codex variants, 5.2) support effort='none'.
    GPT-5 base models (5, 5-mini, 5-nano) only support minimum effort='minimal'.
    """
    # GPT-5.1+ models support full disable with effort='none'
    # These include: gpt-5.1, gpt-5.1-codex, gpt-5.1-codex-mini, gpt-5.1-codex-max, gpt-5.2, gpt-5.2-pro
    if model_name.startswith("gpt-5.1") or model_name.startswith("gpt-5.2"):
        return True
    # GPT-5 base models (gpt-5, gpt-5-mini, gpt-5-nano) don't support full disable
    return False


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

        # Handle reasoning configuration based on user preference (config.reasoning)
        # and model capability (config.model.reasoning)
        if config.model.reasoning:
            # Model supports reasoning - check user preference
            model_config["use_responses_api"] = True

            if config.reasoning:
                # User wants reasoning enabled - use configured effort
                if config.reasoning_summary:
                    model_config["model_kwargs"] = {"reasoning": {"effort": config.reasoning_effort, "summary": config.reasoning_summary}}
            else:
                # User wants reasoning disabled - set appropriate effort level
                if _supports_full_reasoning_disable(config.model.name):
                    # GPT-5.1+ supports effort='none' for full disable
                    model_config["model_kwargs"] = {"reasoning": {"effort": "none"}}
                else:
                    # GPT-5 base models only support minimum effort='minimal'
                    model_config["model_kwargs"] = {"reasoning": {"effort": "minimal"}}
        else:
            # Model doesn't support reasoning
            model_config["temperature"] = config.temperature

        return model_config
