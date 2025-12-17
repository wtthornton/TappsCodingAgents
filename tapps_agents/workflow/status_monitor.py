"""
Real-Time Status Monitoring for Workflow Execution

Monitors workflow status files and triggers progress updates when changes occur.
Epic 8 / Story 8.2: Real-Time Status Monitoring
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .models import WorkflowState
from .progress_updates import ProgressUpdate, UpdateType

logger = logging.getLogger(__name__)


class StatusChangeEvent(Enum):
    """Status change event types."""

    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_STARTED = "workflow_started"


@dataclass
class StatusChange:
    """Represents a status change event."""

    event_type: StatusChangeEvent
    workflow_id: str
    timestamp: datetime
    step_id: str | None = None
    agent: str | None = None
    action: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class StatusFileMonitor:
    """Monitors workflow status files for changes."""

    def __init__(
        self,
        state_dir: Path,
        poll_interval_seconds: float = 2.0,
        on_status_change: Callable[[StatusChange], None] | None = None,
    ):
        """
        Initialize status file monitor.

        Args:
            state_dir: Directory containing workflow state files
            poll_interval_seconds: How often to check for changes
            on_status_change: Callback when status changes detected
        """
        self.state_dir = Path(state_dir)
        self.poll_interval = poll_interval_seconds
        self.on_status_change = on_status_change
        self.monitored_workflows: dict[str, dict[str, Any]] = {}
        self.running = False
        self._monitor_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start monitoring status files."""
        if self.running:
            return

        self.running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Status file monitor started")

    async def stop(self) -> None:
        """Stop monitoring status files."""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Status file monitor stopped")

    async def monitor_workflow(self, workflow_id: str) -> None:
        """
        Start monitoring a specific workflow.

        Args:
            workflow_id: Workflow ID to monitor
        """
        state_file = self.state_dir / f"{workflow_id}.json"
        if state_file.exists():
            # Load initial state
            try:
                state = self._load_state(state_file)
                if state:
                    self.monitored_workflows[workflow_id] = {
                        "state": state,
                        "last_modified": state_file.stat().st_mtime,
                    }
            except Exception as e:
                logger.error(f"Failed to load initial state for {workflow_id}: {e}")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                await self._check_status_files()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _check_status_files(self) -> None:
        """Check all monitored workflow status files for changes."""
        # Find all state files
        if not self.state_dir.exists():
            return

        state_files = list(self.state_dir.glob("*.json"))
        # Exclude history directory
        state_files = [f for f in state_files if "history" not in str(f)]

        for state_file in state_files:
            workflow_id = state_file.stem
            try:
                # Check if file was modified
                current_mtime = state_file.stat().st_mtime

                if workflow_id in self.monitored_workflows:
                    last_mtime = self.monitored_workflows[workflow_id].get(
                        "last_modified", 0
                    )
                    if current_mtime > last_mtime:
                        # File changed, detect what changed
                        await self._detect_changes(workflow_id, state_file)
                else:
                    # New workflow, start monitoring
                    await self.monitor_workflow(workflow_id)

            except Exception as e:
                logger.error(f"Error checking status file {state_file}: {e}")

    async def _detect_changes(
        self, workflow_id: str, state_file: Path
    ) -> None:
        """Detect what changed in workflow state."""
        try:
            new_state = self._load_state(state_file)
            if not new_state:
                return

            old_state_data = self.monitored_workflows.get(workflow_id, {}).get(
                "state"
            )

            # Update stored state
            self.monitored_workflows[workflow_id] = {
                "state": new_state,
                "last_modified": state_file.stat().st_mtime,
            }

            if not old_state_data:
                # New workflow
                if self.on_status_change:
                    self.on_status_change(
                        StatusChange(
                            event_type=StatusChangeEvent.WORKFLOW_STARTED,
                            workflow_id=workflow_id,
                            timestamp=datetime.now(),
                        )
                    )
                return

            # Compare states to detect changes
            old_state = old_state_data

            # Check workflow status changes
            if new_state.get("status") != old_state.get("status"):
                if new_state.get("status") == "completed":
                    if self.on_status_change:
                        self.on_status_change(
                            StatusChange(
                                event_type=StatusChangeEvent.WORKFLOW_COMPLETED,
                                workflow_id=workflow_id,
                                timestamp=datetime.now(),
                            )
                        )
                elif new_state.get("status") == "failed":
                    if self.on_status_change:
                        self.on_status_change(
                            StatusChange(
                                event_type=StatusChangeEvent.WORKFLOW_FAILED,
                                workflow_id=workflow_id,
                                timestamp=datetime.now(),
                                error=new_state.get("error"),
                            )
                        )

            # Check step execution changes
            old_step_executions = {
                se["step_id"]: se
                for se in old_state.get("step_executions", [])
            }
            new_step_executions = {
                se["step_id"]: se
                for se in new_state.get("step_executions", [])
            }

            # Detect new step executions
            for step_id, step_exec in new_step_executions.items():
                old_step_exec = old_step_executions.get(step_id)
                if not old_step_exec:
                    # New step started
                    if self.on_status_change:
                        self.on_status_change(
                            StatusChange(
                                event_type=StatusChangeEvent.STEP_STARTED,
                                workflow_id=workflow_id,
                                timestamp=datetime.now(),
                                step_id=step_id,
                                agent=step_exec.get("agent"),
                                action=step_exec.get("action"),
                            )
                        )
                elif step_exec.get("status") != old_step_exec.get("status"):
                    # Step status changed
                    if step_exec.get("status") == "completed":
                        if self.on_status_change:
                            self.on_status_change(
                                StatusChange(
                                    event_type=StatusChangeEvent.STEP_COMPLETED,
                                    workflow_id=workflow_id,
                                    timestamp=datetime.now(),
                                    step_id=step_id,
                                    agent=step_exec.get("agent"),
                                    action=step_exec.get("action"),
                                )
                            )
                    elif step_exec.get("status") == "failed":
                        if self.on_status_change:
                            self.on_status_change(
                                StatusChange(
                                    event_type=StatusChangeEvent.STEP_FAILED,
                                    workflow_id=workflow_id,
                                    timestamp=datetime.now(),
                                    step_id=step_id,
                                    agent=step_exec.get("agent"),
                                    action=step_exec.get("action"),
                                    error=step_exec.get("error"),
                                )
                            )

        except Exception as e:
            logger.error(f"Error detecting changes for {workflow_id}: {e}")

    def _load_state(self, state_file: Path) -> dict[str, Any] | None:
        """
        Load workflow state from file.

        Args:
            state_file: Path to state file

        Returns:
            State dictionary or None if failed
        """
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse state file {state_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading state file {state_file}: {e}")
            return None


class BackgroundAgentMonitor:
    """Monitors Background Agent execution status."""

    def __init__(
        self,
        worktree_base: Path,
        on_status_change: Callable[[StatusChange], None] | None = None,
    ):
        """
        Initialize Background Agent monitor.

        Args:
            worktree_base: Base directory for worktrees
            on_status_change: Callback when status changes detected
        """
        self.worktree_base = Path(worktree_base)
        self.on_status_change = on_status_change

    async def monitor_worktree(
        self, worktree_path: Path, workflow_id: str, step_id: str
    ) -> None:
        """
        Monitor a specific worktree for Background Agent completion.

        Args:
            worktree_path: Path to worktree
            workflow_id: Workflow ID
            step_id: Step ID
        """
        # Check for progress files or completion markers
        progress_file = worktree_path / ".tapps-agents" / "progress.json"
        completion_file = worktree_path / ".tapps-agents" / "completed.txt"

        if completion_file.exists():
            if self.on_status_change:
                self.on_status_change(
                    StatusChange(
                        event_type=StatusChangeEvent.STEP_COMPLETED,
                        workflow_id=workflow_id,
                        timestamp=datetime.now(),
                        step_id=step_id,
                    )
                )
        elif progress_file.exists():
            # Background Agent is running, could emit progress events
            if self.on_status_change:
                self.on_status_change(
                    StatusChange(
                        event_type=StatusChangeEvent.STEP_PROGRESS,
                        workflow_id=workflow_id,
                        timestamp=datetime.now(),
                        step_id=step_id,
                    )
                )

