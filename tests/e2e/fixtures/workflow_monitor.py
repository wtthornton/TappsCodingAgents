"""
Workflow monitoring utilities for E2E tests.

Provides real-time progress monitoring, activity detection, and hang detection
for workflow execution in e2e tests.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from tapps_agents.workflow.event_log import WorkflowEvent
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.models import WorkflowState
from tapps_agents.workflow.observer import WorkflowObserver
from tapps_agents.workflow.progress_monitor import (
    WorkflowProgressMonitor,
)

logger = logging.getLogger(__name__)


@dataclass
class ActivitySnapshot:
    """Snapshot of workflow activity at a point in time."""

    timestamp: datetime
    step_id: str | None
    agent: str | None
    action: str | None
    status: str
    progress_percentage: float
    completed_steps: int
    total_steps: int
    elapsed_seconds: float | None
    artifacts_count: int
    state_changed: bool = False
    file_activity: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "step_id": self.step_id,
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "progress_percentage": round(self.progress_percentage, 2),
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "elapsed_seconds": round(self.elapsed_seconds, 2) if self.elapsed_seconds else None,
            "artifacts_count": self.artifacts_count,
            "state_changed": self.state_changed,
            "file_activity": self.file_activity,
        }


@dataclass
class HangDetectionConfig:
    """Configuration for hang detection."""

    max_seconds_without_activity: float = 60.0
    max_seconds_without_progress: float = 120.0
    max_seconds_total: float = 600.0
    check_interval_seconds: float = 5.0


@dataclass
class MonitoringConfig:
    """Configuration for workflow monitoring."""

    hang_config: HangDetectionConfig
    progress_callback: Callable[[ActivitySnapshot], None] | None = None
    enable_hang_detection: bool = True
    enable_progress_tracking: bool = True


class BaseWorkflowObserver(WorkflowObserver):
    """
    Base class for workflow observers with helper methods.
    
    Provides filtering and event tracking for test observers.
    """

    def __init__(self):
        """Initialize base observer."""
        self.observed_events: list[WorkflowEvent] = []

    def on_workflow_start(self, event: WorkflowEvent) -> None:
        """Called when workflow starts."""
        self.observed_events.append(event)

    def on_workflow_end(self, event: WorkflowEvent) -> None:
        """Called when workflow ends."""
        self.observed_events.append(event)

    def on_step_start(self, event: WorkflowEvent) -> None:
        """Called when a step starts."""
        self.observed_events.append(event)

    def on_step_complete(self, event: WorkflowEvent) -> None:
        """Called when a step completes successfully."""
        self.observed_events.append(event)

    def on_step_fail(self, event: WorkflowEvent) -> None:
        """Called when a step fails."""
        self.observed_events.append(event)

    def on_artifact_created(self, event: WorkflowEvent) -> None:
        """Called when an artifact is created."""
        self.observed_events.append(event)

    def should_observe(self, event: WorkflowEvent) -> bool:
        """
        Check if observer should process this event.
        
        Override in subclasses for custom filtering.
        """
        return True

    def get_observed_events(self) -> list[WorkflowEvent]:
        """Get all observed events."""
        return list(self.observed_events)

    def clear_events(self) -> None:
        """Clear observed events."""
        self.observed_events.clear()


class WorkflowActivityMonitor(BaseWorkflowObserver):
    """
    Monitors workflow activity for e2e tests.
    
    Tracks:
    - Progress updates (step completion, percentage)
    - State changes (status transitions, step changes)
    - Agent activity (which agent is active, what action)
    - File system activity (artifacts being created)
    - Hang detection (no activity for extended period)
    """

    def __init__(
        self,
        executor: WorkflowExecutor | None = None,
        project_path: Path | None = None,
        hang_config: HangDetectionConfig | None = None,
        progress_callback: Callable[[ActivitySnapshot], None] | None = None,
    ):
        """
        Initialize activity monitor.

        Args:
            executor: WorkflowExecutor instance to monitor (can be set later)
            project_path: Project path for file system monitoring
            hang_config: Configuration for hang detection
            progress_callback: Optional callback for progress updates
        """
        super().__init__()
        self.executor = executor
        self.project_path = project_path
        self.hang_config = hang_config or HangDetectionConfig()
        self.progress_callback = progress_callback

        self.snapshots: list[ActivitySnapshot] = []
        self.last_activity_time: datetime | None = None
        self.last_progress_time: datetime | None = None
        self.start_time: datetime | None = None
        self.last_artifact_count = 0
        self.last_completed_steps = 0
        self.last_state_hash: str | None = None

        # Note: Observer registration happens in workflow_runner when executor is created

    def on_workflow_start(self, event: WorkflowEvent) -> None:
        """Handle workflow start event."""
        super().on_workflow_start(event)
        self.start_time = event.timestamp
        self.last_activity_time = event.timestamp
        self.capture_snapshot()

    def on_workflow_end(self, event: WorkflowEvent) -> None:
        """Handle workflow end event."""
        super().on_workflow_end(event)
        self.capture_snapshot()

    def on_step_start(self, event: WorkflowEvent) -> None:
        """Handle step start event."""
        super().on_step_start(event)
        self.last_activity_time = event.timestamp
        self.capture_snapshot()

    def on_step_complete(self, event: WorkflowEvent) -> None:
        """Handle step complete event."""
        super().on_step_complete(event)
        self.last_activity_time = event.timestamp
        self.last_progress_time = event.timestamp
        self.capture_snapshot()

    def on_step_fail(self, event: WorkflowEvent) -> None:
        """Handle step fail event."""
        super().on_step_fail(event)
        self.last_activity_time = event.timestamp
        self.capture_snapshot()

    def on_artifact_created(self, event: WorkflowEvent) -> None:
        """Handle artifact created event."""
        super().on_artifact_created(event)
        self.last_activity_time = event.timestamp
        self.capture_snapshot()

    def wait_for_step(self, step_id: str, timeout: float = 60.0) -> bool:
        """
        Wait for a specific step to complete.

        Args:
            step_id: Step ID to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            True if step completed, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if step completed
            for event in self.observed_events:
                if (
                    event.event_type == "step_finish"
                    and event.step_id == step_id
                ):
                    return True
            time.sleep(0.1)
        return False

    def capture_snapshot(self) -> ActivitySnapshot:
        """
        Capture current activity snapshot.

        Returns:
            ActivitySnapshot with current state
        """
        if not self.executor or not self.executor.state or not self.executor.workflow:
            return ActivitySnapshot(
                timestamp=datetime.now(),
                step_id=None,
                agent=None,
                action=None,
                status="unknown",
                progress_percentage=0.0,
                completed_steps=0,
                total_steps=0,
                elapsed_seconds=None,
                artifacts_count=0,
            )

        state = self.executor.state
        workflow = self.executor.workflow

        # Use executor's progress monitor if available, otherwise create one
        if self.executor and self.executor.progress_monitor:
            metrics = self.executor.progress_monitor.get_progress()
        else:
            # Fallback: create progress monitor
            try:
                from tapps_agents.workflow.event_log import WorkflowEventLog
                event_log = WorkflowEventLog(Path("/tmp"))
            except ImportError:
                # Fallback: create a minimal event log-like object
                class MinimalEventLog:
                    def get_execution_history(self, workflow_id: str) -> dict[str, Any]:
                        return {}
                event_log = MinimalEventLog()
            
            progress_monitor = WorkflowProgressMonitor(workflow, state, event_log)
            metrics = progress_monitor.get_progress()

        # Get current step info
        current_step_id = state.current_step
        current_agent = None
        current_action = None
        if current_step_id:
            current_step = next((s for s in workflow.steps if s.id == current_step_id), None)
            if current_step:
                current_agent = current_step.agent
                current_action = current_step.action

        # Check for state changes
        state_hash = self._compute_state_hash(state)
        state_changed = state_hash != self.last_state_hash
        self.last_state_hash = state_hash

        # Check for file activity (artifact count change)
        artifact_count = len(state.artifacts)
        file_activity = artifact_count != self.last_artifact_count
        self.last_artifact_count = artifact_count

        # Check for progress (completed steps change)
        completed_steps = metrics.completed_steps
        progress_made = completed_steps != self.last_completed_steps
        self.last_completed_steps = completed_steps

        snapshot = ActivitySnapshot(
            timestamp=datetime.now(),
            step_id=current_step_id,
            agent=current_agent,
            action=current_action,
            status=state.status,
            progress_percentage=metrics.progress_percentage,
            completed_steps=completed_steps,
            total_steps=metrics.total_steps,
            elapsed_seconds=metrics.elapsed_seconds,
            artifacts_count=artifact_count,
            state_changed=state_changed,
            file_activity=file_activity,
        )

        self.snapshots.append(snapshot)

        # Update activity tracking
        if state_changed or file_activity or progress_made:
            self.last_activity_time = snapshot.timestamp
        if progress_made:
            self.last_progress_time = snapshot.timestamp

        # Initialize start time
        if self.start_time is None:
            self.start_time = snapshot.timestamp

        # Call progress callback if provided
        if self.progress_callback:
            try:
                self.progress_callback(snapshot)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

        return snapshot

    def _compute_state_hash(self, state: WorkflowState) -> str:
        """Compute a hash of workflow state for change detection."""
        # Simple hash based on key state attributes
        return f"{state.status}:{state.current_step}:{len(state.completed_steps)}:{len(state.artifacts)}"

    def check_for_hang(self) -> tuple[bool, str | None]:
        """
        Check if workflow appears to be hung.

        Returns:
            Tuple of (is_hung, reason)
        """
        if not self.snapshots:
            return False, None

        self.snapshots[-1]
        now = datetime.now()

        # Check total time
        if self.start_time:
            total_elapsed = (now - self.start_time).total_seconds()
            if total_elapsed > self.hang_config.max_seconds_total:
                return True, f"Total execution time exceeded {self.hang_config.max_seconds_total}s"

        # Check for no activity
        if self.last_activity_time:
            time_since_activity = (now - self.last_activity_time).total_seconds()
            if time_since_activity > self.hang_config.max_seconds_without_activity:
                return True, f"No activity for {time_since_activity:.1f}s (max: {self.hang_config.max_seconds_without_activity}s)"

        # Check for no progress
        if self.last_progress_time:
            time_since_progress = (now - self.last_progress_time).total_seconds()
            if time_since_progress > self.hang_config.max_seconds_without_progress:
                return True, f"No progress for {time_since_progress:.1f}s (max: {self.hang_config.max_seconds_without_progress}s)"

        return False, None

    def get_latest_activity(self) -> ActivitySnapshot | None:
        """Get the latest activity snapshot."""
        return self.snapshots[-1] if self.snapshots else None

    def get_activity_summary(self) -> dict[str, Any]:
        """
        Get summary of all activity.

        Returns:
            Dictionary with activity summary
        """
        if not self.snapshots:
            return {
                "snapshots": 0,
                "status": "no_activity",
                "total_activities": 0,
                "hang_detected": False,
            }

        latest = self.snapshots[-1]
        state_changes = sum(1 for s in self.snapshots if s.state_changed)
        file_activities = sum(1 for s in self.snapshots if s.file_activity)
        total_activities = len(self.observed_events)

        # Check for hang
        hang_detected, hang_reason = self.check_for_hang()

        return {
            "snapshots": len(self.snapshots),
            "status": latest.status,
            "current_step": latest.step_id,
            "current_agent": latest.agent,
            "progress_percentage": latest.progress_percentage,
            "completed_steps": latest.completed_steps,
            "total_steps": latest.total_steps,
            "elapsed_seconds": latest.elapsed_seconds,
            "artifacts_count": latest.artifacts_count,
            "state_changes": state_changes,
            "file_activities": file_activities,
            "total_activities": total_activities,
            "hang_detected": hang_detected,
            "hang_reason": hang_reason,
            "last_activity": self.last_activity_time.isoformat() if self.last_activity_time else None,
            "last_progress": self.last_progress_time.isoformat() if self.last_progress_time else None,
        }

    def format_progress_message(self, snapshot: ActivitySnapshot | None = None) -> str:
        """
        Format a human-readable progress message.

        Args:
            snapshot: Optional snapshot to format (uses latest if not provided)

        Returns:
            Formatted progress message
        """
        if snapshot is None:
            snapshot = self.get_latest_activity()

        if snapshot is None:
            return "No activity yet"

        parts = [
            f"Step {snapshot.completed_steps}/{snapshot.total_steps}",
            f"({snapshot.progress_percentage:.1f}%)",
        ]

        if snapshot.step_id:
            parts.append(f"- {snapshot.step_id}")
        if snapshot.agent:
            parts.append(f"[{snapshot.agent}]")
        if snapshot.action:
            parts.append(f"({snapshot.action})")

        if snapshot.elapsed_seconds:
            parts.append(f"- {snapshot.elapsed_seconds:.1f}s elapsed")

        return " ".join(parts)


def create_progress_logger_callback(logger_instance: logging.Logger | None = None) -> Callable[[ActivitySnapshot], None]:
    """
    Create a progress callback that logs to a logger.

    Args:
        logger_instance: Optional logger instance (uses module logger if not provided)

    Returns:
        Callback function
    """
    log = logger_instance or logger

    def callback(snapshot: ActivitySnapshot) -> None:
        message = (
            f"Progress: {snapshot.completed_steps}/{snapshot.total_steps} "
            f"({snapshot.progress_percentage:.1f}%) - "
            f"Step: {snapshot.step_id or 'none'}, "
            f"Agent: {snapshot.agent or 'none'}, "
            f"Status: {snapshot.status}"
        )
        log.info(message)

        if snapshot.state_changed:
            log.debug(f"State changed: {snapshot.step_id}")
        if snapshot.file_activity:
            log.debug(f"File activity: {snapshot.artifacts_count} artifacts")

    return callback


def create_progress_printer_callback(print_fn: Callable[[str], None] | None = None) -> Callable[[ActivitySnapshot], None]:
    """
    Create a progress callback that prints to console.

    Args:
        print_fn: Optional print function (uses built-in print if not provided)

    Returns:
        Callback function
    """
    printer = print_fn or print

    def callback(snapshot: ActivitySnapshot) -> None:
        message = (
            f"⏳ {snapshot.completed_steps}/{snapshot.total_steps} "
            f"({snapshot.progress_percentage:.1f}%) - "
            f"{snapshot.step_id or 'initializing'} "
            f"[{snapshot.agent or 'none'}]"
        )
        printer(message)

    return callback

