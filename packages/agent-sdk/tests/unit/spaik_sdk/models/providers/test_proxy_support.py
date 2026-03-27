"""Unit tests for proxy support across all model providers."""

from unittest.mock import patch

import pytest

from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.anthropic_provider import AnthropicProvider
from spaik_sdk.models.providers.azure_provider import AzureProvider
from spaik_sdk.models.providers.cohere_provider import CohereProvider
from spaik_sdk.models.providers.deepseek_provider import DeepSeekProvider
from spaik_sdk.models.providers.google_provider import GoogleProvider
from spaik_sdk.models.providers.mistral_provider import MistralProvider
from spaik_sdk.models.providers.ollama_provider import OllamaProvider
from spaik_sdk.models.providers.openai_provider import OpenAIProvider
from spaik_sdk.models.providers.xai_provider import XAIProvider


def _make_config(family: str = "openai", name: str = "test-model") -> LLMConfig:
    model = LLMModel(family=family, name=name, reasoning=False, prompt_caching=False)
    return LLMConfig(model=model, reasoning=False, tool_usage=False, streaming=False)


PROXY_ENV = {
    "LLM_AUTH_MODE": "proxy",
    "LLM_PROXY_BASE_URL": "https://proxy.example.com/v1",
    "LLM_PROXY_API_KEY": "sk-proxy-key",
    "LLM_PROXY_HEADERS": "X-Tenant:abc,X-Region:us",
}

DIRECT_ENV = {
    "LLM_AUTH_MODE": "direct",
}


@pytest.mark.unit
class TestBaseProviderGetProxyConfig:
    """Tests for BaseProvider._get_proxy_config method."""

    def test_returns_all_fields_when_set(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = OpenAIProvider()
        result = provider._get_proxy_config("api_key", "base_url", "default_headers")

        assert result["api_key"] == "sk-proxy-key"
        assert result["base_url"] == "https://proxy.example.com/v1"
        assert result["default_headers"] == {"X-Tenant": "abc", "X-Region": "us"}

    def test_omits_empty_fields(self, monkeypatch):
        monkeypatch.setenv("LLM_AUTH_MODE", "proxy")
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        provider = OpenAIProvider()
        result = provider._get_proxy_config("api_key", "base_url", "default_headers")

        assert result == {}

    def test_uses_custom_param_names(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = GoogleProvider()
        result = provider._get_proxy_config("google_api_key", "base_url", "additional_headers")

        assert "google_api_key" in result
        assert "base_url" in result
        assert "additional_headers" in result


@pytest.mark.unit
class TestAnthropicProviderProxy:
    def test_proxy_mode_uses_proxy_config(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = AnthropicProvider()
        config = _make_config("anthropic", "claude-sonnet-4-20250514")
        result = provider.get_model_config(config)

        assert result["anthropic_api_key"] == "sk-proxy-key"
        assert result["base_url"] == "https://proxy.example.com/v1"
        assert result["default_headers"] == {"X-Tenant": "abc", "X-Region": "us"}
        # Should still include model_kwargs with extra_headers
        assert "model_kwargs" in result

    @patch("spaik_sdk.models.providers.anthropic_provider.credentials_provider")
    def test_direct_mode_uses_credentials_provider(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_provider_key.return_value = "sk-ant-direct"
        provider = AnthropicProvider()
        config = _make_config("anthropic", "claude-sonnet-4-20250514")
        result = provider.get_model_config(config)

        assert result["anthropic_api_key"] == "sk-ant-direct"
        assert "base_url" not in result
        assert "default_headers" not in result

    @patch("spaik_sdk.models.providers.anthropic_provider.credentials_provider")
    def test_direct_mode_no_key_omits_api_key(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_provider_key.return_value = ""
        provider = AnthropicProvider()
        config = _make_config("anthropic", "claude-sonnet-4-20250514")
        result = provider.get_model_config(config)

        assert "anthropic_api_key" not in result


@pytest.mark.unit
class TestOpenAIProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = OpenAIProvider()
        result = provider.get_model_config(_make_config("openai", "gpt-4o"))

        assert result["api_key"] == "sk-proxy-key"
        assert result["base_url"] == "https://proxy.example.com/v1"
        assert result["default_headers"] == {"X-Tenant": "abc", "X-Region": "us"}

    @patch("spaik_sdk.models.providers.openai_provider.credentials_provider")
    def test_direct_mode(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_provider_key.return_value = "sk-openai-direct"
        provider = OpenAIProvider()
        result = provider.get_model_config(_make_config("openai", "gpt-4o"))

        assert result["api_key"] == "sk-openai-direct"
        assert "base_url" not in result


@pytest.mark.unit
class TestGoogleProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = GoogleProvider()
        result = provider.get_model_config(_make_config("google", "gemini-2.5-flash"))

        assert result["google_api_key"] == "sk-proxy-key"
        assert result["base_url"] == "https://proxy.example.com/v1"
        assert result["additional_headers"] == {"X-Tenant": "abc", "X-Region": "us"}

    @patch("spaik_sdk.models.providers.google_provider.credentials_provider")
    def test_direct_mode_no_key(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_provider_key.return_value = ""
        provider = GoogleProvider()
        result = provider.get_model_config(_make_config("google", "gemini-2.5-flash"))

        assert "google_api_key" not in result


@pytest.mark.unit
class TestAzureProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = AzureProvider()
        result = provider.get_model_config(_make_config("azure", "gpt-4o"))

        assert result["api_key"] == "sk-proxy-key"
        assert result["azure_endpoint"] == "https://proxy.example.com/v1"
        assert result["default_headers"] == {"X-Tenant": "abc", "X-Region": "us"}


@pytest.mark.unit
class TestCohereProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = CohereProvider()
        result = provider.get_model_config(_make_config("cohere", "command-r"))

        assert result["cohere_api_key"] == "sk-proxy-key"
        assert result["base_url"] == "https://proxy.example.com/v1"

    @patch("spaik_sdk.models.providers.cohere_provider.credentials_provider")
    def test_direct_mode(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_provider_key.return_value = "cohere-key"
        provider = CohereProvider()
        result = provider.get_model_config(_make_config("cohere", "command-r"))

        assert result["cohere_api_key"] == "cohere-key"


@pytest.mark.unit
class TestDeepSeekProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = DeepSeekProvider()
        result = provider.get_model_config(_make_config("deepseek", "deepseek-chat"))

        assert result["api_key"] == "sk-proxy-key"
        assert result["api_base"] == "https://proxy.example.com/v1"


@pytest.mark.unit
class TestMistralProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = MistralProvider()
        result = provider.get_model_config(_make_config("mistral", "mistral-large"))

        assert result["api_key"] == "sk-proxy-key"
        assert result["endpoint"] == "https://proxy.example.com/v1"


@pytest.mark.unit
class TestOllamaProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = OllamaProvider()
        result = provider.get_model_config(_make_config("ollama", "llama3:8b"))

        assert result["base_url"] == "https://proxy.example.com/v1"
        assert result["client_kwargs"] == {
            "headers": {
                "Authorization": "Bearer sk-proxy-key",
                "X-Tenant": "abc",
                "X-Region": "us",
            }
        }

    @patch("spaik_sdk.models.providers.ollama_provider.credentials_provider")
    def test_direct_mode_uses_ollama_base_url(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_key.return_value = "http://my-ollama:11434"
        provider = OllamaProvider()
        result = provider.get_model_config(_make_config("ollama", "llama3:8b"))

        assert result["base_url"] == "http://my-ollama:11434"


@pytest.mark.unit
class TestXAIProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = XAIProvider()
        result = provider.get_model_config(_make_config("xai", "grok-2"))

        assert result["xai_api_key"] == "sk-proxy-key"
        assert result["xai_api_base"] == "https://proxy.example.com/v1"

    @patch("spaik_sdk.models.providers.xai_provider.credentials_provider")
    def test_direct_mode(self, mock_creds, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)

        mock_creds.get_provider_key.return_value = "xai-key"
        provider = XAIProvider()
        result = provider.get_model_config(_make_config("xai", "grok-2"))

        assert result["xai_api_key"] == "xai-key"
        assert "xai_api_base" not in result
