from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from siili_ai_sdk.config.get_credentials_provider import credentials_provider
from siili_ai_sdk.models.factories.ollama_factory import OllamaModelFactory
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.providers.base_provider import BaseProvider
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class OllamaProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return OllamaModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        provider_config = {}
        provider_config["base_url"] = credentials_provider.get_key("OLLAMA_BASE_URL", "http://localhost:11434")
        return provider_config

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatOllama(model=config.model.name, **full_config)
