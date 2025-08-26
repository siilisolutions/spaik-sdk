import os
from typing import Dict

from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.models.providers.provider_type import ProviderType
from siili_ai_sdk.prompt.prompt_loader_mode import PromptLoaderMode


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

    def get_credentials_provider_type(self) -> str:
        return self.get_key("CREDENTIALS_PROVIDER_TYPE", "env")


env_config = EnvConfig()
