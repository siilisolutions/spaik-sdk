import asyncio
from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
)

from spaik_sdk.orchestration.checkpoint import CheckpointProvider
from spaik_sdk.orchestration.models import OrchestratorEvent
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)

T_State = TypeVar("T_State")
T_Result = TypeVar("T_Result")


class BaseOrchestrator(ABC, Generic[T_State, T_Result]):
    """
    Code-first orchestration without graph DSLs.

    Subclass this and implement `run()` to define your orchestration logic.
    Use `step()` to execute steps with automatic status emission and optional checkpointing.

    Example:
        class MyOrchestrator(BaseOrchestrator[MyState, MyResult]):
            async def run(self) -> AsyncIterator[OrchestratorEvent[MyResult]]:
                state = MyState(items=[])

                # Run a step - yields status events automatically
                async for event in self.step("fetch", "Fetching data", self.fetch_data, state):
                    yield event
                    if event.result:
                        state = event.result

                # Emit progress during processing
                for i, item in enumerate(state.items):
                    yield self.progress("process", i + 1, len(state.items))
                    await self.process_item(item)

                yield self.ok(MyResult(processed=len(state.items)))

            async def fetch_data(self, state: MyState) -> MyState:
                # Your logic here
                return state.copy(items=fetched_items)
    """

    def __init__(
        self,
        checkpoint_provider: Optional[CheckpointProvider[T_State]] = None,
        resume_from: Optional[str] = None,
    ) -> None:
        """
        Args:
            checkpoint_provider: Optional provider for state persistence.
                                 If None, no checkpointing is performed.
            resume_from: Step ID to resume from. Steps up to and including
                        this ID will be skipped, using checkpointed state.
        """
        self.checkpoint_provider = checkpoint_provider
        self.resume_from = resume_from
        self._completed_steps: set[str] = set()
        self._passed_resume_point = False

        if resume_from is not None:
            logger.info(f"Will resume after step '{resume_from}'")

    @abstractmethod
    def run(self) -> AsyncIterator[OrchestratorEvent[T_Result]]:
        """
        Implement your orchestration logic here.

        Yield OrchestratorEvent instances to emit status updates, progress,
        messages, and the final result.
        """
        ...

    def run_sync(self) -> OrchestratorEvent[T_Result]:
        """
        Run the orchestration synchronously and return the final event.

        Returns the last event emitted (typically result or error).
        """

        async def _runner() -> OrchestratorEvent[T_Result]:
            last_event: Optional[OrchestratorEvent[T_Result]] = None
            async for event in self.run():
                last_event = event
                if event.is_terminal():
                    return event
            if last_event is None:
                return self.fail("No events emitted during orchestration")
            return last_event

        return asyncio.run(_runner())

    async def step(
        self,
        step_id: str,
        name: str,
        fn: Union[
            Callable[[T_State], T_State],
            Callable[[T_State], Awaitable[T_State]],
        ],
        state: T_State,
    ) -> AsyncIterator[OrchestratorEvent[T_State]]:
        """
        Execute a step with automatic status emission and checkpointing.

        Yields:
            - step_started event
            - step_completed/step_failed event
            - result event with new state (or error event on failure)

        If resuming and this step was already completed, yields step_skipped
        and the checkpointed state instead.
        """
        if self._should_skip(step_id):
            yield OrchestratorEvent.step_skipped(step_id, name, "Resumed from checkpoint")
            loaded_state = self._load_checkpoint(step_id)
            if loaded_state is not None:
                yield OrchestratorEvent.state_update(loaded_state)
            else:
                yield OrchestratorEvent.fail(f"Checkpoint not found for step '{step_id}'")
            return

        yield OrchestratorEvent.step_started(step_id, name)

        try:
            result = fn(state)
            if asyncio.iscoroutine(result):
                new_state = await result
            else:
                new_state = result

            self._save_checkpoint(step_id, new_state)
            self._completed_steps.add(step_id)

            yield OrchestratorEvent.step_completed(step_id, name)
            yield OrchestratorEvent.state_update(new_state)

        except Exception as e:
            logger.exception(f"Step '{step_id}' failed")
            yield OrchestratorEvent.step_failed(step_id, name, str(e))
            yield OrchestratorEvent.fail(str(e))

    # --- Convenience factory methods ---

    def ok(self, result: T_Result) -> OrchestratorEvent[T_Result]:
        """Create a success result event"""
        return OrchestratorEvent.ok(result)

    def fail(self, error: str) -> OrchestratorEvent[T_Result]:
        """Create an error event"""
        return OrchestratorEvent.fail(error)

    def msg(self, message: str) -> OrchestratorEvent[T_Result]:
        """Create a message event"""
        return OrchestratorEvent.msg(message)

    def progress(self, step_id: str, current: int, total: int, detail: Optional[str] = None) -> OrchestratorEvent[T_Result]:
        """Create a progress update event"""
        return OrchestratorEvent.progress_update(step_id, current, total, detail)

    def step_started(self, step_id: str, name: str, detail: Optional[str] = None) -> OrchestratorEvent[T_Result]:
        """Create a step started event (for manual step management)"""
        return OrchestratorEvent.step_started(step_id, name, detail)

    def step_completed(self, step_id: str, name: str, detail: Optional[str] = None) -> OrchestratorEvent[T_Result]:
        """Create a step completed event (for manual step management)"""
        return OrchestratorEvent.step_completed(step_id, name, detail)

    def step_failed(self, step_id: str, name: str, error: str) -> OrchestratorEvent[T_Result]:
        """Create a step failed event (for manual step management)"""
        return OrchestratorEvent.step_failed(step_id, name, error)

    # --- Internal helpers ---

    def _should_skip(self, step_id: str) -> bool:
        """Check if a step should be skipped due to checkpoint resume"""
        if self.resume_from is None:
            return False
        if self._passed_resume_point:
            return False
        # We skip until we hit the resume_from step, then skip that one too
        if step_id == self.resume_from:
            self._passed_resume_point = True
        return True

    def _load_checkpoint(self, step_id: str) -> Optional[T_State]:
        """Load checkpointed state for a step"""
        if self.checkpoint_provider is None:
            return None
        return self.checkpoint_provider.load(step_id)

    def _save_checkpoint(self, step_id: str, state: T_State) -> None:
        """Save state to checkpoint after step completion"""
        if self.checkpoint_provider is None:
            return
        self.checkpoint_provider.save(step_id, state)
        logger.debug(f"Saved checkpoint for step '{step_id}'")


class SimpleOrchestrator(BaseOrchestrator[None, T_Result]):
    """
    Orchestrator without state management.

    Use this when you don't need to pass state between steps,
    or when steps manage their own state internally.
    """

    async def run_step(
        self,
        step_id: str,
        name: str,
        fn: Union[Callable[[], Any], Callable[[], Awaitable[Any]]],
    ) -> AsyncIterator[OrchestratorEvent[Any]]:
        """Execute a step without state management"""
        yield OrchestratorEvent.step_started(step_id, name)

        try:
            result = fn()
            if asyncio.iscoroutine(result):
                await result

            self._completed_steps.add(step_id)
            yield OrchestratorEvent.step_completed(step_id, name)

        except Exception as e:
            logger.exception(f"Step '{step_id}' failed")
            yield OrchestratorEvent.step_failed(step_id, name, str(e))
            yield OrchestratorEvent.fail(str(e))
