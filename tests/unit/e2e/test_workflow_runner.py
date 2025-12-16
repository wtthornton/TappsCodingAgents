"""
Unit tests for workflow runner E2E harness.
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.workflow_runner import (
    GateController,
    WorkflowRunner,
    control_gate_outcome,
)


@pytest.mark.unit
class TestGateController:
    """Test cases for GateController."""

    def test_set_outcome(self):
        """Test setting gate outcome."""
        controller = GateController()
        controller.set_outcome("gate1", True)
        assert controller.get_outcome("gate1") is True

        controller.set_outcome("gate2", False)
        assert controller.get_outcome("gate2") is False

    def test_get_outcome_default(self):
        """Test getting gate outcome with default."""
        controller = GateController()
        assert controller.get_outcome("unknown_gate") is True  # default
        assert controller.get_outcome("unknown_gate", default=False) is False

    def test_clear(self):
        """Test clearing gate outcomes."""
        controller = GateController()
        controller.set_outcome("gate1", True)
        controller.set_outcome("gate2", False)

        controller.clear()
        assert controller.get_outcome("gate1") is True  # back to default
        assert controller.get_outcome("gate2") is True  # back to default


@pytest.mark.unit
class TestWorkflowRunner:
    """Test cases for WorkflowRunner."""

    @pytest.fixture
    def project_path(self, tmp_path: Path) -> Path:
        """Create a test project path."""
        return tmp_path / "test_project"

    @pytest.fixture
    def workflow_path(self, tmp_path: Path) -> Path:
        """Create a minimal workflow YAML file."""
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text("""
workflow:
  id: test-workflow
  name: Test Workflow
  description: Test
  version: 1.0.0
  steps:
    - id: step1
      agent: analyst
      action: gather
      creates: ["file1.md"]
      requires: []
""")
        return workflow_file

    def test_init(self, project_path: Path):
        """Test WorkflowRunner initialization."""
        runner = WorkflowRunner(project_path)
        assert runner.project_path == project_path
        assert runner.use_mocks is True
        assert runner.gate_controller is not None
        assert runner.correlation_id is not None

    def test_init_with_gate_controller(self, project_path: Path):
        """Test WorkflowRunner initialization with custom gate controller."""
        controller = GateController()
        runner = WorkflowRunner(project_path, gate_controller=controller)
        assert runner.gate_controller is controller

    def test_load_workflow(self, project_path: Path, workflow_path: Path):
        """Test loading a workflow."""
        runner = WorkflowRunner(project_path)
        workflow = runner.load_workflow(workflow_path)

        assert workflow.id == "test-workflow"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].id == "step1"

    def test_create_executor(self, project_path: Path):
        """Test creating a workflow executor."""
        runner = WorkflowRunner(project_path)
        executor = runner.create_executor()

        assert executor is not None
        assert executor.project_root == project_path
        assert executor.auto_mode is True

    def test_capture_workflow_state(self, project_path: Path):
        """Test capturing workflow state."""
        runner = WorkflowRunner(project_path)
        executor = runner.create_executor()

        # Mock executor state
        from datetime import datetime

        from tapps_agents.workflow.models import WorkflowState

        executor.state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            status="running",
            current_step="step1",
        )

        snapshot = runner.capture_workflow_state(executor, step_id="step1")

        assert snapshot["workflow_id"] == "test-workflow"
        assert snapshot["status"] == "running"
        assert snapshot["current_step"] == "step1"
        assert snapshot["step_id"] == "step1"
        assert len(runner.state_snapshots) == 1

    def test_control_gate_outcome(self, project_path: Path):
        """Test controlling gate outcome."""
        runner = WorkflowRunner(project_path)
        runner.control_gate_outcome("gate1", False)

        assert runner.gate_controller.get_outcome("gate1") is False

    def test_assert_workflow_artifacts_missing(self, project_path: Path):
        """Test artifact assertion with missing artifacts."""
        project_path.mkdir(parents=True, exist_ok=True)

        runner = WorkflowRunner(project_path)
        runner.create_executor()

        with pytest.raises(AssertionError, match="Missing expected artifacts"):
            runner.assert_workflow_artifacts(["missing_file.md"])

    def test_assert_workflow_artifacts_exists(self, project_path: Path):
        """Test artifact assertion with existing artifacts."""
        project_path.mkdir(parents=True, exist_ok=True)
        artifact_file = project_path / "test.md"
        artifact_file.write_text("# Test")

        runner = WorkflowRunner(project_path)
        runner.create_executor()

        # Should not raise
        runner.assert_workflow_artifacts(["test.md"])

    def test_assert_workflow_artifacts_in_tapps_agents(self, project_path: Path):
        """Test artifact assertion with artifacts in .tapps-agents directory."""
        project_path.mkdir(parents=True, exist_ok=True)
        tapps_dir = project_path / ".tapps-agents"
        tapps_dir.mkdir()
        artifact_file = tapps_dir / "test.json"
        artifact_file.write_text('{"key": "value"}')

        runner = WorkflowRunner(project_path)
        runner.create_executor()

        # Should not raise
        runner.assert_workflow_artifacts(["test.json"])

    def test_validate_artifact_content_json(self, project_path: Path):
        """Test JSON artifact content validation."""
        project_path.mkdir(parents=True, exist_ok=True)
        artifact_file = project_path / "test.json"
        artifact_file.write_text('{"key": "value"}')

        runner = WorkflowRunner(project_path)
        runner._validate_artifact_content(artifact_file)  # Should not raise

    def test_validate_artifact_content_invalid_json(self, project_path: Path):
        """Test invalid JSON artifact content validation."""
        project_path.mkdir(parents=True, exist_ok=True)
        artifact_file = project_path / "test.json"
        artifact_file.write_text("invalid json")

        runner = WorkflowRunner(project_path)
        with pytest.raises(AssertionError, match="not valid JSON"):
            runner._validate_artifact_content(artifact_file)

    def test_validate_artifact_content_empty(self, project_path: Path):
        """Test empty artifact content validation."""
        project_path.mkdir(parents=True, exist_ok=True)
        artifact_file = project_path / "test.md"
        artifact_file.write_text("")  # Empty file

        runner = WorkflowRunner(project_path)
        with pytest.raises(AssertionError, match="is empty"):
            runner._validate_artifact_content(artifact_file)


@pytest.mark.unit
class TestWorkflowRunnerConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_control_gate_outcome_function(self):
        """Test control_gate_outcome convenience function."""
        controller = control_gate_outcome("gate1", False)
        assert controller.get_outcome("gate1") is False

        # Test with existing controller
        controller2 = control_gate_outcome("gate2", True, controller)
        assert controller2 is controller
        assert controller.get_outcome("gate2") is True
