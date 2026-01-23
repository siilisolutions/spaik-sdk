from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens

    @classmethod
    def from_langchain(cls, usage: Mapping[str, Any]) -> "TokenUsage":
        """Create TokenUsage from LangChain usage_metadata."""
        output_details = usage.get("output_token_details", {})
        input_details = usage.get("input_token_details", {})

        return cls(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            reasoning_tokens=output_details.get("reasoning", 0) if isinstance(output_details, dict) else 0,
            cache_creation_tokens=input_details.get("cache_creation", 0) if isinstance(input_details, dict) else 0,
            cache_read_tokens=input_details.get("cache_read", 0) if isinstance(input_details, dict) else 0,
        )
