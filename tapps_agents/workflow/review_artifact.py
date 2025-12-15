"""
Review Artifact Schema.

Defines versioned JSON schema for review results from Foreground Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ReviewComment:
    """A single review comment."""

    file: str
    line: int | None = None
    severity: str = "suggestion"  # "error", "warning", "suggestion", "info"
    message: str = ""
    category: str | None = None  # "security", "performance", "style", etc.


@dataclass
class ReviewArtifact:
    """
    Versioned review artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled"
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Scoring
    overall_score: float | None = None
    complexity_score: float | None = None
    security_score: float | None = None
    maintainability_score: float | None = None
    test_coverage_score: float | None = None
    performance_score: float | None = None
    linting_score: float | None = None
    type_checking_score: float | None = None
    duplication_score: float | None = None

    # Decision
    decision: str | None = None  # "APPROVED", "APPROVED_WITH_SUGGESTIONS", "CHANGES_REQUESTED"
    passed: bool | None = None
    threshold: float | None = None

    # Comments and findings
    comments: list[ReviewComment] = field(default_factory=list)
    security_findings: list[ReviewComment] = field(default_factory=list)
    refactoring_suggestions: list[ReviewComment] = field(default_factory=list)

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert ReviewComment objects to dicts
        data["comments"] = [asdict(comment) for comment in self.comments]
        data["security_findings"] = [asdict(finding) for finding in self.security_findings]
        data["refactoring_suggestions"] = [
            asdict(suggestion) for suggestion in self.refactoring_suggestions
        ]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewArtifact:
        """Create from dictionary."""
        # Convert comment dicts back to ReviewComment objects
        comments = []
        if "comments" in data:
            for comment_data in data["comments"]:
                comments.append(ReviewComment(**comment_data))
        data["comments"] = comments

        security_findings = []
        if "security_findings" in data:
            for finding_data in data["security_findings"]:
                security_findings.append(ReviewComment(**finding_data))
        data["security_findings"] = security_findings

        refactoring_suggestions = []
        if "refactoring_suggestions" in data:
            for suggestion_data in data["refactoring_suggestions"]:
                refactoring_suggestions.append(ReviewComment(**suggestion_data))
        data["refactoring_suggestions"] = refactoring_suggestions

        return cls(**data)

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
        self.status = "completed"
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
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark review as cancelled."""
        self.status = "cancelled"
        self.cancelled = True
