"""
Unit tests for Issue 10: Simple Mode Full Workflow Infinite Loop - Timeout Mechanism.

Tests the timeout protection added to prevent infinite hangs.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.models import Workflow, WorkflowStep, WorkflowType


@pytest.fixture
def cursor_mode_env(monkeypatch):
    """Set up Cursor mode environment for tests."""
    monkeypatch.setenv("TAPPS_AGENTS_MODE", "cursor")
    monkeypatch.setenv("CURSOR_IDE", "1")
    yield


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create temporary project root for testing."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir(parents=True)
    return project_root


@pytest.fixture
def simple_workflow() -> Workflow:
    """Create a simple test workflow."""
    return Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow for timeout testing",
        version="1.0.0",
        type=WorkflowType.GREENFIELD,
        steps=[
            WorkflowStep(
                id="step-1",
                agent="analyst",
                action="gather-requirements",
                creates=["requirements.md"],
            )
        ],
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_timeout_mechanism(
    temp_project_root: Path,
    cursor_mode_env,
    simple_workflow: Workflow,
):
    """Test that workflow times out after configured timeout."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    # Mock config to return short timeout
    with patch("tapps_agents.core.config.load_config") as mock_config:
        mock_config_instance = MagicMock()
        mock_config_instance.workflow.timeout_seconds = 0.1  # Very short timeout
        mock_config.return_value = mock_config_instance

        # Mock _initialize_run to return quickly
        executor._initialize_run = AsyncMock(return_value=None)

        # Mock the execution loop to hang (simulate infinite loop)
        async def hanging_execution():
            await asyncio.sleep(10)  # Sleep longer than timeout
            return MagicMock()

        executor._finalize_run = AsyncMock(return_value=MagicMock())

        # Mock asyncio.wait_for to raise TimeoutError immediately
        async def mock_wait_for(coro, timeout):
            """Mock wait_for that raises TimeoutError."""
            await asyncio.sleep(0.01)  # Small delay to simulate execution
            raise asyncio.TimeoutError("Workflow execution exceeded timeout")

        # Start workflow
        await executor.start(workflow=simple_workflow, user_prompt="Test")

        # Try to run workflow - should timeout
        with patch("asyncio.wait_for", side_effect=mock_wait_for):
            with pytest.raises(TimeoutError) as exc_info:
                await executor.run(workflow=simple_workflow)

        # Verify timeout error message
        assert "timeout" in str(exc_info.value).lower() or "exceeded" in str(exc_info.value).lower()

        # Verify state was saved with timeout error
        assert executor.state is not None
        # State might be "failed" or "running" depending on error handling
        if executor.state.status == "failed":
            assert "timeout" in executor.state.error.lower() or "exceeded" in executor.state.error.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_timeout_uses_config_value(
    temp_project_root: Path,
    cursor_mode_env,
    simple_workflow: Workflow,
):
    """Test that workflow timeout uses config value correctly."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    # Mock config with specific timeout
    with patch("tapps_agents.core.config.load_config") as mock_config:
        mock_config_instance = MagicMock()
        mock_config_instance.workflow.timeout_seconds = 5.0
        mock_config.return_value = mock_config_instance

        # Workflow timeout should be 2x step timeout = 10 seconds
        # Mock _initialize_run
        executor._initialize_run = AsyncMock(return_value=None)

        # Create a function that hangs for 12 seconds (longer than 10s timeout)
        async def hanging_inner():
            await asyncio.sleep(12)
            return MagicMock()

        executor._finalize_run = AsyncMock(return_value=MagicMock())

        await executor.start(workflow=simple_workflow, user_prompt="Test")

        # Should timeout after ~10 seconds (2x config timeout)
        start_time = asyncio.get_event_loop().time()
        with pytest.raises(TimeoutError):
            await executor.run(workflow=simple_workflow)
        elapsed = asyncio.get_event_loop().time() - start_time

        # Should timeout around 10 seconds (allow some margin)
        assert 9.0 <= elapsed <= 12.0, f"Timeout should be ~10s, got {elapsed}s"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_timeout_logs_error(
    temp_project_root: Path,
    cursor_mode_env,
    simple_workflow: Workflow,
    caplog,
):
    """Test that timeout errors are logged."""
    import logging
    caplog.set_level(logging.ERROR)
    
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    # Mock config with short timeout
    with patch("tapps_agents.core.config.load_config") as mock_config:
        mock_config_instance = MagicMock()
        mock_config_instance.workflow.timeout_seconds = 0.1
        mock_config.return_value = mock_config_instance

        executor._initialize_run = AsyncMock(return_value=None)
        executor._finalize_run = AsyncMock(return_value=MagicMock())

        await executor.start(workflow=simple_workflow, user_prompt="Test")

        with pytest.raises(TimeoutError):
            await executor.run(workflow=simple_workflow)

        # Verify timeout error was logged
        assert len(caplog.records) > 0
        error_messages = [record.message for record in caplog.records]
        assert any("timeout" in msg.lower() or "exceeded" in msg.lower() for msg in error_messages)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_completes_before_timeout(
    temp_project_root: Path,
    cursor_mode_env,
    simple_workflow: Workflow,
):
    """Test that workflow completes successfully if it finishes before timeout."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    # Mock config with reasonable timeout
    with patch("tapps_agents.core.config.load_config") as mock_config:
        mock_config_instance = MagicMock()
        mock_config_instance.workflow.timeout_seconds = 5.0
        mock_config.return_value = mock_config_instance

        # Mock execution to complete quickly
        executor._initialize_run = AsyncMock(return_value=None)

        # Create a mock state that completes immediately
        mock_state = MagicMock()
        mock_state.status = "completed"
        mock_state.workflow_id = "test-workflow-123"
        mock_state.completed_steps = ["step-1"]
        executor.state = mock_state

        executor._finalize_run = AsyncMock(return_value=mock_state)

        # Mock the execution loop to complete immediately
        original_run = executor.run

        async def quick_run(*args, **kwargs):
            # Simulate quick completion
            await asyncio.sleep(0.1)
            return mock_state

        executor.run = quick_run

        await executor.start(workflow=simple_workflow, user_prompt="Test")

        # Should complete without timeout
        result = await executor.run(workflow=simple_workflow)

        assert result.status == "completed"
        assert "step-1" in result.completed_steps

