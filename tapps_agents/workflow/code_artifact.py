"""
Code Generation Artifact Schema.

Defines versioned JSON schema for code generation results from Foreground Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CodeChange:
    """Represents a single code change."""

    file_path: str
    change_type: str  # "feature", "refactor", "bugfix", "enhancement"
    lines_added: int = 0
    lines_removed: int = 0
    functions_added: list[str] = field(default_factory=list)
    functions_modified: list[str] = field(default_factory=list)
    functions_removed: list[str] = field(default_factory=list)
    complexity_before: float | None = None
    complexity_after: float | None = None
    status: str = "pending"  # "pending", "completed", "failed"
    error_message: str | None = None


@dataclass
class CodeArtifact:
    """
    Versioned code generation artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled"
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: str | None = None  # "implement", "refactor", "generate-code"

    # Changes
    changes: list[CodeChange] = field(default_factory=list)
    refactorings: list[CodeChange] = field(default_factory=list)

    # Summary
    total_files_modified: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    total_functions_added: int = 0

    # Review results (if available)
    review_passed: bool | None = None
    review_score: float | None = None
    review_threshold: float | None = None

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert CodeChange objects to dicts
        data["changes"] = [asdict(change) for change in self.changes]
        data["refactorings"] = [asdict(refactor) for refactor in self.refactorings]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CodeArtifact:
        """Create from dictionary."""
        # Convert change dicts back to CodeChange objects
        changes = []
        if "changes" in data:
            for change_data in data["changes"]:
                changes.append(CodeChange(**change_data))
        data["changes"] = changes

        refactorings = []
        if "refactorings" in data:
            for refactor_data in data["refactorings"]:
                refactorings.append(CodeChange(**refactor_data))
        data["refactorings"] = refactorings

        return cls(**data)

    def add_change(self, change: CodeChange) -> None:
        """Add a code change."""
        self.changes.append(change)
        self.total_files_modified += 1
        self.total_lines_added += change.lines_added
        self.total_lines_removed += change.lines_removed
        self.total_functions_added += len(change.functions_added)

    def add_refactoring(self, refactoring: CodeChange) -> None:
        """Add a refactoring change."""
        self.refactorings.append(refactoring)
        self.total_files_modified += 1
        self.total_lines_added += refactoring.lines_added
        self.total_lines_removed += refactoring.lines_removed

    def mark_completed(self) -> None:
        """Mark code generation as completed."""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark code generation as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark code generation as cancelled."""
        self.status = "cancelled"
        self.cancelled = True
