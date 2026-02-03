from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_xai import ChatXAI

from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.xai_factory import XAIModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class XAIProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return XAIModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        return {
            "xai_api_key": credentials_provider.get_provider_key("xai"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatXAI(**full_config)
