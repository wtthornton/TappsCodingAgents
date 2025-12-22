"""
Unit tests for Marker Writer.

Tests DONE/FAILED marker creation, reading, and schema validation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.workflow.marker_writer import MarkerWriter

pytestmark = pytest.mark.unit


class TestMarkerWriter:
    """Test MarkerWriter functionality."""

    def test_marker_writer_initialization(self, tmp_path):
        """Test marker writer can be initialized."""
        writer = MarkerWriter(project_root=tmp_path)
        assert writer.project_root == tmp_path

    def test_get_marker_dir(self, tmp_path):
        """Test marker directory path generation."""
        writer = MarkerWriter(project_root=tmp_path)
        marker_dir = writer.get_marker_dir("workflow-123", "step-1")
        
        expected = (
            tmp_path
            / ".tapps-agents"
            / "workflows"
            / "markers"
            / "workflow-123"
            / "step-step-1"
        )
        assert marker_dir == expected

    def test_write_done_marker(self, tmp_path):
        """Test writing DONE marker."""
        writer = MarkerWriter(project_root=tmp_path)
        started_at = datetime.now()
        completed_at = datetime.now()
        
        marker_path = writer.write_done_marker(
            workflow_id="workflow-123",
            step_id="step-1",
            agent="reviewer",
            action="review",
            worktree_name="worktree-abc",
            worktree_path="/path/to/worktree",
            expected_artifacts=["art1", "art2"],
            found_artifacts=["art1"],
            duration_seconds=5.5,
            started_at=started_at,
            completed_at=completed_at,
        )
        
        assert marker_path.exists()
        assert marker_path.name == "DONE.json"
        
        # Verify marker content
        import json
        marker_data = json.loads(marker_path.read_text(encoding="utf-8"))
        
        assert marker_data["workflow_id"] == "workflow-123"
        assert marker_data["step_id"] == "step-1"
        assert marker_data["agent"] == "reviewer"
        assert marker_data["action"] == "review"
        assert marker_data["status"] == "completed"
        assert marker_data["worktree_name"] == "worktree-abc"
        assert marker_data["worktree_path"] == "/path/to/worktree"
        assert marker_data["expected_artifacts"] == ["art1", "art2"]
        assert marker_data["found_artifacts"] == ["art1"]
        assert marker_data["duration_seconds"] == 5.5
        assert "timestamp" in marker_data
        assert "started_at" in marker_data
        assert "completed_at" in marker_data

    def test_write_failed_marker(self, tmp_path):
        """Test writing FAILED marker."""
        writer = MarkerWriter(project_root=tmp_path)
        started_at = datetime.now()
        failed_at = datetime.now()
        
        marker_path = writer.write_failed_marker(
            workflow_id="workflow-123",
            step_id="step-1",
            agent="implementer",
            action="implement",
            error="Timeout after 3600 seconds",
            worktree_name="worktree-xyz",
            expected_artifacts=["src/main.py"],
            found_artifacts=[],
            duration_seconds=3600.0,
            started_at=started_at,
            failed_at=failed_at,
            error_type="TimeoutError",
        )
        
        assert marker_path.exists()
        assert marker_path.name == "FAILED.json"
        
        # Verify marker content
        import json
        marker_data = json.loads(marker_path.read_text(encoding="utf-8"))
        
        assert marker_data["workflow_id"] == "workflow-123"
        assert marker_data["step_id"] == "step-1"
        assert marker_data["agent"] == "implementer"
        assert marker_data["action"] == "implement"
        assert marker_data["status"] == "failed"
        assert marker_data["error"] == "Timeout after 3600 seconds"
        assert marker_data["error_type"] == "TimeoutError"
        assert marker_data["duration_seconds"] == 3600.0

    def test_read_marker(self, tmp_path):
        """Test reading marker."""
        writer = MarkerWriter(project_root=tmp_path)
        
        # Write a marker first
        writer.write_done_marker(
            workflow_id="workflow-123",
            step_id="step-1",
            agent="reviewer",
            action="review",
        )
        
        # Read it back
        marker_data = writer.read_marker("workflow-123", "step-1", "DONE")
        
        assert marker_data is not None
        assert marker_data["workflow_id"] == "workflow-123"
        assert marker_data["step_id"] == "step-1"
        assert marker_data["status"] == "completed"

    def test_marker_exists(self, tmp_path):
        """Test marker existence check."""
        writer = MarkerWriter(project_root=tmp_path)
        
        # Initially doesn't exist
        assert not writer.marker_exists("workflow-123", "step-1", "DONE")
        
        # Write marker
        writer.write_done_marker(
            workflow_id="workflow-123",
            step_id="step-1",
            agent="reviewer",
            action="review",
        )
        
        # Now exists
        assert writer.marker_exists("workflow-123", "step-1", "DONE")
        assert not writer.marker_exists("workflow-123", "step-1", "FAILED")

    def test_marker_schema_required_fields(self, tmp_path):
        """Test that markers include all required schema fields."""
        writer = MarkerWriter(project_root=tmp_path)
        
        # Write DONE marker
        done_path = writer.write_done_marker(
            workflow_id="wf-1",
            step_id="step-1",
            agent="agent1",
            action="action1",
        )
        
        # Write FAILED marker
        failed_path = writer.write_failed_marker(
            workflow_id="wf-1",
            step_id="step-2",
            agent="agent2",
            action="action2",
            error="Test error",
        )
        
        import json
        
        done_data = json.loads(done_path.read_text(encoding="utf-8"))
        failed_data = json.loads(failed_path.read_text(encoding="utf-8"))
        
        # Required fields for both
        required_fields = ["workflow_id", "step_id", "agent", "action", "status", "timestamp"]
        for field in required_fields:
            assert field in done_data, f"DONE marker missing required field: {field}"
            assert field in failed_data, f"FAILED marker missing required field: {field}"
        
        # FAILED marker must have error
        assert "error" in failed_data
        assert failed_data["error"] == "Test error"

