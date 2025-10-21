from dataclasses import dataclass, field
from typing import Any, Dict

from siili_ai_sdk.llm.consumption.token_usage import TokenUsage


@dataclass
class ConsumptionEstimate:
    """Consumption estimation for a request."""

    token_usage: TokenUsage
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "token_usage": {
                "input_tokens": self.token_usage.input_tokens,
                "output_tokens": self.token_usage.output_tokens,
                "total_tokens": self.token_usage.total_tokens,
                "reasoning_tokens": self.token_usage.reasoning_tokens,
                "cache_creation_tokens": self.token_usage.cache_creation_tokens,
                "cache_read_tokens": self.token_usage.cache_read_tokens,
            },
            "metadata": self.metadata or {},
        }
