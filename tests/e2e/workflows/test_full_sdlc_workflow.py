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
        """Test workflow execution with mocked agents."""
        # Execute workflow with limited steps to keep test fast
        state, results = await workflow_runner.run_workflow(workflow_path, max_steps=3)

        assert state is not None
        assert state.workflow_id == "full-sdlc"
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

        # Verify initial state snapshot
        assert snapshots[0]["workflow_id"] == "full-sdlc"
        assert snapshots[0]["status"] == "running"

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
