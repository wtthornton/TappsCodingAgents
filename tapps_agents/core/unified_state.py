"""
Unified State Management - Phase 3 Simplification

Consolidates progress, results, and workflow state into a single file
to reduce state synchronization issues and simplify monitoring.
"""

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..workflow.file_utils import atomic_write_json

logger = logging.getLogger(__name__)


class UnifiedState:
    """
    Unified state structure that combines progress, results, and workflow state.
    
    This replaces the previous system of multiple files:
    - progress-{task_id}.json
    - result-{task_id}.json
    - workflow-state/{workflow_id}.json
    """

    def __init__(
        self,
        task_id: str,
        workflow_id: str | None = None,
        start_time: float | None = None,
    ):
        """
        Initialize unified state.

        Args:
            task_id: Unique identifier for the task
            workflow_id: Optional workflow identifier
            start_time: Optional start time (default: current time)
        """
        self.task_id = task_id
        self.workflow_id = workflow_id or task_id
        self.start_time = start_time or time.time()
        self.steps: list[dict[str, Any]] = []
        self.status: str = "initialized"
        self.result: dict[str, Any] | None = None
        self.error: dict[str, Any] | None = None
        self.workflow_state: dict[str, Any] | None = None
        self.metadata: dict[str, Any] = {
            "created_at": datetime.now(UTC).isoformat(),
            "version": "1.0",
        }

    def add_step(
        self,
        step_name: str,
        status: str = "in_progress",
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a step to the state.

        Args:
            step_name: Name of the step
            status: Status of the step (in_progress, completed, failed)
            message: Optional message
            data: Optional additional data
        """
        step = {
            "step": step_name,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "elapsed_seconds": time.time() - self.start_time,
        }

        if message:
            step["message"] = message

        if data:
            step["data"] = data

        self.steps.append(step)
        self.status = status

        logger.info(f"[{self.task_id}] {step_name}: {status} - {message or ''}")

    def set_result(self, result: dict[str, Any]) -> None:
        """
        Set the final result.

        Args:
            result: Result data dictionary
        """
        self.result = result
        self.status = "completed"
        self.add_step("task_complete", "completed", "Task completed successfully", result)

    def set_error(self, error: str, error_data: dict[str, Any] | None = None) -> None:
        """
        Set error information.

        Args:
            error: Error message
            error_data: Optional error data
        """
        error_info = {"error": error}
        if error_data:
            error_info.update(error_data)

        self.error = error_info
        self.status = "failed"
        self.add_step("task_failed", "failed", error, error_info)

    def set_workflow_state(self, workflow_state: dict[str, Any]) -> None:
        """
        Set workflow state information.

        Args:
            workflow_state: Workflow state dictionary
        """
        self.workflow_state = workflow_state

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "current_time": datetime.now(UTC).isoformat(),
            "elapsed_seconds": time.time() - self.start_time,
            "status": self.status,
            "steps": self.steps,
            "result": self.result,
            "error": self.error,
            "workflow_state": self.workflow_state,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnifiedState":
        """
        Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            UnifiedState instance
        """
        state = cls(
            task_id=data["task_id"],
            workflow_id=data.get("workflow_id"),
        )
        state.start_time = datetime.fromisoformat(data["start_time"]).timestamp()
        state.steps = data.get("steps", [])
        state.status = data.get("status", "unknown")
        state.result = data.get("result")
        state.error = data.get("error")
        state.workflow_state = data.get("workflow_state")
        state.metadata = data.get("metadata", {})
        return state


class UnifiedStateManager:
    """
    Manages unified state files that consolidate progress, results, and workflow state.
    
    Phase 3 Simplification: Replaces multiple files with single unified state file.
    """

    def __init__(self, state_dir: Path | None = None):
        """
        Initialize UnifiedStateManager.

        Args:
            state_dir: Directory for state files (default: .tapps-agents/state)
        """
        if state_dir is None:
            # Default to current working directory's .tapps-agents/state
            project_root = Path.cwd()
            state_dir = project_root / ".tapps-agents" / "state"

        self.state_dir = Path(state_dir) if not isinstance(state_dir, Path) else state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_file(self, task_id: str) -> Path:
        """
        Get path to state file for a task.

        Args:
            task_id: Task identifier

        Returns:
            Path to state file
        """
        return self.state_dir / f"{task_id}.json"

    def save_state(self, state: UnifiedState, retry: int = 3) -> Path:
        """
        Save unified state to file with atomic write and retry logic.

        Args:
            state: UnifiedState instance
            retry: Number of retry attempts on failure

        Returns:
            Path to saved state file

        Raises:
            IOError: If save fails after retries
        """
        state_file = self.get_state_file(state.task_id)
        state_dict = state.to_dict()

        # Atomic write with retry
        for attempt in range(retry):
            try:
                atomic_write_json(state_file, state_dict, indent=2)
                logger.debug(f"Saved unified state: {state.task_id} to {state_file}")
                return state_file
            except Exception as e:
                if attempt == retry - 1:
                    logger.error(
                        f"Failed to save unified state after {retry} attempts: {e}"
                    )
                    raise OSError(f"Failed to save state file: {e}") from e
                logger.warning(
                    f"Failed to save unified state (attempt {attempt + 1}/{retry}): {e}"
                )
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff

        raise OSError("Failed to save state file after retries")

    def load_state(self, task_id: str) -> UnifiedState | None:
        """
        Load unified state from file.

        Args:
            task_id: Task identifier

        Returns:
            UnifiedState instance or None if not found
        """
        state_file = self.get_state_file(task_id)

        if not state_file.exists():
            return None

        try:
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)
                return UnifiedState.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load unified state from {state_file}: {e}")
            return None

    def list_states(self, status: str | None = None) -> list[UnifiedState]:
        """
        List all state files, optionally filtered by status.

        Args:
            status: Optional status filter (initialized, in_progress, completed, failed)

        Returns:
            List of UnifiedState instances
        """
        states = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                state = self.load_state(state_file.stem)
                if state is None:
                    continue
                if status is None or state.status == status:
                    states.append(state)
            except Exception as e:
                logger.warning(f"Failed to load state from {state_file}: {e}")

        return states

    def cleanup_old_states(
        self, older_than_days: int = 7, keep_completed: bool = True
    ) -> int:
        """
        Clean up old state files.

        Args:
            older_than_days: Remove states older than this many days
            keep_completed: If True, keep completed states regardless of age

        Returns:
            Number of states cleaned up
        """
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        cleaned = 0

        for state_file in self.state_dir.glob("*.json"):
            try:
                # Check file modification time
                file_mtime = state_file.stat().st_mtime
                if file_mtime < cutoff_time:
                    # Check if we should keep completed states
                    if keep_completed:
                        state = self.load_state(state_file.stem)
                        if state and state.status == "completed":
                            continue

                    # Remove old state file
                    state_file.unlink()
                    cleaned += 1
                    logger.debug(f"Cleaned up old state file: {state_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup state file {state_file}: {e}")

        return cleaned

