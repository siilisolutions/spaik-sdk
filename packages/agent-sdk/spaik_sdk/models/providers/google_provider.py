from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.google_factory import GoogleModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class GoogleProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by Google provider."""
        return GoogleModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Get Google provider configuration (provider-specific only)."""
        if env_config.is_proxy_mode():
            return self._get_proxy_config("google_api_key", "base_url", "additional_headers")

        # Direct mode — API key or ADC fallback
        result: Dict[str, Any] = {}
        api_key = credentials_provider.get_provider_key("google")
        if api_key:
            result["google_api_key"] = api_key
        return result

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        """Create Google langchain model with complete configuration."""
        return ChatGoogleGenerativeAI(**full_config)
