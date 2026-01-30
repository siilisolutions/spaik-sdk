import os
from typing import Any, Collection, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI

from spaik_sdk.models.factories.openai_factory import OpenAIModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider

# Model name -> Environment variable for Azure deployment name
AZURE_DEPLOYMENT_ENV_VARS: Dict[str, str] = {
    "gpt-4.1": "AZURE_GPT_4_1_DEPLOYMENT",
    "gpt-4o": "AZURE_GPT_4O_DEPLOYMENT",
    "o4-mini": "AZURE_O4_MINI_DEPLOYMENT",
    "o4-mini-2025-04-16": "AZURE_O4_MINI_2025_04_16_DEPLOYMENT",
    "gpt-5": "AZURE_GPT_5_DEPLOYMENT",
    "gpt-5-mini": "AZURE_GPT_5_MINI_DEPLOYMENT",
    "gpt-5-nano": "AZURE_GPT_5_NANO_DEPLOYMENT",
    "gpt-5.1": "AZURE_GPT_5_1_DEPLOYMENT",
    "gpt-5.1-codex": "AZURE_GPT_5_1_CODEX_DEPLOYMENT",
    "gpt-5.1-codex-mini": "AZURE_GPT_5_1_CODEX_MINI_DEPLOYMENT",
    "gpt-5.1-codex-max": "AZURE_GPT_5_1_CODEX_MAX_DEPLOYMENT",
    "gpt-5.2": "AZURE_GPT_5_2_DEPLOYMENT",
    "gpt-5.2-pro": "AZURE_GPT_5_2_PRO_DEPLOYMENT",
}


class AzureProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        return OpenAIModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        return {
            "api_key": self._get_required_env("AZURE_API_KEY"),
            "api_version": self._get_required_env("AZURE_API_VERSION"),
            "azure_endpoint": self._get_required_env("AZURE_ENDPOINT"),
        }

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        full_config["deployment_name"] = self._get_deployment_name(config.model.name)
        return AzureChatOpenAI(**full_config)

    def _get_deployment_name(self, model_name: str) -> str:
        env_var = AZURE_DEPLOYMENT_ENV_VARS.get(model_name)
        if not env_var:
            raise ValueError(f"Model '{model_name}' not supported on Azure. Add it to AZURE_DEPLOYMENT_ENV_VARS.")
        deployment = os.environ.get(env_var)
        if not deployment:
            raise ValueError(f"Azure deployment not configured. Set {env_var} environment variable.")
        return deployment

    def _get_required_env(self, key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise ValueError(f"Environment variable {key} is required but not set")
        return value
