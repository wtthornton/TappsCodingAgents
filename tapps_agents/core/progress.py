"""
Progress Reporting System for Background Agents

Provides utilities for reporting progress of long-running background tasks.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ProgressReporter:
    """Reports progress for background agent tasks."""

    def __init__(self, task_id: str, output_dir: Path):
        """
        Initialize ProgressReporter.

        Args:
            task_id: Unique identifier for the task
            output_dir: Directory to write progress reports
        """
        self.task_id = task_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.output_dir / f"progress-{task_id}.json"
        self.start_time = time.time()
        self.steps: list[dict[str, Any]] = []

    def report_step(
        self,
        step_name: str,
        status: str = "in_progress",
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """
        Report a step in the task.

        Args:
            step_name: Name of the step
            status: Status of the step (in_progress, completed, failed)
            message: Optional message
            data: Optional additional data
        """
        step = {
            "step": step_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed_seconds": time.time() - self.start_time,
        }

        if message:
            step["message"] = message

        if data:
            step["data"] = data

        self.steps.append(step)
        self._write_progress()

        logger.info(f"[{self.task_id}] {step_name}: {status} - {message or ''}")

    def report_progress(self, current: int, total: int, message: str | None = None):
        """
        Report progress with percentage.

        Args:
            current: Current progress
            total: Total items
            message: Optional message
        """
        percentage = (current / total * 100) if total > 0 else 0

        progress_data = {
            "current": current,
            "total": total,
            "percentage": round(percentage, 2),
        }

        if message:
            progress_data["message"] = message

        self.report_step(
            "progress",
            "in_progress",
            message or f"Progress: {current}/{total} ({percentage:.1f}%)",
            progress_data,
        )

    def complete(self, result: dict[str, Any] | None = None):
        """
        Mark task as completed.

        Args:
            result: Optional result data
        """
        self.report_step(
            "task_complete", "completed", "Task completed successfully", result
        )

    def fail(self, error: str, error_data: dict[str, Any] | None = None):
        """
        Mark task as failed.

        Args:
            error: Error message
            error_data: Optional error data
        """
        error_info = {"error": error}
        if error_data:
            error_info.update(error_data)

        self.report_step("task_failed", "failed", error, error_info)

    def _write_progress(self):
        """Write progress to file."""
        progress_data = {
            "task_id": self.task_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "current_time": datetime.utcnow().isoformat(),
            "elapsed_seconds": time.time() - self.start_time,
            "steps": self.steps,
            "status": self.steps[-1]["status"] if self.steps else "unknown",
        }

        try:
            with open(self.progress_file, "w") as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write progress file: {e}")

    def get_progress(self) -> dict[str, Any]:
        """
        Get current progress.

        Returns:
            Progress data dictionary
        """
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read progress file: {e}")

        return {"task_id": self.task_id, "status": "unknown", "steps": self.steps}


def create_progress_reporter(task_id: str, output_dir: Path) -> ProgressReporter:
    """
    Convenience function to create a progress reporter.

    Args:
        task_id: Unique identifier for the task
        output_dir: Directory to write progress reports

    Returns:
        ProgressReporter instance
    """
    return ProgressReporter(task_id, output_dir)
