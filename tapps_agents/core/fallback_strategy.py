"""
Background Agent Fallback Strategy

Automatically routes heavy tasks to Background Agents when resources are constrained.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .resource_monitor import ResourceMetrics, ResourceMonitor


class TaskType(Enum):
    """Task type classification."""

    LIGHT = "light"  # Quick tasks, can run locally
    MEDIUM = "medium"  # Moderate tasks, may need background
    HEAVY = "heavy"  # Heavy tasks, should use background agent


@dataclass
class TaskDecision:
    """Decision on where to run a task."""

    task_name: str
    task_type: TaskType
    use_background: bool
    reason: str
    resource_metrics: ResourceMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_name": self.task_name,
            "task_type": self.task_type.value,
            "use_background": self.use_background,
            "reason": self.reason,
            "resource_metrics": (
                self.resource_metrics.to_dict() if self.resource_metrics else None
            ),
        }


class FallbackStrategy:
    """Manages fallback strategy for routing tasks to Background Agents."""

    # Task type mappings
    HEAVY_TASKS = {
        "analyze-project",
        "refactor-large",
        "generate-tests",
        "full-review",
        "security-scan",
        "performance-analysis",
        "documentation-generation",
    }

    MEDIUM_TASKS = {"review-file", "refactor-file", "generate-code", "optimize-code"}

    LIGHT_TASKS = {"lint-file", "type-check", "format-code", "quick-review"}

    def __init__(
        self,
        config: ProjectConfig | None = None,
        resource_monitor: ResourceMonitor | None = None,
        force_background: bool = False,
    ):
        """
        Initialize fallback strategy.

        Args:
            config: Optional ProjectConfig
            resource_monitor: Optional ResourceMonitor instance
            force_background: If True, always use background agents
        """
        self.config = config
        self.resource_monitor = resource_monitor
        self.force_background = force_background

        # Load NUC config if available
        self.nuc_config = self._load_nuc_config()

    def _load_nuc_config(self) -> dict[str, Any]:
        """Load NUC configuration."""
        nuc_config_file = Path(".tapps-agents/nuc-config.yaml")
        if nuc_config_file.exists():
            try:
                import yaml

                with open(nuc_config_file) as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

    def classify_task(self, task_name: str) -> TaskType:
        """
        Classify a task by type.

        Args:
            task_name: Name of the task

        Returns:
            TaskType
        """
        task_lower = task_name.lower()

        # Check heavy tasks
        if any(heavy in task_lower for heavy in self.HEAVY_TASKS):
            return TaskType.HEAVY

        # Check medium tasks
        if any(medium in task_lower for medium in self.MEDIUM_TASKS):
            return TaskType.MEDIUM

        # Check light tasks
        if any(light in task_lower for light in self.LIGHT_TASKS):
            return TaskType.LIGHT

        # Default to medium if unknown
        return TaskType.MEDIUM

    def should_use_background_agent(
        self, task_name: str, check_resources: bool = True
    ) -> TaskDecision:
        """
        Determine if a task should use Background Agent.

        Args:
            task_name: Name of the task
            check_resources: If True, check current resource usage

        Returns:
            TaskDecision
        """
        # Force background if configured
        if self.force_background:
            return TaskDecision(
                task_name=task_name,
                task_type=TaskType.HEAVY,
                use_background=True,
                reason="Force background mode enabled",
            )

        # Check NUC config
        nuc_optimization = self.nuc_config.get("optimization", {})
        default_for = nuc_optimization.get("background_agents", {}).get(
            "default_for", []
        )

        if any(default_task in task_name.lower() for default_task in default_for):
            return TaskDecision(
                task_name=task_name,
                task_type=TaskType.HEAVY,
                use_background=True,
                reason="Task configured for background agent in NUC config",
            )

        # Classify task
        task_type = self.classify_task(task_name)

        # Heavy tasks always use background
        if task_type == TaskType.HEAVY:
            return TaskDecision(
                task_name=task_name,
                task_type=task_type,
                use_background=True,
                reason="Heavy task type - should use background agent",
            )

        # Light tasks never use background
        if task_type == TaskType.LIGHT:
            return TaskDecision(
                task_name=task_name,
                task_type=task_type,
                use_background=False,
                reason="Light task type - can run locally",
            )

        # Medium tasks: check resources
        if check_resources and self.resource_monitor:
            metrics = self.resource_monitor.get_current_metrics()

            if metrics.is_high_usage():
                return TaskDecision(
                    task_name=task_name,
                    task_type=task_type,
                    use_background=True,
                    reason=f"Resource usage high (CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_percent:.1f}%)",
                    resource_metrics=metrics,
                )

        # Default: medium tasks run locally if resources are available
        return TaskDecision(
            task_name=task_name,
            task_type=task_type,
            use_background=False,
            reason="Medium task - resources available for local execution",
        )

    def get_background_agent_for_task(self, task_name: str) -> str | None:
        """
        Get the appropriate Background Agent for a task.

        Args:
            task_name: Name of the task

        Returns:
            Background Agent name or None
        """
        # Map tasks to background agents
        task_mapping = {
            "analyze-project": "TappsCodingAgents Quality Analyzer",
            "refactor-large": "TappsCodingAgents Refactoring Agent",
            "generate-tests": "TappsCodingAgents Testing Agent",
            "full-review": "TappsCodingAgents Quality Analyzer",
            "security-scan": "TappsCodingAgents Security Agent",
            "documentation-generation": "TappsCodingAgents Documentation Agent",
        }

        task_lower = task_name.lower()
        for task_key, agent_name in task_mapping.items():
            if task_key in task_lower:
                return agent_name

        # Default agent
        return "TappsCodingAgents Quality Analyzer"

    def get_fallback_recommendations(self) -> list[str]:
        """
        Get recommendations for fallback strategy.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not self.resource_monitor:
            recommendations.append("Enable resource monitoring for automatic fallback")

        if not self.nuc_config:
            recommendations.append("Create NUC configuration file for optimization")

        # Check current resources
        if self.resource_monitor:
            metrics = self.resource_monitor.get_current_metrics()
            if metrics.is_high_usage():
                recommendations.append(
                    "Current resource usage is high - consider using Background Agents"
                )

        return recommendations


def create_fallback_strategy(
    config: ProjectConfig | None = None,
    resource_monitor: ResourceMonitor | None = None,
    force_background: bool = False,
) -> FallbackStrategy:
    """
    Convenience function to create a fallback strategy.

    Args:
        config: Optional ProjectConfig
        resource_monitor: Optional ResourceMonitor
        force_background: Force background mode

    Returns:
        FallbackStrategy instance
    """
    return FallbackStrategy(
        config=config,
        resource_monitor=resource_monitor,
        force_background=force_background,
    )
