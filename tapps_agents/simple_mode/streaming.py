"""
Cursor-Native Streaming Responses for Simple Mode.

2025 Architecture: Progressive streaming with checkpoints to handle Cursor timeouts.

Features:
- Immediate response on workflow start
- Per-step progress streaming
- Checkpoint-based resume on timeout
- Integration with durable workflow state
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of streaming events."""

    WORKFLOW_START = "workflow_start"
    STEP_START = "step_start"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETE = "step_complete"
    STEP_ERROR = "step_error"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    WORKFLOW_PAUSED = "workflow_paused"
    CHECKPOINT = "checkpoint"
    QUALITY_SCORE = "quality_score"
    ARTIFACT_CREATED = "artifact_created"


@dataclass
class StreamEvent:
    """Event for streaming response."""

    type: StreamEventType
    message: str
    step_number: int | None = None
    total_steps: int | None = None
    step_name: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_markdown(self) -> str:
        """Convert to markdown for Cursor display."""
        icon = self._get_icon()
        progress = ""
        if self.step_number is not None and self.total_steps is not None:
            progress = f" ({self.step_number}/{self.total_steps})"

        # Format based on event type
        if self.type == StreamEventType.WORKFLOW_START:
            return f"\n{icon} **{self.message}**{progress}\n"
        elif self.type == StreamEventType.STEP_START:
            return f"\n{icon} **Step {self.step_number}**: {self.message}\n"
        elif self.type == StreamEventType.STEP_PROGRESS:
            return f"  - {self.message}\n"
        elif self.type == StreamEventType.STEP_COMPLETE:
            return f"  {icon} {self.message}\n"
        elif self.type == StreamEventType.STEP_ERROR:
            return f"  {icon} **Error**: {self.message}\n"
        elif self.type == StreamEventType.WORKFLOW_COMPLETE or self.type == StreamEventType.WORKFLOW_ERROR:
            return f"\n{icon} **{self.message}**\n"
        elif self.type == StreamEventType.WORKFLOW_PAUSED:
            return f"\n{icon} **Paused**: {self.message}\n"
        elif self.type == StreamEventType.CHECKPOINT:
            return f"  {icon} Checkpoint saved: {self.message}\n"
        elif self.type == StreamEventType.QUALITY_SCORE:
            score = self.data.get("score", "N/A")
            return f"  {icon} Quality Score: **{score}/100**\n"
        elif self.type == StreamEventType.ARTIFACT_CREATED:
            return f"  {icon} Created: `{self.message}`\n"
        else:
            return f"{icon} {self.message}\n"

    def _get_icon(self) -> str:
        """Get icon for event type."""
        icons = {
            StreamEventType.WORKFLOW_START: "🚀",
            StreamEventType.STEP_START: "📝",
            StreamEventType.STEP_PROGRESS: "→",
            StreamEventType.STEP_COMPLETE: "✅",
            StreamEventType.STEP_ERROR: "❌",
            StreamEventType.WORKFLOW_COMPLETE: "🎉",
            StreamEventType.WORKFLOW_ERROR: "💥",
            StreamEventType.WORKFLOW_PAUSED: "⏸️",
            StreamEventType.CHECKPOINT: "💾",
            StreamEventType.QUALITY_SCORE: "📊",
            StreamEventType.ARTIFACT_CREATED: "📄",
        }
        return icons.get(self.type, "•")


class StreamingWorkflowExecutor:
    """
    Executes workflow steps with streaming progress updates.

    Designed for Cursor's response model:
    - Immediate first response (prevents timeout)
    - Progressive updates during execution
    - Checkpoint on potential timeout
    - Resume command if workflow is paused
    """

    def __init__(
        self,
        workflow_id: str,
        steps: list[dict[str, Any]],
        step_timeout: float = 30.0,
        total_timeout: float = 90.0,
    ):
        """
        Initialize streaming executor.

        Args:
            workflow_id: Unique workflow identifier
            steps: List of step definitions
            step_timeout: Timeout per step in seconds
            total_timeout: Total workflow timeout in seconds
        """
        self.workflow_id = workflow_id
        self.steps = steps
        self.step_timeout = step_timeout
        self.total_timeout = total_timeout

        self._current_step = 0
        self._completed_steps: list[str] = []
        self._events: list[StreamEvent] = []
        self._start_time: float | None = None
        self._paused = False

    async def execute_with_streaming(
        self,
        step_executor: Callable[[dict[str, Any]], Any],
        on_event: Callable[[StreamEvent], None] | None = None,
    ) -> AsyncGenerator[StreamEvent]:
        """
        Execute workflow with streaming events.

        Args:
            step_executor: Function to execute each step
            on_event: Optional callback for each event

        Yields:
            StreamEvent for each workflow event
        """
        import time

        self._start_time = time.time()

        # Emit workflow start immediately
        start_event = StreamEvent(
            type=StreamEventType.WORKFLOW_START,
            message=f"Starting workflow with {len(self.steps)} steps",
            step_number=0,
            total_steps=len(self.steps),
            data={"workflow_id": self.workflow_id},
        )
        self._events.append(start_event)
        if on_event:
            on_event(start_event)
        yield start_event

        # Execute steps
        for i, step in enumerate(self.steps):
            self._current_step = i + 1
            step_id = step.get("id", f"step-{i+1}")
            step_name = step.get("name", f"Step {i+1}")

            # Check total timeout
            elapsed = time.time() - self._start_time
            if elapsed > self.total_timeout:
                pause_event = await self._pause_workflow(
                    f"Total timeout ({self.total_timeout}s) reached"
                )
                yield pause_event
                return

            # Emit step start
            step_start = StreamEvent(
                type=StreamEventType.STEP_START,
                message=step_name,
                step_number=self._current_step,
                total_steps=len(self.steps),
                step_name=step_name,
                data={"step_id": step_id},
            )
            self._events.append(step_start)
            if on_event:
                on_event(step_start)
            yield step_start

            # Execute step with timeout
            try:
                result = await asyncio.wait_for(
                    self._execute_step(step, step_executor),
                    timeout=self.step_timeout,
                )

                # Emit step complete
                complete_event = StreamEvent(
                    type=StreamEventType.STEP_COMPLETE,
                    message=f"{step_name} completed",
                    step_number=self._current_step,
                    total_steps=len(self.steps),
                    step_name=step_name,
                    data={"result": result},
                )
                self._events.append(complete_event)
                if on_event:
                    on_event(complete_event)
                yield complete_event

                self._completed_steps.append(step_id)

                # Emit quality score if available
                if isinstance(result, dict) and "score" in result:
                    score_event = StreamEvent(
                        type=StreamEventType.QUALITY_SCORE,
                        message="Quality check",
                        step_number=self._current_step,
                        total_steps=len(self.steps),
                        data={"score": result.get("score")},
                    )
                    yield score_event

            except TimeoutError:
                # Step timeout - pause and checkpoint
                error_event = StreamEvent(
                    type=StreamEventType.STEP_ERROR,
                    message=f"Step timeout after {self.step_timeout}s",
                    step_number=self._current_step,
                    total_steps=len(self.steps),
                    step_name=step_name,
                )
                yield error_event

                pause_event = await self._pause_workflow(
                    f"Step '{step_name}' timed out"
                )
                yield pause_event
                return

            except Exception as e:
                # Step error
                error_event = StreamEvent(
                    type=StreamEventType.STEP_ERROR,
                    message=str(e),
                    step_number=self._current_step,
                    total_steps=len(self.steps),
                    step_name=step_name,
                    data={"error": str(e)},
                )
                self._events.append(error_event)
                if on_event:
                    on_event(error_event)
                yield error_event

                # Don't fail workflow on step error - continue or pause
                pause_event = await self._pause_workflow(
                    f"Step '{step_name}' failed: {e}"
                )
                yield pause_event
                return

        # Workflow complete
        complete_event = StreamEvent(
            type=StreamEventType.WORKFLOW_COMPLETE,
            message=f"Workflow completed successfully ({len(self._completed_steps)}/{len(self.steps)} steps)",
            step_number=len(self.steps),
            total_steps=len(self.steps),
            data={
                "workflow_id": self.workflow_id,
                "completed_steps": self._completed_steps,
            },
        )
        self._events.append(complete_event)
        if on_event:
            on_event(complete_event)
        yield complete_event

    async def _execute_step(
        self,
        step: dict[str, Any],
        step_executor: Callable[[dict[str, Any]], Any],
    ) -> Any:
        """Execute a single step."""
        if asyncio.iscoroutinefunction(step_executor):
            return await step_executor(step)
        else:
            return step_executor(step)

    async def _pause_workflow(self, reason: str) -> StreamEvent:
        """Pause workflow and create checkpoint."""
        self._paused = True

        # Save checkpoint via durable state
        try:
            from ..workflow.durable_state import get_durable_state

            durable = get_durable_state()
            await durable.pause_workflow(reason)
        except Exception as e:
            logger.warning(f"Failed to save durable checkpoint: {e}")

        pause_event = StreamEvent(
            type=StreamEventType.WORKFLOW_PAUSED,
            message=f"{reason}. Resume with: `@simple-mode *resume {self.workflow_id}`",
            step_number=self._current_step,
            total_steps=len(self.steps),
            data={
                "workflow_id": self.workflow_id,
                "resume_step": self._current_step,
                "completed_steps": self._completed_steps,
            },
        )
        self._events.append(pause_event)
        return pause_event

    def get_resume_command(self) -> str:
        """Get command to resume this workflow."""
        return f"@simple-mode *resume {self.workflow_id}"

    @property
    def is_paused(self) -> bool:
        return self._paused


def format_streaming_response(events: list[StreamEvent]) -> str:
    """
    Format streaming events as markdown for Cursor response.

    Args:
        events: List of stream events

    Returns:
        Formatted markdown string
    """
    lines = []
    for event in events:
        lines.append(event.to_markdown())
    return "".join(lines)


async def create_streaming_response(
    workflow_id: str,
    steps: list[dict[str, Any]],
    step_executor: Callable[[dict[str, Any]], Any],
    step_timeout: float = 30.0,
) -> str:
    """
    Create a streaming response for Cursor.

    This function executes the workflow and returns a formatted markdown
    response that shows progress and can be displayed incrementally.

    Args:
        workflow_id: Unique workflow identifier
        steps: List of step definitions
        step_executor: Function to execute each step
        step_timeout: Timeout per step in seconds

    Returns:
        Formatted markdown response
    """
    executor = StreamingWorkflowExecutor(
        workflow_id=workflow_id,
        steps=steps,
        step_timeout=step_timeout,
    )

    events = []
    async for event in executor.execute_with_streaming(step_executor):
        events.append(event)

    return format_streaming_response(events)
