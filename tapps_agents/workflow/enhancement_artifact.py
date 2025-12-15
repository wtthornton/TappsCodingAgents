"""
Enhancement Artifact Schema.

Defines versioned JSON schema for prompt enhancement results from Foreground Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EnhancementStage:
    """Represents a single enhancement stage result."""

    stage_name: str  # "analysis", "requirements", "architecture", etc.
    status: str = "pending"  # "pending", "completed", "failed"
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time_seconds: float | None = None


@dataclass
class EnhancementArtifact:
    """
    Versioned enhancement artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled"
    worktree_path: str | None = None
    correlation_id: str | None = None
    session_id: str | None = None

    # Original and enhanced prompts
    original_prompt: str = ""
    enhanced_prompt: str = ""

    # Enhancement stages
    stages: dict[str, EnhancementStage] = field(default_factory=dict)

    # Transformation metadata
    intent: str | None = None  # "feature", "bugfix", "refactor", etc.
    domains: list[str] = field(default_factory=list)
    scope: str | None = None  # "small", "medium", "large"
    complexity: str | None = None  # "low", "medium", "high"
    workflow_type: str | None = None  # "greenfield", "brownfield", "quick-fix"

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert EnhancementStage objects to dicts
        data["stages"] = {
            name: asdict(stage) for name, stage in self.stages.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnhancementArtifact:
        """Create from dictionary."""
        # Convert stage dicts back to EnhancementStage objects
        stages = {}
        if "stages" in data:
            for name, stage_data in data["stages"].items():
                stages[name] = EnhancementStage(**stage_data)
        data["stages"] = stages
        return cls(**data)

    def add_stage(self, stage_name: str, stage: EnhancementStage) -> None:
        """Add an enhancement stage."""
        self.stages[stage_name] = stage

    def mark_completed(self) -> None:
        """Mark enhancement as completed."""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark enhancement as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark enhancement as cancelled."""
        self.status = "cancelled"
        self.cancelled = True
