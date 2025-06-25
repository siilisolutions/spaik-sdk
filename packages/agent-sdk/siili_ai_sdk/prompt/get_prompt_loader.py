from typing import Optional

from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.prompt.local_prompt_loader import LocalPromptLoader
from siili_ai_sdk.prompt.prompt_loader import PromptLoader
from siili_ai_sdk.prompt.prompt_loader_mode import PromptLoaderMode


def get_prompt_loader(mode: Optional[PromptLoaderMode] = None) -> PromptLoader:
    mode = mode or env_config.get_prompt_loader_mode()
    if mode == PromptLoaderMode.LOCAL:
        return LocalPromptLoader()
    raise ValueError(f"Unknown PromptLoaderMode: {mode}")
