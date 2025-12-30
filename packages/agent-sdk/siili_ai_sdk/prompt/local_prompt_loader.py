import os
from typing import Optional

from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.prompt.prompt_loader import PromptLoader
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class LocalPromptLoader(PromptLoader):
    def __init__(self, prompts_dir: Optional[str] = None):
        super().__init__()
        self.prompts_dir = prompts_dir if prompts_dir else env_config.get_prompts_dir()

    def _load_raw_prompt(self, prompt_path: str) -> str:
        full_path = os.path.join(self.prompts_dir, f"{prompt_path}.md")
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Prompt file {full_path} not found")
        with open(full_path, "r") as f:
            return f.read().strip()
