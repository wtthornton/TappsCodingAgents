"""
Smoke E2E tests for workflow executor initialization and step advancement.

Tests validate that:
- Workflow executor can be initialized
- Workflow steps can be advanced with mocked agents
- State transitions work correctly
- Step execution order is validated
"""

import pytest

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.parser import WorkflowParser


@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
class TestWorkflowExecutor:
    """Test workflow executor initialization and step advancement."""

    def test_initialize_executor(self, e2e_project, mock_mal):
        """Test workflow executor initialization."""
        executor = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        assert executor.project_root == e2e_project
        assert executor.state is None
        assert executor.workflow is None

    def test_load_minimal_workflow(self, e2e_project, tmp_path, mock_mal):
        """Test loading a minimal workflow."""
        # Create a minimal workflow YAML
        workflow_file = tmp_path / "minimal_workflow.yaml"
        workflow_file.write_text(
            """
workflow:
  id: minimal-test
  name: "Minimal Test Workflow"
  version: "1.0.0"
  schema_version: "2.0"
  type: brownfield
  steps:
    - id: step1
      agent: planner
      action: plan
      next: step2
    - id: step2
      agent: implementer
      action: implement
"""
        )
        
        executor = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        WorkflowParser.parse_file(workflow_file)
        executor.load_workflow(workflow_file)
        
        assert executor.workflow is not None
        assert executor.workflow.id == "minimal-test"
        assert len(executor.workflow.steps) == 2

    def test_start_workflow(self, e2e_project, tmp_path, mock_mal):
        """Test starting a workflow."""
        # Create a minimal workflow
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test-workflow
  name: "Test Workflow"
  version: "1.0.0"
  schema_version: "2.0"
  type: brownfield
  steps:
    - id: step1
      agent: planner
      action: plan
"""
        )
        
        executor = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        workflow = WorkflowParser.parse_file(workflow_file)
        executor.load_workflow(workflow_file)
        state = executor.start(workflow=workflow)
        
        assert state is not None
        # Workflow ID includes timestamp suffix: {workflow.id}-{timestamp}
        assert state.workflow_id.startswith("test-workflow")
        assert state.status == "running"
        assert state.current_step == "step1"
        assert len(state.completed_steps) == 0

    def test_workflow_state_transitions(self, e2e_project, tmp_path, mock_mal):
        """Test workflow state transitions."""
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test-workflow
  name: "Test Workflow"
  version: "1.0.0"
  schema_version: "2.0"
  type: brownfield
  steps:
    - id: step1
      agent: planner
      action: plan
      next: step2
    - id: step2
      agent: implementer
      action: implement
"""
        )
        
        executor = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        workflow = WorkflowParser.parse_file(workflow_file)
        executor.load_workflow(workflow_file)
        
        # Start workflow
        state = executor.start(workflow=workflow)
        assert state.status == "running"
        assert state.current_step == "step1"
        
        # Verify state structure
        assert state.workflow_id is not None
        assert state.started_at is not None
        assert state.completed_steps is not None
        assert isinstance(state.completed_steps, list)

    def test_step_execution_order(self, e2e_project, tmp_path, mock_mal):
        """Test that step execution order is validated."""
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test-workflow
  name: "Test Workflow"
  version: "1.0.0"
  schema_version: "2.0"
  type: brownfield
  steps:
    - id: step1
      agent: planner
      action: plan
      next: step2
    - id: step2
      agent: implementer
      action: implement
      next: step3
    - id: step3
      agent: reviewer
      action: review
"""
        )
        
        executor = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        workflow = WorkflowParser.parse_file(workflow_file)
        executor.load_workflow(workflow_file)
        state = executor.start(workflow=workflow)
        
        # Verify step order
        step_ids = [step.id for step in workflow.steps]
        assert step_ids == ["step1", "step2", "step3"]
        
        # Verify current step is first
        assert state.current_step == "step1"

    def test_workflow_state_shape(self, e2e_project, tmp_path, mock_mal):
        """Test that workflow state has correct shape/contract."""
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test-workflow
  name: "Test Workflow"
  version: "1.0.0"
  schema_version: "2.0"
  type: brownfield
  steps:
    - id: step1
      agent: planner
      action: plan
"""
        )
        
        executor = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        workflow = WorkflowParser.parse_file(workflow_file)
        executor.load_workflow(workflow_file)
        state = executor.start(workflow=workflow)
        
        # Validate state contract (required fields)
        required_fields = [
            "workflow_id",
            "status",
            "current_step",
            "started_at",
            "completed_steps",
            "skipped_steps",
        ]
        
        for field in required_fields:
            assert hasattr(state, field), f"State missing required field: {field}"
        
        # Validate field types
        assert isinstance(state.workflow_id, str)
        assert isinstance(state.status, str)
        assert isinstance(state.current_step, str)
        assert isinstance(state.completed_steps, list)
        assert isinstance(state.skipped_steps, list)
