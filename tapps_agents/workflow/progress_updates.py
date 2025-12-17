"""
Progress Update System for Real-Time Workflow Updates

Provides formatted progress updates for Cursor chat display during workflow execution.
Epic 8 / Story 8.1: Progress Update System Foundation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .models import WorkflowState
from .progress_monitor import ProgressMetrics, WorkflowProgressMonitor
from .visual_feedback import VisualFeedbackGenerator


class UpdateType(Enum):
    """Type of progress update."""

    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_STARTED = "workflow_started"


class UpdatePriority(Enum):
    """Update priority for queue management."""

    CRITICAL = "critical"  # Errors, completion
    HIGH = "high"  # Step transitions
    NORMAL = "normal"  # Routine progress
    LOW = "low"  # Periodic updates


@dataclass
class ProgressUpdate:
    """Progress update message structure."""

    update_type: UpdateType
    timestamp: datetime
    step_number: int | None = None
    total_steps: int | None = None
    percentage: float | None = None
    status: str | None = None
    message: str | None = None
    step_id: str | None = None
    agent: str | None = None
    action: str | None = None
    error: str | None = None
    priority: UpdatePriority = UpdatePriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "update_type": self.update_type.value,
            "timestamp": self.timestamp.isoformat(),
            "step_number": self.step_number,
            "total_steps": self.total_steps,
            "percentage": self.percentage,
            "status": self.status,
            "message": self.message,
            "step_id": self.step_id,
            "agent": self.agent,
            "action": self.action,
            "error": self.error,
            "priority": self.priority.value,
            "metadata": self.metadata,
        }


class ProgressCalculator:
    """Calculates progress metrics from workflow state."""

    def __init__(self, total_steps: int):
        """
        Initialize progress calculator.

        Args:
            total_steps: Total number of steps in the workflow
        """
        self.total_steps = total_steps

    def calculate_progress(
        self, state: WorkflowState
    ) -> dict[str, Any]:
        """
        Calculate progress from workflow state.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with progress metrics
        """
        completed = len(state.completed_steps)
        skipped = len(state.skipped_steps)
        failed = sum(
            1 for exec in state.step_executions if exec.status == "failed"
        )
        running = sum(
            1 for exec in state.step_executions if exec.status == "running"
        )

        # Calculate percentage
        if self.total_steps > 0:
            percentage = ((completed + skipped) / self.total_steps) * 100.0
        else:
            percentage = 0.0

        # Determine current step number
        current_step_number = None
        if state.current_step:
            # Find step index in workflow
            # Note: This assumes steps are ordered, which may not always be true
            # For now, we'll use completed steps count + 1 as approximation
            current_step_number = completed + running + 1

        return {
            "current_step": current_step_number,
            "total_steps": self.total_steps,
            "completed": completed,
            "skipped": skipped,
            "failed": failed,
            "running": running,
            "percentage": round(percentage, 2),
            "current_step_id": state.current_step,
        }


class ProgressUpdateGenerator:
    """Generates formatted progress updates for Cursor chat."""

    # Emoji mapping for status types
    STATUS_EMOJIS = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "skipped": "⏭️",
    }

    def __init__(self, calculator: ProgressCalculator, enable_visual: bool = True):
        """
        Initialize update generator.

        Args:
            calculator: Progress calculator instance
            enable_visual: Whether to enable visual enhancements (Epic 11)
        """
        self.calculator = calculator
        self.visual = VisualFeedbackGenerator(enable_visual=enable_visual)

    def generate_update(
        self,
        update_type: UpdateType,
        state: WorkflowState,
        step_id: str | None = None,
        agent: str | None = None,
        action: str | None = None,
        error: str | None = None,
        message: str | None = None,
    ) -> ProgressUpdate:
        """
        Generate a progress update.

        Args:
            update_type: Type of update
            state: Current workflow state
            step_id: Optional step ID
            agent: Optional agent name
            action: Optional action name
            error: Optional error message
            message: Optional custom message

        Returns:
            ProgressUpdate instance
        """
        progress = self.calculator.calculate_progress(state)

        # Determine priority
        priority = UpdatePriority.NORMAL
        if update_type in (
            UpdateType.WORKFLOW_COMPLETED,
            UpdateType.WORKFLOW_FAILED,
            UpdateType.STEP_FAILED,
        ):
            priority = UpdatePriority.CRITICAL
        elif update_type in (
            UpdateType.STEP_STARTED,
            UpdateType.STEP_COMPLETED,
        ):
            priority = UpdatePriority.HIGH

        # Determine status
        status = state.status
        if update_type == UpdateType.STEP_FAILED:
            status = "failed"
        elif update_type == UpdateType.STEP_COMPLETED:
            status = "completed"

        return ProgressUpdate(
            update_type=update_type,
            timestamp=datetime.now(),
            step_number=progress.get("current_step"),
            total_steps=progress.get("total_steps"),
            percentage=progress.get("percentage"),
            status=status,
            message=message,
            step_id=step_id or progress.get("current_step_id"),
            agent=agent,
            action=action,
            error=error,
            priority=priority,
        )

    def format_for_chat(self, update: ProgressUpdate) -> str:
        """
        Format update for Cursor chat display.

        Args:
            update: Progress update to format

        Returns:
            Formatted markdown string for chat
        """
        lines = []

        # Header based on update type
        if update.update_type == UpdateType.WORKFLOW_STARTED:
            lines.append("## 🚀 Workflow Started")
        elif update.update_type == UpdateType.WORKFLOW_COMPLETED:
            lines.append("## ✅ Workflow Completed")
        elif update.update_type == UpdateType.WORKFLOW_FAILED:
            lines.append("## ❌ Workflow Failed")
        elif update.update_type == UpdateType.STEP_STARTED:
            emoji = self.STATUS_EMOJIS.get("running", "🔄")
            lines.append(f"### {emoji} Step Started")
        elif update.update_type == UpdateType.STEP_COMPLETED:
            emoji = self.STATUS_EMOJIS.get("completed", "✅")
            lines.append(f"### {emoji} Step Completed")
        elif update.update_type == UpdateType.STEP_FAILED:
            emoji = self.STATUS_EMOJIS.get("failed", "❌")
            lines.append(f"### {emoji} Step Failed")
        else:
            lines.append("### 🔄 Progress Update")

        # Progress bar (Epic 11: Enhanced visual feedback)
        if update.percentage is not None:
            progress_bar = self.visual.format_progress_bar(update.percentage)
            lines.append(f"\n{progress_bar}\n")

        # Step information (Epic 11: Enhanced step indicators)
        if update.step_number and update.total_steps:
            step_indicator = self.visual.format_step_indicator(
                update.step_number, update.total_steps, update.step_id
            )
            if update.percentage is not None:
                lines.append(f"{step_indicator} ({update.percentage:.1f}% complete)")
            else:
                lines.append(step_indicator)

        # Step details (Epic 11: Status badges)
        if update.agent and update.action:
            status_badge = self.visual.format_status_badge(update.status or "running")
            lines.append(f"- **Status:** {status_badge}")
            lines.append(f"- **Agent:** {update.agent}")
            lines.append(f"- **Action:** {update.action}")

        if update.step_id:
            lines.append(f"- **Step ID:** `{update.step_id}`")

        # Error information
        if update.error:
            lines.append(f"\n**Error:** {update.error}")

        # Custom message
        if update.message:
            lines.append(f"\n{update.message}")

        return "\n".join(lines)

    def _generate_progress_bar(self, percentage: float, width: int = 30) -> str:
        """
        Generate text-based progress bar.

        Args:
            percentage: Completion percentage (0-100)
            width: Width of progress bar in characters

        Returns:
            Formatted progress bar string
        """
        filled = int((percentage / 100.0) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"`[{bar}] {percentage:.1f}%`"


class UpdateQueue:
    """Manages update frequency to prevent chat spam."""

    def __init__(
        self,
        min_interval_seconds: float = 2.0,
        max_updates_per_minute: int = 30,
    ):
        """
        Initialize update queue.

        Args:
            min_interval_seconds: Minimum time between updates
            max_updates_per_minute: Maximum updates per minute
        """
        self.min_interval = min_interval_seconds
        self.max_per_minute = max_updates_per_minute
        self.queue: list[ProgressUpdate] = []
        self.last_update_time: datetime | None = None
        self.update_times: list[datetime] = []

    def add_update(self, update: ProgressUpdate) -> bool:
        """
        Add update to queue and determine if it should be sent.

        Args:
            update: Progress update to queue

        Returns:
            True if update should be sent immediately, False if queued
        """
        now = datetime.now()

        # Critical updates always sent immediately
        if update.priority == UpdatePriority.CRITICAL:
            self._record_update(now)
            return True

        # Check minimum interval
        if (
            self.last_update_time
            and (now - self.last_update_time).total_seconds() < self.min_interval
        ):
            # Queue for later unless high priority
            if update.priority == UpdatePriority.HIGH:
                # High priority can bypass interval but still check rate limit
                if self._check_rate_limit(now):
                    self._record_update(now)
                    return True
            # Always queue if interval not met (for normal/low priority)
            self.queue.append(update)
            return False

        # Check rate limit
        if not self._check_rate_limit(now):
            self.queue.append(update)
            return False

        # Update can be sent
        self._record_update(now)
        return True

    def get_queued_updates(self) -> list[ProgressUpdate]:
        """
        Get updates that should be sent now.

        Returns:
            List of updates to send
        """
        if not self.queue:
            return []

        now = datetime.now()
        updates_to_send: list[ProgressUpdate] = []

        # Check if we can send queued updates
        if (
            not self.last_update_time
            or (now - self.last_update_time).total_seconds() >= self.min_interval
        ):
            if self._check_rate_limit(now):
                # Send highest priority update from queue
                self.queue.sort(
                    key=lambda u: (
                        UpdatePriority.CRITICAL.value,
                        UpdatePriority.HIGH.value,
                        UpdatePriority.NORMAL.value,
                        UpdatePriority.LOW.value,
                    ).index(u.priority.value)
                )
                if self.queue:
                    update = self.queue.pop(0)
                    updates_to_send.append(update)
                    self._record_update(now)

        return updates_to_send

    def flush_queue(self) -> list[ProgressUpdate]:
        """
        Flush all queued updates (for completion/error states).

        Returns:
            List of all queued updates
        """
        updates = self.queue.copy()
        self.queue.clear()
        return updates

    def _check_rate_limit(self, now: datetime) -> bool:
        """Check if we're within rate limits."""
        # Remove updates older than 1 minute
        cutoff = now.timestamp() - 60
        self.update_times = [
            t for t in self.update_times if t.timestamp() > cutoff
        ]

        return len(self.update_times) < self.max_per_minute

    def _record_update(self, timestamp: datetime) -> None:
        """Record that an update was sent."""
        self.last_update_time = timestamp
        self.update_times.append(timestamp)

