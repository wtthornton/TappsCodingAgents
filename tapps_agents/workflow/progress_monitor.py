"""
Workflow Progress Monitoring

Provides real-time progress tracking and reporting for workflow execution.
Epic 5 / Story 5.5: Standard Workflow Templates & Progress Monitoring
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .event_log import WorkflowEventLog
from .models import Workflow, WorkflowState


@dataclass
class ProgressMetrics:
    """Progress metrics for a workflow."""

    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    running_steps: int
    progress_percentage: float
    elapsed_seconds: float | None = None
    estimated_remaining_seconds: float | None = None
    current_step_id: str | None = None
    current_agent: str | None = None
    current_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "running_steps": self.running_steps,
            "progress_percentage": round(self.progress_percentage, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 2) if self.elapsed_seconds else None,
            "estimated_remaining_seconds": (
                round(self.estimated_remaining_seconds, 2)
                if self.estimated_remaining_seconds
                else None
            ),
            "current_step_id": self.current_step_id,
            "current_agent": self.current_agent,
            "current_action": self.current_action,
        }


class WorkflowProgressMonitor:
    """Monitors and reports workflow execution progress."""

    def __init__(self, workflow: Workflow, state: WorkflowState, event_log: WorkflowEventLog):
        """
        Initialize progress monitor.

        Args:
            workflow: Workflow definition
            state: Current workflow state
            event_log: Event log for additional metrics
        """
        self.workflow = workflow
        self.state = state
        self.event_log = event_log

    def get_progress(self) -> ProgressMetrics:
        """
        Calculate current progress metrics.

        Returns:
            ProgressMetrics with current progress information
        """
        total_steps = len(self.workflow.steps)
        completed_steps = len(self.state.completed_steps)
        skipped_steps = len(self.state.skipped_steps)
        failed_steps = sum(
            1
            for exec in self.state.step_executions
            if exec.status == "failed"
        )
        running_steps = sum(
            1
            for exec in self.state.step_executions
            if exec.status == "running"
        )

        # Calculate progress percentage
        if total_steps > 0:
            progress_percentage = (
                (completed_steps + skipped_steps) / total_steps
            ) * 100.0
        else:
            progress_percentage = 0.0

        # Calculate elapsed time
        elapsed_seconds = None
        if self.state.started_at:
            elapsed_seconds = (datetime.now() - self.state.started_at).total_seconds()

        # Estimate remaining time (simple average-based estimation)
        estimated_remaining_seconds = None
        if completed_steps > 0 and elapsed_seconds:
            avg_time_per_step = elapsed_seconds / completed_steps
            remaining_steps = total_steps - completed_steps - skipped_steps
            estimated_remaining_seconds = avg_time_per_step * remaining_steps

        # Get current step information
        current_step_id = self.state.current_step
        current_agent = None
        current_action = None
        if current_step_id:
            current_step = next(
                (s for s in self.workflow.steps if s.id == current_step_id), None
            )
            if current_step:
                current_agent = current_step.agent
                current_action = current_step.action

        return ProgressMetrics(
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            running_steps=running_steps,
            progress_percentage=progress_percentage,
            elapsed_seconds=elapsed_seconds,
            estimated_remaining_seconds=estimated_remaining_seconds,
            current_step_id=current_step_id,
            current_agent=current_agent,
            current_action=current_action,
        )

    def get_progress_report(self) -> dict[str, Any]:
        """
        Generate a comprehensive progress report.

        Returns:
            Dictionary with progress information and recommendations
        """
        metrics = self.get_progress()
        history = self.event_log.get_execution_history(self.state.workflow_id)

        # Determine status
        status = self.state.status
        if status == "running" and metrics.failed_steps > 0:
            status = "degraded"

        # Generate recommendations
        recommendations = []
        if metrics.progress_percentage < 10 and metrics.elapsed_seconds and metrics.elapsed_seconds > 300:
            recommendations.append("Workflow is taking longer than expected. Consider checking dependencies.")
        if metrics.failed_steps > 0:
            recommendations.append(f"{metrics.failed_steps} step(s) have failed. Review error logs.")
        if metrics.running_steps > 5:
            recommendations.append("Many steps running in parallel. Monitor resource usage.")

        return {
            "workflow_id": self.state.workflow_id,
            "workflow_name": self.workflow.name,
            "status": status,
            "metrics": metrics.to_dict(),
            "history": {
                "duration_seconds": history.get("duration_seconds"),
                "total_events": history.get("total_events", 0),
                "step_count": history.get("step_count", 0),
            },
            "recommendations": recommendations,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }

    def format_progress_bar(self, width: int = 40) -> str:
        """
        Format a text-based progress bar.

        Args:
            width: Width of the progress bar in characters

        Returns:
            Formatted progress bar string
        """
        metrics = self.get_progress()
        filled = int((metrics.progress_percentage / 100.0) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {metrics.progress_percentage:.1f}%"
