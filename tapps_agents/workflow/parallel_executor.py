"""
Parallel workflow step execution with bounded concurrency, timeouts, and cancellation.

Epic 1 / Story 1.3: Workflow Orchestration Agent Core
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, TypeVar

from .models import StepExecution, WorkflowStep, WorkflowState

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class StepExecutionResult:
    """Result of executing a single workflow step."""

    step: WorkflowStep
    step_execution: StepExecution
    artifacts: dict[str, Any] | None = None
    error: Exception | None = None


class ParallelStepExecutor:
    """
    Executes independent workflow steps in parallel with bounded concurrency.

    Features:
    - Bounded parallelism (max concurrent steps)
    - Per-step timeouts
    - Cancellation propagation
    - Deterministic state updates (ordered by step.id)
    """

    def __init__(
        self,
        max_parallel: int = 8,
        default_timeout_seconds: float | None = 3600.0,  # 1 hour default
    ):
        """
        Initialize parallel step executor.

        Args:
            max_parallel: Maximum number of steps to execute concurrently
            default_timeout_seconds: Default timeout per step (None = no timeout)
        """
        self.max_parallel = max_parallel
        self.default_timeout_seconds = default_timeout_seconds

    def find_ready_steps(
        self,
        workflow_steps: list[WorkflowStep],
        completed_step_ids: set[str],
        running_step_ids: set[str],
        available_artifacts: set[str] | None = None,
    ) -> list[WorkflowStep]:
        """
        Find steps that are ready to execute (dependencies met).

        Args:
            workflow_steps: All workflow steps
            completed_step_ids: Set of completed step IDs
            running_step_ids: Set of currently running step IDs
            available_artifacts: Set of available artifact names (from state.artifacts)
            Returns:
                List of steps ready to execute
        """
        ready: list[WorkflowStep] = []
        artifacts = available_artifacts or set()

        for step in workflow_steps:
            if step.id in completed_step_ids or step.id in running_step_ids:
                continue

            # Check if all required artifacts exist and are available
            if step.requires:
                all_met = all(req in artifacts for req in step.requires)
                if not all_met:
                    continue

            ready.append(step)

        return ready

    async def execute_parallel(
        self,
        steps: list[WorkflowStep],
        execute_fn: Callable[[WorkflowStep], Any],
        *,
        state: WorkflowState,
        timeout_seconds: float | None = None,
    ) -> list[StepExecutionResult]:
        """
        Execute multiple steps in parallel with bounded concurrency.

        Args:
            steps: Steps to execute in parallel
            execute_fn: Async function that executes a step and returns artifacts
            state: Workflow state (for recording step executions)
            timeout_seconds: Per-step timeout (uses default if None)

        Returns:
            List of execution results, ordered by step.id for determinism
        """
        if not steps:
            return []

        timeout = timeout_seconds or self.default_timeout_seconds
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(step: WorkflowStep) -> StepExecutionResult:
            """Execute a single step with semaphore and timeout."""
            step_execution = StepExecution(
                step_id=step.id,
                agent=step.agent or "",
                action=step.action or "",
                started_at=datetime.now(),
                status="running",
            )

            # Record start in state (thread-safe: we're in async context)
            state.step_executions.append(step_execution)

            async with semaphore:
                try:
                    if timeout:
                        artifacts = await asyncio.wait_for(
                            execute_fn(step), timeout=timeout
                        )
                    else:
                        artifacts = await execute_fn(step)

                    step_execution.completed_at = datetime.now()
                    step_execution.duration_seconds = (
                        step_execution.completed_at - step_execution.started_at
                    ).total_seconds()
                    step_execution.status = "completed"

                    return StepExecutionResult(
                        step=step,
                        step_execution=step_execution,
                        artifacts=artifacts,
                    )

                except asyncio.TimeoutError:
                    step_execution.completed_at = datetime.now()
                    step_execution.duration_seconds = (
                        step_execution.completed_at - step_execution.started_at
                    ).total_seconds()
                    step_execution.status = "failed"
                    step_execution.error = f"Step timed out after {timeout}s"

                    logger.warning(
                        f"Step {step.id} timed out after {timeout}s",
                        extra={
                            "workflow_id": state.workflow_id,
                            "step_id": step.id,
                            "agent": step.agent or "",
                            "action": step.action or "",
                            "timeout": timeout,
                        },
                    )

                    return StepExecutionResult(
                        step=step,
                        step_execution=step_execution,
                        error=asyncio.TimeoutError(f"Step {step.id} timed out"),
                    )

                except Exception as e:
                    step_execution.completed_at = datetime.now()
                    step_execution.duration_seconds = (
                        step_execution.completed_at - step_execution.started_at
                    ).total_seconds()
                    step_execution.status = "failed"
                    step_execution.error = str(e)

                    logger.error(
                        f"Step {step.id} failed: {e}",
                        exc_info=True,
                        extra={
                            "workflow_id": state.workflow_id,
                            "step_id": step.id,
                            "agent": step.agent or "",
                            "action": step.action or "",
                        },
                    )

                    return StepExecutionResult(
                        step=step,
                        step_execution=step_execution,
                        error=e,
                    )

        # Execute all steps concurrently with bounded concurrency
        # Use gather with return_exceptions=True to collect all results even if some fail
        tasks = [execute_with_semaphore(step) for step in steps]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results, handling both successes and exceptions
        results: list[StepExecutionResult] = []
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                # Task raised an exception
                failed_step = steps[i]
                logger.error(
                    f"Step {failed_step.id} raised exception: {result}",
                    exc_info=result,
                    extra={
                        "workflow_id": state.workflow_id,
                        "step_id": failed_step.id,
                        "agent": failed_step.agent or "",
                        "action": failed_step.action or "",
                    },
                )
                results.append(
                    StepExecutionResult(
                        step=failed_step,
                        step_execution=StepExecution(
                            step_id=failed_step.id,
                            agent=failed_step.agent or "",
                            action=failed_step.action or "",
                            started_at=datetime.now(),
                            completed_at=datetime.now(),
                            status="failed",
                            error=str(result),
                        ),
                        error=result,
                    )
                )
            else:
                # Task completed successfully (result is StepExecutionResult)
                results.append(result)

        # Sort by step.id for deterministic ordering
        results.sort(key=lambda r: r.step.id)

        return results
