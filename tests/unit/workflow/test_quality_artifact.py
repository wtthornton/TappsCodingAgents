"""
Unit tests for Quality Artifact schema.
"""

from __future__ import annotations

import json

import pytest

from tapps_agents.workflow.quality_artifact import QualityArtifact, ToolResult


@pytest.mark.unit
class TestQualityArtifact:
    """Test QualityArtifact schema."""

    def test_artifact_creation(self) -> None:
        """Test creating a quality artifact."""
        artifact = QualityArtifact(
            worktree_path="/test/worktree",
            correlation_id="test-123",
        )

        assert artifact.schema_version == "1.0"
        assert artifact.worktree_path == "/test/worktree"
        assert artifact.correlation_id == "test-123"
        assert artifact.status == "pending"
        assert len(artifact.tools) == 0

    def test_add_tool_result(self) -> None:
        """Test adding tool results."""
        artifact = QualityArtifact()

        tool_result = ToolResult(
            tool_name="ruff",
            available=True,
            status="success",
            issue_count=5,
            error_count=2,
            warning_count=3,
        )

        artifact.add_tool_result("ruff", tool_result)

        assert "ruff" in artifact.tools
        assert artifact.total_issues == 5
        assert artifact.total_errors == 2
        assert artifact.total_warnings == 3

    def test_mark_completed(self) -> None:
        """Test marking artifact as completed."""
        artifact = QualityArtifact()
        artifact.scores["linting"] = 8.5
        artifact.scores["type_checking"] = 9.0

        artifact.mark_completed()

        assert artifact.status == "completed"
        assert artifact.overall_score == 8.75  # Average of 8.5 and 9.0

    def test_mark_failed(self) -> None:
        """Test marking artifact as failed."""
        artifact = QualityArtifact()
        artifact.mark_failed("Test error")

        assert artifact.status == "failed"
        assert artifact.error == "Test error"

    def test_mark_cancelled(self) -> None:
        """Test marking artifact as cancelled."""
        artifact = QualityArtifact()
        artifact.mark_cancelled()

        assert artifact.status == "cancelled"
        assert artifact.cancelled is True

    def test_mark_timeout(self) -> None:
        """Test marking artifact as timed out."""
        artifact = QualityArtifact()
        artifact.mark_timeout()

        assert artifact.status == "timeout"
        assert artifact.timeout is True

    def test_json_serialization(self) -> None:
        """Test JSON serialization and deserialization."""
        artifact = QualityArtifact(
            worktree_path="/test/worktree",
            correlation_id="test-123",
        )

        tool_result = ToolResult(
            tool_name="ruff",
            available=True,
            status="success",
            issue_count=5,
        )
        artifact.add_tool_result("ruff", tool_result)
        artifact.scores["linting"] = 8.5
        artifact.mark_completed()

        # Serialize
        artifact_dict = artifact.to_dict()
        json_str = json.dumps(artifact_dict)

        # Deserialize
        loaded_dict = json.loads(json_str)
        loaded_artifact = QualityArtifact.from_dict(loaded_dict)

        assert loaded_artifact.schema_version == artifact.schema_version
        assert loaded_artifact.worktree_path == artifact.worktree_path
        assert loaded_artifact.status == artifact.status
        assert "ruff" in loaded_artifact.tools
        assert loaded_artifact.tools["ruff"].tool_name == "ruff"
        assert loaded_artifact.scores["linting"] == 8.5
