from collections.abc import Callable
from typing import Any, Collection, Dict, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI

from spaik_sdk.config.env import env_config
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.azure_deployments import get_azure_supported_models, get_deployment_name, get_required_env
from spaik_sdk.models.providers.base_provider import BaseProvider


class AzureProvider(BaseProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        azure_ad_token_provider: Optional[Callable[[], str]] = None,
        azure_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        if api_key and azure_ad_token_provider:
            raise ValueError("Pass either api_key or azure_ad_token_provider, not both")
        self.api_key = api_key
        self.azure_ad_token_provider = azure_ad_token_provider
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version

    def get_supported_models(self) -> Collection[LLMModel]:
        return get_azure_supported_models()

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        if env_config.is_proxy_mode():
            return self._get_proxy_config("api_key", "azure_endpoint", "default_headers")

        result: Dict[str, Any] = {
            "api_version": self.api_version or get_required_env("AZURE_API_VERSION"),
            "azure_endpoint": self.azure_endpoint or get_required_env("AZURE_ENDPOINT"),
        }
        if self.azure_ad_token_provider:
            result["azure_ad_token_provider"] = self.azure_ad_token_provider
            return result
        result["api_key"] = self.api_key or get_required_env("AZURE_API_KEY")
        return result

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        full_config["azure_deployment"] = get_deployment_name(config.model.name)
        return AzureChatOpenAI(**full_config)
