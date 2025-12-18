"""
End-to-end tests for Background Agent auto-execution.

Tests complete workflow execution with auto-execution enabled.
"""

from __future__ import annotations

import pytest
from pathlib import Path
import asyncio

from tests.fixtures.background_agent_fixtures import (
    MockBackgroundAgent,
)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_workflow_with_auto_execution(
    temp_project_root: Path,
    auto_execution_config_file: Path,
):
    """Test complete workflow execution with auto-execution."""
    from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
    from tapps_agents.workflow.workflow import Workflow, WorkflowStep

    # Create mock Background Agent
    worktree_path = temp_project_root / "worktree"
    worktree_path.mkdir()
    (worktree_path / ".cursor").mkdir(exist_ok=True)
    mock_agent = MockBackgroundAgent(worktree_path=worktree_path, delay_seconds=0.2)

    # Create workflow
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        metadata={"auto_execution": True},
        steps=[
            WorkflowStep(
                id="step-1",
                step="Gather Requirements",
                agent="analyst",
                action="gather-requirements",
                params={"target_file": "requirements.md"},
            ),
            WorkflowStep(
                id="step-2",
                step="Design System",
                agent="architect",
                action="design-system",
                params={"target_file": "design.md"},
            ),
        ],
    )

    # Create executor with auto-execution enabled
    executor = CursorWorkflowExecutor(
        workflow=workflow,
        project_root=temp_project_root,
        max_parallel_steps=1,
    )

    # Start mock agents for both steps
    execution_tasks = [
        asyncio.create_task(
            mock_agent.simulate_execution(
                workflow_id="test-workflow",
                step_id="step-1",
                success=True,
                artifacts=["requirements.md"],
            )
        ),
        asyncio.create_task(
            mock_agent.simulate_execution(
                workflow_id="test-workflow",
                step_id="step-2",
                success=True,
                artifacts=["design.md"],
            )
        ),
    ]

    # Execute workflow
    state = await executor.start()

    # Wait for mock agents
    await asyncio.gather(*execution_tasks)

    # Verify workflow completed
    assert state.status == "completed"
    assert len(state.completed_steps) == 2


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workflow_with_error_recovery(
    temp_project_root: Path,
    auto_execution_config_file: Path,
):
    """Test workflow execution with error recovery."""
    from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
    from tapps_agents.workflow.workflow import Workflow, WorkflowStep

    # Create mock Background Agent
    worktree_path = temp_project_root / "worktree"
    worktree_path.mkdir()
    (worktree_path / ".cursor").mkdir(exist_ok=True)
    mock_agent = MockBackgroundAgent(worktree_path=worktree_path, delay_seconds=0.1)

    # Create workflow with error handling
    workflow = Workflow(
        id="error-workflow",
        name="Error Recovery Workflow",
        metadata={"auto_execution": True},
        steps=[
            WorkflowStep(
                id="step-1",
                step="Failing Step",
                agent="analyst",
                action="gather-requirements",
                params={"target_file": "requirements.md"},
                on_error="continue",  # Continue on error
            ),
            WorkflowStep(
                id="step-2",
                step="Recovery Step",
                agent="architect",
                action="design-system",
                params={"target_file": "design.md"},
            ),
        ],
    )

    executor = CursorWorkflowExecutor(
        workflow=workflow,
        project_root=temp_project_root,
        error_recovery_enabled=True,
    )

    # First step fails, second succeeds
    execution_tasks = [
        asyncio.create_task(
            mock_agent.simulate_execution(
                workflow_id="error-workflow",
                step_id="step-1",
                success=False,
                error_message="Test error",
            )
        ),
        asyncio.create_task(
            mock_agent.simulate_execution(
                workflow_id="error-workflow",
                step_id="step-2",
                success=True,
            )
        ),
    ]

    state = await executor.start()
    await asyncio.gather(*execution_tasks)

    # Workflow should complete despite first step failure
    assert state.status in ["completed", "partial"]
    assert len(state.completed_steps) >= 1


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workflow_timeout_handling(
    temp_project_root: Path,
    auto_execution_config_file: Path,
):
    """Test workflow timeout handling."""
    from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
    from tapps_agents.workflow.workflow import Workflow, WorkflowStep

    # Create workflow with short timeout
    workflow = Workflow(
        id="timeout-workflow",
        name="Timeout Workflow",
        metadata={"auto_execution": True},
        steps=[
            WorkflowStep(
                id="step-1",
                step="Slow Step",
                agent="analyst",
                action="gather-requirements",
                params={"target_file": "requirements.md"},
            ),
        ],
    )

    # Configure short timeout
    executor = CursorWorkflowExecutor(
        workflow=workflow,
        project_root=temp_project_root,
    )
    # Set short timeout in executor config
    executor.auto_executor.timeout_seconds = 0.5

    worktree_path = temp_project_root / "worktree"
    worktree_path.mkdir()
    (worktree_path / ".cursor").mkdir(exist_ok=True)

    # Don't create status file (will timeout)
    state = await executor.start()

    # Should timeout
    assert state.status in ["failed", "timeout"]
    assert len(state.failed_steps) >= 1

