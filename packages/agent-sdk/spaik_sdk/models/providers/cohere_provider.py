from typing import Any, Dict

from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.providers.base_provider import BaseProvider


class CohereProvider(BaseProvider):
    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        if env_config.is_proxy_mode():
            return self._get_proxy_config("cohere_api_key", "base_url", "default_headers")

        result: Dict[str, Any] = {}
        api_key = credentials_provider.get_provider_key("cohere")
        if api_key:
            result["cohere_api_key"] = api_key
        return result

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        from langchain_cohere import ChatCohere

        return ChatCohere(**full_config)
