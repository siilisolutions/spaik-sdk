from dataclasses import dataclass, field, replace
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.llm_wrapper import LLMWrapper
from spaik_sdk.models.providers.base_provider import BaseProvider
from spaik_sdk.models.providers.provider_type import ProviderType


@dataclass
class LLMConfig:
    """A provider/model identifier or an already configured LangChain model.

    Strings never consult the preset catalog. Provider kwargs are passed through.
    """

    model: LLMModel | str = ""
    provider_type: ProviderType | str | None = None
    provider: BaseProvider | None = None
    chat_model: BaseChatModel | None = None
    provider_kwargs: dict[str, Any] = field(default_factory=dict)
    reasoning: bool = True
    tool_usage: bool = True
    streaming: bool = True
    reasoning_summary: str | None = "detailed"
    reasoning_effort: str = "medium"
    max_output_tokens: int | None = None
    reasoning_budget_tokens: int = 4096
    max_agent_steps: int = 100
    temperature: float = 0.1
    structured_response: bool = False
    _model_wrapper: LLMWrapper | None = field(default=None, init=False, repr=False)

    @property
    def model_name(self) -> str:
        return self.model.name if isinstance(self.model, LLMModel) else self.model

    @property
    def provider_name(self) -> str:
        if isinstance(self.provider_type, ProviderType):
            return self.provider_type.value
        if self.provider_type:
            return self.provider_type
        return self.model.family if isinstance(self.model, LLMModel) else "injected"

    def get_model_wrapper(self) -> LLMWrapper:
        if self._model_wrapper is None:
            self._model_wrapper = self.create_model_wrapper()
        return self._model_wrapper

    def create_model_wrapper(self) -> LLMWrapper:
        identity = self.model if isinstance(self.model, LLMModel) else LLMModel(self.provider_name, self.model_name, reasoning=False)
        if self.chat_model is not None:
            return LLMWrapper(self.chat_model, None, identity)
        if not self.model_name:
            raise ValueError("Supply a model ID and provider, or chat_model")
        kwargs = self._preset_kwargs()
        if self.max_output_tokens is not None:
            kwargs["max_tokens"] = self.max_output_tokens
        provider = self.provider
        if provider is None:
            try:
                kind = ProviderType.from_name(self.provider_name)
            except ValueError:
                kind = None
            if kind is not None:
                provider = BaseProvider.create_provider(kind)
        if provider is not None:
            kwargs.update(provider.get_model_config(self))
        kwargs.update(self.provider_kwargs)
        if provider is not None and self.provider_name in {"azure_openai", "azure_ai_foundry"}:
            kwargs["model"] = self.model_name
            model = provider.create_langchain_model(self, kwargs)
        else:
            name = {"google": "google_genai", "mistral": "mistralai"}.get(self.provider_name, self.provider_name)
            if name == "injected":
                raise ValueError("An arbitrary model ID requires an explicit provider_type")
            model = init_chat_model(self.model_name, model_provider=name, **kwargs)
        cache = {"type": "ephemeral"} if isinstance(self.model, LLMModel) and self.model.prompt_caching else None
        return LLMWrapper(model, cache, identity)

    def _preset_kwargs(self) -> dict[str, Any]:
        if not isinstance(self.model, LLMModel):
            return {}
        if self.model.family == "anthropic":
            kwargs: dict[str, Any] = {"max_tokens": self.max_output_tokens or 8192}
            if self.model.name.startswith(("claude-opus-5", "claude-fable-5", "claude-sonnet-5", "claude-haiku-5")):
                if not self.reasoning and self.model.name in {"claude-opus-5-5", "claude-fable-5-1"}:
                    raise ValueError(f"{self.model.name} requires adaptive thinking")
                kwargs["thinking"] = {"type": "adaptive" if self.reasoning else "disabled"}
                if self.reasoning:
                    kwargs["output_config"] = {"effort": self.reasoning_effort}
            elif self.reasoning and self.model.reasoning:
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.reasoning_budget_tokens}
            return kwargs
        if self.model.family == "openai" and self.model.reasoning:
            return {
                "use_responses_api": True,
                "reasoning": {
                    "effort": self.reasoning_effort if self.reasoning else self.model.reasoning_min_effort,
                    "summary": self.reasoning_summary,
                },
            }
        if self.model.family == "google":
            if self.model.name.startswith("gemini-3"):
                return {"thinking_level": "high" if self.reasoning else "low"}
            return {"thinking_budget": self.reasoning_budget_tokens if self.reasoning else 0, "include_thoughts": self.reasoning}
        return {}

    def get_provider(self) -> BaseProvider:
        return self.provider or BaseProvider.create_provider(ProviderType.from_name(self.provider_name))

    def as_structured_response_config(self) -> "LLMConfig":
        return replace(self, structured_response=True, tool_usage=False)
