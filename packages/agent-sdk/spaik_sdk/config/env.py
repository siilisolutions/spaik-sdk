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

    def get_azure_keys(self) -> Dict[str, str]:
        return {
            "api_key": self.get_key("AZURE_API_KEY"),
            "api_version": self.get_key("AZURE_API_VERSION"),
            "endpoint": self.get_key("AZURE_ENDPOINT"),
            "o3-mini_deployment": self.get_key("AZURE_O3_MINI_DEPLOYMENT", required=False),
            "gpt-4_1_deployment": self.get_key("AZURE_GPT_4_1_DEPLOYMENT", required=False),
            "gpt-4o_deployment": self.get_key("AZURE_GPT_4O_DEPLOYMENT", required=False),
        }

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


env_config = EnvConfig()
