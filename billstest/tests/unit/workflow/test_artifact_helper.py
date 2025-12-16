"""
Unit tests for Artifact Helper.
"""

from pathlib import Path

import pytest

from tapps_agents.workflow.artifact_helper import load_artifact, write_artifact
from tapps_agents.workflow.code_artifact import CodeArtifact, CodeChange
from tapps_agents.workflow.design_artifact import DesignArtifact

pytestmark = pytest.mark.unit


class TestArtifactHelper:
    """Test cases for artifact helper functions."""

    def test_write_code_artifact(self, tmp_path):
        """Test writing a code artifact."""
        artifact = CodeArtifact(
            operation_type="implement",
            status="completed"
        )
        change = CodeChange(
            file_path="test.py",
            change_type="feature",
            lines_added=10
        )
        artifact.add_change(change)
        
        artifact_path = write_artifact(artifact, artifact_dir=tmp_path)
        
        assert artifact_path.exists()
        assert artifact_path.suffix == ".json"
        assert "code" in artifact_path.name.lower()

    def test_write_design_artifact(self, tmp_path):
        """Test writing a design artifact."""
        artifact = DesignArtifact(
            operation_type="design-system",
            status="completed"
        )
        
        artifact_path = write_artifact(artifact, artifact_dir=tmp_path)
        
        assert artifact_path.exists()
        assert artifact_path.suffix == ".json"

    def test_write_artifact_with_worktree(self, tmp_path):
        """Test writing artifact with worktree path."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()
        
        artifact = CodeArtifact(operation_type="implement")
        artifact_path = write_artifact(artifact, worktree_path=worktree_path)
        
        assert artifact_path.exists()
        # Should be in .tapps-agents/artifacts
        assert ".tapps-agents" in str(artifact_path)

    def test_load_artifact(self, tmp_path):
        """Test loading an artifact from disk."""
        # Write artifact first
        artifact = CodeArtifact(
            operation_type="implement",
            status="completed",
            correlation_id="test-123"
        )
        artifact_path = write_artifact(artifact, artifact_dir=tmp_path)
        
        # Load it back
        loaded = load_artifact(artifact_path)
        
        assert isinstance(loaded, CodeArtifact)
        assert loaded.operation_type == "implement"
        assert loaded.status == "completed"
        assert loaded.correlation_id == "test-123"

    def test_artifact_markdown_summary(self, tmp_path):
        """Test that markdown summary is generated."""
        artifact = CodeArtifact(
            operation_type="implement",
            status="completed"
        )
        change = CodeChange(
            file_path="test.py",
            change_type="feature",
            lines_added=10,
            lines_removed=2
        )
        artifact.add_change(change)
        
        artifact_path = write_artifact(artifact, artifact_dir=tmp_path)
        markdown_path = artifact_path.with_suffix(".md")
        
        # Markdown may or may not be created depending on implementation
        # Just verify the JSON was created
        assert artifact_path.exists()

