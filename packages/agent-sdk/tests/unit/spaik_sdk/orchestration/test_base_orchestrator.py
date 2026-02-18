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

        # Check the sequence - extract steps with narrowing for type checker
        expected = [
            ("step_a", StepStatus.RUNNING),
            ("step_a", StepStatus.COMPLETED),
            ("step_b", StepStatus.RUNNING),
            ("step_b", StepStatus.COMPLETED),
            ("step_c", StepStatus.RUNNING),
            ("step_c", StepStatus.COMPLETED),
        ]
        for i, (expected_id, expected_status) in enumerate(expected):
            step = step_events[i].step
            assert step is not None
            assert step.step_id == expected_id
            assert step.status == expected_status

    @pytest.mark.asyncio
    async def test_final_result_has_correct_state(self):
        """Verify the final result reflects all steps being run."""
        orchestrator = CounterOrchestrator()
        final_event = None

        async for event in orchestrator.run():
            if event.result is not None:
                final_event = event

        assert final_event is not None
        result = final_event.result
        assert result is not None
        assert result.final_value == 3
        assert result.steps_run == ["a", "b", "c"]

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
        state_a = checkpoint.load("step_a")
        assert state_a is not None
        assert state_a.value == 1
        assert state_a.history == ["a"]

        state_b = checkpoint.load("step_b")
        assert state_b is not None
        assert state_b.value == 2
        assert state_b.history == ["a", "b"]

        state_c = checkpoint.load("step_c")
        assert state_c is not None
        assert state_c.value == 3
        assert state_c.history == ["a", "b", "c"]

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
        skipped_ids = set()
        for e in step_events:
            step = e.step
            assert step is not None
            if step.status == StepStatus.SKIPPED:
                skipped_ids.add(step.step_id)
        assert skipped_ids == {"step_a", "step_b"}

        # step_c should run normally
        step_c_events = [e for e in step_events if e.step is not None and e.step.step_id == "step_c"]
        assert len(step_c_events) == 2
        step_c_0 = step_c_events[0].step
        step_c_1 = step_c_events[1].step
        assert step_c_0 is not None
        assert step_c_1 is not None
        assert step_c_0.status == StepStatus.RUNNING
        assert step_c_1.status == StepStatus.COMPLETED

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
        result = final_event.result
        assert result is not None
        assert result.final_value == 201
        assert result.steps_run == ["custom_a", "custom_b", "c"]


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
        first_progress = progress_events[0].progress
        assert first_progress is not None
        assert first_progress.current == 1
        assert first_progress.total == 5
        assert first_progress.percent == 20.0

        last_progress = progress_events[4].progress
        assert last_progress is not None
        assert last_progress.current == 5
        assert last_progress.total == 5
        assert last_progress.percent == 100.0
