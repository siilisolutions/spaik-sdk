from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_mistralai import ChatMistralAI

from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.mistral_factory import MistralModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class MistralProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return MistralModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        return {
            "api_key": credentials_provider.get_provider_key("mistral"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatMistralAI(**full_config)
