"""
Workflow models - Data structures for workflow definitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class WorkflowType(Enum):
    """Workflow type."""

    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"
    HYBRID = "hybrid"


class StepCondition(Enum):
    """Step condition type."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"


@dataclass
class Artifact:
    """Workflow artifact."""

    name: str
    path: str
    status: str = "pending"  # pending, complete, failed
    created_by: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """A single workflow step."""

    id: str
    agent: str
    action: str
    context_tier: int = 2
    creates: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    condition: str = "required"  # required, optional, conditional
    next: str | None = None
    gate: dict[str, Any] | None = None
    consults: list[str] = field(default_factory=list)
    optional_steps: list[str] = field(default_factory=list)
    notes: str | None = None
    repeats: bool = False
    scoring: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowSettings:
    """Workflow settings."""

    quality_gates: bool = True
    code_scoring: bool = True
    context_tier_default: int = 2
    auto_detect: bool = True


@dataclass
class Workflow:
    """Workflow definition."""

    id: str
    name: str
    description: str
    version: str
    type: WorkflowType = WorkflowType.GREENFIELD
    settings: WorkflowSettings = field(default_factory=WorkflowSettings)
    steps: list[WorkflowStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepExecution:
    """Execution tracking for a workflow step."""

    step_id: str
    agent: str
    action: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    status: str = "running"  # running, completed, failed, skipped
    error: str | None = None


@dataclass
class StepResult:
    """Result of step execution with proper error handling.

    This class represents the outcome of executing a workflow step,
    including success/failure status, error details, and artifacts created.
    Used by CursorExecutor to properly track step outcomes and halt
    workflows when required steps fail.
    """

    step_id: str
    status: Literal["completed", "failed", "skipped"]
    success: bool
    duration: float
    started_at: datetime
    completed_at: datetime
    error: str | None = None
    error_traceback: str | None = None
    artifacts: list[str] = field(default_factory=list)
    skip_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "status": self.status,
            "success": self.success,
            "duration": self.duration,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "error": self.error,
            "error_traceback": self.error_traceback,
            "artifacts": self.artifacts,
            "skip_reason": self.skip_reason,
        }


@dataclass
class WorkflowState:
    """Workflow execution state."""

    workflow_id: str
    started_at: datetime
    current_step: str | None = None
    completed_steps: list[str] = field(default_factory=list)
    skipped_steps: list[str] = field(default_factory=list)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    status: str = "running"  # running, paused, completed, failed
    error: str | None = None
    step_executions: list[StepExecution] = field(default_factory=list)
