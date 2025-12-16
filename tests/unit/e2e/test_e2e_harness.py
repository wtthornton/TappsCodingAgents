"""
Unit tests for E2E harness utilities.

Tests project template creation, artifact capture, and cleanup utilities.
"""

import json
import tempfile
from pathlib import Path

import pytest

from tests.e2e.fixtures.e2e_harness import (
    create_test_project,
    capture_artifacts,
    assert_artifact_exists,
    assert_artifact_content,
    assert_json_artifact_shape,
    cleanup_project,
    generate_correlation_id,
    capture_state_snapshot,
    create_failure_bundle,
    redact_secrets,
)
from tests.e2e.fixtures.project_templates import create_minimal_template, create_small_template, create_medium_template

pytestmark = pytest.mark.unit


class TestProjectTemplates:
    """Test project template creation."""

    def test_create_minimal_template(self, tmp_path: Path):
        """Test minimal template creation."""
        project_path = tmp_path / "minimal_project"
        result = create_minimal_template(project_path)

        assert result == project_path
        assert project_path.exists()
        assert (project_path / "main.py").exists()
        assert (project_path / ".tapps-agents").exists()

        # Verify main.py content
        main_content = (project_path / "main.py").read_text()
        assert "def hello()" in main_content

    def test_create_small_template(self, tmp_path: Path):
        """Test small template creation."""
        project_path = tmp_path / "small_project"
        result = create_small_template(project_path)

        assert result == project_path
        assert project_path.exists()
        assert (project_path / "src" / "calculator.py").exists()
        assert (project_path / "tests" / "test_calculator.py").exists()
        assert (project_path / ".tapps-agents").exists()

    def test_create_medium_template(self, tmp_path: Path):
        """Test medium template creation."""
        project_path = tmp_path / "medium_project"
        result = create_medium_template(project_path)

        assert result == project_path
        assert project_path.exists()
        assert (project_path / "src" / "mypackage" / "core.py").exists()
        assert (project_path / "src" / "mypackage" / "utils.py").exists()
        assert (project_path / "tests" / "test_core.py").exists()
        assert (project_path / "tests" / "test_utils.py").exists()
        assert (project_path / ".tapps-agents" / "workflow-state").exists()
        assert (project_path / ".tapps-agents" / "worktrees").exists()
        assert (project_path / "requirements.txt").exists()
        assert (project_path / "pyproject.toml").exists()

    def test_create_test_project_minimal(self, tmp_path: Path):
        """Test create_test_project with minimal template."""
        project_path = create_test_project("minimal", tmp_path)

        assert project_path.exists()
        assert (project_path / "main.py").exists()

    def test_create_test_project_small(self, tmp_path: Path):
        """Test create_test_project with small template."""
        project_path = create_test_project("small", tmp_path)

        assert project_path.exists()
        assert (project_path / "src").exists()

    def test_create_test_project_medium(self, tmp_path: Path):
        """Test create_test_project with medium template."""
        project_path = create_test_project("medium", tmp_path)

        assert project_path.exists()
        assert (project_path / "src" / "mypackage").exists()


class TestArtifactCapture:
    """Test artifact capture utilities."""

    def test_capture_artifacts_basic(self, tmp_path: Path):
        """Test basic artifact capture."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        (project_path / ".tapps-agents").mkdir()

        # Create a test file
        test_file = project_path / "test.txt"
        test_file.write_text("test content")

        artifacts = capture_artifacts(project_path, "test_name")

        assert "correlation_id" in artifacts
        assert "test_name" in artifacts
        assert artifacts["test_name"] == "test_name"
        assert "artifacts" in artifacts
        assert any("test.txt" in a for a in artifacts["artifacts"])

    def test_capture_artifacts_with_logs(self, tmp_path: Path):
        """Test artifact capture with logs."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        config_dir = project_path / ".tapps-agents"
        config_dir.mkdir()
        logs_dir = config_dir / "logs"
        logs_dir.mkdir()

        # Create a log file
        log_file = logs_dir / "test.log"
        log_file.write_text("log content")

        artifacts = capture_artifacts(project_path, "test_name")

        assert len(artifacts["logs"]) > 0
        assert any("test.log" in log for log in artifacts["logs"])

    def test_capture_artifacts_with_state(self, tmp_path: Path):
        """Test artifact capture with workflow state."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        config_dir = project_path / ".tapps-agents"
        config_dir.mkdir()
        state_dir = config_dir / "workflow-state"
        state_dir.mkdir()

        # Create a state file
        state_file = state_dir / "state.json"
        state_file.write_text(json.dumps({"status": "running"}))

        artifacts = capture_artifacts(project_path, "test_name")

        assert len(artifacts["state_snapshots"]) > 0
        assert any("state.json" in s for s in artifacts["state_snapshots"])

    def test_assert_artifact_exists(self, tmp_path: Path):
        """Test assert_artifact_exists."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        test_file = project_path / "test.txt"
        test_file.write_text("content")

        # Should not raise
        assert_artifact_exists(project_path, "test.txt")

        # Should raise
        with pytest.raises(AssertionError):
            assert_artifact_exists(project_path, "nonexistent.txt")

    def test_assert_artifact_content(self, tmp_path: Path):
        """Test assert_artifact_content."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        test_file = project_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Should not raise
        assert_artifact_content(project_path, "test.txt", "Hello")

        # Should raise
        with pytest.raises(AssertionError):
            assert_artifact_content(project_path, "test.txt", "Goodbye")

    def test_assert_json_artifact_shape(self, tmp_path: Path):
        """Test assert_json_artifact_shape."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        json_file = project_path / "data.json"
        json_file.write_text(json.dumps({"key1": "value1", "key2": "value2"}))

        # Should not raise
        result = assert_json_artifact_shape(project_path, "data.json", ["key1", "key2"])
        assert result["key1"] == "value1"

        # Should raise for missing key
        with pytest.raises(AssertionError):
            assert_json_artifact_shape(project_path, "data.json", ["key1", "key3"])

        # Should raise for invalid JSON
        invalid_json = project_path / "invalid.json"
        invalid_json.write_text("{ invalid json }")
        with pytest.raises(AssertionError):
            assert_json_artifact_shape(project_path, "invalid.json", ["key1"])


class TestCleanup:
    """Test cleanup utilities."""

    def test_cleanup_project(self, tmp_path: Path):
        """Test project cleanup."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        test_file = project_path / "test.txt"
        test_file.write_text("content")

        assert project_path.exists()

        cleanup_project(project_path)

        assert not project_path.exists()

    def test_cleanup_project_idempotent(self, tmp_path: Path):
        """Test that cleanup is idempotent."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        cleanup_project(project_path)
        # Should not raise on second call
        cleanup_project(project_path)

        assert not project_path.exists()

    def test_cleanup_nonexistent_project(self, tmp_path: Path):
        """Test cleanup of nonexistent project."""
        project_path = tmp_path / "nonexistent"

        # Should not raise
        cleanup_project(project_path)


class TestCorrelationID:
    """Test correlation ID generation."""

    def test_generate_correlation_id(self):
        """Test correlation ID generation."""
        corr_id = generate_correlation_id()

        assert corr_id.startswith("e2e-")
        assert len(corr_id) > 10

    def test_generate_correlation_id_unique(self):
        """Test that correlation IDs are unique."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()

        # IDs should be different (very unlikely to be the same)
        assert id1 != id2


class TestStateSnapshots:
    """Test state snapshot capture."""

    def test_capture_state_snapshot(self, tmp_path: Path):
        """Test state snapshot capture."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        config_dir = project_path / ".tapps-agents"
        config_dir.mkdir()
        state_dir = config_dir / "workflow-state"
        state_dir.mkdir()

        snapshot = capture_state_snapshot(project_path, "test_snapshot")

        assert snapshot["name"] == "test_snapshot"
        assert "timestamp" in snapshot
        assert "project_structure" in snapshot

    def test_capture_state_snapshot_with_workflow_state(self, tmp_path: Path):
        """Test state snapshot with workflow state."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        config_dir = project_path / ".tapps-agents"
        config_dir.mkdir()
        state_dir = config_dir / "workflow-state"
        state_dir.mkdir()

        state_file = state_dir / "state.json"
        state_file.write_text(json.dumps({"status": "running", "step": 1}))

        snapshot = capture_state_snapshot(project_path, "test_snapshot")

        assert snapshot["workflow_state"] is not None
        assert snapshot["workflow_state"]["status"] == "running"


class TestFailureBundle:
    """Test failure bundle creation."""

    def test_create_failure_bundle(self, tmp_path: Path):
        """Test failure bundle creation."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        error = ValueError("Test error")
        bundle = create_failure_bundle(project_path, "test_name", "corr-123", error)

        assert bundle["correlation_id"] == "corr-123"
        assert bundle["test_name"] == "test_name"
        assert bundle["error"]["type"] == "ValueError"
        assert bundle["error"]["message"] == "Test error"
        assert "artifacts" in bundle


class TestSecretRedaction:
    """Test secret redaction utilities."""

    def test_redact_secrets_api_key_pattern(self):
        """Test redaction of API key patterns."""
        content = '{"api_key": "secret123", "other": "value"}'
        redacted = redact_secrets(content)

        assert "[REDACTED]" in redacted
        assert "secret123" not in redacted

    def test_redact_secrets_custom(self):
        """Test redaction of custom secrets."""
        content = "Password is secret123 and token is abc456"
        redacted = redact_secrets(content, secrets=["secret123", "abc456"])

        assert "[REDACTED]" in redacted
        assert "secret123" not in redacted
        assert "abc456" not in redacted
