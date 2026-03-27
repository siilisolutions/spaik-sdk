from typing import Any, Collection, Dict

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider
from spaik_sdk.models.factories.anthropic_factory import AnthropicModelFactory
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.base_provider import BaseProvider


class AnthropicProvider(BaseProvider):
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by Anthropic provider."""
        return AnthropicModelFactory.MODELS

    def get_model_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Get Anthropic provider configuration (provider-specific only)."""
        result: Dict[str, Any] = {
            "model_kwargs": {
                "extra_headers": {"anthropic-beta": "prompt-caching-2024-07-31"}  # TODO add output length header
            },
        }

        if env_config.is_proxy_mode():
            result.update(self._get_proxy_config("anthropic_api_key", "base_url", "default_headers"))
        else:
            api_key = credentials_provider.get_provider_key("anthropic")
            if api_key:
                result["anthropic_api_key"] = api_key

        return result

    def create_langchain_model(self, config: LLMConfig, full_config: Dict[str, Any]) -> BaseChatModel:
        """Create Anthropic langchain model with complete configuration."""
        return ChatAnthropic(**full_config)
