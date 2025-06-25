from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel


class JobType(Enum):
    THREAD_MESSAGE = "thread_message"
    ORCHESTRATION = "orchestration"


class AgentJob(BaseModel):
    id: str
    job_type: JobType

    def to_json(self) -> str:
        """Convert AgentJob to JSON string"""
        return self.model_dump_json()


class AgentJobQueue(ABC):
    """Minimal queue abstraction - just push jobs"""

    @abstractmethod
    async def push(self, job: AgentJob) -> None:
        """Push job to queue"""
        pass
