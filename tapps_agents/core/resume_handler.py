"""
Resume Handler for Task Resumption

Handles resuming tasks from checkpoints with context restoration and validation.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .checkpoint_manager import CheckpointManager, TaskCheckpoint
from .task_state import TaskState, TaskStateManager

logger = logging.getLogger(__name__)


class ArtifactValidator:
    """Validates checkpoint artifacts exist and are accessible."""

    @staticmethod
    def validate_artifacts(
        artifacts: list[str], project_root: Path | None = None
    ) -> dict[str, bool]:
        """
        Validate that all artifacts exist.

        Args:
            artifacts: List of artifact paths
            project_root: Optional project root for relative paths

        Returns:
            Dictionary mapping artifact paths to existence status
        """
        validation_results = {}

        for artifact_path in artifacts:
            path = Path(artifact_path)

            # Handle relative paths
            if not path.is_absolute() and project_root:
                path = project_root / path

            validation_results[artifact_path] = path.exists()

            if not validation_results[artifact_path]:
                logger.warning(f"Artifact not found: {artifact_path}")

        return validation_results

    @staticmethod
    def all_artifacts_exist(
        artifacts: list[str], project_root: Path | None = None
    ) -> bool:
        """
        Check if all artifacts exist.

        Args:
            artifacts: List of artifact paths
            project_root: Optional project root for relative paths

        Returns:
            True if all artifacts exist
        """
        if not artifacts:
            return True

        validation_results = ArtifactValidator.validate_artifacts(
            artifacts, project_root
        )
        return all(validation_results.values())


class ContextRestorer:
    """Restores agent context from checkpoint."""

    @staticmethod
    def restore_context(checkpoint: TaskCheckpoint) -> dict[str, Any]:
        """
        Restore agent context from checkpoint.

        Args:
            checkpoint: Task checkpoint

        Returns:
            Restored context dictionary
        """
        context = checkpoint.context.copy()

        # Add checkpoint metadata to context
        context["_checkpoint_metadata"] = {
            "task_id": checkpoint.task_id,
            "agent_id": checkpoint.agent_id,
            "command": checkpoint.command,
            "checkpoint_time": checkpoint.checkpoint_time.isoformat(),
            "progress": checkpoint.progress,
        }

        return context


class ResumeHandler:
    """Handles task resumption from checkpoints."""

    def __init__(
        self,
        checkpoint_manager: CheckpointManager | None = None,
        project_root: Path | None = None,
    ):
        """
        Initialize resume handler.

        Args:
            checkpoint_manager: Checkpoint manager instance
            project_root: Project root directory for artifact validation
        """
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.project_root = project_root or Path.cwd()
        self.artifact_validator = ArtifactValidator()
        self.context_restorer = ContextRestorer()

    def can_resume(self, task_id: str) -> tuple[bool, str | None]:
        """
        Check if task can be resumed.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (can_resume, reason_if_not)
        """
        checkpoint = self.checkpoint_manager.load_checkpoint(task_id)

        if not checkpoint:
            return False, f"No checkpoint found for task {task_id}"

        # Validate checkpoint integrity
        if not checkpoint.validate():
            return False, f"Checkpoint integrity check failed for task {task_id}"

        # Check if state allows resumption
        try:
            state = TaskState(checkpoint.state)
        except ValueError:
            return False, f"Invalid state in checkpoint: {checkpoint.state}"

        if state not in {TaskState.PAUSED, TaskState.CHECKPOINTED, TaskState.FAILED}:
            return False, f"Task state {state.value} does not allow resumption"

        # Validate artifacts
        if not self.artifact_validator.all_artifacts_exist(
            checkpoint.artifacts, self.project_root
        ):
            missing = [
                artifact
                for artifact, exists in self.artifact_validator.validate_artifacts(
                    checkpoint.artifacts, self.project_root
                ).items()
                if not exists
            ]
            return False, f"Missing artifacts: {', '.join(missing)}"

        return True, None

    def prepare_resume(self, task_id: str) -> dict[str, Any]:
        """
        Prepare task resumption from checkpoint.

        Args:
            task_id: Task identifier

        Returns:
            Resume data dictionary with:
            - checkpoint: TaskCheckpoint
            - state_manager: TaskStateManager
            - context: Restored context
            - artifacts: Artifact validation results

        Raises:
            ValueError: If task cannot be resumed
        """
        can_resume, reason = self.can_resume(task_id)
        if not can_resume:
            raise ValueError(f"Cannot resume task {task_id}: {reason}")

        checkpoint = self.checkpoint_manager.load_checkpoint(task_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found for task {task_id}")

        # Restore state manager
        state_manager = TaskStateManager(task_id, TaskState(checkpoint.state))
        state_manager.transition(TaskState.RESUMED, "Resuming from checkpoint")
        state_manager.transition(TaskState.RUNNING, "Resumed execution")

        # Restore context
        context = self.context_restorer.restore_context(checkpoint)

        # Validate artifacts
        artifact_validation = self.artifact_validator.validate_artifacts(
            checkpoint.artifacts, self.project_root
        )

        logger.info(
            f"Prepared resume for task {task_id} "
            f"(progress: {checkpoint.progress:.1%}, artifacts: {len(checkpoint.artifacts)})"
        )

        return {
            "checkpoint": checkpoint,
            "state_manager": state_manager,
            "context": context,
            "artifacts": artifact_validation,
            "progress": checkpoint.progress,
            "agent_id": checkpoint.agent_id,
            "command": checkpoint.command,
        }

    def resume(
        self, task_id: str, agent_factory: Callable[..., Any], **agent_kwargs
    ) -> Any:
        """
        Resume task execution from checkpoint.

        Args:
            task_id: Task identifier
            agent_factory: Function to create agent instance
            **agent_kwargs: Additional arguments for agent factory

        Returns:
            Agent execution result

        Raises:
            ValueError: If task cannot be resumed
        """
        resume_data = self.prepare_resume(task_id)

        checkpoint = resume_data["checkpoint"]
        context = resume_data["context"]
        state_manager = resume_data["state_manager"]

        # Create agent with restored context
        agent = agent_factory(**agent_kwargs)

        # Restore agent context if agent has context attribute
        if hasattr(agent, "context"):
            agent.context.update(context)
        elif hasattr(agent, "_context"):
            agent._context.update(context)

        # Log resume information
        logger.info(
            f"Resuming task {task_id} from checkpoint "
            f"(progress: {checkpoint.progress:.1%}, "
            f"state: {state_manager.current_state.value})"
        )

        # Execute command with restored state
        # Note: The actual execution depends on the agent implementation
        # This is a generic resume handler - agents should implement
        # their own resume logic that uses the checkpoint data

        return {
            "agent": agent,
            "checkpoint": checkpoint,
            "state_manager": state_manager,
            "context": context,
            "resume_data": resume_data,
        }

    def list_resumable_tasks(self) -> list[dict[str, Any]]:
        """
        List all tasks that can be resumed.

        Returns:
            List of resumable task information dictionaries
        """
        resumable_tasks = []

        for task_id in self.checkpoint_manager.list_checkpoints():
            can_resume, reason = self.can_resume(task_id)
            if can_resume:
                checkpoint = self.checkpoint_manager.load_checkpoint(task_id)
                if checkpoint:
                    resumable_tasks.append(
                        {
                            "task_id": task_id,
                            "agent_id": checkpoint.agent_id,
                            "command": checkpoint.command,
                            "progress": checkpoint.progress,
                            "state": checkpoint.state,
                            "checkpoint_time": checkpoint.checkpoint_time.isoformat(),
                            "artifacts_count": len(checkpoint.artifacts),
                        }
                    )
            else:
                logger.debug(f"Task {task_id} cannot be resumed: {reason}")

        return resumable_tasks
