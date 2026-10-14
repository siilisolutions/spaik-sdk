"""Thread management and agent convenience using the AG-UI protocol."""

from importlib.metadata import version

from ag_ui.core import Message

from .agent.base_agent import BaseAgent
from .models.llm_config import LLMConfig
from .models.llm_model import LLMModel
from .models.providers.provider_type import ProviderType
from .thread.thread_container import ThreadContainer, message_text

__all__ = ["BaseAgent", "LLMConfig", "LLMModel", "ProviderType", "ThreadContainer", "Message", "message_text"]

__version__ = version("spaik-sdk")
