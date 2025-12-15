"""
Unit tests for Testing Artifact schema.
"""

from __future__ import annotations

import json

import pytest

from tapps_agents.workflow.testing_artifact import (
    CoverageSummary,
    TestingArtifact,
    TestResult,
)


@pytest.mark.unit
class TestTestingArtifact:
    """Test TestingArtifact schema."""

    def test_artifact_creation(self) -> None:
        """Test creating a testing artifact."""
        artifact = TestingArtifact(
            worktree_path="/test/worktree",
            correlation_id="test-123",
            coverage_enabled=True,
        )

        assert artifact.schema_version == "1.0"
        assert artifact.worktree_path == "/test/worktree"
        assert artifact.correlation_id == "test-123"
        assert artifact.status == "pending"
        assert artifact.coverage_enabled is True
        assert artifact.tests_run is False

    def test_mark_completed(self) -> None:
        """Test marking artifact as completed."""
        artifact = TestingArtifact()
        artifact.total_tests = 10
        artifact.passed_tests = 8
        artifact.failed_tests = 2

        artifact.mark_completed()

        assert artifact.status == "completed"
        assert artifact.tests_run is True
        assert artifact.success_rate == 80.0  # 8/10 * 100

    def test_mark_failed(self) -> None:
        """Test marking artifact as failed."""
        artifact = TestingArtifact()
        artifact.mark_failed("Test execution error")

        assert artifact.status == "failed"
        assert artifact.error == "Test execution error"
        assert artifact.tests_run is True

    def test_mark_cancelled(self) -> None:
        """Test marking artifact as cancelled."""
        artifact = TestingArtifact()
        artifact.mark_cancelled()

        assert artifact.status == "cancelled"
        assert artifact.cancelled is True

    def test_mark_timeout(self) -> None:
        """Test marking artifact as timed out."""
        artifact = TestingArtifact()
        artifact.mark_timeout()

        assert artifact.status == "timeout"
        assert artifact.timeout is True

    def test_mark_not_run(self) -> None:
        """Test marking tests as not run."""
        artifact = TestingArtifact()
        artifact.mark_not_run("pytest not available")

        assert artifact.status == "not_run"
        assert artifact.not_run_reason == "pytest not available"
        assert artifact.tests_run is False

    def test_coverage_summary(self) -> None:
        """Test coverage summary."""
        coverage = CoverageSummary(
            total_lines=100,
            covered_lines=80,
            coverage_percentage=80.0,
            branch_coverage=75.0,
            statement_coverage=80.0,
        )

        assert coverage.total_lines == 100
        assert coverage.covered_lines == 80
        assert coverage.coverage_percentage == 80.0

    def test_json_serialization(self) -> None:
        """Test JSON serialization and deserialization."""
        artifact = TestingArtifact(
            worktree_path="/test/worktree",
            correlation_id="test-123",
        )

        artifact.total_tests = 10
        artifact.passed_tests = 8
        artifact.failed_tests = 2
        artifact.coverage = CoverageSummary(
            total_lines=100,
            covered_lines=80,
            coverage_percentage=80.0,
        )

        test_result = TestResult(
            test_name="test_example",
            status="passed",
            duration_seconds=0.5,
        )
        artifact.test_results.append(test_result)
        artifact.mark_completed()

        # Serialize
        artifact_dict = artifact.to_dict()
        json_str = json.dumps(artifact_dict)

        # Deserialize
        loaded_dict = json.loads(json_str)
        loaded_artifact = TestingArtifact.from_dict(loaded_dict)

        assert loaded_artifact.schema_version == artifact.schema_version
        assert loaded_artifact.worktree_path == artifact.worktree_path
        assert loaded_artifact.status == artifact.status
        assert loaded_artifact.total_tests == 10
        assert loaded_artifact.passed_tests == 8
        assert loaded_artifact.success_rate == 80.0
        assert loaded_artifact.coverage is not None
        assert loaded_artifact.coverage.coverage_percentage == 80.0
        assert len(loaded_artifact.test_results) == 1
        assert loaded_artifact.test_results[0].test_name == "test_example"
