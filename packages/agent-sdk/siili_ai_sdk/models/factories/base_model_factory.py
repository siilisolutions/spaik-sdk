from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from siili_ai_sdk.models.llm_config import LLMConfig

from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.llm_wrapper import LLMWrapper
from siili_ai_sdk.models.providers.base_provider import BaseProvider


class BaseModelFactory(ABC):
    def create_model(self, config: "LLMConfig", provider: BaseProvider) -> LLMWrapper:
        """Create a model wrapper for the given config and provider instance."""
        # Check if this factory supports the model with this config
        if not self.supports_model_config(config):
            raise ValueError(f"Factory doesn't support model config: {config}")

        # Get provider config and cache control
        provider_config = provider.get_model_config(config)
        cache_control = self.get_cache_control(config)

        # Get model-specific configuration from subclass
        model_specific_config = self.get_model_specific_config(config)

        # Build complete model config
        model_config = {**model_specific_config, **provider_config}

        # Let provider create the langchain model
        langchain_model = provider.create_langchain_model(config, model_config)

        return LLMWrapper(langchain_model, cache_control, config.model)

    @abstractmethod
    def supports_model(self, model: LLMModel) -> bool:
        """Check if this factory supports the given model (basic check)."""
        pass

    def supports_model_config(self, config: "LLMConfig") -> bool:
        return self.supports_model(config.model)

    @abstractmethod
    def get_cache_control(self, config: "LLMConfig") -> Optional[Dict[str, Any]]:
        """Get cache control settings for this factory's models."""
        pass

    @abstractmethod
    def get_model_specific_config(self, config: "LLMConfig") -> Dict[str, Any]:
        """Get model-specific configuration for the given config."""
        pass

    @classmethod
    def create_factory(cls, config: "LLMConfig") -> "BaseModelFactory":
        """Factory method to create appropriate factory instance."""

        from siili_ai_sdk.models.factories.anthropic_factory import AnthropicModelFactory
        from siili_ai_sdk.models.factories.google_factory import GoogleModelFactory
        from siili_ai_sdk.models.factories.ollama_factory import OllamaModelFactory
        from siili_ai_sdk.models.factories.openai_factory import OpenAIModelFactory

        factories = [
            AnthropicModelFactory(),
            OpenAIModelFactory(),
            GoogleModelFactory(),
            OllamaModelFactory(),
        ]
        for factory in factories:
            if factory.supports_model_config(config):
                return factory

        raise ValueError(f"No factory found that supports model config: {config}")
