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

    def _load_raw_prompt(self, prompt_name: str) -> str:
        prompt_path = os.path.join(self.prompts_dir, f"{prompt_name}.md")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file {prompt_path} not found")
        with open(prompt_path, "r") as f:
            return f.read().strip()
