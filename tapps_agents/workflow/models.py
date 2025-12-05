"""
Workflow models - Data structures for workflow definitions.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """A single workflow step."""
    id: str
    agent: str
    action: str
    context_tier: int = 2
    creates: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    condition: str = "required"  # required, optional, conditional
    next: Optional[str] = None
    gate: Optional[Dict[str, Any]] = None
    consults: List[str] = field(default_factory=list)
    optional_steps: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    repeats: bool = False
    scoring: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState:
    """Workflow execution state."""
    workflow_id: str
    started_at: datetime
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    skipped_steps: List[str] = field(default_factory=list)
    artifacts: Dict[str, Artifact] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"  # running, paused, completed, failed
    error: Optional[str] = None

