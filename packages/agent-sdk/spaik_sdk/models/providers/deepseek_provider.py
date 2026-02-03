from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek

from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.deepseek_factory import DeepSeekModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class DeepSeekProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return DeepSeekModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        return {
            "api_key": credentials_provider.get_provider_key("deepseek"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatDeepSeek(**full_config)
