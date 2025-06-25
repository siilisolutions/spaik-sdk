from abc import ABC, abstractmethod
from typing import Any, Dict

from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class EventPublisher(ABC):
    @abstractmethod
    def publish_event(self, event: Dict[str, Any]) -> None:
        """Publish event - implemented by subclasses"""
        pass
