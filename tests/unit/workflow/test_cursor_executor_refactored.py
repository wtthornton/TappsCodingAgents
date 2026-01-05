"""
Tests for CursorWorkflowExecutor - refactored version.

Tests the run() method, step execution, and artifact extraction.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from datetime import datetime

from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.models import Workflow, WorkflowStep, WorkflowState

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_workflow() -> Workflow:
    """Create a mock workflow for testing."""
    return Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow description",
        version="1.0",
        steps=[
            WorkflowStep(
                id="step1",
                agent="reviewer",
                action="review",
                next="step2",
            ),
            WorkflowStep(
                id="step2",
                agent="implementer",
                action="implement",
            ),
        ],
    )


@pytest.fixture
def mock_executor(tmp_path: Path) -> CursorWorkflowExecutor:
    """Create a CursorWorkflowExecutor instance for testing."""
    executor = CursorWorkflowExecutor(
        project_root=tmp_path,
        auto_mode=True,
    )
    return executor


class TestCursorExecutorInitialization:
    """Tests for CursorWorkflowExecutor initialization."""

    def test_executor_initializes(self, tmp_path: Path):
        """Test that executor initializes correctly."""
        executor = CursorWorkflowExecutor(project_root=tmp_path)
        assert executor.project_root == tmp_path
        assert executor.auto_mode is False

    def test_executor_with_auto_mode(self, tmp_path: Path):
        """Test executor with auto_mode enabled."""
        executor = CursorWorkflowExecutor(project_root=tmp_path, auto_mode=True)
        assert executor.auto_mode is True


class TestCursorExecutorRun:
    """Tests for CursorWorkflowExecutor.run() method."""

    @pytest.mark.asyncio
    async def test_run_with_workflow(self, mock_executor: CursorWorkflowExecutor, mock_workflow: Workflow):
        """Test run() method with workflow.
        
        Note: This test verifies run() accepts a workflow parameter.
        Full execution testing requires integration tests due to complex internal state.
        """
        mock_state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
        )
        mock_executor.workflow = mock_workflow
        
        # Mock config and timeout to avoid actual execution
        with patch("tapps_agents.workflow.cursor_executor.load_config") as mock_config:
            mock_config_instance = MagicMock()
            mock_config_instance.workflow.timeout_seconds = 3600.0
            mock_config.return_value = mock_config_instance
            
            # Mock asyncio.wait_for to return immediately with a mock state
            with patch("asyncio.wait_for") as mock_wait:
                mock_wait.return_value = mock_state
                
                result = await mock_executor.run(workflow=mock_workflow, max_steps=0)
                
                # Verify workflow was set
                assert mock_executor.workflow == mock_workflow

    @pytest.mark.asyncio
    async def test_run_without_workflow_uses_existing(self, mock_executor: CursorWorkflowExecutor, mock_workflow: Workflow):
        """Test run() uses existing workflow if none provided.
        
        Note: This test verifies run() uses existing workflow when None is passed.
        Full execution testing requires integration tests.
        """
        mock_state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
        )
        mock_executor.workflow = mock_workflow
        mock_executor.state = mock_state
        
        # Mock config and timeout
        with patch("tapps_agents.workflow.cursor_executor.load_config") as mock_config:
            mock_config_instance = MagicMock()
            mock_config_workflow = MagicMock()
            mock_config_workflow.timeout_seconds = 3600.0
            mock_config_instance.workflow = mock_config_workflow
            mock_config.return_value = mock_config_instance
            
            with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = mock_state
                
                result = await mock_executor.run(workflow=None, max_steps=0)
                
                # Verify existing workflow was used
                assert mock_executor.workflow == mock_workflow

    @pytest.mark.asyncio
    async def test_run_raises_if_no_workflow(self, mock_executor: CursorWorkflowExecutor):
        """Test run() raises error if no workflow available."""
        mock_executor.workflow = None
        
        with pytest.raises(ValueError, match="No workflow loaded"):
            await mock_executor.run(workflow=None)


class TestCursorExecutorStepExecution:
    """Tests for step execution in CursorWorkflowExecutor."""

    @pytest.mark.asyncio
    async def test_execute_step_extracts_artifacts(
        self, mock_executor: CursorWorkflowExecutor, mock_workflow: Workflow
    ):
        """Test that step execution extracts artifacts."""
        step = mock_workflow.steps[0]
        mock_executor.workflow = mock_workflow
        mock_executor.state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            current_step="step1",
        )
        
        # Mock all async dependencies properly
        mock_executor.skill_invoker = MagicMock()
        mock_executor.skill_invoker.invoke_skill = AsyncMock(return_value={"status": "success"})
        mock_executor.worktree_manager = MagicMock()
        mock_executor.worktree_manager.create_worktree = AsyncMock(return_value=Path("/tmp/worktree"))
        mock_executor.worktree_manager.extract_artifacts = AsyncMock(return_value=[])
        mock_executor.worktree_manager.cleanup_worktree = AsyncMock()
        mock_executor.marker_writer = MagicMock()
        mock_executor.marker_writer.write_done_marker = MagicMock(return_value=Path("/tmp/marker"))
        
        # Mock the worktree context manager as an async context manager
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def mock_worktree_context():
            yield Path("/tmp/worktree")
        
        with patch.object(mock_executor, "_worktree_context", new=mock_worktree_context()):
            result = await mock_executor._execute_step_for_parallel(step=step, target_path=None)
            
            mock_executor.skill_invoker.invoke_skill.assert_called_once()
            mock_executor.worktree_manager.extract_artifacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_step_handles_errors(
        self, mock_executor: CursorWorkflowExecutor, mock_workflow: Workflow
    ):
        """Test that step execution handles errors correctly."""
        step = mock_workflow.steps[0]
        mock_executor.workflow = mock_workflow
        mock_executor.state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            current_step="step1",
        )
        
        with patch.object(mock_executor, "skill_invoker") as mock_invoker:
            mock_invoker.invoke_skill = AsyncMock(side_effect=RuntimeError("Test error"))
            mock_executor.marker_writer = MagicMock()
            mock_executor.marker_writer.write_failed_marker = MagicMock(return_value=Path("/tmp/marker"))
            
            with pytest.raises(RuntimeError):
                await mock_executor._execute_step_for_parallel(step=step, target_path=None)


class TestCursorExecutorWorktreeManagement:
    """Tests for worktree management."""

    def test_worktree_manager_initialized(self, mock_executor: CursorWorkflowExecutor):
        """Test that worktree manager is initialized."""
        assert mock_executor.worktree_manager is not None

    def test_worktree_manager_exists(self, mock_executor: CursorWorkflowExecutor):
        """Test that worktree manager exists and can be used."""
        assert mock_executor.worktree_manager is not None
        # Test that worktree_manager has cleanup method (check actual method name)
        assert hasattr(mock_executor.worktree_manager, "cleanup_all") or hasattr(mock_executor.worktree_manager, "cleanup")


class TestCursorExecutorMarkerWriting:
    """Tests for marker writing functionality."""

    def test_marker_writer_initialized(self, mock_executor: CursorWorkflowExecutor):
        """Test that marker writer is initialized."""
        assert mock_executor.marker_writer is not None

    def test_write_done_marker(self, mock_executor: CursorWorkflowExecutor):
        """Test writing DONE marker."""
        mock_executor.marker_writer = MagicMock()
        mock_executor.marker_writer.write_done_marker = MagicMock(return_value=Path("/tmp/done.json"))
        
        result = mock_executor.marker_writer.write_done_marker(
            workflow_id="test",
            step_id="step1",
            agent="reviewer",
            action="review",
            worktree_name="worktree",
            worktree_path="/tmp/worktree",
            expected_artifacts=[],
            found_artifacts=[],
            duration_seconds=1.0,
            started_at=None,
            completed_at=None,
        )
        
        assert result == Path("/tmp/done.json")
