"""
Review Artifact Schema.

Defines versioned JSON schema for review results from Foreground Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus
from .metadata_models import ArtifactMetadata


class ReviewComment(BaseModel):
    """A single review comment."""

    file: str
    line: int | None = None
    severity: str = "suggestion"  # "error", "warning", "suggestion", "info"
    message: str = ""
    category: str | None = None  # "security", "performance", "style", etc.

    model_config = {"extra": "forbid"}


class ReviewArtifact(BaseModel):
    """
    Versioned review artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Scoring
    overall_score: float | None = None
    complexity_score: float | None = None
    security_score: float | None = None
    maintainability_score: float | None = None
    test_coverage_score: float | None = None
    performance_score: float | None = None
    structure_score: float | None = None  # 7-category: project layout, key files (MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.2)
    devex_score: float | None = None  # 7-category: docs, config, tooling (MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.2)
    linting_score: float | None = None
    type_checking_score: float | None = None
    duplication_score: float | None = None

    # Decision
    decision: str | None = None  # "APPROVED", "APPROVED_WITH_SUGGESTIONS", "CHANGES_REQUESTED"
    passed: bool | None = None
    threshold: float | None = None

    # Comments and findings
    comments: list[ReviewComment] = Field(default_factory=list)
    security_findings: list[ReviewComment] = Field(default_factory=list)
    refactoring_suggestions: list[ReviewComment] = Field(default_factory=list)

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def add_comment(self, comment: ReviewComment) -> None:
        """Add a review comment."""
        self.comments.append(comment)

    def add_security_finding(self, finding: ReviewComment) -> None:
        """Add a security finding."""
        self.security_findings.append(finding)

    def add_refactoring_suggestion(self, suggestion: ReviewComment) -> None:
        """Add a refactoring suggestion."""
        self.refactoring_suggestions.append(suggestion)

    def mark_completed(self) -> None:
        """Mark review as completed."""
        self.status = ArtifactStatus.COMPLETED
        # Determine decision based on score
        if self.overall_score is not None and self.threshold is not None:
            self.passed = self.overall_score >= self.threshold
            if self.overall_score >= 8.0:
                self.decision = "APPROVED"
            elif self.overall_score >= 6.0:
                self.decision = "APPROVED_WITH_SUGGESTIONS"
            else:
                self.decision = "CHANGES_REQUESTED"


    def mark_failed(self, error: str) -> None:
        """Mark review as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark review as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewArtifact:
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
    def _from_dict_legacy(cls, data: dict[str, Any]) -> ReviewArtifact:
        """Convert from legacy dataclass format."""
        # Convert comments from dict to ReviewComment objects
        comments = []
        if "comments" in data:
            for comment_data in data["comments"]:
                if isinstance(comment_data, dict):
                    comments.append(ReviewComment(**comment_data))
                else:
                    comments.append(comment_data)

        security_findings = []
        if "security_findings" in data:
            for finding_data in data["security_findings"]:
                if isinstance(finding_data, dict):
                    security_findings.append(ReviewComment(**finding_data))
                else:
                    security_findings.append(finding_data)

        refactoring_suggestions = []
        if "refactoring_suggestions" in data:
            for suggestion_data in data["refactoring_suggestions"]:
                if isinstance(suggestion_data, dict):
                    refactoring_suggestions.append(ReviewComment(**suggestion_data))
                else:
                    refactoring_suggestions.append(suggestion_data)

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if "status" in data and data["status"]:
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["comments"] = comments
        artifact_data["security_findings"] = security_findings
        artifact_data["refactoring_suggestions"] = refactoring_suggestions
        artifact_data["status"] = status

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
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
