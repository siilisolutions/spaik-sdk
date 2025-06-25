from typing import Any, Dict, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from siili_ai_sdk.models.llm_model import LLMModel


class LLMWrapper:
    def __init__(self, langchain_model: BaseChatModel, cache_control: Optional[Dict[str, Any]], model_type: LLMModel):
        """Initialize wrapper with pre-created langchain model and cache control."""
        self._langchain_model = langchain_model
        self._cache_control = cache_control
        self._model_type = model_type

    def get_langchain_model(self) -> BaseChatModel:
        """Get the underlying langchain model instance."""
        return self._langchain_model

    def get_cache_control(self) -> Optional[Dict[str, Any]]:
        """Get cache control settings for this model."""
        return self._cache_control

    def get_model_type(self) -> LLMModel:
        """Get the model type enum."""
        return self._model_type
