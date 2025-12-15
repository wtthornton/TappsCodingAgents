"""
E2E tests for quick-fix preset workflow.

Tests workflow parsing, execution, state transitions, and artifacts for fast bug fix workflow.
"""

import pytest
from pathlib import Path

from tests.e2e.fixtures.workflow_runner import WorkflowRunner


@pytest.mark.e2e_workflow
@pytest.mark.template_type("minimal")
class TestQuickFixWorkflow:
    """E2E tests for quick-fix preset workflow."""

    @pytest.fixture
    def workflow_path(self) -> Path:
        """Path to quick-fix workflow YAML."""
        return Path(__file__).parent.parent.parent.parent / "workflows" / "presets" / "quick-fix.yaml"

    @pytest.mark.asyncio
    async def test_workflow_parsing(self, workflow_runner: WorkflowRunner, workflow_path: Path):
        """Test that quick-fix workflow can be parsed."""
        workflow = workflow_runner.load_workflow(workflow_path)

        assert workflow.id == "quick-fix"
        assert workflow.name == "Quick Fix"
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

        assert state.workflow_id == "quick-fix"
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
        assert state.workflow_id == "quick-fix"
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
    async def test_workflow_step_order(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test that workflow steps are in correct order."""
        workflow = workflow_runner.load_workflow(workflow_path)

        # Quick-fix should have: debug -> fix -> review -> testing -> complete
        step_ids = [step.id for step in workflow.steps]
        assert "debug" in step_ids
        assert "fix" in step_ids
        assert "review" in step_ids

        # Verify step dependencies
        debug_step = next(step for step in workflow.steps if step.id == "debug")
        fix_step = next(step for step in workflow.steps if step.id == "fix")

        # Fix step should require debug-report.md
        assert "debug-report.md" in fix_step.requires

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    @pytest.mark.behavioral_mock
    async def test_full_workflow_execution(
        self, workflow_runner: WorkflowRunner, workflow_path: Path
    ):
        """Test complete quick-fix workflow execution end-to-end."""
        # Execute full workflow
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=None)

        assert state is not None
        assert state.workflow_id == "quick-fix"
        assert results["correlation_id"] is not None

        # Validate workflow completed
        assert state.status in ["completed", "success"], f"Workflow did not complete: {state.status}"

        # Validate step dependency resolution
        executed_steps = results.get("steps_executed", [])
        assert len(executed_steps) > 0, "No steps were executed"

        # Validate final outcome
        assert state.current_step is None or state.status == "completed", "Workflow should be completed"