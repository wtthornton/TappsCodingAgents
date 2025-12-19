"""
Unit tests for Cursor Skill Helper with structured metadata support.

Tests the Phase 1 enhancement: structured metadata (webMCP pattern) in command files.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.workflow.cursor_skill_helper import (
    check_skill_completion,
    create_skill_command_file,
    get_expected_artifacts_from_metadata,
    read_skill_metadata,
)

pytestmark = pytest.mark.unit


def test_create_skill_command_file_basic(tmp_path: Path):
    """Test basic command file creation (backward compatibility)."""
    command = "@analyst gather-requirements"
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    command_file, metadata_file = create_skill_command_file(
        command=command,
        worktree_path=worktree_path,
    )
    
    # Command file should exist
    assert command_file.exists()
    assert command_file.name == ".cursor-skill-command.txt"
    
    # Metadata file should exist
    assert metadata_file.exists()
    assert metadata_file.name == ".cursor-skill-metadata.json"
    
    # Simple text file should exist
    simple_file = worktree_path / ".cursor-skill-command-simple.txt"
    assert simple_file.exists()
    assert simple_file.read_text(encoding="utf-8") == command


def test_create_skill_command_file_with_metadata(tmp_path: Path):
    """Test command file creation with structured metadata."""
    command = "@analyst gather-requirements"
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    workflow_id = "test-workflow-123"
    step_id = "requirements"
    expected_artifacts = ["requirements.md", "stories/"]
    custom_metadata = {"priority": "high"}
    
    command_file, metadata_file = create_skill_command_file(
        command=command,
        worktree_path=worktree_path,
        workflow_id=workflow_id,
        step_id=step_id,
        expected_artifacts=expected_artifacts,
        metadata=custom_metadata,
    )
    
    # Read and verify metadata
    metadata_content = json.loads(metadata_file.read_text(encoding="utf-8"))
    
    assert metadata_content["version"] == "1.0"
    assert metadata_content["type"] == "skill_command"
    assert metadata_content["command"] == command
    assert metadata_content["workflow_context"]["workflow_id"] == workflow_id
    assert metadata_content["workflow_context"]["step_id"] == step_id
    assert metadata_content["workflow_context"]["expected_artifacts"] == expected_artifacts
    assert metadata_content["interaction_pattern"]["mode"] == "async"
    assert metadata_content["interaction_pattern"]["completion_detection"] == "status_file_and_artifacts"
    assert metadata_content["metadata"]["priority"] == "high"
    assert "timestamp" in metadata_content


def test_read_skill_metadata_exists(tmp_path: Path):
    """Test reading metadata when file exists."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # Create metadata file
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    metadata_data = {
        "version": "1.0",
        "type": "skill_command",
        "command": "@analyst gather-requirements",
        "workflow_context": {
            "workflow_id": "test-123",
            "step_id": "requirements",
            "expected_artifacts": ["requirements.md"],
        },
    }
    metadata_file.write_text(json.dumps(metadata_data), encoding="utf-8")
    
    # Read metadata
    result = read_skill_metadata(worktree_path)
    
    assert result is not None
    assert result["version"] == "1.0"
    assert result["workflow_context"]["workflow_id"] == "test-123"


def test_read_skill_metadata_not_exists(tmp_path: Path):
    """Test reading metadata when file doesn't exist."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    result = read_skill_metadata(worktree_path)
    
    assert result is None


def test_read_skill_metadata_invalid_json(tmp_path: Path):
    """Test reading metadata with invalid JSON (graceful degradation)."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # Create invalid JSON file
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    metadata_file.write_text("invalid json{", encoding="utf-8")
    
    # Should return None without raising exception
    with patch("tapps_agents.workflow.cursor_skill_helper.logger") as mock_logger:
        result = read_skill_metadata(worktree_path)
        assert result is None
        # Should log warning
        assert mock_logger.warning.called


def test_get_expected_artifacts_from_metadata(tmp_path: Path):
    """Test extracting expected artifacts from metadata."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # Create metadata file with expected artifacts
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    metadata_data = {
        "version": "1.0",
        "workflow_context": {
            "expected_artifacts": ["requirements.md", "stories/", "architecture.md"],
        },
    }
    metadata_file.write_text(json.dumps(metadata_data), encoding="utf-8")
    
    # Extract artifacts
    artifacts = get_expected_artifacts_from_metadata(worktree_path)
    
    assert artifacts == ["requirements.md", "stories/", "architecture.md"]


def test_get_expected_artifacts_from_metadata_not_exists(tmp_path: Path):
    """Test extracting artifacts when metadata doesn't exist."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    artifacts = get_expected_artifacts_from_metadata(worktree_path)
    
    assert artifacts == []


def test_get_expected_artifacts_from_metadata_no_artifacts(tmp_path: Path):
    """Test extracting artifacts when metadata has no artifacts field."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # Create metadata file without expected_artifacts
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    metadata_data = {
        "version": "1.0",
        "workflow_context": {},
    }
    metadata_file.write_text(json.dumps(metadata_data), encoding="utf-8")
    
    artifacts = get_expected_artifacts_from_metadata(worktree_path)
    
    assert artifacts == []


def test_backward_compatibility_command_file_format(tmp_path: Path):
    """Test that command file maintains backward compatible JSON format."""
    command = "@analyst gather-requirements"
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    workflow_id = "test-123"
    step_id = "requirements"
    
    command_file, _ = create_skill_command_file(
        command=command,
        worktree_path=worktree_path,
        workflow_id=workflow_id,
        step_id=step_id,
    )
    
    # Read command file (should still be valid JSON with old format)
    command_data = json.loads(command_file.read_text(encoding="utf-8"))
    
    assert command_data["command"] == command
    assert command_data["workflow_id"] == workflow_id
    assert command_data["step_id"] == step_id
    assert "worktree_path" in command_data
    assert "instructions" in command_data


def test_check_skill_completion_with_artifacts(tmp_path: Path):
    """Test completion detection with expected artifacts."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # Create some artifacts
    (worktree_path / "requirements.md").write_text("# Requirements", encoding="utf-8")
    (worktree_path / "stories").mkdir()
    
    result = check_skill_completion(
        worktree_path=worktree_path,
        expected_artifacts=["requirements.md", "stories", "architecture.md"],
    )
    
    assert result["completed"] is True
    assert "requirements.md" in result["found_artifacts"]
    assert "stories" in result["found_artifacts"]
    assert "architecture.md" in result["missing_artifacts"]


def test_check_skill_completion_no_artifacts(tmp_path: Path):
    """Test completion detection when no artifacts exist."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    result = check_skill_completion(
        worktree_path=worktree_path,
        expected_artifacts=["requirements.md", "stories"],
    )
    
    assert result["completed"] is False
    assert len(result["found_artifacts"]) == 0
    assert len(result["missing_artifacts"]) == 2

