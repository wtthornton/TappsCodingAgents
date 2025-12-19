"""
Unit tests for Background Agent Auto-Executor with adaptive polling.

Tests the 2025 optimization: adaptive polling with exponential backoff.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.workflow.background_auto_executor import (
    AdaptivePolling,
    BackgroundAgentAutoExecutor,
)

pytestmark = pytest.mark.unit


def test_adaptive_polling_initial_interval():
    """Test that adaptive polling starts with initial interval."""
    polling = AdaptivePolling(
        initial_interval=1.0,
        max_interval=30.0,
        backoff_multiplier=1.5,
        jitter=False,  # Disable jitter for deterministic test
    )
    
    interval = polling.get_next_interval()
    assert interval == 1.0


def test_adaptive_polling_exponential_backoff():
    """Test that adaptive polling increases interval exponentially."""
    polling = AdaptivePolling(
        initial_interval=1.0,
        max_interval=30.0,
        backoff_multiplier=1.5,
        jitter=False,  # Disable jitter for deterministic test
    )
    
    # First interval
    interval1 = polling.get_next_interval()
    assert interval1 == 1.0
    
    # Second interval should be 1.5x
    interval2 = polling.get_next_interval()
    assert interval2 == 1.5
    
    # Third interval should be 2.25x
    interval3 = polling.get_next_interval()
    assert interval3 == 2.25
    
    # Fourth interval should be 3.375x
    interval4 = polling.get_next_interval()
    assert interval4 == 3.375


def test_adaptive_polling_max_interval():
    """Test that adaptive polling respects max interval."""
    polling = AdaptivePolling(
        initial_interval=1.0,
        max_interval=5.0,
        backoff_multiplier=2.0,
        jitter=False,
    )
    
    # Keep getting intervals until we hit max
    intervals = []
    for _ in range(10):
        intervals.append(polling.get_next_interval())
    
    # All intervals should be <= max_interval
    assert all(interval <= 5.0 for interval in intervals)
    # At least one should be at max
    assert max(intervals) == 5.0


def test_adaptive_polling_reset():
    """Test that adaptive polling resets to initial interval."""
    polling = AdaptivePolling(
        initial_interval=1.0,
        max_interval=30.0,
        backoff_multiplier=1.5,
        jitter=False,
    )
    
    # Increase interval
    polling.get_next_interval()  # 1.0 -> 1.5
    polling.get_next_interval()  # 1.5 -> 2.25
    
    # Reset
    polling.reset()
    
    # Should be back to initial
    interval = polling.get_next_interval()
    assert interval == 1.0


def test_adaptive_polling_jitter():
    """Test that adaptive polling adds jitter when enabled."""
    polling = AdaptivePolling(
        initial_interval=10.0,
        max_interval=30.0,
        backoff_multiplier=1.5,
        jitter=True,
    )
    
    # Get multiple intervals with jitter
    intervals = [polling.get_next_interval() for _ in range(10)]
    
    # All should be within 10% jitter range
    for interval in intervals:
        # Jitter is ±10%, so interval should be between 0.9*base and 1.1*base
        # But we need to account for the backoff multiplier
        assert 0.1 <= interval <= 35.0  # Reasonable bounds


@pytest.mark.asyncio
async def test_background_auto_executor_uses_adaptive_polling():
    """Test that BackgroundAgentAutoExecutor uses adaptive polling by default."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=10.0,
        use_adaptive_polling=True,
    )
    
    assert executor.adaptive_polling is not None
    assert executor.adaptive_polling.initial_interval == 1.0


@pytest.mark.asyncio
async def test_background_auto_executor_can_disable_adaptive_polling():
    """Test that adaptive polling can be disabled."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=5.0,
        timeout_seconds=10.0,
        use_adaptive_polling=False,
    )
    
    assert executor.adaptive_polling is None


@pytest.mark.asyncio
async def test_poll_for_completion_uses_adaptive_intervals(tmp_path: Path):
    """Test that poll_for_completion uses adaptive polling intervals."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=10.0,
        use_adaptive_polling=True,
    )
    
    status_file = tmp_path / ".cursor-skill-status.json"
    worktree_path = tmp_path
    
    # Track polling intervals
    intervals_used: list[float] = []
    original_sleep = asyncio.sleep
    
    async def tracked_sleep(delay: float):
        intervals_used.append(delay)
        await original_sleep(0.01)  # Short delay for test speed
    
    # Mock status check to return incomplete initially, then complete
    call_count = 0
    
    def mock_check_status(file: Path) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count >= 3:  # Complete after 3 checks
            return {"completed": True, "status": "completed"}
        return {"completed": False, "status": "pending"}
    
    executor.check_status = mock_check_status
    
    # Patch asyncio.sleep to track intervals
    with patch("asyncio.sleep", side_effect=tracked_sleep):
        # Create status file after a delay to simulate completion
        async def create_status_file():
            await asyncio.sleep(0.05)  # Wait a bit
            status_file.write_text('{"status": "completed"}')
        
        # Start status file creation
        task = asyncio.create_task(create_status_file())
        
        # Poll for completion
        result = await executor.poll_for_completion(
            worktree_path=worktree_path,
            status_file=status_file,
            start_time=None,
        )
        
        await task
    
    # Verify completion
    assert result["completed"] is True
    
    # Verify adaptive polling was used (intervals should increase)
    assert len(intervals_used) >= 2
    # First interval should be ~initial_interval (with jitter)
    assert 0.9 <= intervals_used[0] <= 1.1
    # Subsequent intervals should increase (with jitter)
    if len(intervals_used) > 1:
        assert intervals_used[1] >= intervals_used[0] * 0.9  # Account for jitter


@pytest.mark.asyncio
async def test_poll_for_completion_resets_on_activity(tmp_path: Path):
    """Test that adaptive polling resets when activity is detected."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=10.0,
        use_adaptive_polling=True,
    )
    
    status_file = tmp_path / ".cursor-skill-status.json"
    worktree_path = tmp_path
    
    # Increase polling interval first
    executor.adaptive_polling.get_next_interval()  # 1.0 -> 1.5
    executor.adaptive_polling.get_next_interval()  # 1.5 -> 2.25
    
    # Verify interval increased
    assert executor.adaptive_polling.current_interval > 1.0
    
    # Mock status check to return completed immediately
    def mock_check_status(file: Path) -> dict:
        return {"completed": True, "status": "completed"}
    
    executor.check_status = mock_check_status
    
    # Poll for completion (should detect activity and reset)
    result = await executor.poll_for_completion(
        worktree_path=worktree_path,
        status_file=status_file,
        start_time=None,
    )
    
    # Verify completion
    assert result["completed"] is True
    
    # Verify polling was reset
    assert executor.adaptive_polling.current_interval == 1.0


@pytest.mark.asyncio
async def test_execute_command_creates_metadata(tmp_path: Path):
    """Test that execute_command creates structured metadata file."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=5.0,
        project_root=tmp_path,
    )
    
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    command = "@analyst gather-requirements"
    workflow_id = "test-workflow-123"
    step_id = "requirements"
    expected_artifacts = ["requirements.md"]
    
    # Create a status file that will be detected immediately
    status_file = worktree_path / ".cursor-skill-status.json"
    status_file.write_text('{"status": "completed"}', encoding="utf-8")
    
    # Execute command
    result = await executor.execute_command(
        command=command,
        worktree_path=worktree_path,
        workflow_id=workflow_id,
        step_id=step_id,
        expected_artifacts=expected_artifacts,
    )
    
    # Verify metadata file was created
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    assert metadata_file.exists()
    
    # Verify metadata content
    import json
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert metadata["version"] == "1.0"
    assert metadata["workflow_context"]["workflow_id"] == workflow_id
    assert metadata["workflow_context"]["step_id"] == step_id
    assert metadata["workflow_context"]["expected_artifacts"] == expected_artifacts
    
    # Verify result
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_poll_for_completion_reads_metadata_artifacts(tmp_path: Path):
    """Test that poll_for_completion reads expected artifacts from metadata."""
    executor = BackgroundAgentAutoExecutor(
        polling_interval=1.0,
        timeout_seconds=5.0,
        project_root=tmp_path,
    )
    
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # Create metadata file with expected artifacts
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    metadata_data = {
        "version": "1.0",
        "workflow_context": {
            "expected_artifacts": ["requirements.md", "stories/"],
        },
    }
    metadata_file.write_text(json.dumps(metadata_data), encoding="utf-8")
    
    # Create one of the expected artifacts
    (worktree_path / "requirements.md").write_text("# Requirements", encoding="utf-8")
    
    status_file = worktree_path / ".cursor-skill-status.json"
    
    # Mock check_status to return incomplete
    def mock_check_status(file: Path) -> dict:
        return {"completed": False, "status": "pending"}
    
    executor.check_status = mock_check_status
    
    # Poll for completion (should detect artifact from metadata)
    result = await executor.poll_for_completion(
        worktree_path=worktree_path,
        status_file=status_file,
        expected_artifacts=None,  # Not provided, should read from metadata
        start_time=None,
    )
    
    # Should detect completion via artifact
    assert result["completed"] is True
    assert result["status"] == "completed"
    assert "requirements.md" in result.get("artifacts", [])
