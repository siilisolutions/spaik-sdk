"""Unit tests for OllamaProvider - verifies model kwarg is not duplicated."""

from unittest.mock import patch

import pytest

from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.ollama_provider import OllamaProvider


@pytest.mark.unit
class TestOllamaProvider:
    def test_create_langchain_model_does_not_duplicate_model_kwarg(self):
        """ChatOllama should receive 'model' only once via full_config, not as a separate kwarg."""
        provider = OllamaProvider()
        ollama_model = LLMModel(family="ollama", name="test-model:7b", reasoning=False, prompt_caching=False)
        config = LLMConfig(model=ollama_model, reasoning=False, tool_usage=False, streaming=False)

        full_config = {
            "model": "test-model:7b",
            "temperature": 0.1,
            "base_url": "http://localhost:11434",
        }

        with patch("spaik_sdk.models.providers.ollama_provider.ChatOllama") as mock_chat_ollama:
            provider.create_langchain_model(config, full_config)
            mock_chat_ollama.assert_called_once_with(**full_config)
