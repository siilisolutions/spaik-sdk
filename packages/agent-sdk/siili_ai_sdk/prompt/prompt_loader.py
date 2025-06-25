from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

if TYPE_CHECKING:
    from siili_ai_sdk.agent.base_agent import BaseAgent

from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class PromptLoader(ABC):
    def __init__(self):
        self._prompts_cache: Dict[str, str] = {}

    @abstractmethod
    def _load_raw_prompt(self, prompt_path: str) -> str:
        pass

    def _get_raw_prompt(self, prompt_path: str) -> str:
        if prompt_path in self._prompts_cache:
            return self._prompts_cache[prompt_path]
        else:
            raw_prompt = self._load_raw_prompt(prompt_path)
            self._prompts_cache[prompt_path] = raw_prompt
            return raw_prompt

    def _format_prompt(self, prompt: str, params: Dict[str, Any]) -> str:
        try:
            return prompt.format(**params)
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise KeyError(f"Missing required variable '{missing_key}' in params: {params} for prompt: '{prompt}'")

    def get_prompt(self, prompt_path: str, params: Dict[str, Any]) -> str:
        return self._format_prompt(self._get_raw_prompt(prompt_path), params)

    def _get_raw_agent_prompt(self, agent_class: Type["BaseAgent"], prompt_name: str, version: Optional[str] = None) -> str:
        return self._get_raw_prompt(f"agent/{agent_class.__name__}/{prompt_name}{f'-{version}' if version else ''}")

    def get_system_prompt(self, agent_class: Type["BaseAgent"], params: Dict[str, Any], version: Optional[str] = None) -> str:
        return self.get_agent_prompt(agent_class, "system", params, version)

    def get_agent_prompt(
        self, agent_class: Type["BaseAgent"], prompt_name: str, params: Dict[str, Any], version: Optional[str] = None
    ) -> str:
        raw_prompt = self._get_raw_agent_prompt(agent_class, prompt_name, version)
        return self._format_prompt(raw_prompt, params)
