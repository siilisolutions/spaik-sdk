from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI

from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.models.factories.openai_factory import OpenAIModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.providers.base_provider import BaseProvider


class AzureProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by Azure provider."""
        return OpenAIModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Get Azure AI Foundry provider configuration (provider-specific only)."""
        return {
            "api_key": env_config.get_azure_keys()["api_key"],
            "api_version": env_config.get_azure_keys()["api_version"],
            "azure_endpoint": env_config.get_azure_keys()["endpoint"],
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        """Create Azure langchain model with complete configuration and model-specific deployments."""
        # Add Azure provider-specific deployment configuration
        full_config["deployment_name"] = env_config.get_azure_keys()[f"{config.model.name.lower()}_deployment"]

        return AzureChatOpenAI(**full_config)
