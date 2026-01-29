from dataclasses import dataclass


@dataclass(frozen=True)
class LLMModel:
    """Model identifier with extensibility support."""

    family: str
    name: str
    reasoning: bool = True
    reasoning_min_effort: str = "none"  # Minimum reasoning effort: 'none' or 'minimal'
    prompt_caching: bool = False

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"LLMModel('{self.name}')"
