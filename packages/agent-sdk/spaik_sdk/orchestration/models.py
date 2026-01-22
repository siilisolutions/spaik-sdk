from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class StepStatus(Enum):
    """Status of an orchestration step"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepInfo:
    """Information about a step's current state"""

    step_id: str
    name: str
    status: StepStatus
    detail: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorEvent(Generic[T]):
    """
    Event emitted during orchestration.

    This is a union-style dataclass - only one field should be set at a time.
    Use the factory methods for cleaner construction.

    Note: `state` is for intermediate step outputs, `result` is for final orchestration result.
    """

    step: Optional[StepInfo] = None
    message: Optional[str] = None
    progress: Optional["ProgressUpdate"] = None
    state: Optional[T] = None  # Intermediate state from steps
    result: Optional[T] = None  # Final result
    error: Optional[str] = None

    @staticmethod
    def step_started(step_id: str, name: str, detail: Optional[str] = None) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(step=StepInfo(step_id, name, StepStatus.RUNNING, detail))

    @staticmethod
    def step_completed(step_id: str, name: str, detail: Optional[str] = None) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(step=StepInfo(step_id, name, StepStatus.COMPLETED, detail))

    @staticmethod
    def step_failed(step_id: str, name: str, error: str) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(step=StepInfo(step_id, name, StepStatus.FAILED, error))

    @staticmethod
    def step_skipped(step_id: str, name: str, reason: Optional[str] = None) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(step=StepInfo(step_id, name, StepStatus.SKIPPED, reason))

    @staticmethod
    def msg(message: str) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(message=message)

    @staticmethod
    def state_update(state: T) -> "OrchestratorEvent[Any]":
        """Emit intermediate state from a step"""
        return OrchestratorEvent(state=state)

    @staticmethod
    def ok(result: T) -> "OrchestratorEvent[Any]":
        """Emit final result"""
        return OrchestratorEvent(result=result)

    @staticmethod
    def fail(error: str) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(error=error)

    @staticmethod
    def progress_update(step_id: str, current: int, total: int, detail: Optional[str] = None) -> "OrchestratorEvent[Any]":
        return OrchestratorEvent(progress=ProgressUpdate(step_id, current, total, detail))

    def is_terminal(self) -> bool:
        """Returns True if this event represents a final state (result or error)"""
        return self.result is not None or self.error is not None


@dataclass
class ProgressUpdate:
    """Progress within a step (e.g., processing item 3/10)"""

    step_id: str
    current: int
    total: int
    detail: Optional[str] = None

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
