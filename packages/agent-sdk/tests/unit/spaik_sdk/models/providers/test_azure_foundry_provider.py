"""Unit tests for AzureFoundryProvider."""

from unittest.mock import patch

import pytest

from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.providers.azure_foundry_provider import (
    AzureFoundryProvider,
    _openai_v1_endpoint_from_project_endpoint,
)
from spaik_sdk.models.providers.base_provider import BaseProvider
from spaik_sdk.models.providers.provider_type import ProviderType

PROJECT_ENDPOINT = "https://my-resource.services.ai.azure.com/api/projects/my-project"
OPENAI_V1_ENDPOINT = "https://my-resource.services.ai.azure.com/openai/v1"

DIRECT_ENV = {
    "LLM_AUTH_MODE": "direct",
}

PROXY_ENV = {
    "LLM_AUTH_MODE": "proxy",
    "LLM_PROXY_BASE_URL": "https://proxy.example.com/v1",
    "LLM_PROXY_API_KEY": "sk-proxy-key",
    "LLM_PROXY_HEADERS": "X-Tenant:abc,X-Region:us",
}


def _make_config(name: str = "gpt-4o") -> LLMConfig:
    model = LLMModel(family="openai", name=name, reasoning=False, prompt_caching=False)
    return LLMConfig(model=model, reasoning=False, tool_usage=False, streaming=False)


@pytest.mark.unit
class TestProviderTypeAliases:
    def test_foundry_alias(self):
        assert ProviderType.from_name("foundry") == ProviderType.AZURE_AI_FOUNDRY

    def test_azure_alias_is_classic_openai(self):
        assert ProviderType.from_name("azure") == ProviderType.AZURE_OPENAI

    def test_create_provider_foundry(self):
        provider = BaseProvider.create_provider(ProviderType.AZURE_AI_FOUNDRY)
        assert isinstance(provider, AzureFoundryProvider)


@pytest.mark.unit
class TestOpenaiV1EndpointFromProject:
    def test_derives_openai_v1_path(self):
        assert _openai_v1_endpoint_from_project_endpoint(PROJECT_ENDPOINT) == OPENAI_V1_ENDPOINT


@pytest.mark.unit
class TestAzureFoundryProviderDirect:
    def test_api_key_uses_openai_v1_endpoint(self, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("AZURE_FOUNDRY_PROJECT_ENDPOINT", PROJECT_ENDPOINT)
        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "foundry-api-key")
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)

        provider = AzureFoundryProvider()
        result = provider.get_model_config(_make_config())

        assert result["endpoint"] == OPENAI_V1_ENDPOINT
        assert result["credential"] == "foundry-api-key"
        assert "project_endpoint" not in result

    def test_explicit_constructor_overrides_env(self, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("AZURE_FOUNDRY_PROJECT_ENDPOINT", PROJECT_ENDPOINT)
        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "env-key")

        provider = AzureFoundryProvider(
            project_endpoint="https://other.services.ai.azure.com/api/projects/other",
            api_key="explicit-key",
        )
        result = provider.get_model_config(_make_config())

        assert result["endpoint"] == "https://other.services.ai.azure.com/openai/v1"
        assert result["credential"] == "explicit-key"

    def test_token_provider_uses_project_endpoint(self, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("AZURE_FOUNDRY_PROJECT_ENDPOINT", PROJECT_ENDPOINT)
        monkeypatch.delenv("AZURE_FOUNDRY_API_KEY", raising=False)

        def token_provider():
            return "token"

        provider = AzureFoundryProvider(azure_ad_token_provider=token_provider)
        result = provider.get_model_config(_make_config())

        assert result["project_endpoint"] == PROJECT_ENDPOINT
        assert result["credential"].get_token() is not None
        assert "endpoint" not in result

    def test_missing_project_endpoint_raises(self, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("AZURE_FOUNDRY_PROJECT_ENDPOINT", raising=False)
        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "key")

        provider = AzureFoundryProvider()
        with pytest.raises(ValueError, match="AZURE_FOUNDRY_PROJECT_ENDPOINT"):
            provider.get_model_config(_make_config())

    def test_rejects_api_key_and_token_provider_together(self):
        def token_provider():
            return "token"

        with pytest.raises(ValueError, match="either api_key or azure_ad_token_provider"):
            AzureFoundryProvider(api_key="api-key", azure_ad_token_provider=token_provider)


@pytest.mark.unit
class TestAzureFoundryProviderProxy:
    def test_proxy_mode(self, monkeypatch):
        for k, v in PROXY_ENV.items():
            monkeypatch.setenv(k, v)

        provider = AzureFoundryProvider()
        result = provider.get_model_config(_make_config())

        assert result["credential"] == "sk-proxy-key"
        assert result["endpoint"] == "https://proxy.example.com/v1"
        assert result["default_headers"] == {"X-Tenant": "abc", "X-Region": "us"}


@pytest.mark.unit
class TestAzureFoundryProviderCreateModel:
    @patch("spaik_sdk.models.providers.azure_foundry_provider.AzureAIOpenAIApiChatModel")
    def test_sets_deployment_model_name(self, mock_chat_model, monkeypatch):
        for k, v in DIRECT_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("AZURE_FOUNDRY_PROJECT_ENDPOINT", PROJECT_ENDPOINT)
        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "foundry-api-key")
        monkeypatch.setenv("AZURE_GPT_4O_DEPLOYMENT", "my-gpt-4o-deployment")

        provider = AzureFoundryProvider()
        config = _make_config("gpt-4o")
        provider_config = provider.get_model_config(config)
        factory_config = {"model": "gpt-4o", "streaming": False}
        full_config = {**factory_config, **provider_config}

        provider.create_langchain_model(config, full_config)

        mock_chat_model.assert_called_once()
        call_kwargs = mock_chat_model.call_args.kwargs
        assert call_kwargs["model"] == "my-gpt-4o-deployment"
