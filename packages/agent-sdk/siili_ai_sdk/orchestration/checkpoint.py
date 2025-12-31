from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

T_State = TypeVar("T_State")


class CheckpointProvider(ABC, Generic[T_State]):
    """
    Protocol for checkpoint storage/retrieval.

    Implement this to add persistence for orchestration state.
    The orchestrator will call these methods automatically during step execution.
    """

    @abstractmethod
    def save(self, step_id: str, state: T_State) -> None:
        """Save state after a step completes"""
        pass

    @abstractmethod
    def load(self, step_id: str) -> Optional[T_State]:
        """Load state for a specific step. Returns None if not found."""
        pass

    @abstractmethod
    def get_completed_steps(self) -> set[str]:
        """Get all step IDs that have been completed"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all checkpoints"""
        pass


class InMemoryCheckpointProvider(CheckpointProvider[T_State]):
    """Simple in-memory checkpoint provider for testing/development"""

    def __init__(self) -> None:
        self._checkpoints: Dict[str, T_State] = {}

    def save(self, step_id: str, state: T_State) -> None:
        self._checkpoints[step_id] = state

    def load(self, step_id: str) -> Optional[T_State]:
        return self._checkpoints.get(step_id)

    def get_completed_steps(self) -> set[str]:
        return set(self._checkpoints.keys())

    def clear(self) -> None:
        self._checkpoints.clear()


class DictCheckpointProvider(CheckpointProvider[Dict[str, Any]]):
    """
    Checkpoint provider that serializes state as dicts.

    Useful when you want to persist to JSON/database but your state
    objects have to_dict()/from_dict() methods.
    """

    def __init__(self, storage: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self._storage = storage if storage is not None else {}

    def save(self, step_id: str, state: Dict[str, Any]) -> None:
        self._storage[step_id] = state

    def load(self, step_id: str) -> Optional[Dict[str, Any]]:
        return self._storage.get(step_id)

    def get_completed_steps(self) -> set[str]:
        return set(self._storage.keys())

    def clear(self) -> None:
        self._storage.clear()

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored checkpoints (for serialization)"""
        return dict(self._storage)
