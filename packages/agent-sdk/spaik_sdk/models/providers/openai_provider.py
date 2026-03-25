from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.openai_factory import OpenAIModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by OpenAI provider."""
        return OpenAIModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Get OpenAI provider configuration (provider-specific only)."""
        if env_config.is_proxy_mode():
            return self._get_proxy_config("api_key", "base_url", "default_headers")

        result: Dict[str, Any] = {}
        api_key = credentials_provider.get_provider_key("openai")
        if api_key:
            result["api_key"] = api_key
        return result

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        """Create OpenAI langchain model with complete configuration."""
        return ChatOpenAI(**full_config)
