"""
Resume Orchestrator - Resumes failed or paused workflows from checkpoints.

Enables workflow recovery by loading saved state and continuing execution.
"""

import logging
from typing import Any

from tapps_agents.workflow.models import WorkflowState
from tapps_agents.workflow.step_checkpoint import (
    CheckpointNotFoundError,
    CheckpointValidationError,
    StepCheckpointManager,
)

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator

logger = logging.getLogger(__name__)


class WorkflowNotFoundError(Exception):
    """Workflow not found."""

    pass


class ResumeOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for resuming failed workflows."""

    async def execute(
        self,
        intent: Intent,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Resume workflow from checkpoint.

        Args:
            intent: Parsed user intent (should contain workflow_id)
            parameters: Additional parameters

        Returns:
            Dictionary with execution results

        Raises:
            WorkflowNotFoundError: If workflow_id not found
            CheckpointValidationError: If checkpoint is invalid
        """
        parameters = parameters or {}
        workflow_id = parameters.get("workflow_id") or intent.original_input

        if not workflow_id:
            raise ValueError("workflow_id is required for resume operation")

        # Initialize checkpoint manager
        state_dir = self.project_root / ".tapps-agents" / "workflow-state"
        checkpoint_manager = StepCheckpointManager(
            state_dir=state_dir,
            workflow_id=workflow_id,
        )

        # Load latest checkpoint
        try:
            latest_checkpoint = checkpoint_manager.get_latest_checkpoint()
            if latest_checkpoint is None:
                raise WorkflowNotFoundError(
                    f"No checkpoints found for workflow: {workflow_id}"
                )

            logger.info(
                f"Resuming workflow {workflow_id} from step {latest_checkpoint.step_number}"
            )

            # Validate checkpoint
            if not latest_checkpoint.validate():
                raise CheckpointValidationError(
                    f"Checkpoint validation failed for workflow: {workflow_id}"
                )

            # Determine resume point (next step after last completed)
            resume_step = latest_checkpoint.step_number + 1
            completed_steps = list(range(1, latest_checkpoint.step_number + 1))

            return {
                "type": "resume",
                "success": True,
                "workflow_id": workflow_id,
                "resume_step": resume_step,
                "completed_steps": completed_steps,
                "checkpoint": {
                    "step_id": latest_checkpoint.step_id,
                    "step_number": latest_checkpoint.step_number,
                    "step_name": latest_checkpoint.step_name,
                    "completed_at": latest_checkpoint.completed_at.isoformat(),
                },
                "message": f"Ready to resume from step {resume_step}",
            }

        except CheckpointNotFoundError as e:
            raise WorkflowNotFoundError(
                f"Workflow not found: {workflow_id}. {e!s}"
            ) from e

    def list_available_workflows(self) -> list[dict[str, Any]]:
        """
        List available workflows that can be resumed.

        Returns:
            List of workflow metadata dictionaries with:
            - workflow_id: str
            - last_step: str
            - last_step_number: int
            - completed_at: str (ISO format)
            - can_resume: bool
        """
        state_dir = self.project_root / ".tapps-agents" / "workflow-state"
        workflows = []

        if not state_dir.exists():
            return workflows

        # Find all workflow directories
        for workflow_dir in state_dir.iterdir():
            if not workflow_dir.is_dir():
                continue

            workflow_id = workflow_dir.name
            checkpoint_dir = workflow_dir / "checkpoints"

            if not checkpoint_dir.exists():
                continue

            try:
                checkpoint_manager = StepCheckpointManager(
                    state_dir=state_dir,
                    workflow_id=workflow_id,
                )
                latest_checkpoint = checkpoint_manager.get_latest_checkpoint()

                if latest_checkpoint:
                    workflows.append(
                        {
                            "workflow_id": workflow_id,
                            "last_step": latest_checkpoint.step_id,
                            "last_step_number": latest_checkpoint.step_number,
                            "completed_at": latest_checkpoint.completed_at.isoformat(),
                            "can_resume": True,
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to load checkpoint for workflow {workflow_id}: {e}",
                    exc_info=True,
                )
                continue

        return sorted(workflows, key=lambda w: w["completed_at"], reverse=True)

    def load_workflow_state(
        self,
        workflow_id: str,
    ) -> tuple[WorkflowState, Any]:
        """
        Load workflow state and latest checkpoint.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Tuple of (WorkflowState, latest StepCheckpoint)

        Raises:
            WorkflowNotFoundError: If workflow not found
            CheckpointValidationError: If checkpoint invalid
        """
        state_dir = self.project_root / ".tapps-agents" / "workflow-state"
        checkpoint_manager = StepCheckpointManager(
            state_dir=state_dir,
            workflow_id=workflow_id,
        )

        latest_checkpoint = checkpoint_manager.get_latest_checkpoint()
        if latest_checkpoint is None:
            raise WorkflowNotFoundError(
                f"No checkpoints found for workflow: {workflow_id}"
            )

        if not latest_checkpoint.validate():
            raise CheckpointValidationError(
                f"Checkpoint validation failed for workflow: {workflow_id}"
            )

        # Create WorkflowState from checkpoint
        # Note: This is a simplified version - full implementation would
        # load complete state from state files

        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            started_at=latest_checkpoint.completed_at,  # Approximate
            current_step=latest_checkpoint.step_id,
            completed_steps=[f"step{i}" for i in range(1, latest_checkpoint.step_number + 1)],
            artifacts=latest_checkpoint.artifacts,
            variables=latest_checkpoint.metadata,
            status="paused",
        )

        return workflow_state, latest_checkpoint
