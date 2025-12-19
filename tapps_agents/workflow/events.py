"""
Event definitions for workflow event bus.

Defines event types and data structures for agent coordination.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of workflow events."""

    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    ARTIFACT_CREATED = "artifact_created"
    GATE_EVALUATED = "gate_evaluated"
    WORKFLOW_STATUS = "workflow_status"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


@dataclass
class WorkflowEvent:
    """Workflow event data structure."""

    event_type: EventType
    workflow_id: str
    step_id: str | None
    data: dict[str, Any]
    timestamp: datetime
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowEvent:
        """Create event from dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            workflow_id=data["workflow_id"],
            step_id=data.get("step_id"),
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
        )

