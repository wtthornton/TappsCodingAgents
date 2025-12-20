"""
Unit tests for Progressive Review functionality (Epic 5).

Tests core logic for:
- ProgressiveReviewPolicy decision making
- ProgressiveReviewStorage save/load
- ProgressiveReviewRollup aggregation
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.progressive_review import (
    ProgressiveReview,
    ProgressiveReviewPolicy,
    ProgressiveReviewRollup,
    ProgressiveReviewStorage,
    ReviewDecision,
    ReviewFinding,
    ReviewMetrics,
    Severity,
)


class TestProgressiveReviewPolicy:
    """Test ProgressiveReviewPolicy decision logic."""

    def test_policy_pass_no_findings(self):
        """Test PASS decision when no findings."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])
        decision, reason = policy.determine_decision([])
        assert decision == ReviewDecision.PASS
        assert "No issues" in reason

    def test_policy_block_high_severity_security(self):
        """Test BLOCK decision for high severity security issues."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])
        findings = [
            ReviewFinding(
                id="SEC-001",
                severity=Severity.HIGH,
                category="security",
                file="test.py",
                finding="SQL injection vulnerability",
            )
        ]
        decision, reason = policy.determine_decision(findings)
        assert decision == ReviewDecision.BLOCK
        assert "blocking" in reason.lower()
        assert "security" in reason.lower()

    def test_policy_block_high_severity_performance(self):
        """Test BLOCK decision for high severity performance issues."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])
        findings = [
            ReviewFinding(
                id="PERF-001",
                severity=Severity.HIGH,
                category="performance",
                file="test.py",
                finding="Blocking operation in async function",
            )
        ]
        decision, reason = policy.determine_decision(findings)
        assert decision == ReviewDecision.BLOCK

    def test_policy_concerns_medium_severity(self):
        """Test CONCERNS decision for medium severity issues."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])
        findings = [
            ReviewFinding(
                id="MAINT-001",
                severity=Severity.MEDIUM,
                category="code_quality",
                file="test.py",
                finding="Maintainability issue",
            )
        ]
        decision, reason = policy.determine_decision(findings)
        assert decision == ReviewDecision.CONCERNS
        assert "non-blocking" in reason.lower() or "concern" in reason.lower()

    def test_policy_concerns_low_severity(self):
        """Test CONCERNS decision for low severity issues."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])
        findings = [
            ReviewFinding(
                id="LINT-001",
                severity=Severity.LOW,
                category="standards",
                file="test.py",
                finding="Minor linting issue",
            )
        ]
        decision, reason = policy.determine_decision(findings)
        assert decision == ReviewDecision.CONCERNS

    def test_policy_mixed_severities_blocks(self):
        """Test that mixed severities with high severity blocks."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high"])
        findings = [
            ReviewFinding(
                id="SEC-001",
                severity=Severity.HIGH,
                category="security",
                file="test.py",
                finding="Critical security issue",
            ),
            ReviewFinding(
                id="LINT-001",
                severity=Severity.LOW,
                category="standards",
                file="test.py",
                finding="Minor linting issue",
            ),
        ]
        decision, reason = policy.determine_decision(findings)
        assert decision == ReviewDecision.BLOCK

    def test_policy_custom_severity_blocks(self):
        """Test custom severity blocks configuration."""
        policy = ProgressiveReviewPolicy(severity_blocks=["high", "medium"])
        findings = [
            ReviewFinding(
                id="MAINT-001",
                severity=Severity.MEDIUM,
                category="code_quality",
                file="test.py",
                finding="Medium severity issue",
            )
        ]
        decision, reason = policy.determine_decision(findings)
        assert decision == ReviewDecision.BLOCK


class TestProgressiveReviewStorage:
    """Test ProgressiveReviewStorage save/load operations."""

    def test_save_and_load_review(self, tmp_path):
        """Test saving and loading a review."""
        storage = ProgressiveReviewStorage(tmp_path, review_location="qa/progressive")

        review = ProgressiveReview(
            story_id="1.3",
            task_number=2,
            task_title="Test Task",
            decision=ReviewDecision.CONCERNS,
            decision_reason="Test reason",
            findings=[
                ReviewFinding(
                    id="TEST-001",
                    severity=Severity.MEDIUM,
                    category="testing",
                    file="test.py",
                    finding="Test finding",
                )
            ],
        )

        # Save
        saved_path = storage.save_review(review)
        assert saved_path.exists()

        # Load
        loaded_review = storage.load_review("1.3", 2)
        assert loaded_review is not None
        assert loaded_review.story_id == "1.3"
        assert loaded_review.task_number == 2
        assert loaded_review.decision == ReviewDecision.CONCERNS
        assert len(loaded_review.findings) == 1
        assert loaded_review.findings[0].id == "TEST-001"

    def test_load_nonexistent_review(self, tmp_path):
        """Test loading a review that doesn't exist."""
        storage = ProgressiveReviewStorage(tmp_path)
        loaded = storage.load_review("999.999", 999)
        assert loaded is None

    def test_naming_convention(self, tmp_path):
        """Test that naming convention is correct."""
        storage = ProgressiveReviewStorage(tmp_path)
        path = storage.get_review_path("1.3", 2)
        assert path.name == "1.3-task-2.yml"
        assert "qa" in str(path) or "progressive" in str(path)

    def test_load_all_for_story(self, tmp_path):
        """Test loading all reviews for a story."""
        storage = ProgressiveReviewStorage(tmp_path)

        # Create multiple reviews for same story
        for task_num in [1, 2, 3]:
            review = ProgressiveReview(
                story_id="1.3",
                task_number=task_num,
                decision=ReviewDecision.PASS,
            )
            storage.save_review(review)

        # Load all
        reviews = storage.load_all_for_story("1.3")
        assert len(reviews) == 3
        assert all(r.story_id == "1.3" for r in reviews)
        task_numbers = sorted([r.task_number for r in reviews])
        assert task_numbers == [1, 2, 3]

    def test_story_id_normalization(self, tmp_path):
        """Test that story IDs with path separators are normalized."""
        storage = ProgressiveReviewStorage(tmp_path)
        path = storage.get_review_path("epic/1.3", 2)
        assert "/" not in path.name
        assert "\\" not in path.name
        assert "epic.1.3-task-2.yml" == path.name or "1.3-task-2.yml" in path.name


class TestProgressiveReviewRollup:
    """Test ProgressiveReviewRollup aggregation logic."""

    def test_rollup_empty_story(self, tmp_path):
        """Test rollup for story with no reviews."""
        storage = ProgressiveReviewStorage(tmp_path)
        rollup = ProgressiveReviewRollup(storage)
        result = rollup.rollup_story_reviews("999.999")
        assert result["total_tasks"] == 0
        assert result["total_findings"] == 0
        assert len(result["blocking_issues"]) == 0
        assert len(result["deferred_concerns"]) == 0

    def test_rollup_single_review_pass(self, tmp_path):
        """Test rollup for story with single PASS review."""
        storage = ProgressiveReviewStorage(tmp_path)
        rollup = ProgressiveReviewRollup(storage)

        review = ProgressiveReview(
            story_id="1.3",
            task_number=1,
            decision=ReviewDecision.PASS,
            findings=[],
        )
        storage.save_review(review)

        result = rollup.rollup_story_reviews("1.3")
        assert result["total_tasks"] == 1
        assert result["total_findings"] == 0
        assert result["decision_summary"][ReviewDecision.PASS.value] == 1
        assert result["decision_summary"][ReviewDecision.CONCERNS.value] == 0
        assert result["decision_summary"][ReviewDecision.BLOCK.value] == 0

    def test_rollup_blocking_issues(self, tmp_path):
        """Test rollup captures blocking issues."""
        storage = ProgressiveReviewStorage(tmp_path)
        rollup = ProgressiveReviewRollup(storage)

        review = ProgressiveReview(
            story_id="1.3",
            task_number=1,
            decision=ReviewDecision.BLOCK,
            findings=[
                ReviewFinding(
                    id="SEC-001",
                    severity=Severity.HIGH,
                    category="security",
                    file="test.py",
                    finding="Critical security issue",
                )
            ],
        )
        storage.save_review(review)

        result = rollup.rollup_story_reviews("1.3")
        assert result["total_tasks"] == 1
        assert result["total_findings"] == 1
        assert len(result["blocking_issues"]) == 1
        assert result["blocking_issues"][0]["id"] == "SEC-001"
        assert result["blocking_issues"][0]["severity"] == "high"

    def test_rollup_deferred_concerns(self, tmp_path):
        """Test rollup captures deferred concerns."""
        storage = ProgressiveReviewStorage(tmp_path)
        rollup = ProgressiveReviewRollup(storage)

        review = ProgressiveReview(
            story_id="1.3",
            task_number=1,
            decision=ReviewDecision.CONCERNS,
            developer_action="deferred",
            deferred_reason="Will fix in next iteration",
            findings=[
                ReviewFinding(
                    id="MAINT-001",
                    severity=Severity.MEDIUM,
                    category="code_quality",
                    file="test.py",
                    finding="Maintainability issue",
                )
            ],
        )
        storage.save_review(review)

        result = rollup.rollup_story_reviews("1.3")
        assert result["total_tasks"] == 1
        assert len(result["deferred_concerns"]) == 1
        assert result["deferred_concerns"][0]["id"] == "MAINT-001"
        assert "deferred_reason" in result["deferred_concerns"][0]

    def test_rollup_multiple_tasks(self, tmp_path):
        """Test rollup aggregates multiple task reviews."""
        storage = ProgressiveReviewStorage(tmp_path)
        rollup = ProgressiveReviewRollup(storage)

        # Create multiple reviews
        for task_num, decision in [
            (1, ReviewDecision.PASS),
            (2, ReviewDecision.CONCERNS),
            (3, ReviewDecision.BLOCK),
        ]:
            review = ProgressiveReview(
                story_id="1.3",
                task_number=task_num,
                decision=decision,
                findings=[
                    ReviewFinding(
                        id=f"FIND-{task_num}",
                        severity=Severity.MEDIUM,
                        category="testing",
                        file="test.py",
                        finding=f"Finding {task_num}",
                    )
                ]
                if decision != ReviewDecision.PASS
                else [],
            )
            storage.save_review(review)

        result = rollup.rollup_story_reviews("1.3")
        assert result["total_tasks"] == 3
        assert result["total_findings"] == 2  # PASS has no findings
        assert result["decision_summary"][ReviewDecision.PASS.value] == 1
        assert result["decision_summary"][ReviewDecision.CONCERNS.value] == 1
        assert result["decision_summary"][ReviewDecision.BLOCK.value] == 1
        assert len(result["evidence"]) == 3  # Three review files

    def test_rollup_evidence_paths(self, tmp_path):
        """Test that rollup includes evidence file paths."""
        storage = ProgressiveReviewStorage(tmp_path)
        rollup = ProgressiveReviewRollup(storage)

        review = ProgressiveReview(
            story_id="1.3",
            task_number=1,
            decision=ReviewDecision.PASS,
        )
        storage.save_review(review)

        result = rollup.rollup_story_reviews("1.3")
        assert len(result["evidence"]) == 1
        assert "1.3-task-1.yml" in result["evidence"][0] or "progressive" in result["evidence"][0]


class TestProgressiveReviewSerialization:
    """Test ProgressiveReview YAML serialization."""

    def test_to_dict_roundtrip(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = ProgressiveReview(
            story_id="1.3",
            task_number=2,
            task_title="Test Task",
            reviewed_at=datetime(2025, 12, 18, 10, 30, 0),
            reviewer="Test Reviewer",
            decision=ReviewDecision.CONCERNS,
            decision_reason="Test reason",
            findings=[
                ReviewFinding(
                    id="TEST-001",
                    severity=Severity.MEDIUM,
                    category="testing",
                    file="test.py",
                    line=42,
                    finding="Test finding",
                    impact="Test impact",
                    suggested_fix="Test fix",
                    references=["ref1", "ref2"],
                )
            ],
            metrics=ReviewMetrics(
                files_reviewed=1,
                lines_changed=100,
                test_coverage_delta="+5%",
            ),
            developer_action="deferred",
            deferred_reason="Will fix later",
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = ProgressiveReview.from_dict(data)

        assert restored.story_id == original.story_id
        assert restored.task_number == original.task_number
        assert restored.task_title == original.task_title
        assert restored.decision == original.decision
        assert restored.decision_reason == original.decision_reason
        assert len(restored.findings) == len(original.findings)
        assert restored.findings[0].id == original.findings[0].id
        assert restored.findings[0].severity == original.findings[0].severity
        assert restored.metrics.files_reviewed == original.metrics.files_reviewed
        assert restored.developer_action == original.developer_action

