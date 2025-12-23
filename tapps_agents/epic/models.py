"""
Data models for Epic parsing and orchestration.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class StoryStatus(str, Enum):
    """Story execution status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class AcceptanceCriterion:
    """Acceptance criterion for a story."""

    description: str
    verified: bool = False


@dataclass
class Story:
    """Represents a single story within an Epic."""

    epic_number: int
    story_number: int
    title: str
    description: str
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # Story IDs like "8.1", "8.2"
    story_points: int | None = None
    status: StoryStatus = StoryStatus.NOT_STARTED
    file_path: Path | None = None  # Path to story file if exists

    @property
    def story_id(self) -> str:
        """Get story ID in format X.Y."""
        return f"{self.epic_number}.{self.story_number}"

    @property
    def full_id(self) -> str:
        """Get full story ID with prefix."""
        return f"Story {self.story_id}"

    def depends_on(self, other_story_id: str) -> bool:
        """Check if this story depends on another story."""
        return other_story_id in self.dependencies


@dataclass
class EpicDocument:
    """Represents a parsed Epic document."""

    epic_number: int
    title: str
    goal: str
    description: str
    stories: list[Story] = field(default_factory=list)
    priority: str | None = None
    timeline: str | None = None
    prerequisites: list[str] = field(default_factory=list)
    execution_notes: dict[str, Any] = field(default_factory=dict)
    definition_of_done: list[str] = field(default_factory=list)
    status: str | None = None
    file_path: Path | None = None

    def get_story(self, story_id: str) -> Story | None:
        """Get a story by its ID (e.g., '8.1')."""
        for story in self.stories:
            if story.story_id == story_id:
                return story
        return None

    def get_stories_by_status(self, status: StoryStatus) -> list[Story]:
        """Get all stories with a specific status."""
        return [s for s in self.stories if s.status == status]

    def is_complete(self) -> bool:
        """Check if all stories are done."""
        return all(s.status == StoryStatus.DONE for s in self.stories)

    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.stories:
            return 0.0
        done_count = sum(1 for s in self.stories if s.status == StoryStatus.DONE)
        return (done_count / len(self.stories)) * 100.0

