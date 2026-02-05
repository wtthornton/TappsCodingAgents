"""
Workflow Summary and Completion Reporting

Generates comprehensive summaries when workflows complete.
Epic 8 / Story 8.5: Progress Summary and Completion
Progress Display Format: phase-grid layout when progress_display_format is 'phasegrid'.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.progress_display import generate_status_report
from .models import Workflow, WorkflowState
from .step_details import (
    calculate_step_duration,
    format_duration,
    get_step_status_emoji,
)
from .visual_feedback import VisualFeedbackGenerator


def workflow_state_to_phases(
    workflow: Workflow,
    state: WorkflowState,
) -> list[dict[str, Any]]:
    """
    Build a list of phase dicts for progress_display.generate_status_report.

    One phase per workflow step; percentage/status/icon from state and
    step_executions. Optional sub_items: duration, artifact count.

    Args:
        workflow: Workflow definition
        state: Current workflow state

    Returns:
        List of dicts with name, percentage, status, icon, optional sub_items
    """
    phases: list[dict[str, Any]] = []
    exec_by_step = {e.step_id: e for e in state.step_executions}

    for i, step in enumerate(workflow.steps):
        name = f"Phase {i}: {step.id}"
        exec_record = exec_by_step.get(step.id)
        sub_items: list[str] = []

        if exec_record:
            status_lower = (exec_record.status or "running").lower()
            if status_lower in ("completed", "skipped"):
                percentage = 100.0
                status_label = "COMPLETE" if status_lower == "completed" else "SKIPPED"
            elif status_lower == "failed":
                percentage = 100.0
                status_label = "FAILED"
            else:
                percentage = 0.0
                status_label = "IN PROGRESS"

            icon = get_step_status_emoji(exec_record.status)
            dur = calculate_step_duration(exec_record)
            if dur is not None:
                sub_items.append(f"Duration: {format_duration(dur)}")
        else:
            percentage = 0.0
            status_label = "PENDING"
            icon = "\u23f3"  # ⏳

        phase: dict[str, Any] = {
            "name": name,
            "percentage": percentage,
            "status": status_label,
            "icon": icon,
        }
        if sub_items:
            phase["sub_items"] = sub_items
        phases.append(phase)

    return phases


class WorkflowSummaryGenerator:
    """Generates workflow completion summaries."""

    def __init__(
        self,
        project_root: Path | None = None,
        enable_visual: bool = True,
        progress_display_format: str = "phasegrid",
        use_unicode_progress: bool = True,
    ):
        """
        Initialize summary generator.

        Args:
            project_root: Project root directory for relative paths
            enable_visual: Whether to enable visual enhancements (Epic 11)
            progress_display_format: 'phasegrid' (default) | 'legacy' | 'plain'. When
                'phasegrid' or 'plain', format_summary_for_chat includes the phase grid.
            use_unicode_progress: When False, use ASCII bars and icons (e.g. --progress plain)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.visual = VisualFeedbackGenerator(enable_visual=enable_visual)
        self.progress_display_format = progress_display_format
        self.use_unicode_progress = use_unicode_progress

    def generate_summary(
        self, workflow: Workflow, state: WorkflowState
    ) -> dict[str, Any]:
        """
        Generate comprehensive workflow summary.

        Args:
            workflow: Workflow definition
            state: Final workflow state

        Returns:
            Dictionary with summary information
        """
        # Determine final status
        status = self._determine_status(state)
        
        # Calculate execution time
        execution_time = self._calculate_execution_time(state)
        
        # Get step breakdown
        step_breakdown = self._get_step_breakdown(state)
        
        # Get artifact summary
        artifact_summary = self._get_artifact_summary(state)
        
        return {
            "workflow_id": state.workflow_id,
            "workflow_name": workflow.name,
            "status": status,
            "execution_time": execution_time,
            "step_breakdown": step_breakdown,
            "artifact_summary": artifact_summary,
            "error": state.error,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        }

    def format_summary_for_chat(
        self, workflow: Workflow, state: WorkflowState
    ) -> str:
        """
        Format summary as markdown for Cursor chat.

        When progress_display_format is 'homeiq' or 'plain', prepends the
        HomeIQ-style phase grid (Progress Summary) before the legacy block.

        Args:
            workflow: Workflow definition
            state: Final workflow state

        Returns:
            Formatted markdown string
        """
        summary = self.generate_summary(workflow, state)
        lines = []

        if self.progress_display_format in ("phasegrid", "plain"):
            phases = workflow_state_to_phases(workflow, state)
            use_unicode = self.use_unicode_progress and self.progress_display_format == "phasegrid"
            progress_block = generate_status_report(
                phases,
                title="Progress Summary",
                use_unicode=use_unicode,
                show_total=True,
            )
            lines.append(progress_block)
            lines.append("")

        # Header
        status_emoji = self._get_status_emoji(summary["status"])
        lines.append(f"## {status_emoji} Workflow Complete: {workflow.name}")
        lines.append("")

        # Status
        lines.append(f"**Status:** {summary['status'].upper()}")
        if summary.get("error"):
            lines.append(f"**Error:** {summary['error']}")
        lines.append("")

        # Execution time
        if summary["execution_time"]:
            lines.append(f"**Execution Time:** {summary['execution_time']}")
        lines.append("")

        # Step breakdown
        breakdown = summary["step_breakdown"]
        lines.append("### Step Summary")
        lines.append(
            f"- ✅ Completed: {breakdown['completed']}"
        )
        if breakdown["failed"] > 0:
            lines.append(f"- ❌ Failed: {breakdown['failed']}")
        if breakdown["skipped"] > 0:
            lines.append(f"- ⏭️ Skipped: {breakdown['skipped']}")
        lines.append(f"- 📊 Total: {breakdown['total']}")
        lines.append("")

        # Timeline (Epic 11: Timeline visualization)
        timeline = self.visual.format_timeline(state, workflow)
        if timeline:
            lines.append(timeline)
            lines.append("")

        # Artifacts (Epic 11: Visual artifact summary)
        artifacts = summary["artifact_summary"]
        if artifacts["count"] > 0:
            # Convert to Artifact objects for visual formatter
            artifact_list = []
            for item in artifacts["items"]:
                artifact_list.append({
                    "name": item["name"],
                    "path": item["path"],
                    "type": item.get("type", "other"),
                })
            
            artifact_summary = self.visual.format_artifact_summary(artifact_list)
            if artifact_summary:
                lines.append(artifact_summary)
                lines.append("")

        return "\n".join(lines)

    def _determine_status(self, state: WorkflowState) -> str:
        """Determine workflow status (success, partial, failed)."""
        if state.status == "failed":
            return "failed"
        
        failed_steps = sum(
            1 for exec in state.step_executions if exec.status == "failed"
        )
        if failed_steps > 0:
            return "partial"
        
        if state.status == "completed":
            return "success"
        
        return "unknown"

    def _calculate_execution_time(self, state: WorkflowState) -> str | None:
        """Calculate and format execution time."""
        if not state.started_at:
            return None
        
        end_time = state.completed_at or datetime.now()
        delta = end_time - state.started_at
        return format_duration(delta.total_seconds())

    def _get_step_breakdown(self, state: WorkflowState) -> dict[str, int]:
        """Get step completion breakdown."""
        completed = len(state.completed_steps)
        skipped = len(state.skipped_steps)
        failed = sum(
            1 for exec in state.step_executions if exec.status == "failed"
        )
        total = completed + skipped + failed
        
        return {
            "completed": completed,
            "skipped": skipped,
            "failed": failed,
            "total": total,
        }

    def _get_artifact_summary(
        self, state: WorkflowState
    ) -> dict[str, Any]:
        """Get artifact summary."""
        artifacts = list(state.artifacts.values())
        
        # Group by type (infer from extension)
        items = []
        for artifact in artifacts:
            path = Path(artifact.path)
            rel_path = self._get_relative_path(path)
            
            items.append({
                "name": artifact.name,
                "path": str(rel_path),
                "status": artifact.status,
                "type": path.suffix[1:] if path.suffix else "unknown",
            })
        
        return {
            "count": len(items),
            "items": items,
        }

    def _get_relative_path(self, path: Path) -> Path:
        """Get relative path from project root."""
        try:
            return path.relative_to(self.project_root)
        except ValueError:
            # Path is outside project root, return as-is
            return path

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for workflow status."""
        emoji_map = {
            "success": "✅",
            "partial": "⚠️",
            "failed": "❌",
            "unknown": "❓",
        }
        return emoji_map.get(status, "❓")

