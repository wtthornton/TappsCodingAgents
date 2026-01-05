"""
Background Agent Auto-Executor.

Handles automatic execution of workflow steps via Background Agents.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BackgroundAgentAutoExecutor:
    """
    Executor for Background Agent auto-execution.

    Polls status files to detect when Background Agents complete execution.
    """

    def __init__(
        self,
        polling_interval: float = 1.0,
        timeout_seconds: float = 300.0,
        project_root: Path | None = None,
        enable_metrics: bool = False,
        enable_audit: bool = False,
    ):
        """
        Initialize Background Agent Auto-Executor.

        Args:
            polling_interval: Interval between status checks (seconds)
            timeout_seconds: Maximum time to wait for completion (seconds)
            project_root: Project root directory
            enable_metrics: Enable metrics collection
            enable_audit: Enable audit logging
        """
        self.polling_interval = polling_interval
        self.timeout_seconds = timeout_seconds
        self.project_root = project_root or Path.cwd()
        self.enable_metrics = enable_metrics
        self.enable_audit = enable_audit

    async def execute_command(
        self,
        command: str,
        worktree_path: Path,
        workflow_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        """
        Execute command and wait for Background Agent completion.

        Args:
            command: Command to execute
            worktree_path: Path to worktree directory
            workflow_id: Workflow ID
            step_id: Step ID

        Returns:
            Execution result dictionary with status, success, artifacts, etc.
        """
        status_file = worktree_path / ".cursor" / ".cursor-skill-status.json"

        # Wait for status file to appear and indicate completion
        start_time = datetime.now()
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > self.timeout_seconds:
                return {
                    "status": "timeout",
                    "success": False,
                    "workflow_id": workflow_id,
                    "step_id": step_id,
                    "elapsed_seconds": elapsed,
                }

            if status_file.exists():
                status_result = self.check_status(status_file)
                if status_result.get("completed"):
                    return {
                        "status": status_result.get("status", "unknown"),
                        "success": status_result.get("status") == "completed",
                        "workflow_id": workflow_id,
                        "step_id": step_id,
                        "artifacts": status_result.get("artifacts", []),
                        "elapsed_seconds": elapsed,
                    }

            await asyncio.sleep(self.polling_interval)

    def check_status(self, status_file: Path) -> dict[str, Any]:
        """
        Check status from structured status file.

        Supports both new structured format and legacy format for backward compatibility.

        Args:
            status_file: Path to status file

        Returns:
            Status dictionary with completed flag, status, artifacts, etc.
        """
        if not status_file.exists():
            return {"completed": False, "status": "pending"}

        try:
            content = status_file.read_text(encoding="utf-8")
            status_data = json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read status file {status_file}: {e}")
            return {"completed": False, "status": "error", "error": str(e)}

        # Check if it's the new structured format (has version field)
        if "version" in status_data:
            # New structured format
            status = status_data.get("status", "unknown")
            completed = status in ("completed", "failed")
            result = {
                "completed": completed,
                "status": status,
                "version": status_data.get("version"),
            }

            if "progress" in status_data:
                result["progress"] = status_data["progress"]
            if "artifacts" in status_data:
                result["artifacts"] = status_data["artifacts"]
            if "partial_results" in status_data:
                result["partial_results"] = status_data["partial_results"]
            if "error" in status_data:
                result["error"] = status_data["error"]
            if "metadata" in status_data:
                result["metadata"] = status_data["metadata"]

            return result
        else:
            # Legacy format (backward compatibility)
            status = status_data.get("status", "unknown")
            completed = status in ("completed", "failed")
            return {
                "completed": completed,
                "status": status,
                "artifacts": status_data.get("artifacts", []),
                "output": status_data.get("output"),
            }
