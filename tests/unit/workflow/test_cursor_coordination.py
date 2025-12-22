"""
Integration tests for Cursor coordination files with correlation IDs and redaction.

Tests that command files, instructions, and metadata include correlation IDs
and properly redact secrets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tapps_agents.workflow.cursor_skill_helper import (
    create_skill_command_file,
    create_skill_execution_instructions,
    check_skill_completion,
)

pytestmark = pytest.mark.unit


class TestCursorCoordinationFiles:
    """Test Cursor coordination file creation with correlation IDs and redaction."""

    def test_command_file_includes_correlation_metadata(self, tmp_path):
        """Test that command files include correlation metadata."""
        command_file, metadata_file = create_skill_command_file(
            command="@reviewer review --file src/main.py",
            worktree_path=tmp_path,
            workflow_id="workflow-123",
            step_id="step-1",
            expected_artifacts=["reports/review.json"],
        )
        
        # Check command file
        command_data = json.loads(command_file.read_text(encoding="utf-8"))
        
        assert "correlation" in command_data
        assert command_data["correlation"]["workflow_id"] == "workflow-123"
        assert command_data["correlation"]["step_id"] == "step-1"
        assert command_data["correlation"]["expected_artifacts"] == ["reports/review.json"]
        assert "created_at" in command_data["correlation"]
        
        # Check metadata file
        metadata_data = json.loads(metadata_file.read_text(encoding="utf-8"))
        
        assert "correlation" in metadata_data
        assert metadata_data["correlation"]["workflow_id"] == "workflow-123"

    def test_command_file_redacts_secrets(self, tmp_path):
        """Test that command files redact secrets."""
        command = "@reviewer review --api_key sk-1234567890abcdefghij --file src/main.py"
        
        command_file, metadata_file = create_skill_command_file(
            command=command,
            worktree_path=tmp_path,
            workflow_id="workflow-123",
            step_id="step-1",
        )
        
        # Check that secrets are redacted
        command_data = json.loads(command_file.read_text(encoding="utf-8"))
        command_text = command_data["command"]
        
        assert "sk-1234567890abcdefghij" not in command_text
        assert "***REDACTED***" in command_text
        assert command_data.get("redaction_applied") is True
        
        # Metadata file should also have redacted command
        metadata_data = json.loads(metadata_file.read_text(encoding="utf-8"))
        assert "sk-1234567890abcdefghij" not in metadata_data["command"]

    def test_instructions_file_includes_correlation(self, tmp_path):
        """Test that instruction files include correlation metadata."""
        instructions_file = create_skill_execution_instructions(
            worktree_path=tmp_path,
            command="@reviewer review --file src/main.py",
            expected_artifacts=["reports/review.json"],
            workflow_id="workflow-123",
            step_id="step-1",
        )
        
        instructions = instructions_file.read_text(encoding="utf-8")
        
        assert "**Workflow ID**: workflow-123" in instructions
        assert "**Step ID**: step-1" in instructions
        assert ".tapps-agents/workflows/markers/workflow-123/step-step-1/FAILED.json" in instructions

    def test_completion_check_with_markers(self, tmp_path):
        """Test completion check that looks for markers."""
        # Create marker directory structure
        marker_dir = (
            tmp_path
            / ".tapps-agents"
            / "workflows"
            / "markers"
            / "workflow-123"
            / "step-step-1"
        )
        marker_dir.mkdir(parents=True, exist_ok=True)
        
        # Create DONE marker
        done_marker = marker_dir / "DONE.json"
        done_marker.write_text(
            json.dumps({
                "workflow_id": "workflow-123",
                "step_id": "step-1",
                "status": "completed",
                "found_artifacts": ["art1", "art2"],
                "expected_artifacts": ["art1", "art2"],
            }),
            encoding="utf-8",
        )
        
        # Check completion
        result = check_skill_completion(
            worktree_path=tmp_path,
            expected_artifacts=["art1", "art2"],
            workflow_id="workflow-123",
            step_id="step-1",
        )
        
        assert result["completed"] is True
        assert result["completion_type"] == "marker"
        assert "done" in result["marker_locations"]
        assert result["found_artifacts"] == ["art1", "art2"]

    def test_completion_check_with_failed_marker(self, tmp_path):
        """Test completion check with FAILED marker."""
        # Create marker directory
        marker_dir = (
            tmp_path
            / ".tapps-agents"
            / "workflows"
            / "markers"
            / "workflow-123"
            / "step-step-1"
        )
        marker_dir.mkdir(parents=True, exist_ok=True)
        
        # Create FAILED marker
        failed_marker = marker_dir / "FAILED.json"
        failed_marker.write_text(
            json.dumps({
                "workflow_id": "workflow-123",
                "step_id": "step-1",
                "status": "failed",
                "error": "Timeout after 3600s",
                "error_type": "TimeoutError",
            }),
            encoding="utf-8",
        )
        
        # Check completion
        result = check_skill_completion(
            worktree_path=tmp_path,
            workflow_id="workflow-123",
            step_id="step-1",
        )
        
        assert result["completed"] is True
        assert result["completion_type"] == "failed_marker"
        assert "failed" in result["marker_locations"]
        assert result["error"] == "Timeout after 3600s"
        assert result["error_type"] == "TimeoutError"

    def test_completion_check_artifacts_only(self, tmp_path):
        """Test completion check falls back to artifacts if no markers."""
        # Create an artifact
        artifact_file = tmp_path / "reports" / "review.json"
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text('{"status": "ok"}', encoding="utf-8")
        
        # Check completion (no markers)
        result = check_skill_completion(
            worktree_path=tmp_path,
            expected_artifacts=["reports/review.json"],
        )
        
        assert result["completed"] is True
        assert result["completion_type"] == "artifacts"
        assert "reports/review.json" in result["found_artifacts"]
        assert len(result["artifact_details"]) > 0

