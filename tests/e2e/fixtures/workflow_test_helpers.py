"""
Workflow Test Helpers

Provides reusable utilities for common workflow testing patterns.
"""

import logging
from typing import Any, Callable

from tapps_agents.workflow.event_log import WorkflowEvent
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.observer import EventFilter, WorkflowObserver

from .workflow_monitor import MonitoringConfig, WorkflowActivityMonitor

logger = logging.getLogger(__name__)


class WorkflowTestHelper:
    """Static helper methods for workflow testing."""

    @staticmethod
    def setup_monitoring(
        executor: WorkflowExecutor,
        config: MonitoringConfig | None = None,
    ) -> WorkflowActivityMonitor:
        """
        Set up monitoring for a workflow executor.

        Args:
            executor: WorkflowExecutor instance
            config: Optional monitoring configuration

        Returns:
            WorkflowActivityMonitor instance
        """
        from .workflow_monitor import (
            HangDetectionConfig,
            create_progress_logger_callback,
        )

        if config is None:
            hang_config = HangDetectionConfig()
            progress_callback = create_progress_logger_callback(logger)
        else:
            hang_config = config.hang_config
            progress_callback = config.progress_callback

        monitor = WorkflowActivityMonitor(
            executor=executor,
            project_path=executor.project_root,
            hang_config=hang_config,
            progress_callback=progress_callback,
        )

        return monitor

    @staticmethod
    def register_custom_observer(
        executor: WorkflowExecutor, observer: WorkflowObserver
    ) -> None:
        """
        Register a custom observer on an executor.

        Args:
            executor: WorkflowExecutor instance
            observer: Observer to register
        """
        executor.register_observer(observer)

    @staticmethod
    async def wait_for_step(
        executor: WorkflowExecutor, step_id: str, timeout: float = 60.0
    ) -> bool:
        """
        Wait for a specific step to complete.

        Args:
            executor: WorkflowExecutor instance
            step_id: Step ID to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            True if step completed, False if timeout
        """
        import asyncio
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if not executor.state:
                await asyncio.sleep(0.1)
                continue

            # Check if step completed
            for execution in executor.state.step_executions:
                if execution.step_id == step_id and execution.status == "completed":
                    return True

            await asyncio.sleep(0.1)

        return False

    @staticmethod
    def assert_workflow_progress(
        executor: WorkflowExecutor,
        min_steps: int,
        min_percentage: float | None = None,
    ) -> None:
        """
        Assert that workflow has made minimum progress.

        Args:
            executor: WorkflowExecutor instance
            min_steps: Minimum number of completed steps
            min_percentage: Optional minimum progress percentage

        Raises:
            AssertionError: If progress doesn't meet requirements
        """
        if not executor.state:
            raise AssertionError("Workflow state not available")

        completed_steps = len(
            [e for e in executor.state.step_executions if e.status == "completed"]
        )

        if completed_steps < min_steps:
            raise AssertionError(
                f"Expected at least {min_steps} completed steps, got {completed_steps}"
            )

        if min_percentage is not None:
            progress = executor.get_current_progress()
            if not progress:
                raise AssertionError("Progress not available")
            if progress.progress_percentage < min_percentage:
                raise AssertionError(
                    f"Expected at least {min_percentage}% progress, got {progress.progress_percentage}%"
                )

    @staticmethod
    def get_step_events(
        monitor: WorkflowActivityMonitor, step_id: str
    ) -> list[WorkflowEvent]:
        """
        Get all events for a specific step.

        Args:
            monitor: WorkflowActivityMonitor instance
            step_id: Step ID to filter by

        Returns:
            List of events for the step
        """
        return [
            event
            for event in monitor.get_observed_events()
            if event.step_id == step_id
        ]

    @staticmethod
    def assert_step_completed(monitor: WorkflowActivityMonitor, step_id: str) -> None:
        """
        Assert that a specific step completed.

        Args:
            monitor: WorkflowActivityMonitor instance
            step_id: Step ID to check

        Raises:
            AssertionError: If step didn't complete
        """
        events = WorkflowTestHelper.get_step_events(monitor, step_id)
        completed_events = [
            e for e in events if e.event_type == "step_finish"
        ]

        if not completed_events:
            raise AssertionError(f"Step {step_id} did not complete")


# Factory functions for common observer patterns
def create_step_tracker_observer(step_ids: list[str]) -> WorkflowObserver:
    """
    Create an observer that tracks specific steps.

    Args:
        step_ids: List of step IDs to track

    Returns:
        WorkflowObserver that tracks specified steps
    """
    from .workflow_monitor import BaseWorkflowObserver

    class StepTrackerObserver(BaseWorkflowObserver):
        def __init__(self, tracked_steps: list[str]):
            super().__init__()
            self.tracked_steps = tracked_steps
            self.step_events: dict[str, list[WorkflowEvent]] = {
                step_id: [] for step_id in tracked_steps
            }

        def on_step_start(self, event: WorkflowEvent) -> None:
            super().on_step_start(event)
            if event.step_id in self.tracked_steps:
                self.step_events[event.step_id].append(event)

        def on_step_complete(self, event: WorkflowEvent) -> None:
            super().on_step_complete(event)
            if event.step_id in self.tracked_steps:
                self.step_events[event.step_id].append(event)

        def get_step_events(self, step_id: str) -> list[WorkflowEvent]:
            """Get events for a tracked step."""
            return self.step_events.get(step_id, [])

    return StepTrackerObserver(step_ids)


def create_artifact_tracker_observer(artifact_names: list[str]) -> WorkflowObserver:
    """
    Create an observer that tracks artifact creation.

    Args:
        artifact_names: List of artifact names to track

    Returns:
        WorkflowObserver that tracks artifact creation
    """
    from .workflow_monitor import BaseWorkflowObserver

    class ArtifactTrackerObserver(BaseWorkflowObserver):
        def __init__(self, tracked_artifacts: list[str]):
            super().__init__()
            self.tracked_artifacts = tracked_artifacts
            self.created_artifacts: set[str] = set()

        def on_artifact_created(self, event: WorkflowEvent) -> None:
            super().on_artifact_created(event)
            if event.artifacts:
                for art_name in event.artifacts.keys():
                    if art_name in self.tracked_artifacts:
                        self.created_artifacts.add(art_name)

        def has_artifact(self, artifact_name: str) -> bool:
            """Check if artifact was created."""
            return artifact_name in self.created_artifacts

    return ArtifactTrackerObserver(artifact_names)


def create_error_collector_observer() -> WorkflowObserver:
    """
    Create an observer that collects all errors.

    Returns:
        WorkflowObserver that collects errors
    """
    from .workflow_monitor import BaseWorkflowObserver

    class ErrorCollectorObserver(BaseWorkflowObserver):
        def __init__(self):
            super().__init__()
            self.errors: list[WorkflowEvent] = []

        def on_step_fail(self, event: WorkflowEvent) -> None:
            super().on_step_fail(event)
            self.errors.append(event)

        def get_errors(self) -> list[WorkflowEvent]:
            """Get all collected errors."""
            return list(self.errors)

    return ErrorCollectorObserver()


def create_progress_logger_observer(logger_instance: logging.Logger) -> WorkflowObserver:
    """
    Create an observer that logs progress to a logger.

    Args:
        logger_instance: Logger to use

    Returns:
        WorkflowObserver that logs progress
    """
    from .workflow_monitor import BaseWorkflowObserver

    class ProgressLoggerObserver(BaseWorkflowObserver):
        def __init__(self, log: logging.Logger):
            super().__init__()
            self.log = log

        def on_step_complete(self, event: WorkflowEvent) -> None:
            super().on_step_complete(event)
            self.log.info(
                f"Step completed: {event.step_id} [{event.agent}] ({event.action})"
            )

        def on_step_fail(self, event: WorkflowEvent) -> None:
            super().on_step_fail(event)
            self.log.error(
                f"Step failed: {event.step_id} [{event.agent}] - {event.error}"
            )

    return ProgressLoggerObserver(logger_instance)

