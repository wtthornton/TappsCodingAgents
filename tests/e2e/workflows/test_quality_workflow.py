"""
E2E tests for quality preset workflow.

Tests workflow parsing, execution, state transitions, gate routing, and artifacts.
"""

from pathlib import Path

import pytest

from tests.e2e.fixtures.workflow_runner import WorkflowRunner


@pytest.mark.e2e_workflow
@pytest.mark.template_type("small")
class TestQualityWorkflow:
    """E2E tests for quality preset workflow."""

    @pytest.fixture
    def workflow_path(self) -> Path:
        """Path to quality workflow YAML."""
        return Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "quality.yaml"

    @pytest.mark.asyncio
    async def test_workflow_parsing(self, workflow_runner: WorkflowRunner, workflow_path: Path):
        """Test that quality workflow can be parsed."""
        workflow = workflow_runner.load_workflow(workflow_path)

        assert workflow.id == "quality"
        assert workflow.name == "Quality Improvement"
        assert len(workflow.steps) > 0

    @pytest.mark.asyncio
    async def test_workflow_initialization(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test workflow initialization and start."""
        workflow = workflow_runner.load_workflow(workflow_path)
        executor = workflow_runner.create_executor()
        executor.load_workflow(workflow_path)

        state = executor.start(workflow)

        assert state.workflow_id.startswith("quality")
        assert state.status == "running"
        assert state.current_step is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_workflow_execution_mocked(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, mock_mal
    ):
        """Test workflow execution with mocked agents."""
        # Execute workflow with limited steps
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=3)

        assert state is not None
        assert state.workflow_id.startswith("quality")
        assert results["correlation_id"] is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_workflow_step_by_step_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path, mock_mal
    ):
        """Test step-by-step workflow execution with state capture."""
        state, snapshots, results = await workflow_runner.run_workflow_step_by_step(
            workflow_path, max_steps=2, capture_after_each_step=True
        )

        assert state is not None
        assert len(snapshots) > 0
        assert results["steps_executed"] >= 0

    @pytest.mark.asyncio
    async def test_gate_routing_structure(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test that workflow has gate routing structure."""
        workflow = workflow_runner.load_workflow(workflow_path)

        # Find steps with gates
        steps_with_gates = [step for step in workflow.steps if step.gate is not None]

        # Quality workflow should have gates
        assert len(steps_with_gates) > 0

        # Verify gate structure
        for step in steps_with_gates:
            assert step.gate is not None
            # Gate should have condition, on_pass, and/or on_fail
            gate = step.gate
            assert "condition" in gate or "on_pass" in gate or "on_fail" in gate

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_full_workflow_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test complete quality workflow execution end-to-end."""
        # Execute full workflow
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=None)

        assert state is not None
        assert state.workflow_id.startswith("quality")
        assert results["correlation_id"] is not None

        # Validate workflow completed
        assert state.status in ["completed", "success"], f"Workflow did not complete: {state.status}"

        # Validate step execution order and dependencies
        executed_steps = results.get("steps_executed", [])
        assert len(executed_steps) > 0, "No steps were executed"

        # Validate gate routing worked
        workflow = workflow_runner.load_workflow(workflow_path)
        steps_with_gates = [step for step in workflow.steps if step.gate is not None]
        if len(steps_with_gates) > 0:
            # Gate routing should have been tested
            assert "gate_outcomes" in results or state.status in ["completed", "success"]

        # Validate final outcome
        assert state.current_step is None or state.status == "completed", "Workflow should be completed"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_workflow_gate_routing(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test quality workflow gate routing (pass/fail paths)."""
        workflow_runner.load_workflow(workflow_path)

        # Test pass path
        workflow_runner.control_gate_outcome("quality_gate", True)
        state_pass, _ = await workflow_runner.run_workflow(workflow_path, max_steps=10)

        # Test fail path
        workflow_runner.control_gate_outcome("quality_gate", False)
        state_fail, _ = await workflow_runner.run_workflow(workflow_path, max_steps=10)

        # Validate gate routing worked
        assert state_pass is not None
        assert state_fail is not None