from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Collection, Dict, Optional

from langchain_core.language_models.chat_models import BaseChatModel

if TYPE_CHECKING:
    from spaik_sdk.models.llm_config import LLMConfig

from spaik_sdk.config.env import env_config
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.provider_type import ProviderType


class BaseProvider(ABC):
    @abstractmethod
    def get_supported_models(self) -> Collection[LLMModel]:
        """Get list of models supported by this provider."""
        pass

    def supports_model(self, model: LLMModel) -> bool:
        return model in self.get_supported_models()

    @abstractmethod
    def get_model_config(self, config: "LLMConfig") -> Dict[str, Any]:
        """Get model configuration based on model and provider type."""
        pass

    @abstractmethod
    def create_langchain_model(self, config: "LLMConfig", full_config: Dict[str, Any]) -> BaseChatModel:
        """Create the langchain model instance with complete configuration and model info."""
        pass

    @classmethod
    def create_provider(cls, provider_type: Optional[ProviderType] = None) -> "BaseProvider":
        """Factory method to create appropriate provider instance."""

        if provider_type is None:
            provider_type = env_config.get_provider_type()

        # Import here to avoid circular imports
        if provider_type == ProviderType.ANTHROPIC:
            from spaik_sdk.models.providers.anthropic_provider import AnthropicProvider

            return AnthropicProvider()
        elif provider_type == ProviderType.AZURE_AI_FOUNDRY:
            from spaik_sdk.models.providers.azure_provider import AzureProvider

            return AzureProvider()
        elif provider_type == ProviderType.OPENAI_DIRECT:
            from spaik_sdk.models.providers.openai_provider import OpenAIProvider

            return OpenAIProvider()
        elif provider_type == ProviderType.GOOGLE:
            from spaik_sdk.models.providers.google_provider import GoogleProvider

            return GoogleProvider()
        elif provider_type == ProviderType.OLLAMA:
            from spaik_sdk.models.providers.ollama_provider import OllamaProvider

            return OllamaProvider()
        elif provider_type == ProviderType.DEEPSEEK:
            from spaik_sdk.models.providers.deepseek_provider import DeepSeekProvider

            return DeepSeekProvider()
        elif provider_type == ProviderType.XAI:
            from spaik_sdk.models.providers.xai_provider import XAIProvider

            return XAIProvider()
        elif provider_type == ProviderType.COHERE:
            from spaik_sdk.models.providers.cohere_provider import CohereProvider

            return CohereProvider()
        elif provider_type == ProviderType.MISTRAL:
            from spaik_sdk.models.providers.mistral_provider import MistralProvider

            return MistralProvider()
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
