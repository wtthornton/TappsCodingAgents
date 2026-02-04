"""
Unit tests for Cursor Workflow Executor context manager (worktree lifecycle).

Tests the 2025 optimization: context managers for guaranteed resource cleanup.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.models import (
    WorkflowState,
    WorkflowStep,
)

pytestmark = pytest.mark.unit

# Patch so CursorWorkflowExecutor can be instantiated in headless CI (GitHub Actions).
_CURSOR_MODE_PATCH = "tapps_agents.workflow.cursor_executor.is_cursor_mode"


@pytest.fixture
def mock_executor(tmp_path: Path):
    """Create a CursorWorkflowExecutor with mocked dependencies."""
    with patch(_CURSOR_MODE_PATCH, return_value=True):
        executor = CursorWorkflowExecutor(project_root=tmp_path)
    
    # Mock worktree manager
    executor.worktree_manager = MagicMock()
    executor.worktree_manager.create_worktree = AsyncMock(return_value=tmp_path / "worktree")
    executor.worktree_manager.copy_artifacts = AsyncMock()
    executor.worktree_manager.remove_worktree = AsyncMock()

    # Mock state
    executor.state = WorkflowState(
        workflow_id="test-workflow",
        started_at=datetime.now(),
        status="running",
        artifacts={},
    )
    
    return executor


@pytest.fixture
def sample_step():
    """Create a sample workflow step."""
    return WorkflowStep(
        id="test-step",
        agent="analyst",
        action="gather",
        requires=[],
        creates=["artifact1"],
    )


@pytest.mark.asyncio
async def test_worktree_context_creates_and_cleans_up(mock_executor, sample_step):
    """Test that worktree context manager creates and cleans up worktree."""
    worktree_path = None
    
    async with mock_executor._worktree_context(sample_step) as wt_path:
        worktree_path = wt_path
        
        # Verify worktree was created
        mock_executor.worktree_manager.create_worktree.assert_called_once()
        mock_executor.worktree_manager.copy_artifacts.assert_called_once()
        
        # Verify worktree path is returned
        assert worktree_path is not None
        assert worktree_path == mock_executor.worktree_manager.create_worktree.return_value
    
    # Verify worktree was cleaned up after context exit
    mock_executor.worktree_manager.remove_worktree.assert_called_once()


@pytest.mark.asyncio
async def test_worktree_context_cleans_up_on_exception(mock_executor, sample_step):
    """Test that worktree is cleaned up even when exception occurs."""
    
    try:
        async with mock_executor._worktree_context(sample_step):
            # Simulate an exception
            raise RuntimeError("Simulated error")
    except RuntimeError:
        pass
    
    # Verify worktree was still cleaned up
    mock_executor.worktree_manager.remove_worktree.assert_called_once()


@pytest.mark.asyncio
async def test_worktree_context_cleans_up_on_cancellation(mock_executor, sample_step):
    """Test that worktree is cleaned up even when task is cancelled."""
    worktree_path = None
    
    async def cancellable_task():
        try:
            async with mock_executor._worktree_context(sample_step) as wt_path:
                nonlocal worktree_path
                worktree_path = wt_path
                # Wait long enough to be cancelled
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            # Verify cleanup happens even on cancellation
            pass
    
    # Create and cancel task
    task = asyncio.create_task(cancellable_task())
    await asyncio.sleep(0.01)  # Let it start
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Verify worktree was cleaned up
    mock_executor.worktree_manager.remove_worktree.assert_called_once()


@pytest.mark.asyncio
async def test_worktree_context_handles_cleanup_failure(mock_executor, sample_step):
    """Test that cleanup failure doesn't break the workflow."""
    # Make cleanup raise an exception
    mock_executor.worktree_manager.remove_worktree = AsyncMock(side_effect=RuntimeError("Cleanup failed"))
    
    # Mock logger to verify warning is logged
    mock_executor.logger = MagicMock()
    
    # Context should still exit normally even if cleanup fails
    async with mock_executor._worktree_context(sample_step) as wt_path:
        assert wt_path is not None
    
    # Verify cleanup was attempted
    mock_executor.worktree_manager.remove_worktree.assert_called_once()
    
    # Verify warning was logged
    if mock_executor.logger:
        mock_executor.logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_worktree_context_copies_artifacts(mock_executor, sample_step):
    """Test that worktree context copies artifacts from previous steps."""
    # Add some artifacts to state
    from datetime import datetime

    from tapps_agents.workflow.models import Artifact
    
    artifact = Artifact(
        name="previous-artifact",
        path="previous.md",
        status="completed",
        created_by="previous-step",
        created_at=datetime.now(),
    )
    mock_executor.state.artifacts["previous-artifact"] = artifact
    
    async with mock_executor._worktree_context(sample_step):
        # Verify artifacts were copied
        mock_executor.worktree_manager.copy_artifacts.assert_called_once()
        call_args = mock_executor.worktree_manager.copy_artifacts.call_args
        assert len(call_args.kwargs["artifacts"]) == 1
        assert call_args.kwargs["artifacts"][0].name == "previous-artifact"


@pytest.mark.asyncio
async def test_worktree_context_uses_correct_worktree_name(mock_executor, sample_step):
    """Test that worktree context uses correct worktree name."""
    async with mock_executor._worktree_context(sample_step):
        # Verify worktree name is based on step ID
        call_args = mock_executor.worktree_manager.create_worktree.call_args
        worktree_name = call_args.args[0] if call_args.args else call_args.kwargs.get("worktree_name")
        
        # Worktree name should contain step ID
        assert worktree_name is not None
        assert "test-step" in worktree_name or sample_step.id in worktree_name

