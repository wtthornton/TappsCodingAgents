"""
Unified Story Models for Workflow Artifacts.

Provides a unified Story model that combines the best features of
UserStory (from PlanningArtifact) and Story (from Epic models).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..epic.models import StoryStatus
from .common_enums import Priority, RiskLevel


class AcceptanceCriterion(BaseModel):
    """Acceptance criterion for a story."""

    description: str
    verified: bool = False
    verification_method: str | None = None

    model_config = {"extra": "forbid"}


class Story(BaseModel):
    """
    Unified story model for all workflows.

    Combines features from UserStory (PlanningArtifact) and Story (Epic models)
    to provide a single, flexible story model that works across all workflows.

    Story ID format is flexible: supports both numeric (e.g., "8.1") and
    semantic (e.g., "auth-001") formats.
    """

    # ID system (flexible: "8.1" or "auth-001")
    story_id: str

    # Core fields
    title: str
    description: str
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)

    # Metadata
    epic: str | None = None  # Epic ID or name
    domain: str | None = None
    priority: Priority = Priority.MEDIUM
    complexity: int = Field(default=3, ge=1, le=5)
    status: StoryStatus = StoryStatus.NOT_STARTED
    story_points: int | None = Field(default=None, ge=1)
    estimated_effort_hours: float | None = Field(default=None, gt=0)
    risk_level: RiskLevel | None = None

    # Dependencies
    dependencies: list[str] = Field(default_factory=list)

    # Tasks (optional breakdown)
    tasks: list[str] = Field(default_factory=list)

    # File reference (if exists)
    file_path: Path | None = None

    model_config = {"extra": "forbid"}

    @classmethod
    def from_user_story(cls, user_story: "UserStory") -> Story:
        """
        Convert from legacy UserStory (dataclass) to unified Story.

        This is a helper method for migration compatibility.
        """
        # Parse acceptance criteria from list of strings to AcceptanceCriterion objects
        acceptance_criteria = [
            AcceptanceCriterion(description=ac) for ac in user_story.acceptance_criteria
        ]

        # Convert risk_level string to RiskLevel enum
        risk_level = None
        if user_story.risk_level:
            try:
                risk_level = RiskLevel(user_story.risk_level.lower())
            except ValueError:
                pass  # Keep as None if invalid

        # Convert priority string to Priority enum
        priority = Priority.MEDIUM
        if user_story.priority:
            try:
                priority = Priority(user_story.priority.lower())
            except ValueError:
                pass  # Default to MEDIUM if invalid

        # Convert status string to StoryStatus enum
        status = StoryStatus.NOT_STARTED
        if user_story.status:
            status_map = {
                "draft": StoryStatus.NOT_STARTED,
                "ready": StoryStatus.NOT_STARTED,
                "in_progress": StoryStatus.IN_PROGRESS,
                "completed": StoryStatus.DONE,
            }
            status = status_map.get(user_story.status.lower(), StoryStatus.NOT_STARTED)

        return cls(
            story_id=user_story.story_id,
            title=user_story.title,
            description=user_story.description,
            acceptance_criteria=acceptance_criteria,
            epic=user_story.epic,
            domain=user_story.domain,
            priority=priority,
            complexity=user_story.complexity,
            status=status,
            estimated_effort_hours=user_story.estimated_effort_hours,
            risk_level=risk_level,
            dependencies=user_story.dependencies,
            tasks=user_story.tasks,
        )

    @classmethod
    def from_epic_story(cls, epic_story: "EpicStory") -> Story:
        """
        Convert from Epic.Story (dataclass) to unified Story.

        This is a helper method for migration compatibility.
        """
        return cls(
            story_id=epic_story.story_id,
            title=epic_story.title,
            description=epic_story.description,
            acceptance_criteria=epic_story.acceptance_criteria,
            story_points=epic_story.story_points,
            status=epic_story.status,
            dependencies=epic_story.dependencies,
            file_path=epic_story.file_path,
        )


# Type hints for forward references (avoid circular imports)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .planning_artifact import UserStory  # noqa: F401
    from ..epic.models import Story as EpicStory  # noqa: F401
