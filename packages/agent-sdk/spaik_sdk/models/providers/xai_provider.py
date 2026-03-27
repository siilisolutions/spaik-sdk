from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_xai import ChatXAI

from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.xai_factory import XAIModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class XAIProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return XAIModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        if env_config.is_proxy_mode():
            return self._get_proxy_config("xai_api_key", "xai_api_base", "default_headers")

        result: Dict[str, Any] = {}
        api_key = credentials_provider.get_provider_key("xai")
        if api_key:
            result["xai_api_key"] = api_key
        return result

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatXAI(**full_config)
