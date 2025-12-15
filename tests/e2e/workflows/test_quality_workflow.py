"""
E2E tests for quality preset workflow.

Tests workflow parsing, execution, state transitions, gate routing, and artifacts.
"""

import pytest
from pathlib import Path

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

        assert state.workflow_id == "quality"
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
        assert state.workflow_id == "quality"
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
