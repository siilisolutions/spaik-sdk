from typing import Any, Collection, Dict

from langchain_cohere import ChatCohere
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.cohere_factory import CohereModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class CohereProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return CohereModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        return {
            "cohere_api_key": credentials_provider.get_provider_key("cohere"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatCohere(**full_config)
