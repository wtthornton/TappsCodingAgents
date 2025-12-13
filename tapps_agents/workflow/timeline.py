"""
Timeline generation for workflow execution.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .models import StepExecution, Workflow, WorkflowState


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


def generate_timeline(state: WorkflowState, workflow: Workflow) -> dict[str, Any]:
    """Generate project timeline from workflow state."""
    completed_at = None
    if state.status == "completed":
        # Find the last step execution completion time
        if state.step_executions:
            last_execution = max(
                (se for se in state.step_executions if se.completed_at),
                key=lambda se: se.completed_at or datetime.min,
                default=None,
            )
            if last_execution and last_execution.completed_at:
                completed_at = last_execution.completed_at.isoformat()
        if not completed_at:
            completed_at = datetime.now().isoformat()

    total_duration = None
    if completed_at:
        total = datetime.fromisoformat(completed_at) - state.started_at
        total_duration = total.total_seconds()

    timeline = {
        "workflow_id": state.workflow_id,
        "workflow_name": workflow.name,
        "started_at": state.started_at.isoformat(),
        "completed_at": completed_at,
        "total_duration_seconds": total_duration,
        "total_duration_formatted": format_duration(total_duration),
        "status": state.status,
        "steps": [],
    }

    for step_exec in state.step_executions:
        step_info = {
            "step_id": step_exec.step_id,
            "agent": step_exec.agent,
            "action": step_exec.action,
            "started_at": step_exec.started_at.isoformat(),
            "completed_at": (
                step_exec.completed_at.isoformat() if step_exec.completed_at else None
            ),
            "duration_seconds": step_exec.duration_seconds,
            "duration_formatted": format_duration(step_exec.duration_seconds),
            "status": step_exec.status,
            "error": step_exec.error,
        }
        timeline["steps"].append(step_info)

    return timeline


def format_timeline_markdown(timeline: dict[str, Any]) -> str:
    """Format timeline as Markdown."""
    lines = [
        "# Project Timeline",
        "",
        f"**Workflow**: {timeline['workflow_name']}",
        f"**Workflow ID**: {timeline['workflow_id']}",
        f"**Started**: {timeline['started_at']}",
        f"**Completed**: {timeline.get('completed_at', 'N/A')}",
        f"**Total Duration**: {timeline.get('total_duration_formatted', 'N/A')}",
        f"**Status**: {timeline.get('status', 'unknown')}",
        "",
        "## Agent Execution Timeline",
        "",
        "| Step ID | Agent | Action | Started | Duration | Status |",
        "|---------|-------|--------|---------|----------|--------|",
    ]

    for step in timeline["steps"]:
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "running": "🔄",
        }.get(step["status"], "❓")

        lines.append(
            f"| {step['step_id']} | {step['agent']} | {step['action']} | "
            f"{step['started_at']} | {step['duration_formatted']} | "
            f"{status_emoji} {step['status']} |"
        )

    # Add summary statistics
    lines.append("")
    lines.append("## Summary Statistics")
    lines.append("")

    completed_steps = [s for s in timeline["steps"] if s["status"] == "completed"]
    failed_steps = [s for s in timeline["steps"] if s["status"] == "failed"]
    skipped_steps = [s for s in timeline["steps"] if s["status"] == "skipped"]

    lines.append(f"- **Total Steps**: {len(timeline['steps'])}")
    lines.append(f"- **Completed**: {len(completed_steps)}")
    lines.append(f"- **Failed**: {len(failed_steps)}")
    lines.append(f"- **Skipped**: {len(skipped_steps)}")

    if completed_steps:
        total_time = sum(
            s["duration_seconds"] or 0 for s in completed_steps
        )
        avg_time = total_time / len(completed_steps)
        lines.append(f"- **Average Step Duration**: {format_duration(avg_time)}")
        lines.append(f"- **Total Execution Time**: {format_duration(total_time)}")

    if failed_steps:
        lines.append("")
        lines.append("## Failed Steps")
        lines.append("")
        for step in failed_steps:
            lines.append(f"- **{step['step_id']}** ({step['agent']}/{step['action']}): {step.get('error', 'Unknown error')}")

    return "\n".join(lines)


def save_timeline(
    timeline: dict[str, Any],
    output_path: Path,
    format: str = "markdown",
) -> Path:
    """Save timeline to file."""
    if format == "markdown":
        content = format_timeline_markdown(timeline)
        output_path.write_text(content, encoding="utf-8")
    elif format == "json":
        import json

        output_path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {format}")

    return output_path

