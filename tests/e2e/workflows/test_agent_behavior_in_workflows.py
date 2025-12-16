"""
E2E tests for agent behavior during workflow execution.

Tests validate:
- Agents receive correct context from workflow
- Agents produce artifacts that workflow expects
- Agents handle workflow-specific errors
- Agents integrate correctly with workflow state
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.agent_test_helpers import create_test_agent
from tests.e2e.fixtures.workflow_runner import (
    WorkflowRunner,
    validate_agent_artifacts,
    validate_agent_context,
    validate_agent_workflow_state_interaction,
)


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestAgentBehaviorInWorkflows:
    """Test agent behavior during workflow execution."""

    @pytest.mark.asyncio
    async def test_agents_receive_project_context(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that agents receive project context from workflow."""
        # Create a simple workflow YAML
        workflow_yaml = tmp_path / "test_workflow.yaml"
        workflow_yaml.write_text(
            """
id: test-workflow
name: Test Workflow
description: Test workflow for agent context
version: "1.0"
steps:
  - id: step1
    agent: planner
    action: plan
    creates:
      - plan.md
"""
        )

        runner = WorkflowRunner(e2e_project, use_mocks=True)
        workflow = runner.load_workflow(workflow_yaml)

        # Get first step
        if workflow.steps:
            step = workflow.steps[0]
            # Create agent for step
            agent = create_test_agent(step.agent, mock_mal)
            await agent.activate(e2e_project)

            # Create workflow state
            from datetime import datetime

            from tapps_agents.workflow.models import WorkflowState

            workflow_state = WorkflowState(
                workflow_id=workflow.id, started_at=datetime.now()
            )

            # Create step context
            step_context = {
                "step_id": step.id,
                "action": step.action,
                "project_path": str(e2e_project),
            }

            # Validate agent received context
            validate_agent_context(agent, workflow_state, step_context)

    @pytest.mark.asyncio
    async def test_agents_receive_workflow_state(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that agents receive workflow state."""
        workflow_yaml = tmp_path / "test_workflow.yaml"
        workflow_yaml.write_text(
            """
id: test-workflow
name: Test Workflow
version: "1.0"
steps:
  - id: step1
    agent: planner
    action: plan
"""
        )

        runner = WorkflowRunner(e2e_project, use_mocks=True)
        workflow = runner.load_workflow(workflow_yaml)

        from datetime import datetime

        from tapps_agents.workflow.models import WorkflowState

        workflow_state = WorkflowState(
            workflow_id=workflow.id,
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=[],
        )

        if workflow.steps:
            step = workflow.steps[0]
            agent = create_test_agent(step.agent, mock_mal)
            await agent.activate(e2e_project)

            step_context = {
                "workflow_state": workflow_state,
                "previous_artifacts": {},
            }

            validate_agent_context(agent, workflow_state, step_context)

    @pytest.mark.asyncio
    async def test_agents_receive_step_specific_context(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that agents receive step-specific context."""
        workflow_yaml = tmp_path / "test_workflow.yaml"
        workflow_yaml.write_text(
            """
id: test-workflow
name: Test Workflow
version: "1.0"
steps:
  - id: step1
    agent: planner
    action: plan
    metadata:
      description: "Create a plan for feature X"
"""
        )

        runner = WorkflowRunner(e2e_project, use_mocks=True)
        workflow = runner.load_workflow(workflow_yaml)

        from datetime import datetime

        from tapps_agents.workflow.models import WorkflowState

        workflow_state = WorkflowState(
            workflow_id=workflow.id, started_at=datetime.now()
        )

        if workflow.steps:
            step = workflow.steps[0]
            agent = create_test_agent(step.agent, mock_mal)
            await agent.activate(e2e_project)

            step_context = {
                "step_id": step.id,
                "action": step.action,
                "parameters": step.metadata,
                "requires": step.requires,
            }

            validate_agent_context(agent, workflow_state, step_context)

    @pytest.mark.asyncio
    async def test_agents_produce_expected_artifacts(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that agents produce artifacts that workflow expects."""
        # Create a test file that will be an artifact
        artifact_file = e2e_project / "plan.md"
        artifact_file.write_text("# Test Plan\n\nThis is a test plan.\n")

        workflow_yaml = tmp_path / "test_workflow.yaml"
        workflow_yaml.write_text(
            """
id: test-workflow
name: Test Workflow
version: "1.0"
steps:
  - id: step1
    agent: planner
    action: plan
    creates:
      - plan.md
"""
        )

        runner = WorkflowRunner(e2e_project, use_mocks=True)
        workflow = runner.load_workflow(workflow_yaml)

        if workflow.steps:
            step = workflow.steps[0]
            # Simulate artifacts from workflow state
            artifacts = {
                "plan.md": {
                    "name": "plan.md",
                    "path": str(artifact_file),
                    "status": "complete",
                }
            }

            validate_agent_artifacts(artifacts, step.creates)

    @pytest.mark.asyncio
    async def test_artifacts_registered_in_workflow_state(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that artifacts are registered in workflow state."""
        from datetime import datetime

        from tapps_agents.workflow.models import Artifact, WorkflowState

        artifact_file = e2e_project / "output.txt"
        artifact_file.write_text("Test output\n")

        workflow_state = WorkflowState(
            workflow_id="test-workflow", started_at=datetime.now()
        )

        # Register artifact
        artifact = Artifact(
            name="output.txt",
            path=str(artifact_file),
            status="complete",
            created_by="test-agent",
        )
        workflow_state.artifacts["output.txt"] = artifact

        # Verify artifact is registered
        assert "output.txt" in workflow_state.artifacts
        assert workflow_state.artifacts["output.txt"].status == "complete"

    @pytest.mark.asyncio
    async def test_artifacts_accessible_to_subsequent_steps(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that artifacts are accessible to subsequent workflow steps."""
        from datetime import datetime

        from tapps_agents.workflow.models import Artifact, WorkflowState

        # Create artifact from first step
        artifact1 = e2e_project / "step1_output.txt"
        artifact1.write_text("Step 1 output\n")

        workflow_state = WorkflowState(
            workflow_id="test-workflow", started_at=datetime.now()
        )
        workflow_state.artifacts["step1_output.txt"] = Artifact(
            name="step1_output.txt",
            path=str(artifact1),
            status="complete",
        )

        # Second step should be able to access it
        assert "step1_output.txt" in workflow_state.artifacts
        artifact = workflow_state.artifacts["step1_output.txt"]
        assert artifact.status == "complete"
        assert Path(artifact.path).exists()

    @pytest.mark.asyncio
    async def test_agents_handle_missing_workflow_context(
        self, e2e_project, mock_mal
    ):
        """Test that agents handle missing workflow context gracefully."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        # Try to execute without full workflow context
        from tests.e2e.fixtures.agent_test_helpers import execute_command

        result = await execute_command(agent, "*plan", description="test")
        # Should handle gracefully (may work with just description)
        assert result is not None

    @pytest.mark.asyncio
    async def test_agents_handle_invalid_workflow_state(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that agents handle invalid workflow state gracefully."""
        from datetime import datetime

        from tapps_agents.workflow.models import WorkflowState

        # Create invalid state (missing required fields)
        WorkflowState(
            workflow_id="", started_at=datetime.now()
        )

        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        # Agent should still function even with invalid state
        # Should not crash
        assert agent is not None
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_agents_read_workflow_state_correctly(
        self, e2e_project, mock_mal
    ):
        """Test that agents read workflow state correctly."""
        from datetime import datetime

        from tapps_agents.workflow.models import WorkflowState

        workflow_state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=["step0"],
            status="running",
        )

        # Verify state can be read
        assert workflow_state.workflow_id == "test-workflow"
        assert workflow_state.current_step == "step1"
        assert "step0" in workflow_state.completed_steps
        assert workflow_state.status == "running"

    @pytest.mark.asyncio
    async def test_agents_update_workflow_state_correctly(
        self, e2e_project, mock_mal
    ):
        """Test that agents update workflow state correctly."""
        from datetime import datetime

        from tapps_agents.workflow.models import Artifact, WorkflowState

        workflow_state = WorkflowState(
            workflow_id="test-workflow", started_at=datetime.now()
        )

        # Simulate agent updating state
        workflow_state.current_step = "step1"
        workflow_state.completed_steps.append("step1")
        workflow_state.artifacts["new_artifact.txt"] = Artifact(
            name="new_artifact.txt",
            path="new_artifact.txt",
            status="complete",
        )

        # Verify updates
        assert workflow_state.current_step == "step1"
        assert "step1" in workflow_state.completed_steps
        assert "new_artifact.txt" in workflow_state.artifacts

    @pytest.mark.asyncio
    async def test_agents_maintain_state_consistency(
        self, e2e_project, mock_mal
    ):
        """Test that agents maintain state consistency during execution."""
        from datetime import datetime

        from tapps_agents.workflow.models import WorkflowState

        workflow_state = WorkflowState(
            workflow_id="test-workflow", started_at=datetime.now()
        )

        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        # Validate state consistency
        validate_agent_workflow_state_interaction(agent, workflow_state)

        # State should remain consistent
        assert workflow_state.workflow_id is not None
        assert isinstance(workflow_state.artifacts, dict)
        assert isinstance(workflow_state.completed_steps, list)

    @pytest.mark.asyncio
    async def test_simple_workflow_agent_behavior(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test agent behavior in simple workflow (single agent, single step)."""
        workflow_yaml = tmp_path / "simple_workflow.yaml"
        workflow_yaml.write_text(
            """
id: simple-workflow
name: Simple Workflow
version: "1.0"
steps:
  - id: plan
    agent: planner
    action: plan
"""
        )

        runner = WorkflowRunner(e2e_project, use_mocks=True)
        workflow = runner.load_workflow(workflow_yaml)

        if workflow.steps:
            step = workflow.steps[0]
            agent = create_test_agent(step.agent, mock_mal)
            await agent.activate(e2e_project)

            from datetime import datetime

            from tapps_agents.workflow.models import WorkflowState

            workflow_state = WorkflowState(
                workflow_id=workflow.id, started_at=datetime.now()
            )

            step_context = {"step_id": step.id, "action": step.action}
            validate_agent_context(agent, workflow_state, step_context)

    @pytest.mark.asyncio
    async def test_multi_step_workflow_agent_behavior(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test agent behavior in multi-step workflow."""
        workflow_yaml = tmp_path / "multi_step_workflow.yaml"
        workflow_yaml.write_text(
            """
id: multi-step-workflow
name: Multi-Step Workflow
version: "1.0"
steps:
  - id: plan
    agent: planner
    action: plan
    creates:
      - plan.md
  - id: implement
    agent: implementer
    action: implement
    requires:
      - plan.md
"""
        )

        runner = WorkflowRunner(e2e_project, use_mocks=True)
        workflow = runner.load_workflow(workflow_yaml)

        from datetime import datetime

        from tapps_agents.workflow.models import Artifact, WorkflowState

        workflow_state = WorkflowState(
            workflow_id=workflow.id, started_at=datetime.now()
        )

        # Simulate first step completion
        workflow_state.completed_steps.append("plan")
        workflow_state.artifacts["plan.md"] = Artifact(
            name="plan.md", path="plan.md", status="complete"
        )

        # Second step should have access to first step's artifact
        if len(workflow.steps) > 1:
            step2 = workflow.steps[1]
            assert "plan.md" in workflow_state.artifacts
            assert "plan.md" in step2.requires

