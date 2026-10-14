from dataclasses import dataclass


@dataclass(frozen=True)
class LLMModel:
    """Model identifier with extensibility support."""

    family: str
    name: str
    reasoning: bool = True
    # Least reasoning the model accepts, used when reasoning is off: an effort level, or "none".
    # Anthropic also accepts "between_tools".
    reasoning_min_effort: str = "none"
    prompt_caching: bool = False

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"LLMModel('{self.name}')"
