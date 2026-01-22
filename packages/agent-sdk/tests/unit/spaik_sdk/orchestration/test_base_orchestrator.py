from dataclasses import dataclass
from typing import AsyncIterator, List

import pytest

from spaik_sdk.orchestration import (
    BaseOrchestrator,
    InMemoryCheckpointProvider,
    OrchestratorEvent,
    StepStatus,
)


@dataclass
class CounterState:
    value: int
    history: List[str]

    def with_step(self, step_name: str) -> "CounterState":
        return CounterState(value=self.value + 1, history=[*self.history, step_name])


@dataclass
class CounterResult:
    final_value: int
    steps_run: List[str]


class CounterOrchestrator(BaseOrchestrator[CounterState, CounterResult]):
    """Simple orchestrator that counts steps for testing."""

    async def run(self) -> AsyncIterator[OrchestratorEvent[CounterResult]]:
        state = CounterState(value=0, history=[])

        async for event in self.step("step_a", "Step A", self.do_step_a, state):
            yield event
            if event.state:
                state = event.state

        async for event in self.step("step_b", "Step B", self.do_step_b, state):
            yield event
            if event.state:
                state = event.state

        async for event in self.step("step_c", "Step C", self.do_step_c, state):
            yield event
            if event.state:
                state = event.state

        yield self.ok(CounterResult(final_value=state.value, steps_run=state.history))

    async def do_step_a(self, state: CounterState) -> CounterState:
        return state.with_step("a")

    async def do_step_b(self, state: CounterState) -> CounterState:
        return state.with_step("b")

    async def do_step_c(self, state: CounterState) -> CounterState:
        return state.with_step("c")


class FailingOrchestrator(BaseOrchestrator[CounterState, CounterResult]):
    """Orchestrator that fails on step_b."""

    async def run(self) -> AsyncIterator[OrchestratorEvent[CounterResult]]:
        state = CounterState(value=0, history=[])

        async for event in self.step("step_a", "Step A", self.do_step_a, state):
            yield event
            if event.state:
                state = event.state

        async for event in self.step("step_b", "Step B (will fail)", self.do_step_b_fail, state):
            yield event
            if event.error:
                return  # Stop on error

        yield self.ok(CounterResult(final_value=state.value, steps_run=state.history))

    async def do_step_a(self, state: CounterState) -> CounterState:
        return state.with_step("a")

    async def do_step_b_fail(self, state: CounterState) -> CounterState:
        raise ValueError("Intentional failure in step_b")


@pytest.mark.unit
class TestBaseOrchestrator:
    @pytest.mark.asyncio
    async def test_full_run_emits_all_step_events(self):
        """Verify that running an orchestrator emits started/completed events for each step."""
        orchestrator = CounterOrchestrator()
        events: List[OrchestratorEvent[CounterResult]] = []

        async for event in orchestrator.run():
            events.append(event)

        # Extract step events
        step_events = [e for e in events if e.step is not None]

        # Should have 2 events per step (started + completed) = 6 total
        assert len(step_events) == 6

        # Check the sequence
        assert step_events[0].step.step_id == "step_a"
        assert step_events[0].step.status == StepStatus.RUNNING
        assert step_events[1].step.step_id == "step_a"
        assert step_events[1].step.status == StepStatus.COMPLETED

        assert step_events[2].step.step_id == "step_b"
        assert step_events[2].step.status == StepStatus.RUNNING
        assert step_events[3].step.step_id == "step_b"
        assert step_events[3].step.status == StepStatus.COMPLETED

        assert step_events[4].step.step_id == "step_c"
        assert step_events[4].step.status == StepStatus.RUNNING
        assert step_events[5].step.step_id == "step_c"
        assert step_events[5].step.status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_final_result_has_correct_state(self):
        """Verify the final result reflects all steps being run."""
        orchestrator = CounterOrchestrator()
        final_event = None

        async for event in orchestrator.run():
            if event.result is not None:
                final_event = event

        assert final_event is not None
        assert final_event.result.final_value == 3
        assert final_event.result.steps_run == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_step_failure_emits_failed_status_and_error(self):
        """Verify that a failing step emits FAILED status and error event."""
        orchestrator = FailingOrchestrator()
        events: List[OrchestratorEvent[CounterResult]] = []

        async for event in orchestrator.run():
            events.append(event)

        # Find step_b events
        step_b_events = [e for e in events if e.step and e.step.step_id == "step_b"]

        assert len(step_b_events) == 2
        assert step_b_events[0].step is not None
        assert step_b_events[0].step.status == StepStatus.RUNNING
        assert step_b_events[1].step is not None
        assert step_b_events[1].step.status == StepStatus.FAILED
        assert step_b_events[1].step.detail is not None
        assert "Intentional failure" in step_b_events[1].step.detail

        # Should also have an error event
        error_events = [e for e in events if e.error is not None]
        assert len(error_events) == 1
        assert error_events[0].error is not None
        assert "Intentional failure" in error_events[0].error

    def test_run_sync_returns_final_event(self):
        """Verify run_sync works and returns the final result."""
        orchestrator = CounterOrchestrator()
        result = orchestrator.run_sync()

        assert result.result is not None
        assert result.result.final_value == 3

    def test_run_sync_returns_error_on_failure(self):
        """Verify run_sync returns error event when orchestration fails."""
        orchestrator = FailingOrchestrator()
        result = orchestrator.run_sync()

        assert result.error is not None
        assert "Intentional failure" in result.error


@pytest.mark.unit
class TestCheckpointResume:
    @pytest.mark.asyncio
    async def test_checkpoint_saves_state_after_each_step(self):
        """Verify checkpoints are saved after each completed step."""
        checkpoint = InMemoryCheckpointProvider[CounterState]()
        orchestrator = CounterOrchestrator(checkpoint_provider=checkpoint)

        async for _ in orchestrator.run():
            pass

        # All three steps should be checkpointed
        assert checkpoint.get_completed_steps() == {"step_a", "step_b", "step_c"}

        # Each checkpoint should have correct cumulative state
        assert checkpoint.load("step_a").value == 1
        assert checkpoint.load("step_a").history == ["a"]

        assert checkpoint.load("step_b").value == 2
        assert checkpoint.load("step_b").history == ["a", "b"]

        assert checkpoint.load("step_c").value == 3
        assert checkpoint.load("step_c").history == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_resume_skips_completed_steps(self):
        """Verify resuming from checkpoint skips already-completed steps."""
        # First, run partially and save checkpoints
        checkpoint = InMemoryCheckpointProvider[CounterState]()
        orchestrator = CounterOrchestrator(checkpoint_provider=checkpoint)

        async for _ in orchestrator.run():
            pass

        # Now resume from step_b (should skip step_a and step_b)
        resumed_orchestrator = CounterOrchestrator(
            checkpoint_provider=checkpoint,
            resume_from="step_b",
        )

        events: List[OrchestratorEvent[CounterResult]] = []
        async for event in resumed_orchestrator.run():
            events.append(event)

        step_events = [e for e in events if e.step is not None]

        # step_a and step_b should be SKIPPED
        skipped = [e for e in step_events if e.step.status == StepStatus.SKIPPED]
        assert len(skipped) == 2
        assert {e.step.step_id for e in skipped} == {"step_a", "step_b"}

        # step_c should run normally
        step_c_events = [e for e in step_events if e.step.step_id == "step_c"]
        assert len(step_c_events) == 2
        assert step_c_events[0].step.status == StepStatus.RUNNING
        assert step_c_events[1].step.status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_resume_uses_checkpointed_state(self):
        """Verify resumed steps use state from checkpoint, not re-compute."""
        checkpoint = InMemoryCheckpointProvider[CounterState]()

        # Manually save a checkpoint with custom state
        checkpoint.save("step_a", CounterState(value=100, history=["custom_a"]))
        checkpoint.save("step_b", CounterState(value=200, history=["custom_a", "custom_b"]))

        resumed_orchestrator = CounterOrchestrator(
            checkpoint_provider=checkpoint,
            resume_from="step_b",
        )

        final_event = None
        async for event in resumed_orchestrator.run():
            if event.result is not None:
                final_event = event

        # step_c should build on the checkpointed state (value=200)
        assert final_event is not None
        assert final_event.result.final_value == 201
        assert final_event.result.steps_run == ["custom_a", "custom_b", "c"]


@pytest.mark.unit
class TestProgressEvents:
    @pytest.mark.asyncio
    async def test_progress_events_are_emitted(self):
        """Verify progress events work correctly."""

        class ProgressOrchestrator(BaseOrchestrator[None, str]):
            async def run(self) -> AsyncIterator[OrchestratorEvent[str]]:
                yield self.step_started("process", "Processing items")
                for i in range(5):
                    yield self.progress("process", i + 1, 5, f"Item {i + 1}")
                yield self.step_completed("process", "Processing items")
                yield self.ok("done")

        orchestrator = ProgressOrchestrator()
        events: List[OrchestratorEvent[str]] = []

        async for event in orchestrator.run():
            events.append(event)

        progress_events = [e for e in events if e.progress is not None]
        assert len(progress_events) == 5

        # Check progress values
        assert progress_events[0].progress.current == 1
        assert progress_events[0].progress.total == 5
        assert progress_events[0].progress.percent == 20.0

        assert progress_events[4].progress.current == 5
        assert progress_events[4].progress.total == 5
        assert progress_events[4].progress.percent == 100.0
