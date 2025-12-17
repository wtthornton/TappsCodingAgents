"""
Visual Feedback and Status System for Workflow Execution

Epic 11: Visual Feedback and Status
Provides enhanced visual feedback in Cursor chat with progress indicators,
status badges, timelines, quality dashboards, and artifact summaries.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ..quality.quality_gates import QualityGateResult
from .models import Artifact, StepExecution, Workflow, WorkflowState, WorkflowStep


class VisualFeedbackGenerator:
    """
    Generates visual feedback elements for Cursor chat display.
    
    Features:
    - Enhanced progress bars and indicators
    - Status badges with emojis
    - Timeline visualization
    - Quality score dashboard
    - Artifact summary visualization
    """

    # Status emoji mapping
    STATUS_EMOJIS = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "skipped": "⏭️",
        "paused": "⏸️",
    }

    # Status badge styles
    STATUS_BADGES = {
        "pending": "⏳ Pending",
        "running": "🔄 Running",
        "completed": "✅ Completed",
        "failed": "❌ Failed",
        "skipped": "⏭️ Skipped",
        "paused": "⏸️ Paused",
    }

    # Artifact type emojis
    ARTIFACT_EMOJIS = {
        "code": "💻",
        "docs": "📝",
        "tests": "🧪",
        "reports": "📊",
        "config": "⚙️",
        "data": "💾",
        "other": "📄",
    }

    def __init__(self, enable_visual: bool = True):
        """
        Initialize visual feedback generator.
        
        Args:
            enable_visual: Whether to enable visual enhancements
        """
        self.enable_visual = enable_visual
        # Check if visual feedback is disabled via env var
        if os.getenv("TAPPS_AGENTS_VISUAL_FEEDBACK", "true").lower() == "false":
            self.enable_visual = False

    def format_progress_bar(
        self, percentage: float, width: int = 30, show_percentage: bool = True
    ) -> str:
        """
        Generate enhanced text-based progress bar.
        
        Args:
            percentage: Completion percentage (0-100)
            width: Width of progress bar in characters
            show_percentage: Whether to show percentage text
            
        Returns:
            Formatted progress bar string
        """
        if not self.enable_visual:
            return f"Progress: {percentage:.1f}%"
        
        # Clamp percentage
        percentage = max(0.0, min(100.0, percentage))
        
        filled = int((percentage / 100.0) * width)
        bar = "█" * filled + "░" * (width - filled)
        
        if show_percentage:
            return f"`[{bar}] {percentage:.1f}%`"
        return f"`[{bar}]`"

    def format_step_indicator(
        self, step_number: int, total_steps: int, step_id: str | None = None
    ) -> str:
        """
        Format step indicator (Step X of Y).
        
        Args:
            step_number: Current step number
            total_steps: Total number of steps
            step_id: Optional step ID
            
        Returns:
            Formatted step indicator string
        """
        if not self.enable_visual:
            return f"Step {step_number} of {total_steps}"
        
        indicator = f"**Step {step_number} of {total_steps}**"
        if step_id:
            indicator += f" (`{step_id}`)"
        return indicator

    def format_status_badge(self, status: str) -> str:
        """
        Format status badge with emoji.
        
        Args:
            status: Status string (pending, running, completed, failed, skipped, paused)
            
        Returns:
            Formatted status badge
        """
        if not self.enable_visual:
            return status.capitalize()
        
        badge = self.STATUS_BADGES.get(status.lower(), f"❓ {status}")
        return f"**{badge}**"

    def format_quality_dashboard(
        self, gate_result: QualityGateResult | dict[str, Any] | None
    ) -> str:
        """
        Format quality score dashboard for display.
        
        Args:
            gate_result: Quality gate result or dictionary with scores
            
        Returns:
            Formatted quality dashboard markdown
        """
        if not gate_result:
            return ""
        
        if not self.enable_visual:
            # Text fallback
            if isinstance(gate_result, dict):
                scores = gate_result.get("scores", {})
                passed = gate_result.get("passed", False)
                return f"Quality Gate: {'PASSED' if passed else 'FAILED'}"
            return f"Quality Gate: {'PASSED' if gate_result.passed else 'FAILED'}"
        
        lines = ["### 📊 Quality Dashboard"]
        
        # Extract scores
        if isinstance(gate_result, dict):
            scores = gate_result.get("scores", {})
            passed = gate_result.get("passed", False)
            overall_passed = gate_result.get("overall_passed", False)
            security_passed = gate_result.get("security_passed", False)
            maintainability_passed = gate_result.get("maintainability_passed", False)
            test_coverage_passed = gate_result.get("test_coverage_passed", False)
            performance_passed = gate_result.get("performance_passed", False)
        else:
            scores = gate_result.scores
            passed = gate_result.passed
            overall_passed = gate_result.overall_passed
            security_passed = gate_result.security_passed
            maintainability_passed = gate_result.maintainability_passed
            test_coverage_passed = gate_result.test_coverage_passed
            performance_passed = gate_result.performance_passed
        
        # Overall status
        status_emoji = "✅" if passed else "❌"
        lines.append(f"\n**{status_emoji} Overall Gate:** {'PASSED' if passed else 'FAILED'}")
        
        # Score bars
        score_items = [
            ("Overall", scores.get("overall_score", 0.0), overall_passed),
            ("Security", scores.get("security_score", 0.0), security_passed),
            ("Maintainability", scores.get("maintainability_score", 0.0), maintainability_passed),
            ("Test Coverage", scores.get("test_coverage_score", 0.0) * 10, test_coverage_passed),  # Convert 0-10 to 0-100
            ("Performance", scores.get("performance_score", 0.0), performance_passed),
        ]
        
        lines.append("\n**Scores:**")
        for name, score, score_passed in score_items:
            # Normalize score to 0-100 for display
            if name == "Overall":
                display_score = score * 10  # Convert 0-10 to 0-100
            elif name == "Test Coverage":
                display_score = score  # Already converted
            else:
                display_score = score * 10  # Convert 0-10 to 0-100
            
            # Clamp to 0-100
            display_score = max(0.0, min(100.0, display_score))
            
            bar = self.format_progress_bar(display_score, width=20, show_percentage=False)
            status_icon = "✅" if score_passed else "❌"
            lines.append(f"- {status_icon} **{name}:** {bar} {display_score:.1f}%")
        
        return "\n".join(lines)

    def format_timeline(
        self, state: WorkflowState, workflow: Workflow
    ) -> str:
        """
        Format workflow execution timeline.
        
        Args:
            state: Workflow state with execution history
            workflow: Workflow definition
            
        Returns:
            Formatted timeline markdown
        """
        if not self.enable_visual:
            # Text fallback
            completed = len(state.completed_steps)
            total = len(workflow.steps)
            return f"Timeline: {completed}/{total} steps completed"
        
        lines = ["### ⏱️ Execution Timeline"]
        
        # Get step executions in order
        executions = sorted(
            state.step_executions,
            key=lambda e: e.started_at or datetime.now(),
        )
        
        if not executions:
            lines.append("\n*No steps executed yet*")
            return "\n".join(lines)
        
        # Group by status
        for execution in executions:
            step = next((s for s in workflow.steps if s.id == execution.step_id), None)
            step_name = step.agent if step else execution.step_id
            
            # Status emoji
            status_emoji = self.STATUS_EMOJIS.get(execution.status, "❓")
            
            # Duration
            duration_str = ""
            if execution.duration_seconds:
                duration_str = f" ({self._format_duration(execution.duration_seconds)})"
            
            # Timestamp
            timestamp_str = ""
            if execution.started_at:
                timestamp_str = execution.started_at.strftime("%H:%M:%S")
            
            lines.append(
                f"- {status_emoji} **{step_name}** (`{execution.step_id}`){duration_str}"
            )
            if timestamp_str:
                lines[-1] += f" - {timestamp_str}"
        
        # Summary
        completed = len(state.completed_steps)
        total = len(workflow.steps)
        failed = sum(1 for e in executions if e.status == "failed")
        
        lines.append(f"\n**Summary:** {completed}/{total} completed")
        if failed > 0:
            lines[-1] += f", {failed} failed"
        
        return "\n".join(lines)

    def format_artifact_summary(
        self, artifacts: list[Artifact] | list[dict[str, Any]]
    ) -> str:
        """
        Format artifact summary with type indicators.
        
        Args:
            artifacts: List of artifacts or artifact dictionaries
            
        Returns:
            Formatted artifact summary markdown
        """
        if not artifacts:
            return ""
        
        if not self.enable_visual:
            # Text fallback
            return f"Artifacts: {len(artifacts)} created"
        
        lines = ["### 📦 Artifacts Created"]
        
        # Group by type
        by_type: dict[str, list[Any]] = {}
        for artifact in artifacts:
            if isinstance(artifact, dict):
                artifact_type = artifact.get("type", "other")
                name = artifact.get("name", artifact.get("path", "unknown"))
            else:
                artifact_type = artifact.type if hasattr(artifact, "type") else "other"
                name = artifact.name if hasattr(artifact, "name") else str(artifact)
            
            if artifact_type not in by_type:
                by_type[artifact_type] = []
            by_type[artifact_type].append(name)
        
        # Format by type
        for artifact_type, items in sorted(by_type.items()):
            emoji = self.ARTIFACT_EMOJIS.get(artifact_type, "📄")
            lines.append(f"\n**{emoji} {artifact_type.capitalize()}:**")
            for item in items:
                lines.append(f"- `{item}`")
        
        lines.append(f"\n**Total:** {len(artifacts)} artifacts")
        
        return "\n".join(lines)

    def format_workflow_status_summary(
        self, state: WorkflowState, workflow: Workflow
    ) -> str:
        """
        Format comprehensive workflow status summary.
        
        Args:
            state: Current workflow state
            workflow: Workflow definition
            
        Returns:
            Formatted status summary markdown
        """
        lines = []
        
        # Overall status
        status_emoji = self.STATUS_EMOJIS.get(state.status, "❓")
        lines.append(f"## {status_emoji} Workflow Status: {state.status.upper()}")
        
        # Progress
        completed = len(state.completed_steps)
        total = len(workflow.steps)
        percentage = (completed / total * 100) if total > 0 else 0.0
        
        lines.append(f"\n{self.format_progress_bar(percentage)}")
        lines.append(f"\n{self.format_step_indicator(completed + 1, total, state.current_step)}")
        
        # Current step
        if state.current_step:
            current_step = next(
                (s for s in workflow.steps if s.id == state.current_step), None
            )
            if current_step:
                lines.append(
                    f"\n**Current Step:** {self.format_status_badge('running')} "
                    f"{current_step.agent} - {current_step.action}"
                )
        
        # Execution time
        if state.started_at:
            elapsed = datetime.now() - state.started_at
            lines.append(f"\n**Elapsed Time:** {self._format_duration(elapsed.total_seconds())}")
        
        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

