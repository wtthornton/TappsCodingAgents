"""
Long-Duration Support for 30+ Hour Operations

Provides durability guarantees, failure recovery, and progress tracking for
long-running tasks.
"""

from __future__ import annotations

import json
import logging
import shutil
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .checkpoint_manager import CheckpointManager, TaskCheckpoint
from .hardware_profiler import HardwareProfile, HardwareProfiler
from .resource_aware_executor import ResourceAwareExecutor
from .session_manager import AgentSession, SessionManager
from .task_state import TaskState, TaskStateManager

logger = logging.getLogger(__name__)


class DurabilityLevel(Enum):
    """Durability guarantee level."""

    BASIC = "basic"  # Checkpoints every 10 minutes
    STANDARD = "standard"  # Checkpoints every 5 minutes
    HIGH = "high"  # Checkpoints every 2 minutes + artifact backup


@dataclass
class ProgressSnapshot:
    """Snapshot of task progress at a point in time."""

    timestamp: datetime
    progress: float  # 0.0 to 1.0
    current_step: str
    steps_completed: int
    total_steps: int
    estimated_remaining_hours: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProgressSnapshot:
        """Create from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class FailureRecord:
    """Record of a failure event."""

    timestamp: datetime
    failure_type: str  # "crash", "timeout", "resource_exhaustion", "error"
    error_message: str
    stack_trace: str | None = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    checkpoint_available: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FailureRecord:
        """Create from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ProgressTracker:
    """Tracks progress over long periods."""

    def __init__(self, storage_dir: Path | None = None):
        """
        Initialize progress tracker.

        Args:
            storage_dir: Directory to store progress snapshots
        """
        self.storage_dir = (
            Path(storage_dir) if storage_dir else Path(".tapps-agents/progress")
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.snapshots: list[ProgressSnapshot] = []
        self.max_snapshots = 1000  # Keep last 1000 snapshots

    def record_progress(
        self,
        progress: float,
        current_step: str,
        steps_completed: int,
        total_steps: int,
        estimated_remaining_hours: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProgressSnapshot:
        """
        Record a progress snapshot.

        Args:
            progress: Progress percentage (0.0 to 1.0)
            current_step: Current step description
            steps_completed: Number of steps completed
            total_steps: Total number of steps
            estimated_remaining_hours: Estimated hours remaining
            metadata: Additional metadata

        Returns:
            ProgressSnapshot instance
        """
        snapshot = ProgressSnapshot(
            timestamp=datetime.now(UTC),
            progress=progress,
            current_step=current_step,
            steps_completed=steps_completed,
            total_steps=total_steps,
            estimated_remaining_hours=estimated_remaining_hours,
            metadata=metadata or {},
        )

        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots :]

        # Persist to disk
        self._save_snapshot(snapshot)

        return snapshot

    def _save_snapshot(self, snapshot: ProgressSnapshot):
        """Save snapshot to disk."""
        snapshot_file = (
            self.storage_dir
            / f"snapshot_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(snapshot_file, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

    def get_latest_progress(self) -> ProgressSnapshot | None:
        """Get the latest progress snapshot."""
        return self.snapshots[-1] if self.snapshots else None

    def get_progress_history(
        self, hours: float | None = None
    ) -> list[ProgressSnapshot]:
        """
        Get progress history.

        Args:
            hours: Optional limit to last N hours

        Returns:
            List of progress snapshots
        """
        if not hours:
            return self.snapshots.copy()

        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return [s for s in self.snapshots if s.timestamp >= cutoff]

    def calculate_velocity(self) -> float | None:
        """
        Calculate progress velocity (progress per hour).

        Returns:
            Progress velocity or None if insufficient data
        """
        if len(self.snapshots) < 2:
            return None

        first = self.snapshots[0]
        last = self.snapshots[-1]

        time_delta = (last.timestamp - first.timestamp).total_seconds() / 3600.0
        if time_delta == 0:
            return None

        progress_delta = last.progress - first.progress
        return progress_delta / time_delta


class DurabilityGuarantee:
    """Ensures task durability through frequent checkpoints and state persistence."""

    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        durability_level: DurabilityLevel = DurabilityLevel.STANDARD,
        hardware_profile: HardwareProfile | None = None,
    ):
        """
        Initialize durability guarantee.

        Args:
            checkpoint_manager: Checkpoint manager instance
            durability_level: Durability level
            hardware_profile: Hardware profile for optimization
        """
        self.checkpoint_manager = checkpoint_manager
        self.durability_level = durability_level
        self.hardware_profile = hardware_profile or HardwareProfiler().detect_profile()

        # Set checkpoint interval based on durability level and hardware
        self.checkpoint_interval = self._get_checkpoint_interval()

        self.last_checkpoint_time: datetime | None = None
        self.checkpoint_count = 0

    def _get_checkpoint_interval(self) -> float:
        """Get checkpoint interval in seconds based on durability level and hardware."""
        # Base intervals by durability level
        base_intervals = {
            DurabilityLevel.BASIC: 600.0,  # 10 minutes
            DurabilityLevel.STANDARD: 300.0,  # 5 minutes
            DurabilityLevel.HIGH: 120.0,  # 2 minutes
        }

        base_interval = base_intervals[self.durability_level]

        # Adjust for hardware profile
        if self.hardware_profile == HardwareProfile.NUC:
            # NUC: More frequent checkpoints due to resource constraints
            return base_interval * 0.8
        elif self.hardware_profile == HardwareProfile.WORKSTATION:
            # Workstation: Can handle less frequent checkpoints
            return base_interval * 1.2

        return base_interval

    def should_checkpoint(self) -> bool:
        """Check if a checkpoint should be created."""
        if self.last_checkpoint_time is None:
            return True

        elapsed = (datetime.now(UTC) - self.last_checkpoint_time).total_seconds()
        return elapsed >= self.checkpoint_interval

    def create_checkpoint(
        self,
        task_id: str,
        agent_id: str,
        command: str,
        state: str,
        progress: float,
        context: dict[str, Any] | None = None,
        artifacts: list[str] | None = None,
    ) -> TaskCheckpoint:
        """
        Create a checkpoint.

        Args:
            task_id: Task ID
            agent_id: Agent ID
            command: Command being executed
            state: Current state (as string, will be converted to TaskState)
            progress: Progress (0.0 to 1.0)
            context: Agent context
            artifacts: Generated artifacts

        Returns:
            Created checkpoint
        """
        # Convert state string to TaskState and create TaskStateManager
        try:
            task_state = TaskState(state)
        except ValueError:
            # Default to RUNNING if state is not recognized
            task_state = TaskState.RUNNING

        state_manager = TaskStateManager(task_id=task_id, initial_state=task_state)

        checkpoint = self.checkpoint_manager.create_checkpoint(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            state_manager=state_manager,
            progress=progress,
            context=context or {},
            artifacts=artifacts or [],
        )

        self.last_checkpoint_time = datetime.now(UTC)
        self.checkpoint_count += 1

        logger.info(f"Created checkpoint {self.checkpoint_count} for task {task_id}")

        return checkpoint

    def backup_artifacts(self, artifacts: list[str], backup_dir: Path) -> list[Path]:
        """
        Backup artifacts to a backup directory.

        Args:
            artifacts: List of artifact file paths
            backup_dir: Backup directory

        Returns:
            List of backed up file paths
        """
        if self.durability_level != DurabilityLevel.HIGH:
            return []  # Only backup artifacts for HIGH durability

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up = []
        for artifact_path in artifacts:
            artifact = Path(artifact_path)
            if not artifact.exists():
                continue

            backup_path = backup_dir / artifact.name
            try:
                if artifact.is_file():
                    shutil.copy2(artifact, backup_path)
                elif artifact.is_dir():
                    shutil.copytree(artifact, backup_path, dirs_exist_ok=True)
                backed_up.append(backup_path)
            except Exception as e:
                logger.error(
                    f"Failed to backup artifact {artifact}: {e}", exc_info=True
                )

        return backed_up


class FailureRecovery:
    """Recovers from failures automatically."""

    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        session_manager: SessionManager | None = None,
    ):
        """
        Initialize failure recovery.

        Args:
            checkpoint_manager: Checkpoint manager instance
            session_manager: Optional session manager
        """
        self.checkpoint_manager = checkpoint_manager
        self.session_manager = session_manager

        self.failure_history: list[FailureRecord] = []
        self.max_failures = 100  # Keep last 100 failures

    def record_failure(
        self,
        failure_type: str,
        error_message: str,
        stack_trace: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FailureRecord:
        """
        Record a failure event.

        Args:
            failure_type: Type of failure
            error_message: Error message
            stack_trace: Optional stack trace
            task_id: Optional task ID
            metadata: Additional metadata

        Returns:
            FailureRecord instance
        """
        # Check if checkpoint is available (prefer list_checkpoints for testability/mocks)
        checkpoint_available = False
        if task_id:
            try:
                listed = self.checkpoint_manager.list_checkpoints()
            except (OSError, PermissionError) as e:
                # File system errors when listing files
                logger.debug(f"Failed to list files: {e}")
                listed = []

            # `list_checkpoints()` may return task_ids or TaskCheckpoint objects depending on implementation/mocks.
            if listed:
                first = listed[0]
                if hasattr(first, "task_id"):
                    checkpoint_available = any(
                        getattr(cp, "task_id", None) == task_id for cp in listed
                    )
                else:
                    checkpoint_available = task_id in listed

        failure_metadata = metadata or {}
        if task_id:
            failure_metadata["task_id"] = task_id

        failure = FailureRecord(
            timestamp=datetime.now(UTC),
            failure_type=failure_type,
            error_message=error_message,
            stack_trace=stack_trace,
            checkpoint_available=checkpoint_available,
            metadata=failure_metadata,
        )

        self.failure_history.append(failure)
        if len(self.failure_history) > self.max_failures:
            self.failure_history = self.failure_history[-self.max_failures :]

        logger.warning(f"Recorded failure: {failure_type} - {error_message}")

        return failure

    def recover_from_checkpoint(
        self, task_id: str, agent_id: str | None = None
    ) -> TaskCheckpoint | None:
        """
        Recover from the latest checkpoint.

        Args:
            task_id: Task ID
            agent_id: Optional agent ID

        Returns:
            Latest checkpoint or None if not available
        """
        # Prefer list_checkpoints() so mocked managers can provide TaskCheckpoint objects directly.
        try:
            listed: list[Any] = self.checkpoint_manager.list_checkpoints()
        except (OSError, PermissionError) as e:
            # File system errors when listing files
            logger.debug(f"Failed to list files: {e}")
            listed = []

        if not listed:
            logger.warning(f"No checkpoints available for task {task_id}")
            return None

        candidates: list[TaskCheckpoint] = []
        first = listed[0]

        if hasattr(first, "task_id"):
            # Mock/test path: list contains TaskCheckpoint objects
            candidates = [
                cp for cp in listed if getattr(cp, "task_id", None) == task_id
            ]
        else:
            # Storage path: list contains task_id strings
            if task_id in listed:
                cp = self.checkpoint_manager.load_checkpoint(task_id)
                if cp:
                    candidates = [cp]

        if agent_id:
            candidates = [
                cp for cp in candidates if getattr(cp, "agent_id", None) == agent_id
            ]

        if not candidates:
            logger.warning(f"No checkpoints available for task {task_id}")
            return None

        # Choose latest by checkpoint_time if present
        checkpoint = max(
            candidates,
            key=lambda cp: getattr(
                cp, "checkpoint_time", datetime.min.replace(tzinfo=UTC)
            ),
        )

        # Validate checkpoint
        if not checkpoint.validate():
            logger.error(f"Checkpoint validation failed for task {task_id}")
            return None

        logger.info(
            f"Recovering task {task_id} from checkpoint at {checkpoint.checkpoint_time}"
        )

        # Update failure record if this is a recovery attempt
        if self.failure_history:
            last_failure = self.failure_history[-1]
            last_failure.recovery_attempted = True
            last_failure.recovery_successful = True

        return checkpoint

    def get_recovery_strategy(self, failure_type: str) -> str:
        """
        Get recovery strategy for a failure type.

        Args:
            failure_type: Type of failure

        Returns:
            Recovery strategy description
        """
        strategies = {
            "crash": "Restore from latest checkpoint and resume",
            "timeout": "Restore from latest checkpoint and retry with extended timeout",
            "resource_exhaustion": "Restore from latest checkpoint and resume with resource limits",
            "error": "Restore from latest checkpoint and retry with error handling",
        }

        return strategies.get(failure_type, "Restore from latest checkpoint and resume")

    def get_failure_history(self, task_id: str | None = None) -> list[FailureRecord]:
        """
        Get failure history.

        Args:
            task_id: Optional task ID to filter by

        Returns:
            List of failure records
        """
        if not task_id:
            return self.failure_history.copy()

        # Filter by task_id if present in metadata
        return [f for f in self.failure_history if f.metadata.get("task_id") == task_id]


class LongDurationManager:
    """Manages 30+ hour operations with durability guarantees."""

    def __init__(
        self,
        session_manager: SessionManager,
        checkpoint_manager: CheckpointManager,
        resource_executor: ResourceAwareExecutor | None = None,
        durability_level: DurabilityLevel = DurabilityLevel.STANDARD,
        hardware_profile: HardwareProfile | None = None,
    ):
        """
        Initialize long-duration manager.

        Args:
            session_manager: Session manager instance
            checkpoint_manager: Checkpoint manager instance
            resource_executor: Optional resource-aware executor
            durability_level: Durability guarantee level
            hardware_profile: Hardware profile
        """
        self.session_manager = session_manager
        self.checkpoint_manager = checkpoint_manager
        self.resource_executor = resource_executor

        self.durability = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=durability_level,
            hardware_profile=hardware_profile,
        )

        self.failure_recovery = FailureRecovery(
            checkpoint_manager=checkpoint_manager, session_manager=session_manager
        )

        self.progress_tracker = ProgressTracker()

        self.active_tasks: dict[str, AgentSession] = {}
        self._lock = threading.Lock()

        # Background checkpoint thread
        self._checkpoint_thread: threading.Thread | None = None
        self._checkpoint_active = False

    def start_long_duration_task(
        self,
        task_id: str,
        agent_id: str,
        command: str,
        initial_context: dict[str, Any] | None = None,
    ) -> AgentSession:
        """
        Start a long-duration task.

        Args:
            task_id: Task ID
            agent_id: Agent ID
            command: Command to execute
            initial_context: Initial context

        Returns:
            Created session
        """
        # Create session with metadata
        metadata = {"task_id": task_id, "command": command, **(initial_context or {})}
        session = self.session_manager.create_session(
            agent_id=agent_id, metadata=metadata
        )

        with self._lock:
            self.active_tasks[task_id] = session

        # Create initial checkpoint
        self.durability.create_checkpoint(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            state="running",
            progress=0.0,
            context=initial_context or {},
        )

        # Start background checkpointing
        self._start_checkpoint_thread()

        logger.info(
            f"Started long-duration task {task_id} with session {session.session_id}"
        )

        return session

    def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: str,
        steps_completed: int,
        total_steps: int,
        estimated_remaining_hours: float | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Update task progress.

        Args:
            task_id: Task ID
            progress: Progress (0.0 to 1.0)
            current_step: Current step description
            steps_completed: Steps completed
            total_steps: Total steps
            estimated_remaining_hours: Estimated hours remaining
            metadata: Additional metadata
        """
        self.progress_tracker.record_progress(
            progress=progress,
            current_step=current_step,
            steps_completed=steps_completed,
            total_steps=total_steps,
            estimated_remaining_hours=estimated_remaining_hours,
            metadata=metadata or {},
        )

        # Create checkpoint if needed
        if self.durability.should_checkpoint():
            session = self.active_tasks.get(task_id)
            if session:
                self.durability.create_checkpoint(
                    task_id=task_id,
                    agent_id=session.agent_id,
                    command=session.metadata.get("command", ""),
                    state=session.state.value,
                    progress=progress,
                    context=session.metadata,
                    artifacts=session.metadata.get("artifacts", []),
                )

                # Backup artifacts if HIGH durability
                if self.durability.durability_level == DurabilityLevel.HIGH:
                    artifacts = session.metadata.get("artifacts", [])
                    if artifacts:
                        backup_dir = Path(".tapps-agents/backups") / task_id
                        self.durability.backup_artifacts(artifacts, backup_dir)

    def handle_failure(
        self,
        task_id: str,
        failure_type: str,
        error_message: str,
        stack_trace: str | None = None,
    ) -> TaskCheckpoint | None:
        """
        Handle a task failure.

        Args:
            task_id: Task ID
            failure_type: Type of failure
            error_message: Error message
            stack_trace: Optional stack trace

        Returns:
            Recovery checkpoint or None
        """
        # Record failure
        self.failure_recovery.record_failure(
            failure_type=failure_type,
            error_message=error_message,
            stack_trace=stack_trace,
            task_id=task_id,
        )

        # Attempt recovery
        session = self.active_tasks.get(task_id)
        if not session:
            logger.error(f"No active session found for task {task_id}")
            return None

        checkpoint = self.failure_recovery.recover_from_checkpoint(
            task_id=task_id, agent_id=session.agent_id
        )

        if checkpoint:
            logger.info(f"Recovery checkpoint available for task {task_id}")
            # Update session with recovery checkpoint
            self.session_manager.add_checkpoint(session.session_id, checkpoint)
        else:
            logger.warning(f"No recovery checkpoint available for task {task_id}")

        return checkpoint

    def get_progress(self, task_id: str) -> ProgressSnapshot | None:
        """Get latest progress for a task."""
        return self.progress_tracker.get_latest_progress()

    def get_progress_history(
        self, task_id: str, hours: float | None = None
    ) -> list[ProgressSnapshot]:
        """Get progress history for a task."""
        return self.progress_tracker.get_progress_history(hours=hours)

    def _start_checkpoint_thread(self):
        """Start background checkpoint thread."""
        if self._checkpoint_active:
            return

        self._checkpoint_active = True
        self._checkpoint_thread = threading.Thread(
            target=self._checkpoint_loop, daemon=True
        )
        self._checkpoint_thread.start()

    def _checkpoint_loop(self):
        """Background checkpoint loop."""
        while self._checkpoint_active:
            try:
                time.sleep(60)  # Check every minute

                with self._lock:
                    for task_id, session in list(self.active_tasks.items()):
                        if self.durability.should_checkpoint():
                            # Get latest progress
                            progress_snapshot = (
                                self.progress_tracker.get_latest_progress()
                            )
                            progress = (
                                progress_snapshot.progress if progress_snapshot else 0.0
                            )

                            checkpoint = self.durability.create_checkpoint(
                                task_id=task_id,
                                agent_id=session.agent_id,
                                command=session.metadata.get("command", ""),
                                state=session.state.value,
                                progress=progress,
                                context=session.metadata,
                                artifacts=session.metadata.get("artifacts", []),
                            )

                            self.session_manager.add_checkpoint(
                                session.session_id, checkpoint
                            )
            except Exception as e:
                logger.error(f"Error in checkpoint loop: {e}", exc_info=True)

    def stop(self):
        """Stop the long-duration manager."""
        self._checkpoint_active = False
        if self._checkpoint_thread:
            self._checkpoint_thread.join(timeout=5.0)

        logger.info("Long-duration manager stopped")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
