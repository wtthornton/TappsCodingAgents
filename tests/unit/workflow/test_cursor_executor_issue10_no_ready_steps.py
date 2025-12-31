"""
Unit tests for Issue 10: Simple Mode Full Workflow Infinite Loop - No Ready Steps.

Tests the improved diagnostics for when no steps are ready to execute.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.models import Artifact, Workflow, WorkflowState, WorkflowStep, WorkflowType


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
def test_handle_no_ready_steps_when_complete(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _handle_no_ready_steps detects workflow completion."""
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

    # Create state with all steps completed
    state = WorkflowState(
        workflow_id="test-workflow-123",
        started_at=datetime.now(),
        status="running",
        completed_steps=["step-1", "step-2"],
        current_step="step-2",
    )
    executor.state = state

    # Mock save_state to avoid file I/O issues
    executor.save_state = MagicMock()

    # Should detect completion and return True
    result = executor._handle_no_ready_steps(set(["step-1", "step-2"]))

    assert result is True
    assert state.status == "completed"
    assert state.current_step is None
    assert executor.save_state.called


@pytest.mark.unit
def test_handle_no_ready_steps_when_blocked(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _handle_no_ready_steps provides diagnostics when blocked."""
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
                creates=["requirements.md"],
            ),
            WorkflowStep(
                id="step-2",
                agent="planner",
                action="create_stories",
                requires=["requirements.md"],  # Requires step-1 output
            ),
        ],
    )

    executor.workflow = workflow

    # Create state with step-1 completed but missing artifact
    state = WorkflowState(
        workflow_id="test-workflow-123",
        started_at=datetime.now(),
        status="running",
        completed_steps=["step-1"],
    )
    
    # Mock save_state to avoid file I/O issues
    executor.save_state = MagicMock()
    executor.state = state
    state.artifacts = {}  # Missing requirements.md

    # Should detect blocking and provide diagnostics
    result = executor._handle_no_ready_steps(set(["step-1"]))

    assert result is True
    assert state.status == "failed"
    assert state.error is not None
    assert "blocked" in state.error.lower() or "no ready steps" in state.error.lower()


@pytest.mark.unit
def test_handle_no_ready_steps_identifies_missing_artifacts(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _handle_no_ready_steps identifies missing artifacts."""
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
                creates=["requirements.md"],
            ),
            WorkflowStep(
                id="step-2",
                agent="planner",
                action="create_stories",
                requires=["requirements.md", "architecture.md"],  # Missing architecture.md
            ),
        ],
    )

    executor.workflow = workflow

    # Create state with only requirements.md artifact
    artifact = Artifact(
        name="requirements.md",
        path="requirements.md",
        status="complete",
    )

    state = WorkflowState(
        workflow_id="test-workflow-123",
        started_at=datetime.now(),
        status="running",
        completed_steps=["step-1"],
        artifacts={"requirements.md": artifact},  # Missing architecture.md
    )
    
    # Mock save_state to avoid file I/O issues
    executor.save_state = MagicMock()
    executor.state = state

    result = executor._handle_no_ready_steps(set(["step-1"]))

    # Should identify missing architecture.md
    assert result is True
    assert state.error is not None
    assert "architecture.md" in state.error or "blocking" in state.error.lower()


@pytest.mark.unit
def test_handle_no_ready_steps_with_multiple_blocking_steps(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that _handle_no_ready_steps handles multiple blocking steps."""
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
                creates=["requirements.md"],
            ),
            WorkflowStep(
                id="step-2",
                agent="planner",
                action="create_stories",
                requires=["requirements.md"],
            ),
            WorkflowStep(
                id="step-3",
                agent="architect",
                action="design_system",
                requires=["requirements.md", "stories/"],
            ),
        ],
    )

    executor.workflow = workflow

    state = WorkflowState(
        workflow_id="test-workflow-123",
        started_at=datetime.now(),
        status="running",
        completed_steps=["step-1"],
        artifacts={},  # No artifacts
    )
    
    # Mock save_state to avoid file I/O issues
    executor.save_state = MagicMock()
    executor.state = state

    result = executor._handle_no_ready_steps(set(["step-1"]))

    # Should identify both step-2 and step-3 as blocking
    assert result is True
    assert state.error is not None
    assert "step-2" in state.error or "step-3" in state.error or "blocking" in state.error.lower()

