from abc import ABC, abstractmethod

from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
from siili_ai_sdk.llm.cost.cost_estimate import CostEstimate
from siili_ai_sdk.models.llm_model import LLMModel


class CostProvider(ABC):
    def get_cost_estimate(self, model: LLMModel, token_usage: TokenUsage) -> CostEstimate:
        token_pricing: TokenUsage = self.get_token_pricing(model)

        total = 0

        total += token_usage.input_tokens * token_pricing.input_tokens
        total += token_usage.output_tokens * token_pricing.output_tokens
        total += token_usage.reasoning_tokens * token_pricing.reasoning_tokens
        total += token_usage.cache_creation_tokens * token_pricing.cache_creation_tokens
        total += token_usage.cache_read_tokens * token_pricing.cache_read_tokens

        return CostEstimate(
            cost=(total) / 100000000.0,
            currency="USD",
            is_estimate=False,
        )

    @abstractmethod
    def get_token_pricing(self, model: LLMModel) -> TokenUsage:
        pass
