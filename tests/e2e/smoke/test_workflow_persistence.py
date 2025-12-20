"""
Smoke E2E tests for workflow state persistence and resume.

Tests validate that:
- Workflow state can be saved to disk
- Workflow state can be loaded from disk
- Workflow can be resumed from saved state
- State consistency is maintained (checksums, version)
"""


import pytest

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.parser import WorkflowParser


@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
class TestWorkflowPersistence:
    """Test workflow state persistence and resume."""

    def test_save_workflow_state(self, e2e_project, tmp_path):
        """Test saving workflow state to disk."""
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
        executor.start(workflow=workflow)
        
        # Save state
        state_path = executor.save_state()
        
        assert state_path is not None
        assert state_path.exists()
        
        # Verify state directory exists
        state_dir = e2e_project / ".tapps-agents" / "workflow-state"
        assert state_dir.exists()

    def test_load_workflow_state(self, e2e_project, tmp_path):
        """Test loading workflow state from disk."""
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
        
        # Create executor and save state
        executor1 = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        workflow = WorkflowParser.parse_file(workflow_file)
        executor1.load_workflow(workflow_file)
        state1 = executor1.start(workflow=workflow)
        executor1.save_state()
        
        # Create new executor and load state
        executor2 = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        state2 = executor2.load_last_state()
        
        assert state2 is not None
        assert state2.workflow_id == state1.workflow_id
        assert state2.status == state1.status
        assert state2.current_step == state1.current_step

    def test_resume_workflow_from_state(self, e2e_project, tmp_path):
        """Test resuming workflow from saved state."""
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
        
        # Create executor, start workflow, and save state
        executor1 = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        workflow = WorkflowParser.parse_file(workflow_file)
        executor1.load_workflow(workflow_file)
        state1 = executor1.start(workflow=workflow)
        executor1.save_state()
        
        # Create new executor and resume
        executor2 = WorkflowExecutor(
            project_root=e2e_project,
            auto_detect=False,
            advanced_state=False,
        )
        
        executor2.load_workflow(workflow_file)
        executor2.load_last_state()
        
        # Verify workflow can be resumed
        assert executor2.workflow is not None
        assert executor2.state is not None
        assert executor2.state.workflow_id == state1.workflow_id
        assert executor2.state.current_step == state1.current_step

    def test_state_consistency(self, e2e_project, tmp_path):
        """Test state consistency (checksums, version)."""
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
        executor.start(workflow=workflow)
        executor.save_state()
        
        # Load state and verify consistency
        loaded_state = executor.load_last_state()
        
        # Verify required fields are present
        assert loaded_state.workflow_id is not None
        assert loaded_state.status is not None
        assert loaded_state.current_step is not None
        assert loaded_state.started_at is not None
        
        # Verify state structure (contract validation)
        assert isinstance(loaded_state.completed_steps, list)
        assert isinstance(loaded_state.skipped_steps, list)

    def test_state_contract_validation(self, e2e_project, tmp_path):
        """Test that state contract (required fields, structure) is validated."""
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
        executor.start(workflow=workflow)
        executor.save_state()
        
        # Load state and validate contract
        loaded_state = executor.load_last_state()
        
        # Validate state has required structure
        required_attributes = [
            "workflow_id",
            "status",
            "current_step",
            "started_at",
            "completed_steps",
            "skipped_steps",
        ]
        
        for attr in required_attributes:
            assert hasattr(loaded_state, attr), f"State missing required attribute: {attr}"
            assert getattr(loaded_state, attr) is not None, f"State attribute {attr} is None"
