from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.ollama_factory import OllamaModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class OllamaProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return OllamaModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        if env_config.is_proxy_mode():
            return self._get_proxy_config("api_key", "base_url", "headers")

        return {"base_url": credentials_provider.get_key("OLLAMA_BASE_URL", "http://localhost:11434")}

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        return ChatOllama(**full_config)
