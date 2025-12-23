"""
Evaluation models for Tier 1 Enhancement: Evaluation & Quality Assurance Engine.

Provides data models for structured issues, evaluation results, and prompt tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IssueSeverity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueCategory(str, Enum):
    """Issue categories."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    CORRECTNESS = "correctness"
    COMPLIANCE = "compliance"
    UX = "ux"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class Issue:
    """
    Machine-actionable issue with structured information.
    
    Schema matches SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md requirements.
    """

    id: str
    severity: IssueSeverity
    category: IssueCategory
    evidence: str
    repro: str
    suggested_fix: str
    owner_step: str
    traceability: dict[str, Any] = field(default_factory=dict)
    file_path: str | None = None
    line_number: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category.value,
            "evidence": self.evidence,
            "repro": self.repro,
            "suggested_fix": self.suggested_fix,
            "owner_step": self.owner_step,
            "traceability": self.traceability,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "created_at": self.created_at.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Create Issue from dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data.get("created_at", datetime.now())
        )
        resolved_at = (
            datetime.fromisoformat(data["resolved_at"])
            if isinstance(data.get("resolved_at"), str)
            else data.get("resolved_at")
        )
        return cls(
            id=data["id"],
            severity=IssueSeverity(data["severity"]),
            category=IssueCategory(data["category"]),
            evidence=data["evidence"],
            repro=data["repro"],
            suggested_fix=data["suggested_fix"],
            owner_step=data["owner_step"],
            traceability=data.get("traceability", {}),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            created_at=created_at,
            resolved=data.get("resolved", False),
            resolved_at=resolved_at,
        )


@dataclass
class IssueManifest:
    """
    Collection of issues with aggregation and prioritization capabilities.
    
    Provides methods for deduplication, filtering, and traceability.
    """

    issues: list[Issue] = field(default_factory=list)

    def add_issue(self, issue: Issue) -> None:
        """Add an issue to the manifest."""
        self.issues.append(issue)

    def add_issues(self, issues: list[Issue]) -> None:
        """Add multiple issues to the manifest."""
        self.issues.extend(issues)

    def get_by_severity(self, severity: IssueSeverity) -> list[Issue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_by_category(self, category: IssueCategory) -> list[Issue]:
        """Get issues filtered by category."""
        return [issue for issue in self.issues if issue.category == category]

    def get_critical_issues(self) -> list[Issue]:
        """Get all critical issues."""
        return self.get_by_severity(IssueSeverity.CRITICAL)

    def get_high_issues(self) -> list[Issue]:
        """Get all high-severity issues."""
        return self.get_by_severity(IssueSeverity.HIGH)

    def count_by_severity(self) -> dict[IssueSeverity, int]:
        """Count issues by severity."""
        counts: dict[IssueSeverity, int] = {
            severity: 0 for severity in IssueSeverity
        }
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts

    def deduplicate(self) -> "IssueManifest":
        """Remove duplicate issues based on ID."""
        seen_ids: set[str] = set()
        unique_issues: list[Issue] = []
        for issue in self.issues:
            if issue.id not in seen_ids:
                seen_ids.add(issue.id)
                unique_issues.append(issue)
        return IssueManifest(issues=unique_issues)

    def merge(self, other: "IssueManifest") -> "IssueManifest":
        """Merge another manifest into this one."""
        merged = IssueManifest(issues=self.issues + other.issues)
        return merged.deduplicate()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": {
                "total": len(self.issues),
                "by_severity": {
                    k.value: v for k, v in self.count_by_severity().items()
                },
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueManifest":
        """Create IssueManifest from dictionary."""
        issues = [Issue.from_dict(issue_data) for issue_data in data.get("issues", [])]
        return cls(issues=issues)


@dataclass
class EvaluationResult:
    """
    Comprehensive evaluation result combining scores and issues.
    
    Provides structured output from multi-dimensional evaluation.
    """

    overall_score: float
    scores: dict[str, float]
    issues: IssueManifest
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def has_critical_issues(self) -> bool:
        """Check if evaluation has critical issues."""
        return len(self.issues.get_critical_issues()) > 0

    def has_high_issues(self) -> bool:
        """Check if evaluation has high-severity issues."""
        return len(self.issues.get_high_issues()) > 0

    def passes_threshold(self, threshold: float) -> bool:
        """Check if overall score passes threshold."""
        return self.overall_score >= threshold

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "scores": self.scores,
            "issues": self.issues.to_dict(),
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationResult":
        """Create EvaluationResult from dictionary."""
        timestamp = (
            datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data.get("timestamp", datetime.now())
        )
        return cls(
            overall_score=data["overall_score"],
            scores=data["scores"],
            issues=IssueManifest.from_dict(data["issues"]),
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
        )


@dataclass
class PromptVersion:
    """Tracks version and metadata for prompt variations."""

    id: str
    version: str
    prompt_text: str
    prompt_type: str  # "eval", "system", "instruction"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "version": self.version,
            "prompt_text": self.prompt_text,
            "prompt_type": self.prompt_type,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptVersion":
        """Create PromptVersion from dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data.get("created_at", datetime.now())
        )
        return cls(
            id=data["id"],
            version=data["version"],
            prompt_text=data["prompt_text"],
            prompt_type=data["prompt_type"],
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class FeedbackRecord:
    """Record of feedback from Cursor IDE interactions."""

    id: str
    agent_name: str
    command: str
    prompt_version_id: str | None
    accepted: bool
    feedback_text: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "command": self.command,
            "prompt_version_id": self.prompt_version_id,
            "accepted": self.accepted,
            "feedback_text": self.feedback_text,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeedbackRecord":
        """Create FeedbackRecord from dictionary."""
        timestamp = (
            datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data.get("timestamp", datetime.now())
        )
        return cls(
            id=data["id"],
            agent_name=data["agent_name"],
            command=data["command"],
            prompt_version_id=data.get("prompt_version_id"),
            accepted=data["accepted"],
            feedback_text=data.get("feedback_text"),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )

