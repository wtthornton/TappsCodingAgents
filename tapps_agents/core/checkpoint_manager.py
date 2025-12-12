"""
Checkpoint Manager for Task State Persistence

Manages checkpoint creation, storage, and retrieval for task resumption.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .hardware_profiler import HardwareProfile, HardwareProfiler
from .task_state import TaskStateManager

logger = logging.getLogger(__name__)


@dataclass
class TaskCheckpoint:
    """Task checkpoint data structure."""

    task_id: str
    agent_id: str
    command: str
    state: str  # TaskState value as string
    progress: float  # 0.0 to 1.0
    checkpoint_time: datetime
    context: dict[str, Any] = field(
        default_factory=dict
    )  # Agent context, intermediate results
    artifacts: list[str] = field(default_factory=list)  # Generated files, outputs
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata
    checksum: str | None = None  # Integrity checksum

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["checkpoint_time"] = self.checkpoint_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskCheckpoint:
        """Create from dictionary."""
        data = data.copy()
        data["checkpoint_time"] = datetime.fromisoformat(data["checkpoint_time"])
        return cls(**data)

    def calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification."""
        # Create a stable representation for checksum
        checksum_data = {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "command": self.command,
            "state": self.state,
            "progress": self.progress,
            "checkpoint_time": self.checkpoint_time.isoformat(),
            "context": json.dumps(self.context, sort_keys=True),
            "artifacts": sorted(self.artifacts),
        }
        checksum_str = json.dumps(checksum_data, sort_keys=True)
        return hashlib.sha256(checksum_str.encode()).hexdigest()

    def validate(self) -> bool:
        """Validate checkpoint integrity."""
        if not self.checksum:
            return False
        calculated = self.calculate_checksum()
        return calculated == self.checksum


class CheckpointStorage:
    """Handles checkpoint storage with hardware-aware compression."""

    def __init__(
        self, storage_dir: Path, hardware_profile: HardwareProfile | None = None
    ):
        """
        Initialize checkpoint storage.

        Args:
            storage_dir: Directory to store checkpoints
            hardware_profile: Hardware profile for optimization
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Detect hardware profile if not provided
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.hardware_profile = hardware_profile
        self.compression_enabled = self._should_compress()

    def _should_compress(self) -> bool:
        """Determine if compression should be enabled based on hardware profile."""
        # NUC devices benefit from compression due to limited storage
        return self.hardware_profile == HardwareProfile.NUC

    def save(self, checkpoint: TaskCheckpoint) -> Path:
        """
        Save checkpoint to disk.

        Args:
            checkpoint: Checkpoint to save

        Returns:
            Path to saved checkpoint file
        """
        # Calculate checksum before saving
        checkpoint.checksum = checkpoint.calculate_checksum()

        # Create checkpoint file path
        checkpoint_file = self.storage_dir / f"checkpoint-{checkpoint.task_id}.json"
        if self.compression_enabled:
            checkpoint_file = checkpoint_file.with_suffix(".json.gz")

        # Serialize checkpoint
        data = checkpoint.to_dict()
        json_str = json.dumps(data, indent=2, default=str)

        # Write to file (with compression if enabled)
        try:
            if self.compression_enabled:
                with gzip.open(checkpoint_file, "wt", encoding="utf-8") as f:
                    f.write(json_str)
            else:
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    f.write(json_str)

            logger.info(
                f"Saved checkpoint for task {checkpoint.task_id} to {checkpoint_file}"
            )
            return checkpoint_file
        except Exception as e:
            logger.error(
                f"Failed to save checkpoint for task {checkpoint.task_id}: {e}"
            )
            raise

    def load(self, task_id: str) -> TaskCheckpoint | None:
        """
        Load checkpoint from disk.

        Args:
            task_id: Task identifier

        Returns:
            TaskCheckpoint if found, None otherwise
        """
        # Try compressed first, then uncompressed
        for ext in [".json.gz", ".json"]:
            checkpoint_file = self.storage_dir / f"checkpoint-{task_id}{ext}"
            if checkpoint_file.exists():
                try:
                    if ext == ".json.gz":
                        with gzip.open(checkpoint_file, "rt", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        with open(checkpoint_file, encoding="utf-8") as f:
                            data = json.load(f)

                    checkpoint = TaskCheckpoint.from_dict(data)

                    # Validate integrity
                    if not checkpoint.validate():
                        logger.warning(
                            f"Checkpoint integrity check failed for task {task_id}"
                        )
                        return None

                    logger.info(
                        f"Loaded checkpoint for task {task_id} from {checkpoint_file}"
                    )
                    return checkpoint
                except Exception as e:
                    logger.error(f"Failed to load checkpoint for task {task_id}: {e}")
                    continue

        return None

    def list_checkpoints(self) -> list[str]:
        """
        List all available checkpoint task IDs.

        Returns:
            List of task IDs with checkpoints
        """
        task_ids = set()

        # Find all checkpoint files
        for checkpoint_file in self.storage_dir.glob("checkpoint-*.json*"):
            # Extract task_id from filename
            name = checkpoint_file.stem  # Remove extension
            if name.startswith("checkpoint-"):
                task_id = name[len("checkpoint-") :]
                task_ids.add(task_id)

        return sorted(task_ids)

    def delete(self, task_id: str) -> bool:
        """
        Delete checkpoint for a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        deleted = False

        # Try both compressed and uncompressed
        for ext in [".json.gz", ".json"]:
            checkpoint_file = self.storage_dir / f"checkpoint-{task_id}{ext}"
            if checkpoint_file.exists():
                try:
                    checkpoint_file.unlink()
                    deleted = True
                    logger.info(f"Deleted checkpoint for task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to delete checkpoint for task {task_id}: {e}")

        return deleted


class CheckpointManager:
    """Manages task checkpoints with hardware-aware frequency."""

    def __init__(
        self,
        storage_dir: Path | None = None,
        hardware_profile: HardwareProfile | None = None,
        checkpoint_interval: int | None = None,
    ):
        """
        Initialize checkpoint manager.

        Args:
            storage_dir: Directory for checkpoint storage (default: .tapps-agents/checkpoints)
            hardware_profile: Hardware profile (auto-detected if None)
            checkpoint_interval: Checkpoint interval in seconds (auto-configured if None)
        """
        if storage_dir is None:
            storage_dir = Path(".tapps-agents/checkpoints")

        # Detect hardware profile if not provided
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.hardware_profile = hardware_profile
        self.storage = CheckpointStorage(storage_dir, hardware_profile)

        # Set checkpoint interval based on hardware profile
        if checkpoint_interval is None:
            checkpoint_interval = self._get_default_interval()

        self.checkpoint_interval = checkpoint_interval
        self.last_checkpoint_time: dict[str, float] = {}  # task_id -> timestamp

    def _get_default_interval(self) -> int:
        """Get default checkpoint interval based on hardware profile."""
        intervals = {
            HardwareProfile.NUC: 30,  # 30 seconds for NUC
            HardwareProfile.DEVELOPMENT: 60,  # 1 minute for development
            HardwareProfile.WORKSTATION: 120,  # 2 minutes for workstation
            HardwareProfile.SERVER: 60,  # 1 minute default for server
        }
        return intervals.get(self.hardware_profile, 60)

    def should_checkpoint(self, task_id: str) -> bool:
        """
        Check if checkpoint should be created for task.

        Args:
            task_id: Task identifier

        Returns:
            True if checkpoint should be created
        """
        import time

        current_time = time.time()
        last_time = self.last_checkpoint_time.get(task_id, 0)

        if current_time - last_time >= self.checkpoint_interval:
            return True

        return False

    def create_checkpoint(
        self,
        task_id: str,
        agent_id: str,
        command: str,
        state_manager: TaskStateManager,
        progress: float,
        context: dict[str, Any] | None = None,
        artifacts: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskCheckpoint:
        """
        Create and save a checkpoint.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            command: Command being executed
            state_manager: Task state manager
            progress: Progress (0.0 to 1.0)
            context: Agent context
            artifacts: List of artifact paths
            metadata: Additional metadata

        Returns:
            Created checkpoint
        """
        checkpoint = TaskCheckpoint(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            state=state_manager.current_state.value,
            progress=progress,
            checkpoint_time=datetime.utcnow(),
            context=context or {},
            artifacts=artifacts or [],
            metadata=metadata or {},
        )

        # Save checkpoint
        self.storage.save(checkpoint)

        # Update last checkpoint time
        import time

        self.last_checkpoint_time[task_id] = time.time()

        logger.info(
            f"Created checkpoint for task {task_id} "
            f"(progress: {progress:.1%}, state: {state_manager.current_state.value})"
        )

        return checkpoint

    def load_checkpoint(self, task_id: str) -> TaskCheckpoint | None:
        """
        Load checkpoint for a task.

        Args:
            task_id: Task identifier

        Returns:
            TaskCheckpoint if found, None otherwise
        """
        return self.storage.load(task_id)

    def list_checkpoints(self) -> list[str]:
        """
        List all available checkpoints.

        Returns:
            List of task IDs with checkpoints
        """
        return self.storage.list_checkpoints()

    def delete_checkpoint(self, task_id: str) -> bool:
        """
        Delete checkpoint for a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        return self.storage.delete(task_id)
