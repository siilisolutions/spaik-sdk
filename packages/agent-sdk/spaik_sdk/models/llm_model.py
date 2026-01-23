from dataclasses import dataclass


@dataclass(frozen=True)
class LLMModel:
    """Model identifier with extensibility support."""

    family: str
    name: str
    reasoning: bool = True
    prompt_caching: bool = False

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"LLMModel('{self.name}')"
