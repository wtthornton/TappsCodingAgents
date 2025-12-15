"""
Planning Artifact Schema.

Defines versioned JSON schema for planning results from Foreground Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class UserStory:
    """A user story."""

    story_id: str
    title: str
    description: str
    epic: str | None = None
    domain: str | None = None
    priority: str = "medium"  # "high", "medium", "low"
    complexity: int = 3  # 1-5 scale
    status: str = "draft"  # "draft", "ready", "in_progress", "completed"
    acceptance_criteria: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    estimated_effort_hours: float | None = None
    risk_level: str | None = None  # "low", "medium", "high"
    dependencies: list[str] = field(default_factory=list)


@dataclass
class PlanningArtifact:
    """
    Versioned planning artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled"
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: str | None = None  # "plan", "create-story", "list-stories"

    # Planning outputs
    plan: dict[str, Any] = field(default_factory=dict)
    user_stories: list[UserStory] = field(default_factory=list)

    # Summary
    total_stories: int = 0
    total_estimated_hours: float | None = None
    high_priority_stories: int = 0

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert UserStory objects to dicts
        data["user_stories"] = [asdict(story) for story in self.user_stories]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanningArtifact:
        """Create from dictionary."""
        # Convert story dicts back to UserStory objects
        user_stories = []
        if "user_stories" in data:
            for story_data in data["user_stories"]:
                user_stories.append(UserStory(**story_data))
        data["user_stories"] = user_stories
        return cls(**data)

    def add_story(self, story: UserStory) -> None:
        """Add a user story."""
        self.user_stories.append(story)
        self.total_stories += 1
        if story.priority == "high":
            self.high_priority_stories += 1
        if story.estimated_effort_hours:
            if self.total_estimated_hours is None:
                self.total_estimated_hours = 0.0
            self.total_estimated_hours += story.estimated_effort_hours

    def mark_completed(self) -> None:
        """Mark planning as completed."""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark planning as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark planning as cancelled."""
        self.status = "cancelled"
        self.cancelled = True
