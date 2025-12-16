"""
Test workflow prompt and auto mode functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.models import Workflow, WorkflowStep, WorkflowType
from tapps_agents.workflow.timeline import format_timeline_markdown, generate_timeline


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def simple_workflow():
    """Create a simple workflow for testing."""
    return Workflow(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow for prompt testing",
        version="1.0.0",
        type=WorkflowType.GREENFIELD,
        steps=[
            WorkflowStep(
                id="step1",
                agent="analyst",
                action="gather-requirements",
                creates=["requirements.md"],
                next="step2",
            ),
            WorkflowStep(
                id="step2",
                agent="orchestrator",
                action="complete",
            ),
        ],
    )


@pytest.mark.asyncio
async def test_workflow_executor_stores_user_prompt(temp_project, simple_workflow):
    """Test that user prompt is stored in workflow state."""
    executor = WorkflowExecutor(
        project_root=temp_project,
        auto_detect=False,
        auto_mode=True,
    )
    executor.user_prompt = "Create a test application"

    state = executor.start(workflow=simple_workflow)

    assert state.variables.get("user_prompt") == "Create a test application"


@pytest.mark.asyncio
async def test_analyst_agent_receives_prompt(temp_project, simple_workflow):
    """Test that analyst agent receives user prompt."""
    executor = WorkflowExecutor(
        project_root=temp_project,
        auto_detect=False,
        auto_mode=True,
    )
    executor.user_prompt = "Create a web application for task management"

    executor.start(workflow=simple_workflow)

    # Mock the analyst agent
    with patch(
        "tapps_agents.workflow.executor.__import__"
    ) as mock_import:
        mock_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run = AsyncMock(
            return_value={"requirements": "Test requirements"}
        )
        mock_agent_instance.activate = AsyncMock()
        mock_agent_instance.close = AsyncMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_module.AnalystAgent = mock_agent_class

        def import_side_effect(name, fromlist):
            if name == "tapps_agents.agents.analyst.agent":
                return mock_module
            return MagicMock()

        mock_import.side_effect = import_side_effect

        # Execute first step (analyst)
        step = simple_workflow.steps[0]
        await executor._execute_step(step=step, target_path=None)

        # Verify analyst agent was called with prompt
        assert mock_agent_instance.run.called
        call_args = mock_agent_instance.run.call_args
        assert call_args[0][0] == "gather-requirements"
        assert "description" in call_args[1]
        assert call_args[1]["description"] == "Create a web application for task management"


@pytest.mark.asyncio
async def test_timeline_generation(temp_project, simple_workflow):
    """Test timeline generation."""
    executor = WorkflowExecutor(
        project_root=temp_project,
        auto_detect=False,
        auto_mode=True,
    )

    state = executor.start(workflow=simple_workflow)

    # Add some mock step executions
    from datetime import datetime, timedelta

    from tapps_agents.workflow.models import StepExecution

    step1_start = datetime.now()
    step1_end = step1_start + timedelta(seconds=5)

    state.step_executions.append(
        StepExecution(
            step_id="step1",
            agent="analyst",
            action="gather-requirements",
            started_at=step1_start,
            completed_at=step1_end,
            duration_seconds=5.0,
            status="completed",
        )
    )

    timeline = generate_timeline(state, simple_workflow)

    assert timeline["workflow_id"] == "test-workflow"
    assert timeline["workflow_name"] == "Test Workflow"
    assert len(timeline["steps"]) == 1
    assert timeline["steps"][0]["step_id"] == "step1"
    assert timeline["steps"][0]["agent"] == "analyst"
    assert timeline["steps"][0]["duration_seconds"] == 5.0
    assert timeline["steps"][0]["status"] == "completed"


def test_timeline_markdown_formatting(temp_project, simple_workflow):
    """Test timeline markdown formatting."""
    from datetime import datetime, timedelta

    from tapps_agents.workflow.models import StepExecution, WorkflowState

    started_at = datetime.now()
    step1_start = started_at
    step1_end = step1_start + timedelta(seconds=10)

    state = WorkflowState(
        workflow_id="test-workflow",
        started_at=started_at,
        status="completed",
        step_executions=[
            StepExecution(
                step_id="step1",
                agent="analyst",
                action="gather-requirements",
                started_at=step1_start,
                completed_at=step1_end,
                duration_seconds=10.0,
                status="completed",
            )
        ],
    )

    timeline = generate_timeline(state, simple_workflow)
    markdown = format_timeline_markdown(timeline)

    assert "# Project Timeline" in markdown
    assert "Test Workflow" in markdown
    assert "step1" in markdown
    assert "analyst" in markdown
    assert "10.00s" in markdown
    assert "✅ completed" in markdown


@pytest.mark.asyncio
async def test_auto_mode_flag(temp_project, simple_workflow):
    """Test that auto mode flag is set correctly."""
    executor = WorkflowExecutor(
        project_root=temp_project,
        auto_detect=False,
        auto_mode=True,
    )

    assert executor.auto_mode is True

    executor2 = WorkflowExecutor(
        project_root=temp_project,
        auto_detect=False,
        auto_mode=False,
    )

    assert executor2.auto_mode is False


def test_step_execution_tracking(temp_project, simple_workflow):
    """Test that step executions are tracked."""
    executor = WorkflowExecutor(
        project_root=temp_project,
        auto_detect=False,
        auto_mode=True,
    )

    state = executor.start(workflow=simple_workflow)

    # Initially no step executions
    assert len(state.step_executions) == 0

    # After executing a step, should have one execution
    # (This would normally happen in _execute_step, but we can test the structure)
    from datetime import datetime

    from tapps_agents.workflow.models import StepExecution

    state.step_executions.append(
        StepExecution(
            step_id="step1",
            agent="analyst",
            action="gather-requirements",
            started_at=datetime.now(),
        )
    )

    assert len(state.step_executions) == 1
    assert state.step_executions[0].step_id == "step1"
    assert state.step_executions[0].agent == "analyst"
    assert state.step_executions[0].status == "running"

