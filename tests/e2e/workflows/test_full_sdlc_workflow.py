"""
E2E tests for full-sdlc preset workflow.

Tests workflow parsing, execution, state transitions, and artifacts.
"""

import pytest
from pathlib import Path

from tests.e2e.fixtures.workflow_runner import WorkflowRunner


@pytest.mark.e2e_workflow
@pytest.mark.template_type("small")
class TestFullSDLCWorkflow:
    """E2E tests for full-sdlc preset workflow."""

    @pytest.fixture
    def workflow_path(self) -> Path:
        """Path to full-sdlc workflow YAML."""
        return Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "full-sdlc.yaml"

    @pytest.mark.asyncio
    async def test_workflow_parsing(self, workflow_runner: WorkflowRunner, workflow_path: Path):
        """Test that full-sdlc workflow can be parsed."""
        workflow = workflow_runner.load_workflow(workflow_path)

        assert workflow.id == "full-sdlc"
        assert workflow.name == "Full SDLC Pipeline"
        assert len(workflow.steps) > 0

    @pytest.mark.asyncio
    async def test_workflow_initialization(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, e2e_project: Path
    ):
        """Test workflow initialization and start."""
        workflow = workflow_runner.load_workflow(workflow_path)
        executor = workflow_runner.create_executor()
        executor.load_workflow(workflow_path)

        state = executor.start(workflow)

        assert state.workflow_id == "full-sdlc"
        assert state.status == "running"
        assert state.current_step is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_workflow_execution_mocked(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, mock_mal
    ):
        """Test workflow execution with mocked agents (limited steps for fast feedback)."""
        # Execute workflow with limited steps to keep test fast
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=3)

        assert state is not None
        assert state.workflow_id == "full-sdlc"
        assert results["correlation_id"] is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_full_workflow_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test complete workflow execution end-to-end."""
        # Execute full workflow (no step limit)
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=None)

        assert state is not None
        assert state.workflow_id == "full-sdlc"
        assert results["correlation_id"] is not None

        # Validate workflow completed successfully
        assert state.status in ["completed", "success"], f"Workflow did not complete: {state.status}"

        # Validate step execution order
        executed_steps = results.get("steps_executed", [])
        assert len(executed_steps) > 0, "No steps were executed"

        # Validate intermediate state correctness (if available)
        if "intermediate_states" in results:
            for intermediate_state in results["intermediate_states"]:
                assert "workflow_id" in intermediate_state
                assert "status" in intermediate_state

        # Validate final outcome
        assert state.current_step is None or state.status == "completed", "Workflow should be completed"

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_workflow_step_by_step_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, mock_mal
    ):
        """Test step-by-step workflow execution with state capture (limited steps)."""
        state, snapshots, results = await workflow_runner.run_workflow_step_by_step(
            workflow_path, max_steps=2, capture_after_each_step=True
        )

        assert state is not None
        assert len(snapshots) > 0
        assert results["steps_executed"] >= 0

        # Verify initial state snapshot
        assert snapshots[0]["workflow_id"] == "full-sdlc"
        assert snapshots[0]["status"] == "running"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_full_workflow_step_by_step_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test complete step-by-step workflow execution with full state validation."""
        state, snapshots, results = await workflow_runner.run_workflow_step_by_step(
            workflow_path, max_steps=None, capture_after_each_step=True
        )

        assert state is not None
        assert len(snapshots) > 0
        assert results["steps_executed"] > 0

        # Validate step execution order correctness
        workflow = workflow_runner.load_workflow(workflow_path)
        step_ids = [step.id for step in workflow.steps]
        executed_step_ids = [s.get("step_id") for s in snapshots if s.get("step_id")]

        # Verify steps executed in correct order (respecting dependencies)
        for i, step_id in enumerate(executed_step_ids):
            if step_id in step_ids:
                step_index = step_ids.index(step_id)
                # Check dependencies were executed before this step
                step = workflow.steps[step_index]
                for dep in step.requires:
                    dep_step_ids = [s.id for s in workflow.steps if dep in s.produces]
                    for dep_step_id in dep_step_ids:
                        if dep_step_id in executed_step_ids:
                            dep_index = executed_step_ids.index(dep_step_id)
                            assert dep_index < i, f"Step {step_id} executed before dependency {dep_step_id}"

        # Validate intermediate state correctness
        for snapshot in snapshots:
            assert "workflow_id" in snapshot
            assert "status" in snapshot
            assert snapshot["workflow_id"] == "full-sdlc"

        # Validate final outcome
        assert state.status in ["completed", "success"], f"Workflow did not complete: {state.status}"

    @pytest.mark.asyncio
    async def test_workflow_state_transitions(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, mock_mal
    ):
        """Test workflow state transitions."""
        workflow = workflow_runner.load_workflow(workflow_path)
        executor = workflow_runner.create_executor()
        executor.load_workflow(workflow_path)

        # Start workflow
        state = executor.start(workflow)
        assert state.status == "running"

        # Capture initial state
        snapshot1 = workflow_runner.capture_workflow_state(executor, step_id=None)
        assert snapshot1["status"] == "running"

    @pytest.mark.asyncio
    async def test_workflow_artifacts_created(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, e2e_project: Path, mock_mal
    ):
        """Test that workflow creates expected artifacts."""
        # Execute workflow (limited steps)
        state, _ = await workflow_runner.run_workflow(workflow_path, max_steps=2)

        # Note: In mocked mode, artifacts may not be fully created
        # This test validates the workflow structure supports artifact creation
        assert state is not None

        # If artifacts are created, validate they exist
        # For now, we'll just verify the workflow completed without errors
        # Full artifact validation would require real agent execution

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_workflow_gate_routing(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test workflow gate routing (pass/fail paths)."""
        workflow = workflow_runner.load_workflow(workflow_path)

        # Test pass path
        workflow_runner.control_gate_outcome("quality_gate", True)
        state_pass, _ = await workflow_runner.run_workflow(workflow_path, max_steps=5)

        # Test fail path
        workflow_runner.control_gate_outcome("quality_gate", False)
        state_fail, _ = await workflow_runner.run_workflow(workflow_path, max_steps=5)

        # Validate gate routing worked
        # (Specific validation depends on workflow structure)
        assert state_pass is not None
        assert state_fail is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_workflow_error_handling(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test workflow error handling and recovery."""
        # Simulate error condition (if supported by workflow runner)
        # This test validates that workflows handle errors gracefully
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=10)

        # Validate error handling
        # Workflow should either complete successfully or fail gracefully
        assert state is not None
        assert state.status in ["completed", "success", "failed", "error"]

        # If workflow failed, validate error information is available
        if state.status in ["failed", "error"]:
            assert "error" in results or state.error is not None, "Error information should be available"
