from dataclasses import dataclass, replace
from typing import Optional

from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.llm_wrapper import LLMWrapper
from siili_ai_sdk.models.providers.base_provider import BaseProvider
from siili_ai_sdk.models.providers.provider_type import ProviderType


@dataclass
class LLMConfig:
    model: LLMModel
    provider_type: Optional[ProviderType] = None
    reasoning: bool = True
    tool_usage: bool = True
    streaming: bool = True
    reasoning_summary: str = "detailed"  # Options: "auto", "concise", "detailed", None
    reasoning_effort: str = "medium"  # Options: "low", "medium", "high"
    max_output_tokens: int = 8192
    reasoning_budget_tokens: int = 4096
    temperature: float = 0.1
    structured_response: bool = False

    _model_wrapper: Optional[LLMWrapper] = None

    def get_model_wrapper(self) -> LLMWrapper:
        if self._model_wrapper is None:
            self._model_wrapper = self.create_model_wrapper()
        return self._model_wrapper

    def create_model_wrapper(self) -> LLMWrapper:
        provider = self.get_provider()
        factory = self.get_factory()
        return factory.create_model(self, provider)

    def get_provider(self) -> BaseProvider:
        return BaseProvider.create_provider(self.provider_type)

    def get_factory(self):
        # Late import to avoid circular dependency
        from siili_ai_sdk.models.factories.base_model_factory import BaseModelFactory

        return BaseModelFactory.create_factory(self)

    def as_structured_response_config(self) -> "LLMConfig":
        return replace(self, structured_response=True)
