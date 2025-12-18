"""
Workflow Summary and Completion Reporting

Generates comprehensive summaries when workflows complete.
Epic 8 / Story 8.5: Progress Summary and Completion
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Workflow, WorkflowState
from .step_details import format_duration
from .visual_feedback import VisualFeedbackGenerator


class WorkflowSummaryGenerator:
    """Generates workflow completion summaries."""

    def __init__(self, project_root: Path | None = None, enable_visual: bool = True):
        """
        Initialize summary generator.

        Args:
            project_root: Project root directory for relative paths
            enable_visual: Whether to enable visual enhancements (Epic 11)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.visual = VisualFeedbackGenerator(enable_visual=enable_visual)

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

        Args:
            workflow: Workflow definition
            state: Final workflow state

        Returns:
            Formatted markdown string
        """
        summary = self.generate_summary(workflow, state)
        lines = []

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

