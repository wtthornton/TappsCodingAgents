"""
Unit tests for parallel workflow step execution.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.workflow.models import StepExecution, WorkflowStep
from tapps_agents.workflow.parallel_executor import (
    ParallelStepExecutor,
    StepExecutionResult,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_steps() -> list[WorkflowStep]:
    """Create sample workflow steps for testing."""
    return [
        WorkflowStep(
            id="step1",
            agent="analyst",
            action="gather",
            requires=[],
            creates=["artifact1"],
        ),
        WorkflowStep(
            id="step2",
            agent="planner",
            action="plan",
            requires=["artifact1"],
            creates=["artifact2"],
        ),
        WorkflowStep(
            id="step3",
            agent="implementer",
            action="write",
            requires=[],
            creates=["artifact3"],
        ),
    ]


@pytest.fixture
def sample_state() -> dict:
    """Create a minimal state-like dict for testing."""
    return {
        "step_executions": [],
        "artifacts": {},
    }


@pytest.mark.asyncio
async def test_execute_parallel_runs_steps_concurrently(sample_steps: list[WorkflowStep]) -> None:
    """Test that parallel executor runs independent steps concurrently."""
    executor = ParallelStepExecutor(max_parallel=8, default_timeout_seconds=10.0)

    execution_order: list[str] = []
    execution_times: dict[str, float] = {}

    async def mock_execute(step: WorkflowStep) -> dict:
        """Mock step execution that records timing."""
        start = asyncio.get_event_loop().time()
        execution_order.append(step.id)
        # Simulate work with different delays
        delay = {"step1": 0.1, "step2": 0.15, "step3": 0.1}.get(step.id, 0.1)
        await asyncio.sleep(delay)
        end = asyncio.get_event_loop().time()
        execution_times[step.id] = end - start
        return {"artifact": f"result-{step.id}"}

    # Execute step1 and step3 in parallel (both have no requirements)
    ready_steps = [sample_steps[0], sample_steps[2]]  # step1, step3

    class MockState:
        step_executions: list[StepExecution] = []

    state = MockState()

    results = await executor.execute_parallel(
        ready_steps,
        mock_execute,
        state=state,  # type: ignore[arg-type]
    )

    assert len(results) == 2
    assert all(r.step.id in ["step1", "step3"] for r in results)
    # Both should complete (concurrent execution means total time ~max of delays)
    total_time = max(execution_times.values())
    assert total_time < 0.3  # Should be ~0.15s (max delay), not 0.25s (sum)


@pytest.mark.asyncio
async def test_execute_parallel_handles_timeout(sample_steps: list[WorkflowStep]) -> None:
    """Test that parallel executor handles step timeouts."""
    executor = ParallelStepExecutor(max_parallel=8, default_timeout_seconds=0.1)

    async def slow_execute(step: WorkflowStep) -> dict:
        """Mock step that takes too long."""
        await asyncio.sleep(1.0)  # Longer than timeout
        return {"artifact": "result"}

    class MockState:
        step_executions: list[StepExecution] = []

    state = MockState()

    results = await executor.execute_parallel(
        [sample_steps[0]],
        slow_execute,
        state=state,  # type: ignore[arg-type]
        timeout_seconds=0.1,
    )

    assert len(results) == 1
    assert results[0].step_execution.status == "failed"
    assert "timed out" in results[0].step_execution.error.lower()
    assert results[0].error is not None


@pytest.mark.asyncio
async def test_execute_parallel_handles_exceptions(sample_steps: list[WorkflowStep]) -> None:
    """Test that parallel executor handles step exceptions."""
    executor = ParallelStepExecutor(max_parallel=8)

    async def failing_execute(step: WorkflowStep) -> dict:
        """Mock step that raises an exception."""
        raise ValueError(f"Step {step.id} failed")

    class MockState:
        step_executions: list[StepExecution] = []

    state = MockState()

    results = await executor.execute_parallel(
        [sample_steps[0]],
        failing_execute,
        state=state,  # type: ignore[arg-type]
    )

    assert len(results) == 1
    assert results[0].step_execution.status == "failed"
    assert "failed" in results[0].step_execution.error.lower()
    assert results[0].error is not None
    assert isinstance(results[0].error, ValueError)


@pytest.mark.asyncio
async def test_find_ready_steps_filters_by_dependencies(
    sample_steps: list[WorkflowStep],
) -> None:
    """Test that find_ready_steps only returns steps with met dependencies."""
    executor = ParallelStepExecutor()

    # Initially, only steps with no requirements should be ready
    ready = executor.find_ready_steps(
        sample_steps,
        completed_step_ids=set(),
        running_step_ids=set(),
        available_artifacts=set(),
    )
    assert len(ready) == 2  # step1 and step3 have no requirements
    assert all(s.id in ["step1", "step3"] for s in ready)

    # After step1 completes, step2 should become ready (step3 was already ready)
    ready = executor.find_ready_steps(
        sample_steps,
        completed_step_ids={"step1"},
        running_step_ids=set(),
        available_artifacts={"artifact1"},
    )
    assert len(ready) == 2  # step2 (now ready) and step3 (still ready, step1 already completed)
    assert all(s.id in ["step2", "step3"] for s in ready)


@pytest.mark.asyncio
async def test_execute_parallel_respects_max_parallel() -> None:
    """Test that parallel executor respects max_parallel limit."""
    executor = ParallelStepExecutor(max_parallel=2, default_timeout_seconds=10.0)

    concurrent_count = 0
    max_concurrent = 0
    lock = asyncio.Lock()

    async def counting_execute(step: WorkflowStep) -> dict:
        """Mock step that tracks concurrent execution."""
        nonlocal concurrent_count, max_concurrent
        async with lock:
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)

        await asyncio.sleep(0.1)  # Simulate work

        async with lock:
            concurrent_count -= 1

        return {"artifact": f"result-{step.id}"}

    # Create 5 steps
    steps = [
        WorkflowStep(id=f"step{i}", agent="test", action="test", requires=[])
        for i in range(5)
    ]

    class MockState:
        step_executions: list[StepExecution] = []

    state = MockState()

    await executor.execute_parallel(
        steps,
        counting_execute,
        state=state,  # type: ignore[arg-type]
    )

    # Should never exceed max_parallel=2
    assert max_concurrent <= 2
