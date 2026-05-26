import time
from collections.abc import Callable
from typing import Any, Collection, Dict, Optional
from urllib.parse import urlparse

from azure.core.credentials import AccessToken, TokenCredential
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.config.env import env_config
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.azure_deployments import (
    get_azure_supported_models,
    get_deployment_name,
    get_required_env,
)
from spaik_sdk.models.providers.base_provider import BaseProvider


class _CallableTokenCredential(TokenCredential):
    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._token_provider = token_provider

    def get_token(self, *_scopes: str, **kwargs: Any) -> AccessToken:
        del kwargs
        result = self._token_provider()
        if isinstance(result, AccessToken):
            return result
        return AccessToken(str(result), int(time.time()) + 300)


def openai_v1_endpoint_from_project_endpoint(project_endpoint: str) -> str:
    parsed = urlparse(project_endpoint.rstrip("/"))
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid AZURE_FOUNDRY_PROJECT_ENDPOINT: {project_endpoint!r}")
    return f"{parsed.scheme}://{parsed.netloc}/openai/v1"


class AzureFoundryProvider(BaseProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        azure_ad_token_provider: Optional[Callable[[], str]] = None,
        project_endpoint: Optional[str] = None,
    ) -> None:
        if api_key and azure_ad_token_provider:
            raise ValueError("Pass either api_key or azure_ad_token_provider, not both")
        self.api_key = api_key
        self.azure_ad_token_provider = azure_ad_token_provider
        self.project_endpoint = project_endpoint

    def get_supported_models(self) -> Collection[LLMModel]:
        return get_azure_supported_models()

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        if env_config.is_proxy_mode():
            return self._get_proxy_config("credential", "endpoint", "default_headers")

        project_endpoint = self.project_endpoint or get_required_env("AZURE_FOUNDRY_PROJECT_ENDPOINT")
        if self.azure_ad_token_provider:
            return {
                "project_endpoint": project_endpoint,
                "credential": _CallableTokenCredential(self.azure_ad_token_provider),
            }
        api_key = self.api_key or get_required_env("AZURE_FOUNDRY_API_KEY")
        return {
            "endpoint": openai_v1_endpoint_from_project_endpoint(project_endpoint),
            "credential": api_key,
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        full_config["model"] = get_deployment_name(config.model.name)
        return AzureAIOpenAIApiChatModel(**full_config)
