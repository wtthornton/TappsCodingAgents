"""
Code Generation Artifact Schema.

Defines versioned JSON schema for code generation results from Foreground Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus, OperationType
from .metadata_models import ArtifactMetadata


class CodeChange(BaseModel):
    """Represents a single code change."""

    file_path: str
    change_type: str  # "feature", "refactor", "bugfix", "enhancement"
    lines_added: int = 0
    lines_removed: int = 0
    functions_added: list[str] = Field(default_factory=list)
    functions_modified: list[str] = Field(default_factory=list)
    functions_removed: list[str] = Field(default_factory=list)
    complexity_before: float | None = None
    complexity_after: float | None = None
    status: str = "pending"  # "pending", "completed", "failed"
    error_message: str | None = None

    model_config = {"extra": "forbid"}


class CodeArtifact(BaseModel):
    """
    Versioned code generation artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: OperationType | None = None

    # Changes
    changes: list[CodeChange] = Field(default_factory=list)
    refactorings: list[CodeChange] = Field(default_factory=list)

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
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

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
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark code generation as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark code generation as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CodeArtifact:
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
    def _from_dict_legacy(cls, data: dict[str, Any]) -> CodeArtifact:
        """Convert from legacy dataclass format."""
        # Convert changes from dict to CodeChange objects
        changes = []
        if "changes" in data:
            for change_data in data["changes"]:
                if isinstance(change_data, dict):
                    changes.append(CodeChange(**change_data))
                else:
                    changes.append(change_data)

        refactorings = []
        if "refactorings" in data:
            for refactor_data in data["refactorings"]:
                if isinstance(refactor_data, dict):
                    refactorings.append(CodeChange(**refactor_data))
                else:
                    refactorings.append(refactor_data)

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if "status" in data and data["status"]:
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Convert operation_type string to enum
        operation_type = None
        if "operation_type" in data and data["operation_type"]:
            try:
                operation_type = OperationType(data["operation_type"].lower().replace("-", "_"))
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["changes"] = changes
        artifact_data["refactorings"] = refactorings
        artifact_data["status"] = status
        artifact_data["operation_type"] = operation_type

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_change", None)
        artifact_data.pop("add_refactoring", None)
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
