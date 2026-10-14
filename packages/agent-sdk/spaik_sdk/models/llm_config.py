from dataclasses import dataclass, field, replace
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from spaik_sdk.models.family_settings import family_kwargs
from spaik_sdk.models.llm_families import LLMFamilies
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.llm_wrapper import LLMWrapper
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.base_provider import BaseProvider
from spaik_sdk.models.providers.provider_type import ProviderType

PROVIDER_FAMILIES = {ProviderType.AZURE_OPENAI.value: LLMFamilies.OPENAI}
LANGCHAIN_PROVIDER_NAMES = {"google": "google_genai", "mistral": "mistralai"}


@dataclass
class LLMConfig:
    """A model plus generation settings, or an already configured LangChain model.

    A string model ID that matches a preset uses the preset; any other string becomes an
    LLMModel with provider defaults. Family settings apply by model family, provider
    kwargs override everything, and Spaik providers build every model they know.
    Structured responses use the model's minimum reasoning unless structured_reasoning_effort is set.
    """

    model: LLMModel | str = ""
    provider_type: ProviderType | str | None = None
    provider: BaseProvider | None = None
    chat_model: BaseChatModel | None = None
    provider_kwargs: dict[str, Any] = field(default_factory=dict)
    reasoning: bool = True
    streaming: bool = True
    reasoning_summary: str | None = "detailed"
    reasoning_effort: str = "medium"
    max_output_tokens: int | None = None
    reasoning_budget_tokens: int = 4096
    max_agent_steps: int = 100
    temperature: float | None = None
    structured_response: bool = False
    structured_reasoning_effort: str | None = None
    _model_wrapper: LLMWrapper | None = field(default=None, init=False, repr=False)

    @property
    def model_name(self) -> str:
        name = self.model.name if isinstance(self.model, LLMModel) else self.model
        if not name and self.chat_model is not None:
            name = getattr(self.chat_model, "model_name", None) or getattr(self.chat_model, "model", "")
        return str(name)

    @property
    def provider_name(self) -> str:
        if isinstance(self.provider_type, ProviderType):
            return self.provider_type.value
        if self.provider_type:
            try:
                return ProviderType.from_name(self.provider_type).value
            except ValueError:
                return self.provider_type
        preset = self.model if isinstance(self.model, LLMModel) else ModelRegistry.by_id(self.model)
        if preset is not None:
            return preset.family
        if self.chat_model is not None:
            for base in type(self.chat_model).__mro__:
                module = base.__module__.split(".")[0]
                if module.startswith("langchain_") and module != "langchain_core":
                    return module.removeprefix("langchain_")
        return "injected"

    def resolved_model(self) -> LLMModel:
        if isinstance(self.model, LLMModel):
            return self.model
        preset = ModelRegistry.by_id(self.model_name)
        if preset is not None:
            return preset
        family = PROVIDER_FAMILIES.get(self.provider_name, self.provider_name)
        return LLMModel(family=family, name=self.model_name, reasoning=False)

    def get_model_wrapper(self) -> LLMWrapper:
        if self._model_wrapper is None:
            self._model_wrapper = self.create_model_wrapper()
        return self._model_wrapper

    def create_model_wrapper(self) -> LLMWrapper:
        model = self.resolved_model()
        if self.chat_model is not None:
            return LLMWrapper(self.chat_model, None, model)
        if not self.model_name:
            raise ValueError("Supply a model ID and provider, or chat_model")
        kwargs = family_kwargs(model, self)
        if self.max_output_tokens is not None:
            kwargs["max_tokens"] = self.max_output_tokens
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if not self.streaming:
            kwargs["disable_streaming"] = True
        provider = self.provider or self._known_provider()
        if provider is not None:
            kwargs.update(provider.get_model_config(self))
        kwargs.update(self.provider_kwargs)
        if provider is not None:
            kwargs["model"] = self.model_name
            langchain_model = provider.create_langchain_model(self, kwargs)
        elif self.provider_name == "injected":
            raise ValueError("An arbitrary model ID requires an explicit provider_type")
        else:
            name = LANGCHAIN_PROVIDER_NAMES.get(self.provider_name, self.provider_name)
            langchain_model = init_chat_model(self.model_name, model_provider=name, **kwargs)
        cache = {"type": "ephemeral"} if model.prompt_caching else None
        return LLMWrapper(langchain_model, cache, model)

    def _known_provider(self) -> BaseProvider | None:
        try:
            kind = ProviderType.from_name(self.provider_name)
        except ValueError:
            return None
        return BaseProvider.create_provider(kind)

    def get_provider(self) -> BaseProvider:
        return self.provider or BaseProvider.create_provider(ProviderType.from_name(self.provider_name))

    def as_structured_response_config(self, reasoning_effort: str | None = None) -> "LLMConfig":
        effort = reasoning_effort or self.structured_reasoning_effort
        return replace(self, structured_response=True, structured_reasoning_effort=effort)
