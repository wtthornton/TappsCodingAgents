"""
Unit tests for Issue 10: Simple Mode Full Workflow Infinite Loop - Health Check.

Tests the get_workflow_health() method for workflow diagnostics.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.models import StepExecution, Workflow, WorkflowStep, WorkflowType


@pytest.fixture
def cursor_mode_env(monkeypatch):
    """Set up Cursor mode environment for tests. Also patch is_cursor_mode so
    CursorWorkflowExecutor can be instantiated in headless CI (GitHub Actions).
    """
    monkeypatch.setenv("TAPPS_AGENTS_MODE", "cursor")
    monkeypatch.setenv("CURSOR_IDE", "1")
    with patch("tapps_agents.workflow.cursor_executor.is_cursor_mode", return_value=True):
        yield


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create temporary project root for testing."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir(parents=True)
    return project_root


@pytest.mark.unit
def test_get_workflow_health_when_not_started(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that get_workflow_health returns not_started when workflow not started."""
    executor = CursorWorkflowExecutor(
        project_root=temp_project_root,
        auto_mode=True,
    )

    executor.state = None

    health = executor.get_workflow_health()

    assert health["status"] == "not_started"
    assert "message" in health


@pytest.mark.unit
def test_get_workflow_health_returns_basic_info(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that get_workflow_health returns basic workflow information."""
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
            WorkflowStep(id="step-1", agent="analyst", action="gather-requirements"),
            WorkflowStep(id="step-2", agent="planner", action="create_stories"),
        ],
    )

    executor.workflow = workflow

    # Create state
    mock_state = MagicMock()
    mock_state.status = "running"
    mock_state.started_at = datetime.now() - timedelta(seconds=100)
    mock_state.completed_steps = ["step-1"]
    mock_state.current_step = "step-2"
    mock_state.error = None
    mock_state.step_executions = []
    executor.state = mock_state

    health = executor.get_workflow_health()

    assert health["status"] == "running"
    assert health["completed_steps"] == 1
    assert health["total_steps"] == 2
    assert health["progress_percent"] == 50.0
    assert health["current_step"] == "step-2"
    assert health["elapsed_seconds"] > 0


@pytest.mark.unit
def test_get_workflow_health_detects_stuck_workflow(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that get_workflow_health detects stuck workflows."""
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
            WorkflowStep(id="step-1", agent="analyst", action="gather-requirements"),
        ],
    )

    executor.workflow = workflow

    # Create state with last step completed 6 minutes ago (stuck)
    mock_step_execution = MagicMock(spec=StepExecution)
    mock_step_execution.completed_at = datetime.now() - timedelta(minutes=6)

    mock_state = MagicMock()
    mock_state.status = "running"
    mock_state.started_at = datetime.now() - timedelta(minutes=10)
    mock_state.completed_steps = ["step-1"]
    mock_state.current_step = "step-1"
    mock_state.error = None
    mock_state.step_executions = [mock_step_execution]
    executor.state = mock_state

    health = executor.get_workflow_health()

    assert health["is_stuck"] is True
    assert health["time_since_last_step"] > 300  # 5 minutes


@pytest.mark.unit
def test_get_workflow_health_not_stuck_when_recent_progress(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that get_workflow_health doesn't flag workflow as stuck when progress is recent."""
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
            WorkflowStep(id="step-1", agent="analyst", action="gather-requirements"),
        ],
    )

    executor.workflow = workflow

    # Create state with last step completed 1 minute ago (not stuck)
    mock_step_execution = MagicMock(spec=StepExecution)
    mock_step_execution.completed_at = datetime.now() - timedelta(minutes=1)

    mock_state = MagicMock()
    mock_state.status = "running"
    mock_state.started_at = datetime.now() - timedelta(minutes=5)
    mock_state.completed_steps = ["step-1"]
    mock_state.current_step = "step-1"
    mock_state.error = None
    mock_state.step_executions = [mock_step_execution]
    executor.state = mock_state

    health = executor.get_workflow_health()

    assert health["is_stuck"] is False
    assert health["time_since_last_step"] < 300  # Less than 5 minutes


@pytest.mark.unit
def test_get_workflow_health_includes_error_info(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that get_workflow_health includes error information."""
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
            WorkflowStep(id="step-1", agent="analyst", action="gather-requirements"),
        ],
    )

    executor.workflow = workflow

    mock_state = MagicMock()
    mock_state.status = "failed"
    mock_state.started_at = datetime.now() - timedelta(seconds=50)
    mock_state.completed_steps = []
    mock_state.current_step = None
    mock_state.error = "Test error message"
    mock_state.step_executions = []
    executor.state = mock_state

    health = executor.get_workflow_health()

    assert health["status"] == "failed"
    assert health["error"] == "Test error message"


@pytest.mark.unit
def test_get_workflow_health_calculates_progress_percent(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that get_workflow_health calculates progress percentage correctly."""
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
            WorkflowStep(id="step-1", agent="analyst", action="gather-requirements"),
            WorkflowStep(id="step-2", agent="planner", action="create_stories"),
            WorkflowStep(id="step-3", agent="architect", action="design_system"),
            WorkflowStep(id="step-4", agent="implementer", action="write_code"),
        ],
    )

    executor.workflow = workflow

    mock_state = MagicMock()
    mock_state.status = "running"
    mock_state.started_at = datetime.now()
    mock_state.completed_steps = ["step-1", "step-2"]  # 2 of 4 steps
    mock_state.current_step = "step-3"
    mock_state.error = None
    mock_state.step_executions = []
    executor.state = mock_state

    health = executor.get_workflow_health()

    assert health["progress_percent"] == 50.0  # 2/4 = 50%

