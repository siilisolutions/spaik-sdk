from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore

from siili_ai_sdk.config.get_credentials_provider import credentials_provider
from siili_ai_sdk.models.factories.google_factory import GoogleModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.providers.base_provider import BaseProvider


class GoogleProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by Google provider."""
        return GoogleModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Get Google provider configuration (provider-specific only)."""
        return {
            "google_api_key": credentials_provider.get_provider_key("google"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        """Create Google langchain model with complete configuration."""
        return ChatGoogleGenerativeAI(**full_config)
