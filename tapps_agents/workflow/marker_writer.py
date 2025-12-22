"""
Marker Writer - Writes DONE/FAILED markers for workflow step completion.

This module provides utilities for writing explicit completion markers
that indicate when a workflow step has completed successfully or failed.
These markers provide durability and observability for file-based Cursor
workflow coordination.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .file_utils import atomic_write_json


class MarkerWriter:
    """
    Writes DONE/FAILED markers for workflow step execution.
    
    Markers provide explicit completion/failure signals for workflow steps,
    enabling better observability and troubleshooting of file-based Cursor
    workflow execution.
    """

    def __init__(self, project_root: Path):
        """
        Initialize marker writer.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)

    def get_marker_dir(self, workflow_id: str, step_id: str) -> Path:
        """
        Get directory path for workflow step markers.
        
        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            
        Returns:
            Path to marker directory
        """
        markers_dir = (
            self.project_root
            / ".tapps-agents"
            / "workflows"
            / "markers"
            / workflow_id
            / f"step-{step_id}"
        )
        return markers_dir

    def write_done_marker(
        self,
        workflow_id: str,
        step_id: str,
        agent: str,
        action: str,
        worktree_name: str | None = None,
        worktree_path: str | None = None,
        expected_artifacts: list[str] | None = None,
        found_artifacts: list[str] | None = None,
        duration_seconds: float | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Write DONE marker for successful step completion.
        
        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            agent: Agent name
            action: Action name
            worktree_name: Optional worktree name
            worktree_path: Optional worktree path
            expected_artifacts: List of expected artifact paths
            found_artifacts: List of found artifact paths
            duration_seconds: Execution duration in seconds
            started_at: Start timestamp
            completed_at: Completion timestamp
            metadata: Optional additional metadata
            
        Returns:
            Path to written marker file
        """
        marker_dir = self.get_marker_dir(workflow_id, step_id)
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker_file = marker_dir / "DONE.json"

        now = completed_at or datetime.now()
        marker_data = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "agent": agent,
            "action": action,
            "status": "completed",
            "timestamp": now.isoformat(),
        }

        if worktree_name:
            marker_data["worktree_name"] = worktree_name
        if worktree_path:
            marker_data["worktree_path"] = worktree_path
        if expected_artifacts:
            marker_data["expected_artifacts"] = expected_artifacts
        if found_artifacts:
            marker_data["found_artifacts"] = found_artifacts
        if duration_seconds is not None:
            marker_data["duration_seconds"] = duration_seconds
        if started_at:
            marker_data["started_at"] = started_at.isoformat()
        if completed_at:
            marker_data["completed_at"] = completed_at.isoformat()
        if metadata:
            marker_data["metadata"] = metadata

        # Write atomically
        atomic_write_json(marker_file, marker_data, indent=2)

        return marker_file

    def write_failed_marker(
        self,
        workflow_id: str,
        step_id: str,
        agent: str,
        action: str,
        error: str,
        worktree_name: str | None = None,
        worktree_path: str | None = None,
        expected_artifacts: list[str] | None = None,
        found_artifacts: list[str] | None = None,
        duration_seconds: float | None = None,
        started_at: datetime | None = None,
        failed_at: datetime | None = None,
        error_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Write FAILED marker for failed step execution.
        
        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            agent: Agent name
            action: Action name
            error: Error message
            worktree_name: Optional worktree name
            worktree_path: Optional worktree path
            expected_artifacts: List of expected artifact paths
            found_artifacts: List of found artifact paths (if any)
            duration_seconds: Execution duration in seconds (if available)
            started_at: Start timestamp
            failed_at: Failure timestamp
            error_type: Optional error type (e.g., "TimeoutError", "RuntimeError")
            metadata: Optional additional metadata
            
        Returns:
            Path to written marker file
        """
        marker_dir = self.get_marker_dir(workflow_id, step_id)
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker_file = marker_dir / "FAILED.json"

        now = failed_at or datetime.now()
        marker_data = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "agent": agent,
            "action": action,
            "status": "failed",
            "timestamp": now.isoformat(),
            "error": error,
        }

        if worktree_name:
            marker_data["worktree_name"] = worktree_name
        if worktree_path:
            marker_data["worktree_path"] = worktree_path
        if expected_artifacts:
            marker_data["expected_artifacts"] = expected_artifacts
        if found_artifacts:
            marker_data["found_artifacts"] = found_artifacts
        if duration_seconds is not None:
            marker_data["duration_seconds"] = duration_seconds
        if started_at:
            marker_data["started_at"] = started_at.isoformat()
        if error_type:
            marker_data["error_type"] = error_type
        if metadata:
            marker_data["metadata"] = metadata

        # Write atomically
        atomic_write_json(marker_file, marker_data, indent=2)

        return marker_file

    def read_marker(
        self, workflow_id: str, step_id: str, status: str = "DONE"
    ) -> dict[str, Any] | None:
        """
        Read a marker file.
        
        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            status: Marker status ("DONE" or "FAILED")
            
        Returns:
            Marker data dictionary or None if not found
        """
        marker_dir = self.get_marker_dir(workflow_id, step_id)
        marker_file = marker_dir / f"{status}.json"

        if not marker_file.exists():
            return None

        try:
            import json

            content = marker_file.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None

    def marker_exists(
        self, workflow_id: str, step_id: str, status: str = "DONE"
    ) -> bool:
        """
        Check if a marker file exists.
        
        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            status: Marker status ("DONE" or "FAILED")
            
        Returns:
            True if marker exists, False otherwise
        """
        marker_dir = self.get_marker_dir(workflow_id, step_id)
        marker_file = marker_dir / f"{status}.json"
        return marker_file.exists()

