"""
Progressive Task-Level Review Module

Implements Epic 5: Autonomous Progressive Task-Level Review
Integrates with BMAD's progressive review automation to provide
task-level reviews that catch issues early.

Based on: .bmad-core/tasks/progressive-code-review.md
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ReviewDecision(str, Enum):
    """Progressive review decision types."""

    PASS = "PASS"
    CONCERNS = "CONCERNS"
    BLOCK = "BLOCK"


class Severity(str, Enum):
    """Issue severity levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ReviewFinding:
    """A single finding from a progressive review."""

    id: str
    severity: Severity
    category: str  # security, performance, testing, standards, code_quality
    file: str
    line: int | None = None
    finding: str = ""
    impact: str = ""
    suggested_fix: str = ""
    references: list[str] = field(default_factory=list)


@dataclass
class ReviewMetrics:
    """Metrics about the reviewed code."""

    files_reviewed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    lines_changed: int = 0
    test_files: int = 0
    test_coverage_delta: str = ""


@dataclass
class ProgressiveReview:
    """
    Progressive task-level review result.

    Aligned with BMAD's progressive review format from
    .bmad-core/tasks/progressive-code-review.md
    """

    story_id: str
    task_number: int
    task_title: str = ""
    reviewed_at: datetime = field(default_factory=datetime.utcnow)
    reviewer: str = "TappsCodingAgents Progressive Review"
    decision: ReviewDecision = ReviewDecision.PASS
    decision_reason: str = ""
    findings: list[ReviewFinding] = field(default_factory=list)
    metrics: ReviewMetrics = field(default_factory=ReviewMetrics)
    developer_action: str = ""  # "fixed", "deferred", or empty
    deferred_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "schema": 1,
            "story": self.story_id,
            "task": self.task_number,
            "task_title": self.task_title,
            "reviewed_at": self.reviewed_at.isoformat(),
            "reviewer": self.reviewer,
            "decision": self.decision.value,
            "decision_reason": self.decision_reason,
            "findings": [
                {
                    "id": f.id,
                    "severity": f.severity.value,
                    "category": f.category,
                    "file": f.file,
                    "line": f.line,
                    "finding": f.finding,
                    "impact": f.impact,
                    "suggested_fix": f.suggested_fix,
                    "references": f.references,
                }
                for f in self.findings
            ],
            "metrics": {
                "files_reviewed": self.metrics.files_reviewed,
                "lines_changed": self.metrics.lines_changed,
                "test_coverage_delta": self.metrics.test_coverage_delta,
            },
            "developer_action": self.developer_action,
            "deferred_reason": self.deferred_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgressiveReview":
        """Create from dictionary (YAML deserialization)."""
        findings = [
            ReviewFinding(
                id=f["id"],
                severity=Severity(f["severity"]),
                category=f["category"],
                file=f["file"],
                line=f.get("line"),
                finding=f.get("finding", ""),
                impact=f.get("impact", ""),
                suggested_fix=f.get("suggested_fix", ""),
                references=f.get("references", []),
            )
            for f in data.get("findings", [])
        ]

        metrics_data = data.get("metrics", {})
        metrics = ReviewMetrics(
            files_reviewed=metrics_data.get("files_reviewed", 0),
            lines_changed=metrics_data.get("lines_changed", 0),
            test_coverage_delta=metrics_data.get("test_coverage_delta", ""),
        )

        return cls(
            story_id=data["story"],
            task_number=data["task"],
            task_title=data.get("task_title", ""),
            reviewed_at=datetime.fromisoformat(data["reviewed_at"]),
            reviewer=data.get("reviewer", ""),
            decision=ReviewDecision(data["decision"]),
            decision_reason=data.get("decision_reason", ""),
            findings=findings,
            metrics=metrics,
            developer_action=data.get("developer_action", ""),
            deferred_reason=data.get("deferred_reason", ""),
        )


class ProgressiveReviewStorage:
    """
    Handles storage and retrieval of progressive reviews.

    Story 37.2: Task Review Storage and Naming Conventions
    """

    def __init__(self, project_root: Path, review_location: str = "docs/qa/progressive"):
        """
        Initialize storage.

        Args:
            project_root: Project root directory
            review_location: Relative path for storing reviews (BMAD convention)
        """
        self.project_root = project_root
        self.review_dir = project_root / review_location
        self.review_dir.mkdir(parents=True, exist_ok=True)

    def get_review_path(self, story_id: str, task_number: int) -> Path:
        """
        Get file path for a review.

        Naming convention: {epic}.{story}-task-{n}.yml
        Example: 1.3-task-2.yml

        Args:
            story_id: Story identifier (e.g., "1.3")
            task_number: Task number

        Returns:
            Path to review file
        """
        # Normalize story_id (remove any path separators)
        safe_story_id = story_id.replace("/", ".").replace("\\", ".")
        filename = f"{safe_story_id}-task-{task_number}.yml"
        return self.review_dir / filename

    def save_review(self, review: ProgressiveReview) -> Path:
        """
        Save a progressive review to disk.

        Args:
            review: Review to save

        Returns:
            Path to saved file
        """
        path = self.get_review_path(review.story_id, review.task_number)
        data = review.to_dict()

        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved progressive review to {path}")
        return path

    def load_review(self, story_id: str, task_number: int) -> ProgressiveReview | None:
        """
        Load a progressive review from disk.

        Args:
            story_id: Story identifier
            task_number: Task number

        Returns:
            Review if found, None otherwise
        """
        path = self.get_review_path(story_id, task_number)
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return ProgressiveReview.from_dict(data)

    def load_all_for_story(self, story_id: str) -> list[ProgressiveReview]:
        """
        Load all progressive reviews for a story.

        Args:
            story_id: Story identifier

        Returns:
            List of reviews, sorted by task number
        """
        safe_story_id = story_id.replace("/", ".").replace("\\", ".")
        pattern = f"{safe_story_id}-task-*.yml"
        reviews = []

        for path in self.review_dir.glob(pattern):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    reviews.append(ProgressiveReview.from_dict(data))
            except Exception as e:
                logger.warning(f"Failed to load review from {path}: {e}")

        # Sort by task number
        reviews.sort(key=lambda r: r.task_number)
        return reviews


class ProgressiveReviewPolicy:
    """
    Defines review policy and decision logic.

    Story 37.1: Progressive Review Policy and Output Format
    """

    def __init__(self, severity_blocks: list[str] | None = None):
        """
        Initialize policy.

        Args:
            severity_blocks: List of severities that block progress (default: ["high"])
        """
        self.severity_blocks = severity_blocks or ["high"]

    def determine_decision(
        self, findings: list[ReviewFinding]
    ) -> tuple[ReviewDecision, str]:
        """
        Determine review decision based on findings.

        Decision logic (aligned with BMAD):
        - BLOCK: Any high severity security issues, critical performance problems,
                 missing tests for critical paths, violates mandatory architecture
        - CONCERNS: Medium severity issues, non-critical performance improvements,
                   test coverage gaps for edge cases, minor standards violations
        - PASS: No blocking issues, all critical paths tested, follows standards

        Args:
            findings: List of review findings

        Returns:
            Tuple of (decision, reason)
        """
        if not findings:
            return ReviewDecision.PASS, "No issues found"

        # Check for blocking issues
        blocking_findings = [
            f
            for f in findings
            if f.severity.value in self.severity_blocks
            or (f.severity == Severity.HIGH and f.category == "security")
            or (f.severity == Severity.HIGH and f.category == "performance")
        ]

        if blocking_findings:
            blocking_count = len(blocking_findings)
            categories = ", ".join(set(f.category for f in blocking_findings))
            return (
                ReviewDecision.BLOCK,
                f"{blocking_count} blocking issue(s) found in {categories}",
            )

        # Check for concerns
        concern_findings = [
            f for f in findings if f.severity == Severity.MEDIUM or f.severity == Severity.LOW
        ]

        if concern_findings:
            concern_count = len(concern_findings)
            return (
                ReviewDecision.CONCERNS,
                f"{concern_count} non-blocking issue(s) found",
            )

        return ReviewDecision.PASS, "All issues are low severity or informational"


class ProgressiveReviewRollup:
    """
    Handles rollup of progressive reviews into final QA summary.

    Story 37.4: Final QA Rollup Rules
    """

    def __init__(self, storage: ProgressiveReviewStorage):
        """
        Initialize rollup.

        Args:
            storage: Progressive review storage instance
        """
        self.storage = storage

    def rollup_story_reviews(
        self, story_id: str
    ) -> dict[str, Any]:
        """
        Rollup all progressive reviews for a story into final QA summary.

        Args:
            story_id: Story identifier

        Returns:
            Rollup summary with:
            - total_tasks: Number of tasks reviewed
            - total_findings: Total number of findings
            - blocking_issues: List of blocking issues
            - deferred_concerns: List of deferred concerns
            - decision_summary: Summary of decisions
            - evidence: List of review file paths
        """
        reviews = self.storage.load_all_for_story(story_id)

        if not reviews:
            return {
                "total_tasks": 0,
                "total_findings": 0,
                "blocking_issues": [],
                "deferred_concerns": [],
                "decision_summary": {},
                "evidence": [],
            }

        total_findings = sum(len(r.findings) for r in reviews)
        blocking_issues = []
        deferred_concerns = []
        decision_counts = {
            ReviewDecision.PASS.value: 0,
            ReviewDecision.CONCERNS.value: 0,
            ReviewDecision.BLOCK.value: 0,
        }

        for review in reviews:
            decision_counts[review.decision.value] += 1

            # Collect blocking issues
            if review.decision == ReviewDecision.BLOCK:
                blocking_issues.extend(review.findings)

            # Collect deferred concerns
            if review.decision == ReviewDecision.CONCERNS and review.developer_action == "deferred":
                deferred_concerns.extend(review.findings)

        evidence = [
            str(self.storage.get_review_path(r.story_id, r.task_number))
            for r in reviews
        ]

        return {
            "total_tasks": len(reviews),
            "total_findings": total_findings,
            "blocking_issues": [
                {
                    "id": f.id,
                    "severity": f.severity.value,
                    "category": f.category,
                    "file": f.file,
                    "finding": f.finding,
                }
                for f in blocking_issues
            ],
            "deferred_concerns": [
                {
                    "id": f.id,
                    "severity": f.severity.value,
                    "category": f.category,
                    "file": f.file,
                    "finding": f.finding,
                    "deferred_reason": review.deferred_reason,
                }
                for review in reviews
                for f in review.findings
                if review.developer_action == "deferred"
            ],
            "decision_summary": decision_counts,
            "evidence": evidence,
        }

