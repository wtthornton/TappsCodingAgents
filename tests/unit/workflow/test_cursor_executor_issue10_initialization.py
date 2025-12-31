"""
Unit tests for Issue 10: Simple Mode Full Workflow Infinite Loop - Initialization.

Tests the workflow initialization validation improvements.
"""

from __future__ import annotations

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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_run_validates_workflow_has_steps(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _initialize_run validates workflow has steps."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    # Create workflow with no steps
    empty_workflow = Workflow(
        id="empty-workflow",
        name="Empty Workflow",
        description="Workflow with no steps",
        version="1.0.0",
        type=WorkflowType.GREENFIELD,
        steps=[],  # No steps
    )

    executor.workflow = empty_workflow

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await executor._initialize_run(workflow=empty_workflow, target_file=None)

    assert "no steps" in str(exc_info.value).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_run_validates_first_step_ready(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _initialize_run validates first step can be executed."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    # Create workflow with first step that has no dependencies
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow",
        version="1.0.0",
        type=WorkflowType.GREENFIELD,
        steps=[
            WorkflowStep(
                id="step-1",
                agent="analyst",
                action="gather-requirements",
                requires=[],  # No dependencies
                creates=["requirements.md"],
            )
        ],
    )

    # Mock logger
    mock_logger = MagicMock()
    executor.logger = mock_logger

    # Mock start method
    executor.start = AsyncMock(return_value=MagicMock())

    # Should succeed and log that first step is ready
    result = await executor._initialize_run(workflow=workflow, target_file=None)

    # Verify logger was called with first step info
    assert mock_logger.info.called
    log_calls = [str(call) for call in mock_logger.info.call_args_list]
    assert any("first step" in str(call).lower() for call in log_calls)
    assert any("step-1" in str(call) for call in log_calls)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_run_creates_state_if_missing(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _initialize_run creates state if it doesn't exist."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow",
        version="1.0.0",
        type=WorkflowType.GREENFIELD,
        steps=[
            WorkflowStep(
                id="step-1",
                agent="analyst",
                action="gather-requirements",
            )
        ],
    )

    # Ensure state is None
    executor.state = None

    # Mock start to create state and set executor.state
    mock_state = MagicMock()
    mock_state.workflow_id = "test-workflow-123"
    
    async def mock_start(workflow=None, user_prompt=None):
        executor.state = mock_state
        return mock_state
    
    executor.start = mock_start

    # Should call start to create state
    await executor._initialize_run(workflow=workflow, target_file=None)

    assert executor.state == mock_state
    assert executor.state.workflow_id == "test-workflow-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_run_handles_target_file(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _initialize_run handles target file correctly."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow",
        version="1.0.0",
        type=WorkflowType.GREENFIELD,
        steps=[
            WorkflowStep(
                id="step-1",
                agent="analyst",
                action="gather-requirements",
            )
        ],
    )

    # Create mock state
    mock_state = MagicMock()
    mock_state.workflow_id = "test-workflow-123"
    mock_state.variables = {}
    executor.state = mock_state
    executor.workflow = workflow

    executor.start = AsyncMock(return_value=mock_state)

    target_file = "src/main.py"
    result = await executor._initialize_run(workflow=workflow, target_file=target_file)

    # Verify target file was set in state variables
    assert "target_file" in mock_state.variables
    assert mock_state.variables["target_file"] == str(temp_project_root / target_file)

