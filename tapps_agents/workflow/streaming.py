"""
Streaming Workflow Responses - Progressive streaming for Cursor integration.

2025 Architecture Pattern:
- Progressive streaming with immediate feedback
- Per-step timeout with graceful degradation
- Checkpoint-based resume for long workflows
- SSE-style streaming for Cursor
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
    """Types of stream events."""
    
    # Workflow events
    WORKFLOW_START = "workflow_start"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    WORKFLOW_TIMEOUT = "workflow_timeout"
    
    # Step events
    STEP_START = "step_start"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETE = "step_complete"
    STEP_ERROR = "step_error"
    STEP_TIMEOUT = "step_timeout"
    STEP_SKIP = "step_skip"
    
    # Quality events
    QUALITY_CHECK = "quality_check"
    QUALITY_PASS = "quality_pass"
    QUALITY_FAIL = "quality_fail"
    
    # Output events
    OUTPUT_CHUNK = "output_chunk"
    ARTIFACT = "artifact"
    
    # Resume events
    CHECKPOINT = "checkpoint"
    RESUME_AVAILABLE = "resume_available"


@dataclass
class StreamEvent:
    """
    Event for streaming workflow progress.
    
    Designed for SSE-style streaming to Cursor.
    """
    
    event_type: StreamEventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat() + "Z")
    
    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        import json
        return f"event: {self.event_type.value}\ndata: {json.dumps(self.data)}\n\n"
    
    def to_markdown(self) -> str:
        """Format as Markdown for Cursor chat."""
        event_type = self.event_type
        data = self.data
        
        if event_type == StreamEventType.WORKFLOW_START:
            return f"## Starting Workflow: {data.get('workflow_name', 'unnamed')}\n"
        
        elif event_type == StreamEventType.STEP_START:
            step_num = data.get("step_index", 0) + 1
            step_name = data.get("step_name", "unknown")
            total = data.get("total_steps", "?")
            return f"\n### Step {step_num}/{total}: {step_name}\n"
        
        elif event_type == StreamEventType.STEP_PROGRESS:
            return f"  - {data.get('message', '...')}\n"
        
        elif event_type == StreamEventType.STEP_COMPLETE:
            return "  ✅ Completed\n"
        
        elif event_type == StreamEventType.STEP_ERROR:
            return f"  ❌ Error: {data.get('error', 'unknown')}\n"
        
        elif event_type == StreamEventType.STEP_TIMEOUT:
            return f"  ⏱️ Timeout after {data.get('timeout_seconds', '?')}s\n"
        
        elif event_type == StreamEventType.QUALITY_CHECK:
            return f"  📊 Quality check: {data.get('gate_name', 'quality')}\n"
        
        elif event_type == StreamEventType.QUALITY_PASS:
            score = data.get("score", 0)
            threshold = data.get("threshold", 0)
            return f"  ✅ Quality passed: {score:.1f}/{threshold:.1f}\n"
        
        elif event_type == StreamEventType.QUALITY_FAIL:
            score = data.get("score", 0)
            threshold = data.get("threshold", 0)
            return f"  ⚠️ Quality below threshold: {score:.1f}/{threshold:.1f}\n"
        
        elif event_type == StreamEventType.WORKFLOW_COMPLETE:
            return "\n## ✅ Workflow Complete!\n"
        
        elif event_type == StreamEventType.WORKFLOW_ERROR:
            return f"\n## ❌ Workflow Failed: {data.get('error', 'unknown')}\n"
        
        elif event_type == StreamEventType.WORKFLOW_TIMEOUT:
            workflow_id = data.get("workflow_id", "")
            return (
                f"\n## ⏱️ Workflow Timeout\n"
                f"Resume with: `@simple-mode *resume {workflow_id}`\n"
            )
        
        elif event_type == StreamEventType.CHECKPOINT:
            return "  💾 Checkpoint saved\n"
        
        elif event_type == StreamEventType.RESUME_AVAILABLE:
            workflow_id = data.get("workflow_id", "")
            return f"\n💡 Resume available: `@simple-mode *resume {workflow_id}`\n"
        
        elif event_type == StreamEventType.ARTIFACT:
            return f"  📄 Created: {data.get('path', 'unknown')}\n"
        
        elif event_type == StreamEventType.OUTPUT_CHUNK:
            return data.get("content", "")
        
        return ""


class StreamingWorkflowExecutor:
    """
    Streaming workflow executor for Cursor integration.
    
    Features:
    - Immediate response with streaming progress
    - Per-step timeout (prevents cascade delays)
    - Automatic checkpointing for resume
    - Graceful timeout handling
    """
    
    def __init__(
        self,
        workflow_timeout: float = 60.0,
        step_timeout: float = 30.0,
        checkpoint_after_step: bool = True,
    ):
        """
        Initialize streaming executor.
        
        Args:
            workflow_timeout: Total workflow timeout (for Cursor response limit)
            step_timeout: Per-step timeout
            checkpoint_after_step: Whether to checkpoint after each step
        """
        self.workflow_timeout = workflow_timeout
        self.step_timeout = step_timeout
        self.checkpoint_after_step = checkpoint_after_step
        
        self._current_workflow_id: str | None = None
        self._events: list[StreamEvent] = []
    
    async def execute_streaming(
        self,
        workflow_name: str,
        steps: list[dict[str, Any]],
        workflow_id: str | None = None,
        on_event: Callable[[StreamEvent], None] | None = None,
    ) -> AsyncGenerator[StreamEvent]:
        """
        Execute workflow with streaming events.
        
        Yields events as they occur for progressive streaming.
        
        Args:
            workflow_name: Name of the workflow
            steps: List of step definitions (each has 'name', 'func', optional 'timeout')
            workflow_id: Optional workflow ID for resume
            on_event: Optional callback for each event
            
        Yields:
            StreamEvent instances
        """
        from .durable_state import DurableWorkflowState
        
        # Initialize durable state
        if workflow_id:
            # Try to resume from checkpoint
            state = DurableWorkflowState.load_from_checkpoint(workflow_id)
            if state:
                yield StreamEvent(
                    StreamEventType.WORKFLOW_PROGRESS,
                    {"message": f"Resuming from step {state.current_step + 1}"},
                )
                start_step = state.current_step
            else:
                state = DurableWorkflowState(workflow_id=workflow_id, workflow_name=workflow_name)
                start_step = 0
        else:
            state = DurableWorkflowState(workflow_name=workflow_name)
            start_step = 0
        
        self._current_workflow_id = state.workflow_id
        
        # Connect event handler
        def handle_state_event(event):
            if on_event:
                stream_event = StreamEvent(
                    StreamEventType.WORKFLOW_PROGRESS,
                    {"event_type": event.event_type.value, **event.data},
                )
                on_event(stream_event)
        
        state.set_event_handler(handle_state_event)
        
        # Start workflow
        state.start({"total_steps": len(steps)})
        
        yield StreamEvent(
            StreamEventType.WORKFLOW_START,
            {
                "workflow_id": state.workflow_id,
                "workflow_name": workflow_name,
                "total_steps": len(steps),
                "starting_step": start_step,
            },
        )
        
        workflow_start = datetime.now(UTC)
        
        # Execute steps
        for i, step in enumerate(steps[start_step:], start=start_step):
            step_name = step.get("name", f"step_{i}")
            step_func = step.get("func")
            step_timeout = step.get("timeout", self.step_timeout)
            
            # Check workflow timeout
            elapsed = (datetime.now(UTC) - workflow_start).total_seconds()
            if elapsed >= self.workflow_timeout:
                state.pause("workflow_timeout")
                yield StreamEvent(
                    StreamEventType.WORKFLOW_TIMEOUT,
                    {
                        "workflow_id": state.workflow_id,
                        "elapsed_seconds": elapsed,
                        "current_step": i,
                        "step_name": step_name,
                    },
                )
                yield StreamEvent(
                    StreamEventType.RESUME_AVAILABLE,
                    {"workflow_id": state.workflow_id},
                )
                return
            
            # Start step
            state.start_step(i, step_name)
            yield StreamEvent(
                StreamEventType.STEP_START,
                {
                    "step_index": i,
                    "step_name": step_name,
                    "total_steps": len(steps),
                },
            )
            
            # Execute with timeout
            try:
                if step_func:
                    # Execute step function with timeout
                    if asyncio.iscoroutinefunction(step_func):
                        result = await asyncio.wait_for(
                            step_func(),
                            timeout=step_timeout,
                        )
                    else:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, step_func),
                            timeout=step_timeout,
                        )
                    
                    state.complete_step(output=result)
                    yield StreamEvent(
                        StreamEventType.STEP_COMPLETE,
                        {"step_index": i, "step_name": step_name, "has_result": result is not None},
                    )
                else:
                    # No function, just mark as complete
                    state.complete_step()
                    yield StreamEvent(
                        StreamEventType.STEP_COMPLETE,
                        {"step_index": i, "step_name": step_name},
                    )
                
                # Checkpoint after step
                if self.checkpoint_after_step:
                    yield StreamEvent(
                        StreamEventType.CHECKPOINT,
                        {"step_index": i, "step_name": step_name},
                    )
                    
            except TimeoutError:
                state.fail_step(f"Timeout after {step_timeout}s")
                yield StreamEvent(
                    StreamEventType.STEP_TIMEOUT,
                    {
                        "step_index": i,
                        "step_name": step_name,
                        "timeout_seconds": step_timeout,
                    },
                )
                
                # Pause workflow for resume
                state.pause("step_timeout")
                yield StreamEvent(
                    StreamEventType.RESUME_AVAILABLE,
                    {"workflow_id": state.workflow_id},
                )
                return
                
            except Exception as e:
                state.fail_step(str(e))
                yield StreamEvent(
                    StreamEventType.STEP_ERROR,
                    {"step_index": i, "step_name": step_name, "error": str(e)},
                )
                
                # Fail workflow
                state.fail(str(e))
                yield StreamEvent(
                    StreamEventType.WORKFLOW_ERROR,
                    {"error": str(e), "step_index": i, "step_name": step_name},
                )
                return
        
        # Complete workflow
        state.complete()
        yield StreamEvent(
            StreamEventType.WORKFLOW_COMPLETE,
            {
                "workflow_id": state.workflow_id,
                "total_steps": len(steps),
                "outputs": list(state.outputs.keys()),
            },
        )
    
    async def collect_all(
        self,
        workflow_name: str,
        steps: list[dict[str, Any]],
        workflow_id: str | None = None,
    ) -> tuple[list[StreamEvent], dict[str, Any]]:
        """
        Execute workflow and collect all events.
        
        Convenience method when streaming is not needed.
        
        Returns:
            Tuple of (events, final_state)
        """
        events = []
        final_state = {}
        
        async for event in self.execute_streaming(workflow_name, steps, workflow_id):
            events.append(event)
            
            if event.event_type == StreamEventType.WORKFLOW_COMPLETE:
                final_state = {"status": "completed", **event.data}
            elif event.event_type == StreamEventType.WORKFLOW_ERROR:
                final_state = {"status": "failed", **event.data}
            elif event.event_type == StreamEventType.WORKFLOW_TIMEOUT:
                final_state = {"status": "timeout", **event.data}
        
        return events, final_state


async def format_streaming_response(
    events: AsyncGenerator[StreamEvent],
    format: str = "markdown",
) -> AsyncGenerator[str]:
    """
    Format streaming events for output.
    
    Args:
        events: AsyncGenerator of StreamEvent
        format: Output format ("markdown", "sse", "json")
        
    Yields:
        Formatted strings
    """
    import json
    
    async for event in events:
        if format == "markdown":
            yield event.to_markdown()
        elif format == "sse":
            yield event.to_sse()
        elif format == "json":
            yield json.dumps({
                "event": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp,
            }) + "\n"
        else:
            yield event.to_markdown()
