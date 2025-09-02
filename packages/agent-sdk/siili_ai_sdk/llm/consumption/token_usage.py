from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    def __post_init__(self):
        """Ensure total_tokens is calculated if not provided."""
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens
