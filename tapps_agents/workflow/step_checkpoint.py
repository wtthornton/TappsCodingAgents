"""
Step Checkpoint Manager - Manages step-level checkpoints for workflow state persistence.

Enables resume capability by saving workflow progress after each step.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import logging

from .file_utils import atomic_write_json
from .models import Artifact

logger = logging.getLogger(__name__)


class CheckpointError(Exception):
    """Base exception for checkpoint operations."""

    pass


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint not found."""

    pass


class CheckpointValidationError(CheckpointError):
    """Checkpoint validation failed."""

    pass


@dataclass
class StepCheckpoint:
    """Step checkpoint data model."""

    workflow_id: str
    step_id: str
    step_number: int
    step_name: str
    completed_at: datetime
    step_output: dict[str, Any]
    artifacts: dict[str, Artifact]
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO format
        data["completed_at"] = self.completed_at.isoformat()
        # Convert artifacts to dict
        data["artifacts"] = {
            k: asdict(v) if hasattr(v, "__dict__") else v
            for k, v in self.artifacts.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepCheckpoint":
        """Create checkpoint from dictionary."""
        # Convert ISO datetime string back to datetime
        if isinstance(data.get("completed_at"), str):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        # Reconstruct artifacts
        artifacts = {}
        for k, v in data.get("artifacts", {}).items():
            if isinstance(v, dict):
                artifacts[k] = Artifact(**v)
            else:
                artifacts[k] = v
        data["artifacts"] = artifacts
        return cls(**data)

    def _calculate_checksum(self) -> str:
        """Calculate checksum for checkpoint data."""
        data = self.to_dict()
        # Remove checksum from calculation
        data.pop("checksum", None)
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def validate(self) -> bool:
        """Validate checkpoint integrity."""
        expected_checksum = self._calculate_checksum()
        return self.checksum == expected_checksum

    def update_checksum(self) -> None:
        """Update checksum for checkpoint."""
        self.checksum = self._calculate_checksum()


class StepCheckpointManager:
    """Manages step-level checkpoints for workflow state persistence."""

    def __init__(
        self,
        state_dir: Path,
        workflow_id: str,
        compression: bool = False,
    ):
        """
        Initialize checkpoint manager.

        Args:
            state_dir: Base directory for state storage
            workflow_id: Workflow identifier
            compression: Enable compression for checkpoint files (not implemented yet)
        """
        self.state_dir = Path(state_dir)
        self.workflow_id = workflow_id
        self.compression = compression
        self.checkpoint_dir = self.state_dir / workflow_id / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        step_id: str,
        step_number: int,
        step_output: dict[str, Any],
        artifacts: dict[str, Artifact],
        step_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Save checkpoint after step completion.

        Args:
            step_id: Step identifier (e.g., "step1", "enhance")
            step_number: Step number (1-based)
            step_output: Step execution output
            artifacts: Step artifacts
            step_name: Optional step name
            metadata: Optional metadata

        Returns:
            Path to saved checkpoint file

        Raises:
            CheckpointError: If checkpoint save fails
        """
        checkpoint = StepCheckpoint(
            workflow_id=self.workflow_id,
            step_id=step_id,
            step_number=step_number,
            step_name=step_name or step_id,
            completed_at=datetime.now(),
            step_output=step_output,
            artifacts=artifacts,
            metadata=metadata or {},
        )

        # Calculate and set checksum
        checkpoint.update_checksum()

        # Generate filename
        filename = f"step{step_number}-{step_id}.json"
        checkpoint_path = self.checkpoint_dir / filename

        try:
            # Atomic write
            atomic_write_json(checkpoint_path, checkpoint.to_dict(), indent=2)
            logger.debug(f"Saved checkpoint: {checkpoint_path}")
            return checkpoint_path
        except OSError as e:
            raise CheckpointError(
                f"Failed to save checkpoint to {checkpoint_path}: {e}"
            ) from e

    def load_checkpoint(
        self,
        step_id: str | None = None,
        step_number: int | None = None,
    ) -> StepCheckpoint:
        """
        Load checkpoint for step.

        Args:
            step_id: Step identifier (if None, load latest)
            step_number: Step number (if None, load latest)

        Returns:
            StepCheckpoint object

        Raises:
            CheckpointNotFoundError: If checkpoint not found
            CheckpointValidationError: If checkpoint is invalid
        """
        if step_id and step_number:
            filename = f"step{step_number}-{step_id}.json"
            checkpoint_path = self.checkpoint_dir / filename
        else:
            # Load latest checkpoint
            checkpoint = self.get_latest_checkpoint()
            if checkpoint is None:
                raise CheckpointNotFoundError(
                    f"No checkpoint found for workflow {self.workflow_id}"
                )
            return checkpoint

        if not checkpoint_path.exists():
            raise CheckpointNotFoundError(
                f"Checkpoint not found: {checkpoint_path}"
            )

        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)

            checkpoint = StepCheckpoint.from_dict(data)

            # Validate checkpoint
            if not checkpoint.validate():
                raise CheckpointValidationError(
                    f"Checkpoint validation failed: {checkpoint_path}"
                )

            return checkpoint
        except json.JSONDecodeError as e:
            raise CheckpointValidationError(
                f"Invalid checkpoint JSON: {checkpoint_path}: {e}"
            ) from e
        except Exception as e:
            raise CheckpointError(
                f"Failed to load checkpoint: {checkpoint_path}: {e}"
            ) from e

    def get_latest_checkpoint(self) -> StepCheckpoint | None:
        """
        Get latest checkpoint for workflow.

        Returns:
            Latest StepCheckpoint or None if no checkpoints exist
        """
        checkpoints = self.list_checkpoints()
        if not checkpoints:
            return None
        # Return checkpoint with highest step_number
        return max(checkpoints, key=lambda c: c.step_number)

    def list_checkpoints(self) -> list[StepCheckpoint]:
        """
        List all checkpoints for workflow.

        Returns:
            List of StepCheckpoint objects, sorted by step_number
        """
        checkpoints = []
        if not self.checkpoint_dir.exists():
            return checkpoints

        for checkpoint_file in sorted(self.checkpoint_dir.glob("step*.json")):
            try:
                with open(checkpoint_file, encoding="utf-8") as f:
                    data = json.load(f)
                checkpoint = StepCheckpoint.from_dict(data)
                if checkpoint.validate():
                    checkpoints.append(checkpoint)
            except Exception as e:
                logger.warning(
                    f"Failed to load checkpoint {checkpoint_file}: {e}",
                    exc_info=True,
                )

        return sorted(checkpoints, key=lambda c: c.step_number)

    def cleanup_old_checkpoints(
        self,
        retention_days: int = 30,
    ) -> int:
        """
        Clean up checkpoints older than retention period.

        Args:
            retention_days: Days to retain checkpoints

        Returns:
            Number of checkpoints deleted
        """
        if not self.checkpoint_dir.exists():
            return 0

        cutoff_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff_date = cutoff_date.replace(
            day=cutoff_date.day - retention_days
        )

        deleted_count = 0
        for checkpoint_file in self.checkpoint_dir.glob("step*.json"):
            try:
                with open(checkpoint_file, encoding="utf-8") as f:
                    data = json.load(f)
                completed_at = datetime.fromisoformat(data["completed_at"])

                if completed_at < cutoff_date:
                    checkpoint_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to process checkpoint {checkpoint_file}: {e}",
                    exc_info=True,
                )

        return deleted_count
