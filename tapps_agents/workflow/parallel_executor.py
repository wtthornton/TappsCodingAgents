"""
Parallel workflow step execution with bounded concurrency, timeouts, and cancellation.

Epic 1 / Story 1.3: Workflow Orchestration Agent Core
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

from .models import StepExecution, WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for step retry behavior."""

    max_attempts: int = 1
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_errors: tuple[type[Exception], ...] = (Exception,)
    non_retryable_errors: tuple[type[Exception], ...] = ()

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """
        Determine if a step should be retried.

        Args:
            attempt: Current attempt number (1-indexed)
            error: Exception that occurred

        Returns:
            True if step should be retried
        """
        if attempt >= self.max_attempts:
            return False

        # Check if error is explicitly non-retryable
        if self.non_retryable_errors:
            if isinstance(error, self.non_retryable_errors):
                return False

        # Check if error is retryable
        if self.retryable_errors:
            return isinstance(error, self.retryable_errors)

        # Default: retry all errors if max_attempts > 1
        return self.max_attempts > 1

    def get_backoff_seconds(self, attempt: int) -> float:
        """
        Calculate backoff delay for a retry attempt.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Backoff delay in seconds
        """
        backoff = self.initial_backoff_seconds * (
            self.backoff_multiplier ** (attempt - 1)
        )
        return min(backoff, self.max_backoff_seconds)


@dataclass(frozen=True)
class StepExecutionResult:
    """Result of executing a single workflow step."""

    step: WorkflowStep
    step_execution: StepExecution
    artifacts: dict[str, Any] | None = None
    error: Exception | None = None
    attempts: int = 1


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
        default_retry_config: RetryConfig | None = None,
    ):
        """
        Initialize parallel step executor.

        Args:
            max_parallel: Maximum number of steps to execute concurrently
            default_timeout_seconds: Default timeout per step (None = no timeout)
            default_retry_config: Default retry configuration (no retries if None)
        """
        self.max_parallel = max_parallel
        self.default_timeout_seconds = default_timeout_seconds
        self.default_retry_config = default_retry_config or RetryConfig(max_attempts=1)

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

    def _get_retry_config(self, step: WorkflowStep) -> RetryConfig:
        """
        Get retry configuration for a step.

        Args:
            step: Workflow step

        Returns:
            Retry configuration (from step metadata or default)
        """
        # Check step metadata for retry configuration
        if step.metadata:
            retry_meta = step.metadata.get("retry", {})
            if retry_meta:
                return RetryConfig(
                    max_attempts=retry_meta.get("max_attempts", 1),
                    initial_backoff_seconds=retry_meta.get("initial_backoff_seconds", 1.0),
                    max_backoff_seconds=retry_meta.get("max_backoff_seconds", 60.0),
                    backoff_multiplier=retry_meta.get("backoff_multiplier", 2.0),
                )
        return self.default_retry_config

    async def execute_parallel(
        self,
        steps: list[WorkflowStep],
        execute_fn: Callable[[WorkflowStep], Any],
        *,
        state: WorkflowState,
        timeout_seconds: float | None = None,
    ) -> list[StepExecutionResult]:
        """
        Execute multiple steps in parallel with bounded concurrency and retries.

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

        async def execute_with_retries(step: WorkflowStep) -> StepExecutionResult:
            """Execute a single step with retries, semaphore, and timeout."""
            retry_config = self._get_retry_config(step)
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
                last_error: Exception | None = None
                attempts = 0

                while attempts < retry_config.max_attempts:
                    attempts += 1
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
                            attempts=attempts,
                        )

                    except TimeoutError as e:
                        last_error = e
                        # Use error envelope for structured error
                        from ..core.error_envelope import ErrorEnvelopeBuilder
                        envelope = ErrorEnvelopeBuilder.from_exception(
                            e,
                            workflow_id=state.workflow_id,
                            step_id=step.id,
                            agent=step.agent or "",
                        )
                        step_execution.error = envelope.to_user_message()

                        logger.warning(
                            f"Step {step.id} timed out after {timeout}s (attempt {attempts}/{retry_config.max_attempts})",
                            extra={
                                "workflow_id": state.workflow_id,
                                "step_id": step.id,
                                "agent": step.agent or "",
                                "action": step.action or "",
                                "timeout": timeout,
                                "attempt": attempts,
                            },
                        )

                        if not retry_config.should_retry(attempts, e):
                            break

                        # Wait before retry
                        backoff = retry_config.get_backoff_seconds(attempts)
                        await asyncio.sleep(backoff)
                        continue

                    except Exception as e:
                        last_error = e
                        # Use error envelope for structured error
                        from ..core.error_envelope import ErrorEnvelopeBuilder
                        envelope = ErrorEnvelopeBuilder.from_exception(
                            e,
                            workflow_id=state.workflow_id,
                            step_id=step.id,
                            agent=step.agent or "",
                        )
                        step_execution.error = envelope.to_user_message()

                        logger.error(
                            f"Step {step.id} failed: {e} (attempt {attempts}/{retry_config.max_attempts})",
                            exc_info=attempts == retry_config.max_attempts,  # Only log full trace on final attempt
                            extra={
                                "workflow_id": state.workflow_id,
                                "step_id": step.id,
                                "agent": step.agent or "",
                                "action": step.action or "",
                                "attempt": attempts,
                            },
                        )

                        if not retry_config.should_retry(attempts, e):
                            break

                        # Wait before retry
                        backoff = retry_config.get_backoff_seconds(attempts)
                        logger.info(
                            f"Retrying step {step.id} after {backoff:.2f}s (attempt {attempts + 1}/{retry_config.max_attempts})"
                        )
                        await asyncio.sleep(backoff)
                        continue

                # All retries exhausted
                step_execution.completed_at = datetime.now()
                step_execution.duration_seconds = (
                    step_execution.completed_at - step_execution.started_at
                ).total_seconds()
                step_execution.status = "failed"

                return StepExecutionResult(
                    step=step,
                    step_execution=step_execution,
                    error=last_error,
                    attempts=attempts,
                )

        # Execute all steps concurrently with bounded concurrency
        # Use gather with return_exceptions=True to collect all results even if some fail
        tasks = [execute_with_retries(step) for step in steps]
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
