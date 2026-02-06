"""
Planning Artifact Schema.

Defines versioned JSON schema for planning results from Foreground Agents.
"""

from __future__ import annotations

# Legacy UserStory dataclass - kept for backward compatibility during migration
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus, OperationType, Priority
from .metadata_models import ArtifactMetadata, PlanDetails
from .story_models import Story


@dataclass
class UserStory:
    """Legacy user story dataclass - deprecated, use Story from story_models instead."""

    story_id: str
    title: str
    description: str
    epic: str | None = None
    domain: str | None = None
    priority: str = "medium"  # "high", "medium", "low"
    complexity: int = 3  # 1-5 scale
    status: str = "draft"  # "draft", "ready", "in_progress", "completed"
    acceptance_criteria: list[str] = dataclass_field(default_factory=list)
    tasks: list[str] = dataclass_field(default_factory=list)
    estimated_effort_hours: float | None = None
    risk_level: str | None = None  # "low", "medium", "high"
    dependencies: list[str] = dataclass_field(default_factory=list)


class PlanningArtifact(BaseModel):
    """
    Versioned planning artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: OperationType | None = None

    # Planning outputs
    plan: PlanDetails | None = None
    user_stories: list[Story] = Field(default_factory=list)

    # Summary
    total_stories: int = 0
    total_estimated_hours: float | None = None
    high_priority_stories: int = 0

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def add_story(self, story: Story) -> None:
        """Add a user story."""
        self.user_stories.append(story)
        self.total_stories += 1
        if story.priority == Priority.HIGH:
            self.high_priority_stories += 1
        if story.estimated_effort_hours:
            if self.total_estimated_hours is None:
                self.total_estimated_hours = 0.0
            self.total_estimated_hours += story.estimated_effort_hours

    def mark_completed(self) -> None:
        """Mark planning as completed."""
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark planning as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark planning as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanningArtifact:
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
    def _from_dict_legacy(cls, data: dict[str, Any]) -> PlanningArtifact:
        """Convert from legacy dataclass format."""
        # Convert user_stories from legacy UserStory to new Story format
        user_stories = []
        if "user_stories" in data:
            for story_data in data["user_stories"]:
                # If it's already a dict with story_id, try to convert
                if isinstance(story_data, dict):
                    # Try to convert legacy UserStory dict to Story
                    legacy_story = UserStory(**story_data)
                    unified_story = Story.from_user_story(legacy_story)
                    user_stories.append(unified_story)
                else:
                    # Already a Story object (unlikely but handle it)
                    user_stories.append(story_data)

        # Convert plan dict to PlanDetails if present
        plan = None
        if data.get("plan"):
            plan_data = data["plan"]
            if isinstance(plan_data, dict):
                plan = PlanDetails(**plan_data)
            elif isinstance(plan_data, PlanDetails):
                plan = plan_data

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if data.get("status"):
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Convert operation_type string to enum
        operation_type = None
        if data.get("operation_type"):
            try:
                operation_type = OperationType(data["operation_type"].lower().replace("-", "_"))
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["user_stories"] = user_stories
        artifact_data["plan"] = plan
        artifact_data["status"] = status
        artifact_data["operation_type"] = operation_type

        # Remove fields that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_story", None)
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
