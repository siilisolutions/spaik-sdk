import os
from typing import Dict
from typing import Optional as OptionalType

from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.provider_type import ProviderType
from spaik_sdk.prompt.prompt_loader_mode import PromptLoaderMode
from spaik_sdk.tracing.trace_sink_mode import TraceSinkMode


class EnvConfig:
    def get_key(self, key: str, default: str = "", required: bool = True) -> str:
        value = os.environ.get(key, default)
        if required and not value:
            raise ValueError(f"Environment variable {key} is required but not set")
        return value

    def get_default_model(self) -> LLMModel:
        return ModelRegistry.from_name(self.get_key("DEFAULT_MODEL"))

    def get_provider_type(self) -> ProviderType:
        provider_type_name = self.get_key("MODEL_PROVIDER", required=False)
        if not provider_type_name:
            return ProviderType.from_model_name(self.get_default_model().name)
        return ProviderType.from_name(provider_type_name)

    def is_debug_mode(self, key: str) -> bool:
        debug_modes = self.get_key("DEBUG_MODES", required=False)
        if debug_modes:
            return key in debug_modes.split(",")
        return False

    def get_prompts_dir(self) -> str:
        return self.get_key("PROMPTS_DIR", "prompts")

    def get_prompt_loader_mode(self) -> PromptLoaderMode:
        return PromptLoaderMode.from_name(self.get_key("PROMPT_LOADER_MODE", "local"))

    def get_trace_sink_mode(self) -> OptionalType[TraceSinkMode]:
        """Get the trace sink mode from environment variable.

        Returns:
            TraceSinkMode.LOCAL if TRACE_SINK_MODE=local,
            TraceSinkMode.NOOP if TRACE_SINK_MODE=noop,
            None if TRACE_SINK_MODE is not set or empty (allows global/default behavior).
        """
        mode_str = self.get_key("TRACE_SINK_MODE", "", required=False)
        return TraceSinkMode.from_name(mode_str)

    def get_credentials_provider_type(self) -> str:
        return self.get_key("CREDENTIALS_PROVIDER_TYPE", "env")

    def get_image_model(self) -> str:
        return self.get_key("IMAGE_MODEL")

    # ── LLM proxy configuration ──────────────────────────────────────────

    def get_llm_auth_mode(self) -> str:
        """Get LLM auth mode: 'direct' (default) or 'proxy'."""
        return self.get_key("LLM_AUTH_MODE", "direct", required=False)

    def is_proxy_mode(self) -> bool:
        return self.get_llm_auth_mode() == "proxy"

    def get_proxy_base_url(self) -> str:
        return self.get_key("LLM_PROXY_BASE_URL", "", required=False)

    def get_proxy_api_key(self) -> str:
        return self.get_key("LLM_PROXY_API_KEY", "", required=False)

    def get_proxy_headers(self) -> Dict[str, str]:
        raw = self.get_key("LLM_PROXY_HEADERS", "", required=False)
        if not raw:
            return {}
        return dict(h.split(":", 1) for h in raw.split(",") if ":" in h)


env_config = EnvConfig()
