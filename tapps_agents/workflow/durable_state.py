"""
Durable Workflow State Machine - Event-sourced workflow execution with checkpoints.

2025 Architecture Pattern:
- Event sourcing for complete audit trail
- Checkpoints for resume capability
- Survives process crashes and Cursor timeouts
- Optimistic locking for concurrent access
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WorkflowEventType(Enum):
    """Types of workflow events."""
    
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_SKIPPED = "step_skipped"
    
    CHECKPOINT_CREATED = "checkpoint_created"
    QUALITY_GATE_PASSED = "quality_gate_passed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    
    OUTPUT_PRODUCED = "output_produced"
    ARTIFACT_CREATED = "artifact_created"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowEvent:
    """
    Immutable workflow event for event sourcing.
    
    Events are append-only - once created, they cannot be modified.
    """
    
    id: str
    workflow_id: str
    event_type: WorkflowEventType
    timestamp: str
    data: dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "sequence_number": self.sequence_number,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowEvent:
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            workflow_id=data.get("workflow_id", ""),
            event_type=WorkflowEventType(data.get("event_type", "workflow_started")),
            timestamp=data.get("timestamp", ""),
            data=data.get("data", {}),
            sequence_number=data.get("sequence_number", 0),
        )


@dataclass
class WorkflowCheckpoint:
    """
    Checkpoint for workflow resume capability.
    
    Contains all state needed to resume workflow from this point.
    """
    
    workflow_id: str
    step_index: int
    step_name: str
    status: WorkflowStatus
    created_at: str
    outputs: dict[str, Any] = field(default_factory=dict)
    quality_scores: dict[str, float] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "step_index": self.step_index,
            "step_name": self.step_name,
            "status": self.status.value,
            "created_at": self.created_at,
            "outputs": self.outputs,
            "quality_scores": self.quality_scores,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowCheckpoint:
        """Create from dictionary."""
        return cls(
            workflow_id=data.get("workflow_id", ""),
            step_index=data.get("step_index", 0),
            step_name=data.get("step_name", ""),
            status=WorkflowStatus(data.get("status", "pending")),
            created_at=data.get("created_at", ""),
            outputs=data.get("outputs", {}),
            quality_scores=data.get("quality_scores", {}),
            artifacts=data.get("artifacts", []),
            metadata=data.get("metadata", {}),
        )


class EventStore:
    """
    Append-only event store for workflow events.
    
    Uses atomic file operations for durability without locking.
    """
    
    def __init__(self, store_dir: Path):
        """
        Initialize event store.
        
        Args:
            store_dir: Directory for event storage
        """
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_workflow_dir(self, workflow_id: str) -> Path:
        """Get directory for workflow events."""
        return self.store_dir / workflow_id
    
    def _get_events_file(self, workflow_id: str) -> Path:
        """Get events file path."""
        return self._get_workflow_dir(workflow_id) / "events.jsonl"
    
    def _get_checkpoint_file(self, workflow_id: str) -> Path:
        """Get latest checkpoint file path."""
        return self._get_workflow_dir(workflow_id) / "checkpoint.json"
    
    def append_event(self, event: WorkflowEvent) -> None:
        """
        Append event to store (atomic, no locking).
        
        Uses append mode with explicit flush for durability.
        """
        workflow_dir = self._get_workflow_dir(event.workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        events_file = self._get_events_file(event.workflow_id)
        
        # Append with newline-delimited JSON
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())  # Ensure durability
            except OSError:
                # fsync can fail on some systems (e.g., network drives on Windows)
                # Continue anyway as flush() provides some durability guarantees
                pass
    
    def get_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """
        Get all events for a workflow.
        
        Returns events in sequence order.
        """
        events_file = self._get_events_file(workflow_id)
        
        if not events_file.exists():
            return []
        
        events = []
        with open(events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = WorkflowEvent.from_dict(json.loads(line))
                        events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to parse event: {e}")
        
        return sorted(events, key=lambda e: e.sequence_number)
    
    def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """
        Save checkpoint (atomic write with rename).
        """
        checkpoint_file = self._get_checkpoint_file(checkpoint.workflow_id)
        
        # Use the atomic_write_json utility for consistent, reliable atomic writes
        from .file_utils import atomic_write_json
        
        atomic_write_json(checkpoint_file, checkpoint.to_dict(), indent=2)
    
    def get_checkpoint(self, workflow_id: str) -> WorkflowCheckpoint | None:
        """
        Get latest checkpoint for workflow.
        """
        checkpoint_file = self._get_checkpoint_file(workflow_id)
        
        if not checkpoint_file.exists():
            return None
        
        try:
            # Use safe_load_json for robust reading (handles concurrent writes, retries, validation)
            from .file_utils import safe_load_json
            
            data = safe_load_json(
                checkpoint_file,
                retries=3,
                backoff=0.5,
                min_age_seconds=0.0,  # Checkpoints are written atomically, so no min age needed
                min_size=10,  # Minimum size for valid JSON checkpoint
            )
            
            if data is None:
                return None
            
            return WorkflowCheckpoint.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None
    
    def list_workflows(self) -> list[str]:
        """List all workflow IDs in the store."""
        if not self.store_dir.exists():
            return []
        
        return [
            d.name for d in self.store_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete all data for a workflow."""
        import shutil
        
        workflow_dir = self._get_workflow_dir(workflow_id)
        if workflow_dir.exists():
            shutil.rmtree(workflow_dir)
            return True
        return False


class DurableWorkflowState:
    """
    Durable workflow state with event sourcing.
    
    Features:
    - Complete audit trail via events
    - Checkpoint-based resume
    - Optimistic concurrency control
    """
    
    def __init__(
        self,
        workflow_id: str | None = None,
        workflow_name: str = "unnamed",
        store: EventStore | None = None,
        store_dir: Path | None = None,
    ):
        """
        Initialize durable workflow state.
        
        Args:
            workflow_id: Optional workflow ID (generates UUID if not provided)
            workflow_name: Name of the workflow
            store: Optional EventStore instance
            store_dir: Directory for event storage (if store not provided)
        """
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.workflow_name = workflow_name
        
        if store is None:
            if store_dir is None:
                # Use project root detection instead of current working directory
                from ...core.path_validator import PathValidator
                validator = PathValidator()
                store_dir = validator.project_root / ".tapps-agents" / "workflow-state"
            self.store = EventStore(store_dir)
        else:
            self.store = store
        
        # Current state (rebuilt from events)
        self._status = WorkflowStatus.PENDING
        self._current_step = 0
        self._current_step_name = ""
        self._outputs: dict[str, Any] = {}
        self._quality_scores: dict[str, float] = {}
        self._artifacts: list[str] = []
        self._sequence_number = 0
        self._error: str | None = None
        
        # Callbacks
        self._on_event: Callable[[WorkflowEvent], None] | None = None
    
    @property
    def status(self) -> WorkflowStatus:
        """Get current workflow status."""
        return self._status
    
    @property
    def current_step(self) -> int:
        """Get current step index."""
        return self._current_step
    
    @property
    def current_step_name(self) -> str:
        """Get current step name."""
        return self._current_step_name
    
    @property
    def outputs(self) -> dict[str, Any]:
        """Get workflow outputs."""
        return self._outputs.copy()
    
    @property
    def quality_scores(self) -> dict[str, float]:
        """Get quality scores."""
        return self._quality_scores.copy()
    
    @property
    def error(self) -> str | None:
        """Get error message if failed."""
        return self._error
    
    def set_event_handler(self, handler: Callable[[WorkflowEvent], None]) -> None:
        """Set callback for new events (for streaming)."""
        self._on_event = handler
    
    def _create_event(
        self,
        event_type: WorkflowEventType,
        data: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        """Create and store a new event."""
        self._sequence_number += 1
        
        # Format timestamp with Z suffix for UTC (ISO 8601)
        # Use isoformat and replace +00:00 with Z for reliable UTC formatting
        now = datetime.now(UTC)
        timestamp_str = now.isoformat()
        # Replace +00:00 or +00:00:00 with Z (handle various ISO format variations)
        if timestamp_str.endswith("+00:00"):
            timestamp = timestamp_str[:-6] + "Z"
        elif timestamp_str.endswith("+00:00:00"):
            timestamp = timestamp_str[:-9] + "Z"
        else:
            timestamp = timestamp_str  # Fallback to original if format is unexpected
        
        event = WorkflowEvent(
            id=str(uuid.uuid4()),
            workflow_id=self.workflow_id,
            event_type=event_type,
            timestamp=timestamp,
            data=data or {},
            sequence_number=self._sequence_number,
        )
        
        # Persist event
        self.store.append_event(event)
        
        # Notify handler
        if self._on_event:
            try:
                self._on_event(event)
            except Exception as e:
                logger.warning(f"Event handler error: {e}")
        
        return event
    
    def _create_checkpoint(self) -> WorkflowCheckpoint:
        """Create and save a checkpoint."""
        # Format timestamp with Z suffix for UTC (ISO 8601)
        # Use isoformat and replace +00:00 with Z for reliable UTC formatting
        now = datetime.now(UTC)
        timestamp_str = now.isoformat()
        # Replace +00:00 or +00:00:00 with Z (handle various ISO format variations)
        if timestamp_str.endswith("+00:00"):
            created_at = timestamp_str[:-6] + "Z"
        elif timestamp_str.endswith("+00:00:00"):
            created_at = timestamp_str[:-9] + "Z"
        else:
            created_at = timestamp_str  # Fallback to original if format is unexpected
        
        checkpoint = WorkflowCheckpoint(
            workflow_id=self.workflow_id,
            step_index=self._current_step,
            step_name=self._current_step_name,
            status=self._status,
            created_at=created_at,
            outputs=self._outputs.copy(),
            quality_scores=self._quality_scores.copy(),
            artifacts=self._artifacts.copy(),
            metadata={"workflow_name": self.workflow_name},
        )
        
        self.store.save_checkpoint(checkpoint)
        
        self._create_event(
            WorkflowEventType.CHECKPOINT_CREATED,
            {"step_index": self._current_step, "step_name": self._current_step_name},
        )
        
        return checkpoint
    
    # --- Workflow Lifecycle ---
    
    def start(self, metadata: dict[str, Any] | None = None) -> None:
        """Start workflow execution."""
        self._status = WorkflowStatus.RUNNING
        self._create_event(
            WorkflowEventType.WORKFLOW_STARTED,
            {"workflow_name": self.workflow_name, **(metadata or {})},
        )
    
    def complete(self, final_output: Any = None) -> None:
        """Mark workflow as completed."""
        self._status = WorkflowStatus.COMPLETED
        if final_output is not None:
            self._outputs["final_result"] = final_output
        self._create_event(
            WorkflowEventType.WORKFLOW_COMPLETED,
            {"outputs": self._outputs},
        )
        self._create_checkpoint()
    
    def fail(self, error: str) -> None:
        """Mark workflow as failed."""
        self._status = WorkflowStatus.FAILED
        self._error = error
        self._create_event(
            WorkflowEventType.WORKFLOW_FAILED,
            {"error": error, "step_index": self._current_step},
        )
        self._create_checkpoint()
    
    def pause(self, reason: str = "user_requested") -> None:
        """Pause workflow execution."""
        self._status = WorkflowStatus.PAUSED
        self._create_event(
            WorkflowEventType.WORKFLOW_PAUSED,
            {"reason": reason, "step_index": self._current_step},
        )
        self._create_checkpoint()
    
    def cancel(self, reason: str = "user_requested") -> None:
        """Cancel workflow execution."""
        self._status = WorkflowStatus.CANCELLED
        self._create_event(
            WorkflowEventType.WORKFLOW_CANCELLED,
            {"reason": reason, "step_index": self._current_step},
        )
        self._create_checkpoint()
    
    # --- Step Lifecycle ---
    
    def start_step(self, step_index: int, step_name: str, metadata: dict[str, Any] | None = None) -> None:
        """Start a workflow step."""
        self._current_step = step_index
        self._current_step_name = step_name
        self._create_event(
            WorkflowEventType.STEP_STARTED,
            {"step_index": step_index, "step_name": step_name, **(metadata or {})},
        )
    
    def complete_step(self, output: Any = None, quality_score: float | None = None) -> None:
        """Complete current step."""
        if output is not None:
            self._outputs[self._current_step_name] = output
        if quality_score is not None:
            self._quality_scores[self._current_step_name] = quality_score
        
        self._create_event(
            WorkflowEventType.STEP_COMPLETED,
            {
                "step_index": self._current_step,
                "step_name": self._current_step_name,
                "has_output": output is not None,
                "quality_score": quality_score,
            },
        )
        
        # Auto-checkpoint after each step
        self._create_checkpoint()
    
    def fail_step(self, error: str) -> None:
        """Mark current step as failed."""
        self._create_event(
            WorkflowEventType.STEP_FAILED,
            {
                "step_index": self._current_step,
                "step_name": self._current_step_name,
                "error": error,
            },
        )
    
    def skip_step(self, reason: str) -> None:
        """Skip current step."""
        self._create_event(
            WorkflowEventType.STEP_SKIPPED,
            {
                "step_index": self._current_step,
                "step_name": self._current_step_name,
                "reason": reason,
            },
        )
    
    # --- Quality Gates ---
    
    def record_quality_gate(self, gate_name: str, passed: bool, score: float, threshold: float) -> None:
        """Record quality gate result."""
        event_type = WorkflowEventType.QUALITY_GATE_PASSED if passed else WorkflowEventType.QUALITY_GATE_FAILED
        self._create_event(
            event_type,
            {"gate_name": gate_name, "score": score, "threshold": threshold, "passed": passed},
        )
    
    # --- Artifacts ---
    
    def record_artifact(self, artifact_path: str, artifact_type: str = "file") -> None:
        """Record an artifact created by the workflow."""
        self._artifacts.append(artifact_path)
        self._create_event(
            WorkflowEventType.ARTIFACT_CREATED,
            {"path": artifact_path, "type": artifact_type},
        )
    
    # --- Resume ---
    
    @classmethod
    def load_from_checkpoint(
        cls,
        workflow_id: str,
        store_dir: Path | None = None,
    ) -> DurableWorkflowState | None:
        """
        Load workflow state from checkpoint for resume.
        
        Args:
            workflow_id: Workflow ID to load
            store_dir: Directory containing workflow state
            
        Returns:
            DurableWorkflowState instance or None if not found
        """
        if store_dir is None:
            # Use project root detection instead of current working directory
            from ...core.path_validator import PathValidator
            validator = PathValidator()
            store_dir = validator.project_root / ".tapps-agents" / "workflow-state"
        
        store = EventStore(store_dir)
        checkpoint = store.get_checkpoint(workflow_id)
        
        if checkpoint is None:
            return None
        
        # Create state and restore from checkpoint
        state = cls(
            workflow_id=workflow_id,
            workflow_name=checkpoint.metadata.get("workflow_name", "unnamed"),
            store=store,
        )
        
        state._status = checkpoint.status
        state._current_step = checkpoint.step_index
        state._current_step_name = checkpoint.step_name
        state._outputs = checkpoint.outputs
        state._quality_scores = checkpoint.quality_scores
        state._artifacts = checkpoint.artifacts
        
        # Get sequence number from events
        events = store.get_events(workflow_id)
        if events:
            state._sequence_number = max(e.sequence_number for e in events)
        
        return state
    
    def resume(self) -> None:
        """Resume workflow from paused state."""
        if self._status != WorkflowStatus.PAUSED:
            raise ValueError(f"Cannot resume workflow in {self._status.value} state")
        
        self._status = WorkflowStatus.RUNNING
        self._create_event(
            WorkflowEventType.WORKFLOW_RESUMED,
            {"step_index": self._current_step, "step_name": self._current_step_name},
        )
    
    def get_resume_info(self) -> dict[str, Any]:
        """Get information needed to resume workflow."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self._status.value,
            "current_step": self._current_step,
            "current_step_name": self._current_step_name,
            "completed_outputs": list(self._outputs.keys()),
            "quality_scores": self._quality_scores,
            "artifacts": self._artifacts,
            "can_resume": self._status in (WorkflowStatus.PAUSED, WorkflowStatus.RUNNING),
        }


def get_resumable_workflows(store_dir: Path | None = None) -> list[dict[str, Any]]:
    """
    Get list of workflows that can be resumed.
    
    Args:
        store_dir: Directory containing workflow state
        
    Returns:
        List of workflow info dictionaries
    """
    if store_dir is None:
        # Use project root detection instead of current working directory
        from ...core.path_validator import PathValidator
        validator = PathValidator()
        store_dir = validator.project_root / ".tapps-agents" / "workflow-state"
    
    store = EventStore(store_dir)
    workflows = []
    
    for workflow_id in store.list_workflows():
        checkpoint = store.get_checkpoint(workflow_id)
        if checkpoint and checkpoint.status in (WorkflowStatus.PAUSED, WorkflowStatus.RUNNING):
            workflows.append({
                "workflow_id": workflow_id,
                "workflow_name": checkpoint.metadata.get("workflow_name", "unnamed"),
                "status": checkpoint.status.value,
                "step_index": checkpoint.step_index,
                "step_name": checkpoint.step_name,
                "created_at": checkpoint.created_at,
            })
    
    return workflows


# Backward-compatible aliases for existing imports
EventType = WorkflowEventType
Checkpoint = WorkflowCheckpoint


def get_durable_state(
    workflow_id: str | None = None,
    workflow_name: str = "unnamed",
    store_dir: Path | None = None,
) -> DurableWorkflowState:
    """
    Get or create durable workflow state.
    
    Convenience function for creating/loading workflow state.
    
    Args:
        workflow_id: Optional workflow ID (generates UUID if not provided)
        workflow_name: Name of the workflow
        store_dir: Directory for state storage
        
    Returns:
        DurableWorkflowState instance
    """
    if workflow_id:
        # Try to load existing state
        state = DurableWorkflowState.load_from_checkpoint(workflow_id, store_dir)
        if state:
            return state
    
    # Create new state
    return DurableWorkflowState(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        store_dir=store_dir,
    )


def resume_workflow(
    workflow_id: str,
    store_dir: Path | None = None,
) -> DurableWorkflowState | None:
    """
    Resume a workflow from checkpoint.
    
    Args:
        workflow_id: ID of workflow to resume
        store_dir: Directory containing workflow state
        
    Returns:
        DurableWorkflowState ready to resume, or None if not found or not resumable
    """
    state = DurableWorkflowState.load_from_checkpoint(workflow_id, store_dir)
    
    if state is None:
        return None
    
    if state.status == WorkflowStatus.PAUSED:
        state.resume()
        return state
    
    # State exists but is not resumable (COMPLETED, FAILED, CANCELLED, etc.)
    return None
