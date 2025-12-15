"""
Workflow runner E2E harness for executing workflows in tests.

Provides:
- Workflow execution utilities (run_workflow, run_workflow_step_by_step)
- State snapshot capture
- Artifact assertions
- Controlled gate outcomes
- Integration with E2E foundation
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.models import Workflow, WorkflowState
from tapps_agents.workflow.parser import WorkflowParser

from .e2e_harness import capture_artifacts, generate_correlation_id
from .project_templates import TemplateType, create_template

# Configure logging for workflow runner
logger = logging.getLogger(__name__)


class GateController:
    """Controller for deterministic gate outcomes in tests."""

    def __init__(self):
        """Initialize gate controller with empty outcome map."""
        self._outcomes: Dict[str, bool] = {}  # gate_id -> pass (True) or fail (False)

    def set_outcome(self, gate_id: str, outcome: bool) -> None:
        """
        Set the outcome for a specific gate.

        Args:
            gate_id: ID of the gate to control
            outcome: True for pass, False for fail
        """
        self._outcomes[gate_id] = outcome
        logger.debug(f"Gate controller: Set {gate_id} = {'pass' if outcome else 'fail'}")

    def get_outcome(self, gate_id: str, default: bool = True) -> bool:
        """
        Get the outcome for a specific gate.

        Args:
            gate_id: ID of the gate to check
            default: Default outcome if gate not controlled

        Returns:
            True for pass, False for fail
        """
        return self._outcomes.get(gate_id, default)

    def clear(self) -> None:
        """Clear all gate outcomes."""
        self._outcomes.clear()


class WorkflowRunner:
    """Workflow runner for E2E tests."""

    def __init__(
        self,
        project_path: Path,
        use_mocks: bool = True,
        gate_controller: Optional[GateController] = None,
    ):
        """
        Initialize workflow runner.

        Args:
            project_path: Path to the test project
            use_mocks: Whether to use mocked agents (default: True)
            gate_controller: Optional gate controller for deterministic gate outcomes
        """
        self.project_path = project_path
        self.use_mocks = use_mocks
        self.gate_controller = gate_controller or GateController()
        self.executor: Optional[WorkflowExecutor] = None
        self.workflow: Optional[Workflow] = None
        self.state_snapshots: List[Dict[str, Any]] = []
        self.correlation_id = generate_correlation_id()

    def load_workflow(self, workflow_path: Path) -> Workflow:
        """
        Load a workflow from YAML file.

        Args:
            workflow_path: Path to workflow YAML file

        Returns:
            Parsed Workflow object
        """
        parser = WorkflowParser()
        self.workflow = parser.parse_file(workflow_path)
        logger.info(f"Loaded workflow: {self.workflow.id} ({self.workflow.name})")
        return self.workflow

    def create_executor(self, expert_registry: Any = None) -> WorkflowExecutor:
        """
        Create a workflow executor for the test project.

        Args:
            expert_registry: Optional expert registry for expert consultation

        Returns:
            WorkflowExecutor instance
        """
        self.executor = WorkflowExecutor(
            project_root=self.project_path,
            expert_registry=expert_registry,
            auto_detect=False,
            advanced_state=True,
            auto_mode=True,  # No prompts in tests
        )
        return self.executor

    async def run_workflow(
        self,
        workflow_path: Path,
        expert_registry: Any = None,
        max_steps: int = 50,
        **kwargs: Any,
    ) -> Tuple[WorkflowState, Dict[str, Any]]:
        """
        Run a workflow to completion.

        Args:
            workflow_path: Path to workflow YAML file
            expert_registry: Optional expert registry
            max_steps: Maximum number of steps to execute
            **kwargs: Additional arguments for executor

        Returns:
            Tuple of (final workflow state, execution results)
        """
        # Load workflow
        workflow = self.load_workflow(workflow_path)

        # Create executor
        executor = self.create_executor(expert_registry)

        # Load workflow into executor
        executor.load_workflow(workflow_path)

        # Start workflow
        state = executor.start(workflow)

        # Capture initial state
        self.capture_workflow_state(executor, step_id=None)

        # Execute workflow to completion
        final_state = await executor.execute(workflow=workflow, max_steps=max_steps, **kwargs)

        # Capture final state
        self.capture_workflow_state(executor, step_id=None)

        results = {
            "workflow_id": final_state.workflow_id,
            "status": final_state.status,
            "correlation_id": self.correlation_id,
            "steps_completed": len([e for e in final_state.executions if e.status == "completed"]),
        }

        return final_state, results

    async def run_workflow_step_by_step(
        self,
        workflow_path: Path,
        expert_registry: Any = None,
        max_steps: Optional[int] = None,
        capture_after_each_step: bool = True,
        **kwargs: Any,
    ) -> Tuple[WorkflowState, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run a workflow step-by-step with state capture.

        Args:
            workflow_path: Path to workflow YAML file
            expert_registry: Optional expert registry
            max_steps: Maximum number of steps to execute (None = all)
            capture_after_each_step: Whether to capture state after each step
            **kwargs: Additional arguments for executor

        Returns:
            Tuple of (final workflow state, state snapshots, execution results)
        """
        # Load workflow
        workflow = self.load_workflow(workflow_path)

        # Create executor
        executor = self.create_executor(expert_registry)

        # Load workflow into executor
        executor.load_workflow(workflow_path)

        # Start workflow
        state = executor.start(workflow)

        # Capture initial state
        self.capture_workflow_state(executor, step_id=None)

        # Track previous completed steps to detect step transitions
        previous_completed = set()

        # Execute workflow with step-level monitoring
        # NOTE: The executor.execute() runs all steps to completion in a loop.
        # State is saved after each batch of steps, but we capture snapshots
        # after execution completes. For true step-by-step capture, we would
        # need to implement a custom execution loop or use executor callbacks.
        # For now, we capture the final state which includes all step executions.
        max_execution_steps = max_steps or 50
        final_state = await executor.execute(workflow=workflow, max_steps=max_execution_steps, **kwargs)

        # Capture state after execution
        # The final_state contains all step executions, so we can capture
        # snapshots for each completed step from the final state
        if capture_after_each_step:
            # Capture state for each completed step
            for execution in final_state.executions:
                if execution.status == "completed" and execution.step_id not in previous_completed:
                    self.capture_workflow_state(executor, step_id=execution.step_id)
                    previous_completed.add(execution.step_id)

        # Capture final state
        self.capture_workflow_state(executor, step_id=None)

        results = {
            "workflow_id": final_state.workflow_id,
            "status": final_state.status,
            "steps_executed": len([e for e in final_state.executions if e.status in ["completed", "failed"]]),
            "correlation_id": self.correlation_id,
        }

        return final_state, self.state_snapshots, results

    def capture_workflow_state(
        self, executor: WorkflowExecutor, step_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Capture a workflow state snapshot.

        Args:
            executor: WorkflowExecutor instance
            step_id: Optional step ID for step-specific capture

        Returns:
            State snapshot dictionary
        """
        if not executor.state:
            return {}

        snapshot = {
            "timestamp": executor.state.started_at.isoformat() if executor.state.started_at else None,
            "workflow_id": executor.state.workflow_id,
            "status": executor.state.status,
            "current_step": executor.state.current_step,
            "step_id": step_id,
            "completed_steps": [
                exec.step_id for exec in executor.state.executions if exec.status == "completed"
            ],
            "failed_steps": [
                exec.step_id for exec in executor.state.executions if exec.status == "failed"
            ],
            "artifacts": [
                {
                    "name": art.name,
                    "path": art.path,
                    "status": art.status,
                }
                for art in executor.state.artifacts
            ],
            "variables": dict(executor.state.variables) if executor.state.variables else {},
        }

        self.state_snapshots.append(snapshot)
        logger.debug(f"Captured state snapshot: step={step_id}, status={executor.state.status}")

        return snapshot

    def assert_workflow_artifacts(
        self, expected_artifacts: List[str], project_path: Optional[Path] = None
    ) -> None:
        """
        Assert that expected workflow artifacts exist.

        Args:
            expected_artifacts: List of artifact paths (relative to project root) or artifact names
            project_path: Optional project path (defaults to self.project_path)

        Raises:
            AssertionError: If any expected artifact is missing
        """
        project = project_path or self.project_path

        missing_artifacts = []
        for artifact_spec in expected_artifacts:
            # Try as path first
            artifact_path = project / artifact_spec
            if not artifact_path.exists():
                # Try in .tapps-agents directory
                artifact_path = project / ".tapps-agents" / artifact_spec
                if not artifact_path.exists():
                    # Try as artifact name in state
                    if self.executor and self.executor.state:
                        found_artifact = None
                        for art in self.executor.state.artifacts.values():
                            if art.name == artifact_spec or art.path == artifact_spec:
                                found_artifact = art
                                break
                        
                        if found_artifact:
                            # Artifact found in state - validate file exists at path
                            if found_artifact.path:
                                artifact_file_path = Path(found_artifact.path)
                                if not artifact_file_path.is_absolute():
                                    artifact_file_path = project / artifact_file_path
                                if artifact_file_path.exists():
                                    self._validate_artifact_content(artifact_file_path)
                                else:
                                    # Artifact in state but file doesn't exist
                                    missing_artifacts.append(f"{artifact_spec} (file not found at {found_artifact.path})")
                            else:
                                # Artifact in state but no path - consider it missing
                                missing_artifacts.append(f"{artifact_spec} (no path in state)")
                        else:
                            missing_artifacts.append(artifact_spec)
                    else:
                        missing_artifacts.append(artifact_spec)
                else:
                    # Validate minimal content
                    self._validate_artifact_content(artifact_path)
            else:
                # Validate minimal content
                self._validate_artifact_content(artifact_path)

        if missing_artifacts:
            raise AssertionError(
                f"Missing expected artifacts: {', '.join(missing_artifacts)}"
            )

    def _validate_artifact_content(self, artifact_path: Path) -> None:
        """
        Validate minimal content of an artifact file.

        Args:
            artifact_path: Path to artifact file

        Raises:
            AssertionError: If artifact is empty or invalid
        """
        if not artifact_path.exists():
            raise AssertionError(f"Artifact does not exist: {artifact_path}")

        if artifact_path.is_file():
            # Check file is not empty
            if artifact_path.stat().st_size == 0:
                raise AssertionError(f"Artifact is empty: {artifact_path}")

            # If JSON, validate structure
            if artifact_path.suffix == ".json":
                try:
                    with open(artifact_path, "r", encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    raise AssertionError(f"Artifact is not valid JSON: {artifact_path} - {e}")

    def control_gate_outcome(self, gate_id: str, outcome: bool) -> None:
        """
        Control the outcome of a gate for deterministic testing.

        NOTE: This method sets the gate outcome in the controller, but actual
        gate control during workflow execution requires mocking the review agent's
        response to include the desired gate outcome. The executor evaluates gates
        based on review results, not directly from the controller.

        To use gate control in tests:
        1. Set the gate outcome using this method
        2. Mock the review agent to return a result with `passed: True/False`
           matching the desired outcome
        3. The executor will use the mocked result for gate evaluation

        Args:
            gate_id: ID of the gate to control
            outcome: True for pass, False for fail
        """
        self.gate_controller.set_outcome(gate_id, outcome)


# Convenience functions for direct use in tests


async def run_workflow(
    workflow_path: Path,
    project_path: Path,
    use_mocks: bool = True,
    expert_registry: Any = None,
    max_steps: int = 50,
    **kwargs: Any,
) -> Tuple[WorkflowState, Dict[str, Any]]:
    """
    Run a workflow to completion.

    Args:
        workflow_path: Path to workflow YAML file
        project_path: Path to test project
        use_mocks: Whether to use mocked agents
        expert_registry: Optional expert registry
        max_steps: Maximum number of steps to execute
        **kwargs: Additional arguments

    Returns:
        Tuple of (final workflow state, execution results)
    """
    runner = WorkflowRunner(project_path, use_mocks=use_mocks)
    return await runner.run_workflow(workflow_path, expert_registry=expert_registry, max_steps=max_steps, **kwargs)


async def run_workflow_step_by_step(
    workflow_path: Path,
    project_path: Path,
    use_mocks: bool = True,
    expert_registry: Any = None,
    max_steps: Optional[int] = None,
    capture_after_each_step: bool = True,
    **kwargs: Any,
) -> Tuple[WorkflowState, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run a workflow step-by-step with state capture.

    Args:
        workflow_path: Path to workflow YAML file
        project_path: Path to test project
        use_mocks: Whether to use mocked agents
        expert_registry: Optional expert registry
        max_steps: Maximum number of steps to execute
        capture_after_each_step: Whether to capture state after each step
        **kwargs: Additional arguments

    Returns:
        Tuple of (final workflow state, state snapshots, execution results)
    """
    runner = WorkflowRunner(project_path, use_mocks=use_mocks)
    return await runner.run_workflow_step_by_step(
        workflow_path,
        expert_registry=expert_registry,
        max_steps=max_steps,
        capture_after_each_step=capture_after_each_step,
        **kwargs,
    )


def capture_workflow_state(
    executor: WorkflowExecutor, step_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capture a workflow state snapshot.

    Args:
        executor: WorkflowExecutor instance
        step_id: Optional step ID

    Returns:
        State snapshot dictionary
    """
    runner = WorkflowRunner(executor.project_root)
    return runner.capture_workflow_state(executor, step_id=step_id)


def assert_workflow_artifacts(
    project_path: Path, expected_artifacts: List[str], executor: Optional[WorkflowExecutor] = None
) -> None:
    """
    Assert that expected workflow artifacts exist.

    Args:
        project_path: Path to test project
        expected_artifacts: List of expected artifact paths/names
        executor: Optional executor for artifact state lookup
    """
    runner = WorkflowRunner(project_path)
    if executor:
        runner.executor = executor
    runner.assert_workflow_artifacts(expected_artifacts, project_path)


def control_gate_outcome(gate_id: str, outcome: bool, gate_controller: Optional[GateController] = None) -> GateController:
    """
    Control the outcome of a gate.

    Args:
        gate_id: ID of the gate to control
        outcome: True for pass, False for fail
        gate_controller: Optional existing gate controller

    Returns:
        GateController instance
    """
    controller = gate_controller or GateController()
    controller.set_outcome(gate_id, outcome)
    return controller
