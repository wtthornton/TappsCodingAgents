"""
Unit tests for Structured Status File Format.

Tests the Phase 4 enhancement: enhanced status file format with progress updates.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.workflow.background_auto_executor import BackgroundAgentAutoExecutor
from tapps_agents.workflow.cursor_skill_helper import write_structured_status_file

pytestmark = pytest.mark.unit


def test_write_structured_status_file_basic(tmp_path: Path):
    """Test writing basic structured status file."""
    status_file = tmp_path / ".cursor-skill-status.json"
    
    write_structured_status_file(
        status_file=status_file,
        status="running",
        started_at=datetime.now().isoformat(),
    )
    
    assert status_file.exists()
    status_data = json.loads(status_file.read_text(encoding="utf-8"))
    
    assert status_data["version"] == "1.0"
    assert status_data["status"] == "running"
    assert "started_at" in status_data


def test_write_structured_status_file_with_progress(tmp_path: Path):
    """Test writing status file with progress information."""
    status_file = tmp_path / ".cursor-skill-status.json"
    
    write_structured_status_file(
        status_file=status_file,
        status="running",
        progress={
            "percentage": 50,
            "current_step": "Generating code",
            "message": "Halfway through implementation",
        },
    )
    
    status_data = json.loads(status_file.read_text(encoding="utf-8"))
    
    assert status_data["progress"]["percentage"] == 50
    assert status_data["progress"]["current_step"] == "Generating code"
    assert status_data["progress"]["message"] == "Halfway through implementation"


def test_write_structured_status_file_with_partial_results(tmp_path: Path):
    """Test writing status file with partial results."""
    status_file = tmp_path / ".cursor-skill-status.json"
    
    write_structured_status_file(
        status_file=status_file,
        status="running",
        partial_results={
            "artifacts": ["requirements.md", "stories/"],
            "output": "Partial output from execution",
        },
    )
    
    status_data = json.loads(status_file.read_text(encoding="utf-8"))
    
    assert len(status_data["partial_results"]["artifacts"]) == 2
    assert status_data["partial_results"]["output"] == "Partial output from execution"


def test_write_structured_status_file_with_error(tmp_path: Path):
    """Test writing status file with error information."""
    status_file = tmp_path / ".cursor-skill-status.json"
    
    write_structured_status_file(
        status_file=status_file,
        status="failed",
        error={
            "message": "Test error message",
            "code": "TEST_ERROR",
            "retryable": True,
            "retry_count": 1,
        },
    )
    
    status_data = json.loads(status_file.read_text(encoding="utf-8"))
    
    assert status_data["error"]["message"] == "Test error message"
    assert status_data["error"]["code"] == "TEST_ERROR"
    assert status_data["error"]["retryable"] is True
    assert status_data["error"]["retry_count"] == 1


def test_check_status_reads_structured_format(tmp_path: Path):
    """Test that check_status reads structured format correctly."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=5.0,
    )
    
    status_file = tmp_path / ".cursor-skill-status.json"
    
    # Write structured status file
    write_structured_status_file(
        status_file=status_file,
        status="completed",
        progress={"percentage": 100, "current_step": "Done", "message": "Complete"},
        artifacts=["requirements.md"],
        metadata={"workflow_id": "test-123", "step_id": "requirements"},
        started_at=datetime.now().isoformat(),
        completed_at=datetime.now().isoformat(),
    )
    
    # Check status
    result = executor.check_status(status_file)
    
    assert result["completed"] is True
    assert result["status"] == "completed"
    assert result["version"] == "1.0"
    assert result["progress"]["percentage"] == 100
    assert "requirements.md" in result["artifacts"]
    assert result["metadata"]["workflow_id"] == "test-123"


def test_check_status_backward_compatibility(tmp_path: Path):
    """Test that check_status maintains backward compatibility with old format."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=5.0,
    )
    
    status_file = tmp_path / ".cursor-skill-status.json"
    
    # Write old format status file
    old_format = {
        "status": "completed",
        "artifacts": ["requirements.md"],
        "output": "Execution complete",
    }
    status_file.write_text(json.dumps(old_format), encoding="utf-8")
    
    # Check status
    result = executor.check_status(status_file)
    
    assert result["completed"] is True
    assert result["status"] == "completed"
    assert "requirements.md" in result["artifacts"]


def test_check_status_progress_extraction(tmp_path: Path):
    """Test extracting progress information from structured status file."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=5.0,
    )
    
    status_file = tmp_path / ".cursor-skill-status.json"
    
    # Write status file with progress
    write_structured_status_file(
        status_file=status_file,
        status="running",
        progress={
            "percentage": 75,
            "current_step": "Running tests",
            "message": "75% complete",
        },
    )
    
    result = executor.check_status(status_file)
    
    assert result["progress"]["percentage"] == 75
    assert result["progress"]["current_step"] == "Running tests"
    assert result["progress"]["message"] == "75% complete"


def test_check_status_partial_results_extraction(tmp_path: Path):
    """Test extracting partial results from structured status file."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=5.0,
    )
    
    status_file = tmp_path / ".cursor-skill-status.json"
    
    # Write status file with partial results
    write_structured_status_file(
        status_file=status_file,
        status="running",
        partial_results={
            "artifacts": ["partial-code.py"],
            "output": "Partial execution output",
        },
    )
    
    result = executor.check_status(status_file)
    
    assert "partial_results" in result
    assert "partial-code.py" in result["partial_results"]["artifacts"]
    assert result["partial_results"]["output"] == "Partial execution output"

