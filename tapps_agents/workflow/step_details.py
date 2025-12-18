"""
Step-Level Progress Details

Extracts and formats detailed step information for progress updates.
Epic 8 / Story 8.4: Step-Level Progress Details
"""

from datetime import datetime
from typing import Any

from .models import StepExecution, WorkflowStep


class StepDetailExtractor:
    """Extracts step detail information from workflow steps."""

    @staticmethod
    def extract_step_details(step: WorkflowStep, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Extract step details from step definition.

        Args:
            step: Workflow step definition
            variables: Workflow variables for interpolation

        Returns:
            Dictionary with step details
        """
        variables = variables or {}
        
        # Extract agent name
        agent = step.agent or "unknown"
        
        # Extract action
        action = step.action or "unknown"
        
        # Extract target (from step metadata or variables)
        target = None
        if hasattr(step, "target") and step.target:
            target = step.target
        elif "target_file" in variables:
            target = variables["target_file"]
        
        # Interpolate variables in target if needed
        if target and isinstance(target, str) and "{" in target:
            try:
                target = target.format(**variables)
            except (KeyError, ValueError):
                # If interpolation fails, use raw target
                pass
        
        return {
            "agent": agent,
            "action": action,
            "target": target,
            "step_id": step.id,
        }


class StepSummaryGenerator:
    """Generates human-readable step summaries."""

    @staticmethod
    def generate_summary(
        agent: str,
        action: str,
        target: str | None = None,
    ) -> str:
        """
        Generate human-readable step summary.

        Args:
            agent: Agent name
            action: Action name
            target: Optional target (file, resource, etc.)

        Returns:
            Formatted summary string
        """
        action_verb = action.replace("_", " ").replace("-", " ")
        
        if target:
            # Try to make target more readable
            if "/" in target or "\\" in target:
                # It's a path, show just the filename
                from pathlib import Path
                target_display = Path(target).name
            else:
                target_display = target
            
            return f"**{agent}** is {action_verb} **{target_display}**"
        else:
            return f"**{agent}** is {action_verb}"

    @staticmethod
    def generate_from_step(
        step: WorkflowStep,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate summary from step definition.

        Args:
            step: Workflow step
            variables: Workflow variables

        Returns:
            Formatted summary string
        """
        details = StepDetailExtractor.extract_step_details(step, variables)
        return StepSummaryGenerator.generate_summary(
            agent=details["agent"],
            action=details["action"],
            target=details.get("target"),
        )


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1m 30s", "45s", "2h 15m")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if secs > 0:
            return f"{minutes}m {secs}s"
        return f"{minutes}m"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"


def calculate_step_duration(step_execution: StepExecution) -> float | None:
    """
    Calculate step execution duration.

    Args:
        step_execution: Step execution record

    Returns:
        Duration in seconds, or None if step not completed
    """
    if step_execution.completed_at and step_execution.started_at:
        delta = step_execution.completed_at - step_execution.started_at
        return delta.total_seconds()
    elif step_execution.duration_seconds is not None:
        return step_execution.duration_seconds
    return None


def get_step_status_emoji(status: str) -> str:
    """
    Get emoji for step status.

    Args:
        status: Step status (pending, running, completed, failed, skipped)

    Returns:
        Emoji character
    """
    emoji_map = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "skipped": "⏭️",
    }
    return emoji_map.get(status.lower(), "❓")


def get_elapsed_time(step_execution: StepExecution) -> float | None:
    """
    Get elapsed time for a running step.

    Args:
        step_execution: Step execution record

    Returns:
        Elapsed time in seconds, or None if step not started
    """
    if step_execution.started_at:
        if step_execution.completed_at:
            delta = step_execution.completed_at - step_execution.started_at
            return delta.total_seconds()
        else:
            # Step is still running
            delta = datetime.now() - step_execution.started_at
            return delta.total_seconds()
    return None

