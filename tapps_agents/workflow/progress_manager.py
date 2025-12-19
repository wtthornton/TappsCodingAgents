"""
Progress Update Manager

Orchestrates all progress update components for real-time workflow updates.
Epic 8: Real-Time Progress Updates - Integration
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from .cursor_chat import ChatUpdateSender
from .cursor_skill_helper import read_skill_metadata
from .models import Workflow, WorkflowState
from .progress_updates import (
    ProgressCalculator,
    ProgressUpdateGenerator,
    UpdateQueue,
    UpdateType,
)
from .status_monitor import StatusChange, StatusChangeEvent, StatusFileMonitor
from .step_details import (
    StepSummaryGenerator,
    format_duration,
)
from .visual_feedback import VisualFeedbackGenerator
from .workflow_summary import WorkflowSummaryGenerator

logger = logging.getLogger(__name__)


class ProgressUpdateManager:
    """Manages real-time progress updates for workflow execution."""

    def __init__(
        self,
        workflow: Workflow,
        state: WorkflowState,
        project_root: Path | None = None,
        enable_updates: bool = True,
    ):
        """
        Initialize progress update manager.

        Args:
            workflow: Workflow definition
            state: Workflow state
            project_root: Project root directory
            enable_updates: Whether to enable progress updates
        """
        self.workflow = workflow
        self.state = state
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.enable_updates = enable_updates

        # Initialize components
        self.calculator = ProgressCalculator(total_steps=len(workflow.steps))
        enable_visual = os.getenv("TAPPS_AGENTS_VISUAL_FEEDBACK", "true").lower() == "true"
        self.generator = ProgressUpdateGenerator(self.calculator, enable_visual=enable_visual)
        self.queue = UpdateQueue(min_interval_seconds=2.0, max_updates_per_minute=30)
        self.chat_sender = ChatUpdateSender(enable_updates=enable_updates)
        self.summary_generator = WorkflowSummaryGenerator(project_root=project_root, enable_visual=enable_visual)
        self.visual = VisualFeedbackGenerator(enable_visual=enable_visual)

        # Status monitoring
        state_dir = self.project_root / ".tapps-agents" / "workflow-state"
        # Note: event_bus will be set by CursorWorkflowExecutor if available
        self.status_monitor = StatusFileMonitor(
            state_dir=state_dir,
            poll_interval_seconds=2.0,
            on_status_change=self._handle_status_change,
            event_bus=None,  # Will be set by executor if available
        )

        self.monitoring_started = False

    async def start(self) -> None:
        """Start progress update monitoring."""
        if not self.enable_updates:
            return

        # Start status monitoring
        await self.status_monitor.start()
        await self.status_monitor.monitor_workflow(self.state.workflow_id)
        self.monitoring_started = True

        # Send initial workflow started message
        await self.send_workflow_started()

    async def stop(self) -> None:
        """Stop progress update monitoring."""
        if self.monitoring_started:
            await self.status_monitor.stop()
            self.monitoring_started = False

    async def send_workflow_started(self) -> None:
        """Send workflow started update."""
        if not self.enable_updates:
            return

        update = self.generator.generate_update(
            update_type=UpdateType.WORKFLOW_STARTED,
            state=self.state,
        )
        formatted = self.generator.format_for_chat(update)
        self.chat_sender.send_update(formatted)

    async def send_step_started(
        self, step_id: str, agent: str, action: str
    ) -> None:
        """Send step started update."""
        if not self.enable_updates:
            return

        # Get step details
        step = next(
            (s for s in self.workflow.steps if s.id == step_id), None
        )
        if step:
            summary = StepSummaryGenerator.generate_from_step(
                step, self.state.variables
            )
        else:
            summary = f"**{agent}** is {action}"

        update = self.generator.generate_update(
            update_type=UpdateType.STEP_STARTED,
            state=self.state,
            step_id=step_id,
            agent=agent,
            action=action,
            message=summary,
        )

        # Format with step details
        formatted = self._format_step_update(update, summary)
        
        if self.queue.add_update(update):
            self.chat_sender.send_progress_update(update, formatted)

    async def send_step_completed(
        self, 
        step_id: str, 
        agent: str, 
        action: str, 
        duration: float | None = None,
        gate_result: dict[str, Any] | None = None,
    ) -> None:
        """
        Send step completed update.
        
        Args:
            step_id: Step ID that completed
            agent: Agent name
            action: Action name
            duration: Step duration in seconds
            gate_result: Optional quality gate result (Epic 11: Quality dashboard)
        """
        if not self.enable_updates:
            return

        duration_str = format_duration(duration) if duration else None
        message = "Step completed"
        if duration_str:
            message += f" in {duration_str}"

        update = self.generator.generate_update(
            update_type=UpdateType.STEP_COMPLETED,
            state=self.state,
            step_id=step_id,
            agent=agent,
            action=action,
            message=message,
        )

        formatted = self._format_step_update(update, message)
        
        # Add quality dashboard if gate result available (Epic 11)
        if gate_result and agent == "reviewer":
            quality_dashboard = self.visual.format_quality_dashboard(gate_result)
            if quality_dashboard:
                formatted += f"\n\n{quality_dashboard}"
        
        if self.queue.add_update(update):
            self.chat_sender.send_progress_update(update, formatted)

    async def send_step_failed(
        self, step_id: str, agent: str, action: str, error: str
    ) -> None:
        """Send step failed update."""
        if not self.enable_updates:
            return

        update = self.generator.generate_update(
            update_type=UpdateType.STEP_FAILED,
            state=self.state,
            step_id=step_id,
            agent=agent,
            action=action,
            error=error,
        )

        formatted = self.generator.format_for_chat(update)
        # Critical updates always sent
        self.chat_sender.send_progress_update(update, formatted)

    async def send_workflow_completed(self) -> None:
        """Send workflow completion summary."""
        if not self.enable_updates:
            return

        # Generate and send summary
        summary = self.summary_generator.format_summary_for_chat(
            self.workflow, self.state
        )
        self.chat_sender.send_completion_summary(summary)

    async def send_workflow_failed(self, error: str) -> None:
        """Send workflow failed update."""
        if not self.enable_updates:
            return

        update = self.generator.generate_update(
            update_type=UpdateType.WORKFLOW_FAILED,
            state=self.state,
            error=error,
        )
        formatted = self.generator.format_for_chat(update)
        self.chat_sender.send_progress_update(update, formatted)

    def _handle_status_change(self, change: StatusChange) -> None:
        """Handle status change event from monitor."""
        if not self.enable_updates:
            return

        # Convert status change to progress update
        update_type_map = {
            StatusChangeEvent.STEP_STARTED: UpdateType.STEP_STARTED,
            StatusChangeEvent.STEP_COMPLETED: UpdateType.STEP_COMPLETED,
            StatusChangeEvent.STEP_FAILED: UpdateType.STEP_FAILED,
            StatusChangeEvent.WORKFLOW_COMPLETED: UpdateType.WORKFLOW_COMPLETED,
            StatusChangeEvent.WORKFLOW_FAILED: UpdateType.WORKFLOW_FAILED,
        }

        update_type = update_type_map.get(change.event_type)
        if not update_type:
            return

        # Create task to send update (non-blocking)
        asyncio.create_task(
            self._send_update_from_change(update_type, change)
        )

    async def _send_update_from_change(
        self, update_type: UpdateType, change: StatusChange
    ) -> None:
        """Send update from status change event."""
        # Reload state to get latest
        # For now, use current state
        update = self.generator.generate_update(
            update_type=update_type,
            state=self.state,
            step_id=change.step_id,
            agent=change.agent,
            action=change.action,
            error=change.error,
        )

        formatted = self.generator.format_for_chat(update)
        
        if self.queue.add_update(update):
            self.chat_sender.send_progress_update(update, formatted)

    def _format_step_update(
        self, update: Any, summary: str | None = None
    ) -> str:
        """Format step update with additional details."""
        base_formatted = self.generator.format_for_chat(update)
        
        if summary:
            # Add summary to the formatted message
            lines = base_formatted.split("\n")
            # Insert summary after header
            if len(lines) > 1:
                lines.insert(1, f"\n{summary}\n")
            else:
                lines.append(f"\n{summary}")
            return "\n".join(lines)
        
        return base_formatted

    async def process_queued_updates(self) -> None:
        """Process any queued updates that should be sent now."""
        if not self.enable_updates:
            return

        queued = self.queue.get_queued_updates()
        for update in queued:
            formatted = self.generator.format_for_chat(update)
            self.chat_sender.send_progress_update(update, formatted)

