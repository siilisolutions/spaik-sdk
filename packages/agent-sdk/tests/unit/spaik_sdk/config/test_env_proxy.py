"""Unit tests for EnvConfig proxy configuration methods."""

import pytest

from spaik_sdk.config.env import EnvConfig


@pytest.mark.unit
class TestEnvConfigProxy:
    def setup_method(self):
        self.config = EnvConfig()

    def test_is_proxy_mode_defaults_to_false(self, monkeypatch):
        monkeypatch.delenv("LLM_AUTH_MODE", raising=False)
        assert self.config.is_proxy_mode() is False

    def test_is_proxy_mode_direct(self, monkeypatch):
        monkeypatch.setenv("LLM_AUTH_MODE", "direct")
        assert self.config.is_proxy_mode() is False

    def test_is_proxy_mode_proxy(self, monkeypatch):
        monkeypatch.setenv("LLM_AUTH_MODE", "proxy")
        assert self.config.is_proxy_mode() is True

    def test_get_llm_auth_mode_default(self, monkeypatch):
        monkeypatch.delenv("LLM_AUTH_MODE", raising=False)
        assert self.config.get_llm_auth_mode() == "direct"

    def test_get_proxy_base_url(self, monkeypatch):
        monkeypatch.setenv("LLM_PROXY_BASE_URL", "https://proxy.example.com")
        assert self.config.get_proxy_base_url() == "https://proxy.example.com"

    def test_get_proxy_base_url_default_empty(self, monkeypatch):
        monkeypatch.delenv("LLM_PROXY_BASE_URL", raising=False)
        assert self.config.get_proxy_base_url() == ""

    def test_get_proxy_api_key(self, monkeypatch):
        monkeypatch.setenv("LLM_PROXY_API_KEY", "sk-proxy-123")
        assert self.config.get_proxy_api_key() == "sk-proxy-123"

    def test_get_proxy_api_key_default_empty(self, monkeypatch):
        monkeypatch.delenv("LLM_PROXY_API_KEY", raising=False)
        assert self.config.get_proxy_api_key() == ""

    def test_get_proxy_headers_empty(self, monkeypatch):
        monkeypatch.delenv("LLM_PROXY_HEADERS", raising=False)
        assert self.config.get_proxy_headers() == {}

    def test_get_proxy_headers_single(self, monkeypatch):
        monkeypatch.setenv("LLM_PROXY_HEADERS", "X-Custom:value1")
        assert self.config.get_proxy_headers() == {"X-Custom": "value1"}

    def test_get_proxy_headers_multiple(self, monkeypatch):
        monkeypatch.setenv("LLM_PROXY_HEADERS", "X-Custom:value1,Authorization:Bearer token")
        assert self.config.get_proxy_headers() == {
            "X-Custom": "value1",
            "Authorization": "Bearer token",
        }

    def test_get_proxy_headers_value_with_colon(self, monkeypatch):
        monkeypatch.setenv("LLM_PROXY_HEADERS", "Authorization:Bearer:token:extra")
        assert self.config.get_proxy_headers() == {"Authorization": "Bearer:token:extra"}

    def test_get_proxy_headers_skips_malformed(self, monkeypatch):
        monkeypatch.setenv("LLM_PROXY_HEADERS", "valid:header,nocolon,another:good")
        assert self.config.get_proxy_headers() == {"valid": "header", "another": "good"}
