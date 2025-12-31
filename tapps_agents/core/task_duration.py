"""
Task Duration Detection and Estimation

Estimates task duration to determine whether to use background agents or direct execution.
Routes short tasks (< threshold) to direct execution, long tasks to background agents.
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DurationEstimate:
    """Estimate of task duration."""

    estimated_seconds: float
    confidence: float  # 0.0 to 1.0
    method: str  # "historical", "heuristic", "default"
    factors: dict[str, Any]  # Factors that influenced the estimate


class TaskDurationEstimator:
    """Estimates task duration based on command type, file count, and historical data."""

    # Base duration estimates (seconds) for different command types
    BASE_DURATIONS = {
        "reviewer": {
            "score": 2.0,
            "lint": 1.0,
            "type-check": 3.0,
            "review": 5.0,
            "analyze-project": 300.0,  # 5 minutes
            "report": 120.0,  # 2 minutes
        },
        "tester": {
            "test": 10.0,
            "generate-tests": 5.0,
            "run-tests": 30.0,
        },
        "implementer": {
            "implement": 15.0,
            "refactor": 20.0,
            "generate-code": 10.0,
        },
        "planner": {
            "plan": 8.0,
            "create-story": 3.0,
        },
        "architect": {
            "design": 12.0,
        },
        "designer": {
            "design-api": 10.0,
            "design-model": 8.0,
        },
        "documenter": {
            "document": 5.0,
            "generate-docs": 60.0,  # 1 minute
        },
        "ops": {
            "security-scan": 180.0,  # 3 minutes
            "audit-dependencies": 60.0,  # 1 minute
        },
    }

    # Multipliers for file count
    FILE_COUNT_MULTIPLIERS = {
        1: 1.0,
        2: 1.2,
        3: 1.5,
        5: 2.0,
        10: 3.0,
        20: 5.0,
        50: 10.0,
    }

    def __init__(
        self,
        project_root: Path | None = None,
        history_file: Path | None = None,
        default_threshold: float = 30.0,
    ):
        """
        Initialize task duration estimator.

        Args:
            project_root: Project root directory
            history_file: Path to historical execution data file
            default_threshold: Default threshold in seconds (default: 30s)
        """
        self.project_root = project_root or Path.cwd()
        self.history_file = (
            history_file
            or self.project_root / ".tapps-agents" / "task-duration-history.json"
        )
        self.default_threshold = default_threshold
        self.history: dict[str, list[dict[str, Any]]] = self._load_history()

    def _load_history(self) -> dict[str, list[dict[str, Any]]]:
        """Load historical execution data."""
        if not self.history_file.exists():
            return {}

        try:
            with open(self.history_file, encoding="utf-8") as f:
                data = json.load(f)
                # Filter out old entries (keep last 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                filtered = {}
                for task_key, entries in data.items():
                    filtered_entries = [
                        e
                        for e in entries
                        if datetime.fromisoformat(e.get("timestamp", "")) > cutoff_date
                    ]
                    if filtered_entries:
                        filtered[task_key] = filtered_entries
                return filtered
        except Exception as e:
            logger.warning(f"Failed to load task duration history: {e}")
            return {}

    def _save_history(self) -> None:
        """Save historical execution data."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save task duration history: {e}")

    def _get_file_count_multiplier(self, file_count: int) -> float:
        """Get multiplier based on file count."""
        for threshold, multiplier in sorted(
            self.FILE_COUNT_MULTIPLIERS.items(), reverse=True
        ):
            if file_count >= threshold:
                return multiplier
        return 1.0

    def estimate_duration(
        self,
        agent_name: str,
        command: str,
        file_count: int = 1,
        file_size_kb: float = 0.0,
    ) -> DurationEstimate:
        """
        Estimate task duration.

        Args:
            agent_name: Name of the agent (e.g., "reviewer", "tester")
            command: Command name (e.g., "score", "test")
            file_count: Number of files to process
            file_size_kb: Total file size in KB

        Returns:
            DurationEstimate with estimated duration and confidence
        """
        task_key = f"{agent_name}:{command}"
        factors: dict[str, Any] = {
            "agent": agent_name,
            "command": command,
            "file_count": file_count,
            "file_size_kb": file_size_kb,
        }

        # Try historical data first
        if task_key in self.history:
            historical_times = [
                e["duration_seconds"] for e in self.history[task_key]
            ]
            if historical_times:
                avg_duration = sum(historical_times) / len(historical_times)
                # Adjust for file count
                file_multiplier = self._get_file_count_multiplier(file_count)
                estimated = avg_duration * file_multiplier
                factors["historical_avg"] = avg_duration
                factors["file_multiplier"] = file_multiplier
                factors["sample_count"] = len(historical_times)

                return DurationEstimate(
                    estimated_seconds=estimated,
                    confidence=min(0.9, 0.5 + len(historical_times) * 0.1),
                    method="historical",
                    factors=factors,
                )

        # Fall back to heuristic
        base_duration = self._get_base_duration(agent_name, command)
        file_multiplier = self._get_file_count_multiplier(file_count)
        size_multiplier = 1.0 + (file_size_kb / 1000.0) * 0.1  # 10% per MB
        estimated = base_duration * file_multiplier * size_multiplier

        factors["base_duration"] = base_duration
        factors["file_multiplier"] = file_multiplier
        factors["size_multiplier"] = size_multiplier

        return DurationEstimate(
            estimated_seconds=estimated,
            confidence=0.6,  # Lower confidence for heuristic
            method="heuristic",
            factors=factors,
        )

    def _get_base_duration(self, agent_name: str, command: str) -> float:
        """Get base duration for agent/command combination."""
        agent_durations = self.BASE_DURATIONS.get(agent_name, {})
        return agent_durations.get(command, 10.0)  # Default: 10 seconds

    def should_use_background_agent(
        self,
        agent_name: str,
        command: str,
        file_count: int = 1,
        file_size_kb: float = 0.0,
        threshold: float | None = None,
    ) -> tuple[bool, DurationEstimate]:
        """
        Determine if task should use background agent based on duration estimate.

        Args:
            agent_name: Name of the agent
            command: Command name
            file_count: Number of files to process
            file_size_kb: Total file size in KB
            threshold: Duration threshold in seconds (default: self.default_threshold)

        Returns:
            Tuple of (should_use_background, duration_estimate)
        """
        threshold = threshold or self.default_threshold
        estimate = self.estimate_duration(agent_name, command, file_count, file_size_kb)

        should_use = estimate.estimated_seconds >= threshold

        return should_use, estimate

    def record_execution(
        self,
        agent_name: str,
        command: str,
        duration_seconds: float,
        file_count: int = 1,
    ) -> None:
        """
        Record actual execution time for learning.

        Args:
            agent_name: Name of the agent
            command: Command name
            duration_seconds: Actual execution time
            file_count: Number of files processed
        """
        task_key = f"{agent_name}:{command}"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "file_count": file_count,
        }

        if task_key not in self.history:
            self.history[task_key] = []

        self.history[task_key].append(entry)

        # Keep only last 100 entries per task
        if len(self.history[task_key]) > 100:
            self.history[task_key] = self.history[task_key][-100:]

        self._save_history()


def create_duration_estimator(
    project_root: Path | None = None,
    threshold: float = 30.0,
) -> TaskDurationEstimator:
    """
    Convenience function to create a task duration estimator.

    Args:
        project_root: Project root directory
        threshold: Duration threshold in seconds

    Returns:
        TaskDurationEstimator instance
    """
    return TaskDurationEstimator(
        project_root=project_root, default_threshold=threshold
    )

