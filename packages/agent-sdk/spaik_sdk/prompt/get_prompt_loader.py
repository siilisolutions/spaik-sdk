from typing import Optional

from spaik_sdk.config.env import env_config
from spaik_sdk.prompt.local_prompt_loader import LocalPromptLoader
from spaik_sdk.prompt.prompt_loader import PromptLoader
from spaik_sdk.prompt.prompt_loader_mode import PromptLoaderMode


def get_prompt_loader(mode: Optional[PromptLoaderMode] = None) -> PromptLoader:
    mode = mode or env_config.get_prompt_loader_mode()
    if mode == PromptLoaderMode.LOCAL:
        return LocalPromptLoader()
    raise ValueError(f"Unknown PromptLoaderMode: {mode}")
