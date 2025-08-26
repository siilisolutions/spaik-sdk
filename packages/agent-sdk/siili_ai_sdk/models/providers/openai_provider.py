from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from siili_ai_sdk.config.get_credentials_provider import credentials_provider
from siili_ai_sdk.models.factories.openai_factory import OpenAIModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by OpenAI provider."""
        return OpenAIModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Get OpenAI provider configuration (provider-specific only)."""
        return {
            "api_key": credentials_provider.get_provider_key("openai"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        """Create OpenAI langchain model with complete configuration."""
        return ChatOpenAI(**full_config)
