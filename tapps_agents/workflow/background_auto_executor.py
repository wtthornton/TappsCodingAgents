"""
Background Agent Auto-Executor for Workflow Integration.

Handles automatic execution of workflow commands via Background Agents
with polling-based completion detection.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .audit_logger import AuditLogger
from .cursor_skill_helper import check_skill_completion, create_skill_command_file
from .execution_metrics import ExecutionMetricsCollector

logger = logging.getLogger(__name__)


class BackgroundAgentAutoExecutor:
    """
    Handles auto-execution of workflow commands via Background Agents.
    
    This class integrates with Background Agents configured to watch for
    command files and automatically execute them. It polls for completion
    status files to detect when execution is complete.
    """

    def __init__(
        self,
        polling_interval: float = 5.0,
        timeout_seconds: float = 3600.0,
        status_file_name: str = ".cursor-skill-status.json",
        project_root: Path | None = None,
        enable_metrics: bool = True,
        enable_audit: bool = True,
    ):
        """
        Initialize Background Agent Auto-Executor.

        Args:
            polling_interval: Seconds between status checks (default: 5.0)
            timeout_seconds: Maximum time to wait for completion (default: 3600.0 = 1 hour)
            status_file_name: Name of status file to poll for (default: .cursor-skill-status.json)
            project_root: Project root directory (for metrics/audit)
            enable_metrics: Enable metrics collection (default: True)
            enable_audit: Enable audit logging (default: True)
        """
        self.polling_interval = polling_interval
        self.timeout_seconds = timeout_seconds
        self.status_file_name = status_file_name
        self.project_root = project_root or Path.cwd()

        # Initialize metrics and audit logging (Story 7.9)
        self.metrics_collector = (
            ExecutionMetricsCollector(project_root=self.project_root) if enable_metrics else None
        )
        self.audit_logger = AuditLogger(project_root=self.project_root) if enable_audit else None

    async def execute_command(
        self,
        command: str,
        worktree_path: Path,
        workflow_id: str | None = None,
        step_id: str | None = None,
        expected_artifacts: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a command via Background Agent auto-execution.

        This method:
        1. Creates the command file that Background Agents watch for
        2. Waits for Background Agent to detect and execute the command
        3. Polls for completion status
        4. Returns execution results

        Args:
            command: Skill command to execute (e.g., "@analyst gather-requirements ...")
            worktree_path: Path to worktree where command should execute
            workflow_id: Optional workflow ID for tracking
            step_id: Optional step ID for tracking
            expected_artifacts: List of expected artifact paths (for fallback detection)

        Returns:
            Dictionary with execution results:
            - status: "completed", "failed", or "timeout"
            - command: The command that was executed
            - worktree: Worktree path
            - artifacts: List of created artifacts (if available)
            - error: Error message (if failed)
            - duration_seconds: Execution duration
        """
        start_time = datetime.now()
        status_file = worktree_path / self.status_file_name

        # Create command file (Background Agents watch for this)
        command_file = create_skill_command_file(
            command=command,
            worktree_path=worktree_path,
            workflow_id=workflow_id,
            step_id=step_id,
        )

        # Audit log: command detected
        if self.audit_logger and workflow_id and step_id:
            self.audit_logger.log_command_detected(
                workflow_id=workflow_id,
                step_id=step_id,
                command=command,
                command_file=command_file,
            )

        logger.info(
            f"Created command file for auto-execution: {command_file}",
            extra={
                "command": command,
                "worktree": str(worktree_path),
                "workflow_id": workflow_id,
                "step_id": step_id,
            },
        )

        # Audit log: execution started
        if self.audit_logger and workflow_id and step_id:
            self.audit_logger.log_execution_started(
                workflow_id=workflow_id,
                step_id=step_id,
                command=command,
            )

        # Poll for completion
        result = await self.poll_for_completion(
            worktree_path=worktree_path,
            status_file=status_file,
            expected_artifacts=expected_artifacts,
            start_time=start_time,
        )

        # Add execution metadata
        duration = (datetime.now() - start_time).total_seconds()
        duration_ms = duration * 1000
        result["command"] = command
        result["worktree"] = str(worktree_path)
        result["command_file"] = str(command_file)
        result["duration_seconds"] = duration

        # Record metrics and audit log (Story 7.9)
        if workflow_id and step_id:
            status = result.get("status", "unknown")
            error_message = result.get("error")

            # Record metrics
            if self.metrics_collector:
                self.metrics_collector.record_execution(
                    workflow_id=workflow_id,
                    step_id=step_id,
                    command=command,
                    status=status,
                    duration_ms=duration_ms,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    error_message=error_message,
                )

            # Audit log: execution completed or failed
            if self.audit_logger:
                if status == "completed":
                    self.audit_logger.log_execution_completed(
                        workflow_id=workflow_id,
                        step_id=step_id,
                        command=command,
                        duration_ms=duration_ms,
                    )
                elif status in ["failed", "timeout"]:
                    self.audit_logger.log_execution_failed(
                        workflow_id=workflow_id,
                        step_id=step_id,
                        command=command,
                        error=error_message or f"Execution {status}",
                        duration_ms=duration_ms,
                    )

        return result

    async def poll_for_completion(
        self,
        worktree_path: Path,
        status_file: Path,
        expected_artifacts: list[str] | None = None,
        start_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Poll for command completion by checking status file and artifacts.

        Args:
            worktree_path: Path to worktree
            status_file: Path to status file to check
            expected_artifacts: Fallback: check for artifacts if status file unavailable
            start_time: Start time for timeout calculation

        Returns:
            Dictionary with completion status and results
        """
        if start_time is None:
            start_time = datetime.now()

        elapsed = 0.0
        last_log_time = 0.0
        log_interval = 10.0  # Log progress every 10 seconds

        logger.info(
            f"Polling for completion: {status_file}",
            extra={"worktree": str(worktree_path)},
        )

        while elapsed < self.timeout_seconds:
            # Check status file first (preferred method)
            status_result = self.check_status(status_file)
            if status_result["completed"]:
                logger.info(
                    f"Command completed (status file): {status_file}",
                    extra={
                        "status": status_result.get("status"),
                        "worktree": str(worktree_path),
                    },
                )
                return status_result

            # Fallback: Check for artifacts if status file not available
            if expected_artifacts:
                artifact_result = check_skill_completion(
                    worktree_path=worktree_path,
                    expected_artifacts=expected_artifacts,
                )
                if artifact_result["completed"]:
                    logger.info(
                        f"Command completed (artifacts detected): {worktree_path}",
                        extra={
                            "found_artifacts": artifact_result.get("found_artifacts", []),
                            "worktree": str(worktree_path),
                        },
                    )
                    return {
                        "status": "completed",
                        "completed": True,
                        "artifacts": artifact_result.get("found_artifacts", []),
                        "completion_method": "artifact_detection",
                    }

            # Wait before next poll
            await asyncio.sleep(self.polling_interval)
            elapsed = (datetime.now() - start_time).total_seconds()

            # Log progress periodically
            if elapsed - last_log_time >= log_interval:
                logger.debug(
                    f"Still waiting for completion... ({elapsed:.1f}s elapsed)",
                    extra={"worktree": str(worktree_path)},
                )
                last_log_time = elapsed

        # Timeout reached
        logger.warning(
            f"Command execution timeout after {elapsed:.1f}s: {worktree_path}",
            extra={
                "timeout_seconds": self.timeout_seconds,
                "worktree": str(worktree_path),
            },
        )

        return {
            "status": "timeout",
            "completed": False,
            "error": f"Command did not complete within {self.timeout_seconds}s timeout",
            "elapsed_seconds": elapsed,
        }

    def check_status(self, status_file: Path) -> dict[str, Any]:
        """
        Check status file for execution completion.

        Status file format (JSON):
        {
            "status": "running" | "completed" | "failed",
            "started_at": "ISO datetime",
            "completed_at": "ISO datetime" | null,
            "error": "error message" | null,
            "artifacts": ["artifact1", "artifact2"],
            "output": "execution output"
        }

        Args:
            status_file: Path to status file

        Returns:
            Dictionary with status information
        """
        if not status_file.exists():
            return {
                "completed": False,
                "status": "pending",
                "status_file_exists": False,
            }

        try:
            status_data = json.loads(status_file.read_text(encoding="utf-8"))
            status = status_data.get("status", "unknown")

            if status == "completed":
                return {
                    "completed": True,
                    "status": "completed",
                    "status_file_exists": True,
                    "artifacts": status_data.get("artifacts", []),
                    "output": status_data.get("output"),
                    "started_at": status_data.get("started_at"),
                    "completed_at": status_data.get("completed_at"),
                }
            elif status == "failed":
                return {
                    "completed": True,  # Failed is a completion state
                    "status": "failed",
                    "status_file_exists": True,
                    "error": status_data.get("error", "Unknown error"),
                    "started_at": status_data.get("started_at"),
                    "completed_at": status_data.get("completed_at"),
                }
            else:
                # Still running
                return {
                    "completed": False,
                    "status": status,
                    "status_file_exists": True,
                    "started_at": status_data.get("started_at"),
                }

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(
                f"Error reading status file {status_file}: {e}",
                extra={"status_file": str(status_file)},
                exc_info=True,
            )
            return {
                "completed": False,
                "status": "error",
                "status_file_exists": True,
                "error": f"Error reading status file: {e}",
            }

    def handle_completion(
        self,
        result: dict[str, Any],
        step_execution: Any | None = None,
    ) -> dict[str, Any]:
        """
        Handle completion result and update step execution if provided.

        Args:
            result: Result from poll_for_completion or execute_command
            step_execution: Optional StepExecution object to update

        Returns:
            Processed result dictionary
        """
        if step_execution:
            if result.get("status") == "completed":
                step_execution.status = "completed"
                step_execution.completed_at = datetime.now()
            elif result.get("status") == "failed":
                step_execution.status = "failed"
                step_execution.error = result.get("error", "Unknown error")
                step_execution.completed_at = datetime.now()
            elif result.get("status") == "timeout":
                step_execution.status = "failed"
                step_execution.error = result.get("error", "Execution timeout")
                step_execution.completed_at = datetime.now()

            # Calculate duration if available
            if result.get("duration_seconds"):
                step_execution.duration_seconds = result["duration_seconds"]

        return result

