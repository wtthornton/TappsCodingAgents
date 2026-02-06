"""
Enhancement Artifact Schema.

Defines versioned JSON schema for prompt enhancement results from Foreground Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus
from .metadata_models import ArtifactMetadata


class EnhancementStage(BaseModel):
    """Represents a single enhancement stage result."""

    stage_name: str  # "analysis", "requirements", "architecture", etc.
    status: str = "pending"  # "pending", "completed", "failed"
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    execution_time_seconds: float | None = None

    model_config = {"extra": "forbid"}


class EnhancementArtifact(BaseModel):
    """
    Versioned enhancement artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None
    session_id: str | None = None

    # Original and enhanced prompts
    original_prompt: str = ""
    enhanced_prompt: str = ""

    # Enhancement stages
    stages: dict[str, EnhancementStage] = Field(default_factory=dict)

    # Transformation metadata
    intent: str | None = None  # "feature", "bugfix", "refactor", etc.
    domains: list[str] = Field(default_factory=list)
    scope: str | None = None  # "small", "medium", "large"
    complexity: str | None = None  # "low", "medium", "high"
    workflow_type: str | None = None  # "greenfield", "brownfield", "quick-fix"

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def add_stage(self, stage_name: str, stage: EnhancementStage) -> None:
        """Add an enhancement stage."""
        self.stages[stage_name] = stage

    def mark_completed(self) -> None:
        """Mark enhancement as completed."""
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark enhancement as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark enhancement as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnhancementArtifact:
        """
        Create from dictionary (backward compatibility with old dataclass format).

        This method supports both old dataclass format and new Pydantic format.
        """
        # Try Pydantic validation first (new format)
        try:
            return cls.model_validate(data)
        except Exception:
            # Fall back to manual conversion (old dataclass format)
            return cls._from_dict_legacy(data)

    @classmethod
    def _from_dict_legacy(cls, data: dict[str, Any]) -> EnhancementArtifact:
        """Convert from legacy dataclass format."""
        # Convert stages from dict of dicts to dict of EnhancementStage objects
        stages = {}
        if "stages" in data:
            for name, stage_data in data["stages"].items():
                if isinstance(stage_data, dict):
                    stages[name] = EnhancementStage(**stage_data)
                else:
                    stages[name] = stage_data

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if data.get("status"):
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["stages"] = stages
        artifact_data["status"] = status

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_stage", None)
        artifact_data.pop("mark_completed", None)
        artifact_data.pop("mark_failed", None)
        artifact_data.pop("mark_cancelled", None)

        return cls(**artifact_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (backward compatibility method).

        For new code, use model_dump(mode="json") instead.
        """
        return self.model_dump(mode="json", exclude_none=False)
