"""Workflow checkpoint and resume system.

Enables saving workflow state at any point and resuming in new sessions,
preventing token exhaustion and enabling long-running workflows.

@ai-prime-directive: Checkpoints must:
- Preserve complete workflow state
- Be resumable across sessions
- Include token budget tracking
- Support auto-checkpointing at thresholds
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WorkflowCheckpoint:
    """Workflow checkpoint for pause/resume.

    Attributes:
        checkpoint_id: Unique checkpoint identifier
        workflow_id: Parent workflow ID
        workflow_type: Workflow type (full-sdlc, standard, etc.)
        completed_steps: List of completed step names
        current_step: Current step name
        pending_steps: List of pending step names
        workflow_context: Workflow context dict
        step_results: Results from completed steps
        tokens_consumed: Tokens consumed so far
        tokens_remaining: Tokens remaining
        time_elapsed_minutes: Time elapsed in minutes
        created_at: Checkpoint creation timestamp
        checkpoint_reason: Reason for checkpoint
    """
    checkpoint_id: str
    workflow_id: str
    workflow_type: str
    completed_steps: list[str]
    current_step: str
    pending_steps: list[str]
    workflow_context: dict[str, Any]
    step_results: dict[str, Any]
    tokens_consumed: int
    tokens_remaining: int
    time_elapsed_minutes: float
    created_at: datetime
    checkpoint_reason: str

    def save(self, checkpoint_dir: Path) -> Path:
        """Save checkpoint to disk.

        Args:
            checkpoint_dir: Directory to save checkpoint

        Returns:
            Path to saved checkpoint file
        """
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / f"{self.checkpoint_id}.json"

        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()

        checkpoint_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Checkpoint saved: {checkpoint_path}")

        return checkpoint_path

    @classmethod
    def load(cls, checkpoint_path: Path) -> "WorkflowCheckpoint":
        """Load checkpoint from disk.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Loaded WorkflowCheckpoint instance
        """
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        data["created_at"] = datetime.fromisoformat(data["created_at"])

        logger.info(f"Checkpoint loaded: {checkpoint_path}")
        return cls(**data)

    def format_summary(self) -> str:
        """Format checkpoint summary for display."""
        return f"""
Checkpoint Summary
──────────────────
ID: {self.checkpoint_id}
Workflow: {self.workflow_type}
Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Reason: {self.checkpoint_reason}

Progress:
  Completed: {len(self.completed_steps)} steps
  Current: {self.current_step}
  Remaining: {len(self.pending_steps)} steps

Resources:
  Tokens consumed: {self.tokens_consumed:,}
  Tokens remaining: {self.tokens_remaining:,}
  Time elapsed: {self.time_elapsed_minutes:.1f} minutes
"""


class CheckpointManager:
    """Manage workflow checkpoints."""

    def __init__(self, checkpoint_dir: Path | None = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoints (default: .tapps-agents/checkpoints)
        """
        if checkpoint_dir is None:
            checkpoint_dir = Path(".tapps-agents/checkpoints")

        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        workflow_state: dict[str, Any],
        reason: str = "user_request"
    ) -> WorkflowCheckpoint:
        """Create checkpoint from workflow state.

        Args:
            workflow_state: Current workflow state
            reason: Reason for checkpoint creation

        Returns:
            Created WorkflowCheckpoint instance
        """
        checkpoint_id = f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        checkpoint = WorkflowCheckpoint(
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_state["workflow_id"],
            workflow_type=workflow_state["workflow_type"],
            completed_steps=workflow_state["completed_steps"],
            current_step=workflow_state["current_step"],
            pending_steps=workflow_state["pending_steps"],
            workflow_context=workflow_state["context"],
            step_results=workflow_state["results"],
            tokens_consumed=workflow_state.get("tokens_consumed", 0),
            tokens_remaining=workflow_state.get("tokens_remaining", 200000),
            time_elapsed_minutes=workflow_state.get("time_elapsed", 0.0),
            created_at=datetime.now(),
            checkpoint_reason=reason
        )

        path = checkpoint.save(self.checkpoint_dir)

        print(f"Checkpoint saved: {path}")
        print(f"Resume with: tapps-agents resume {checkpoint_id}")

        return checkpoint

    def resume_from_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        """Resume workflow from checkpoint.

        Args:
            checkpoint_id: Checkpoint to resume from

        Returns:
            Restored workflow state

        Raises:
            ValueError: If checkpoint not found
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        checkpoint = WorkflowCheckpoint.load(checkpoint_path)

        print(checkpoint.format_summary())
        print("\nResuming workflow...")

        return {
            "workflow_id": checkpoint.workflow_id,
            "workflow_type": checkpoint.workflow_type,
            "completed_steps": checkpoint.completed_steps,
            "current_step": checkpoint.current_step,
            "pending_steps": checkpoint.pending_steps,
            "context": checkpoint.workflow_context,
            "results": checkpoint.step_results,
            "tokens_consumed": checkpoint.tokens_consumed,
            "tokens_remaining": checkpoint.tokens_remaining,
            "time_elapsed": checkpoint.time_elapsed_minutes,
            "resumed_from_checkpoint": True,
            "checkpoint_id": checkpoint.checkpoint_id
        }

    def list_checkpoints(self) -> list[WorkflowCheckpoint]:
        """List all available checkpoints.

        Returns:
            List of WorkflowCheckpoint instances, sorted by creation time
        """
        checkpoints = []
        for path in self.checkpoint_dir.glob("*.json"):
            try:
                checkpoint = WorkflowCheckpoint.load(path)
                checkpoints.append(checkpoint)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint {path}: {e}")

        return sorted(checkpoints, key=lambda c: c.created_at, reverse=True)

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint to delete

        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info(f"Checkpoint deleted: {checkpoint_id}")
            return True

        return False


def create_checkpoint(
    workflow_state: dict[str, Any],
    reason: str = "user_request",
    checkpoint_dir: Path | None = None
) -> WorkflowCheckpoint:
    """Convenience function to create checkpoint.

    Args:
        workflow_state: Workflow state
        reason: Checkpoint reason
        checkpoint_dir: Optional checkpoint directory

    Returns:
        Created checkpoint
    """
    manager = CheckpointManager(checkpoint_dir)
    return manager.create_checkpoint(workflow_state, reason)
