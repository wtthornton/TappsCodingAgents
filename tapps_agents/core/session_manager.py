"""
Session Manager for Long-Duration Operations

Manages long-running agent sessions with persistence, recovery, and health monitoring.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .checkpoint_manager import CheckpointManager, TaskCheckpoint
from .hardware_profiler import HardwareProfile, HardwareProfiler
from .resource_monitor import ResourceMetrics, ResourceMonitor

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"


class HealthStatus(Enum):
    """Session health status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class AgentSession:
    """Long-running agent session."""

    session_id: str
    agent_id: str
    start_time: datetime
    last_activity: datetime
    duration_hours: float
    state: SessionState
    checkpoints: list[TaskCheckpoint] = field(default_factory=list)
    resource_usage: ResourceMetrics | None = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["state"] = self.state.value
        data["health_status"] = self.health_status.value
        data["start_time"] = self.start_time.isoformat()
        data["last_activity"] = self.last_activity.isoformat()
        data["checkpoints"] = [cp.to_dict() for cp in self.checkpoints]
        if self.resource_usage:
            data["resource_usage"] = self.resource_usage.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSession:
        """Create from dictionary."""
        data = data.copy()
        data["state"] = SessionState(data["state"])
        data["health_status"] = HealthStatus(data["health_status"])
        data["start_time"] = datetime.fromisoformat(data["start_time"])
        data["last_activity"] = datetime.fromisoformat(data["last_activity"])
        data["checkpoints"] = [
            TaskCheckpoint.from_dict(cp) for cp in data.get("checkpoints", [])
        ]
        if "resource_usage" in data and data["resource_usage"]:
            from .resource_monitor import ResourceMetrics

            data["resource_usage"] = ResourceMetrics(**data["resource_usage"])
        else:
            data["resource_usage"] = None
        return cls(**data)

    def update_duration(self):
        """Update duration based on current time."""
        delta = datetime.now(UTC) - self.start_time
        self.duration_hours = delta.total_seconds() / 3600.0

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(UTC)
        self.update_duration()


class SessionStorage:
    """Handles session persistence to disk."""

    def __init__(self, storage_dir: Path | None = None):
        """
        Initialize session storage.

        Args:
            storage_dir: Directory to store sessions (defaults to .tapps-agents/sessions)
        """
        if storage_dir is None:
            storage_dir = Path(".tapps-agents/sessions")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: AgentSession) -> Path:
        """
        Save session to disk.

        Args:
            session: Session to save

        Returns:
            Path to saved session file
        """
        session_file = self.storage_dir / f"{session.session_id}.json"

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)

        logger.debug(f"Saved session {session.session_id} to {session_file}")
        return session_file

    def load(self, session_id: str) -> AgentSession | None:
        """
        Load session from disk.

        Args:
            session_id: Session ID to load

        Returns:
            AgentSession if found, None otherwise
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, encoding="utf-8") as f:
                data = json.load(f)

            return AgentSession.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def list_sessions(self, state: SessionState | None = None) -> list[str]:
        """
        List all session IDs.

        Args:
            state: Optional filter by session state

        Returns:
            List of session IDs
        """
        session_ids = []

        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, encoding="utf-8") as f:
                    data = json.load(f)

                if state is None or SessionState(data["state"]) == state:
                    session_ids.append(data["session_id"])
            except Exception as e:
                logger.warning(f"Failed to read session file {session_file}: {e}")

        return session_ids

    def delete(self, session_id: str) -> bool:
        """
        Delete session from disk.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted successfully
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if session_file.exists():
            try:
                session_file.unlink()
                logger.debug(f"Deleted session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                return False

        return False


class SessionMonitor:
    """Monitors session health and resource usage."""

    def __init__(self, resource_monitor: ResourceMonitor | None = None):
        """
        Initialize session monitor.

        Args:
            resource_monitor: ResourceMonitor instance (creates default if not provided)
        """
        self.resource_monitor = resource_monitor or ResourceMonitor()

    def check_health(self, session: AgentSession) -> HealthStatus:
        """
        Check session health based on resource usage and activity.

        Args:
            session: Session to check

        Returns:
            HealthStatus
        """
        # Update resource usage
        session.resource_usage = self.resource_monitor.get_current_metrics()

        # Check if session is stale (no activity for 1 hour)
        time_since_activity = datetime.now(UTC) - session.last_activity
        if time_since_activity > timedelta(hours=1):
            return HealthStatus.CRITICAL

        # Check resource usage
        if session.resource_usage:
            # Critical if memory > 90% or CPU > 85%
            if (
                session.resource_usage.memory_percent > 90.0
                or session.resource_usage.cpu_percent > 85.0
            ):
                return HealthStatus.CRITICAL

            # Warning if memory > 80% or CPU > 70%
            if (
                session.resource_usage.memory_percent > 80.0
                or session.resource_usage.cpu_percent > 70.0
            ):
                return HealthStatus.WARNING

        # Check if session has been running for a very long time (>24 hours)
        if session.duration_hours > 24.0:
            return HealthStatus.WARNING

        return HealthStatus.HEALTHY

    def should_pause(self, session: AgentSession) -> bool:
        """
        Determine if session should be paused due to resource constraints.

        Args:
            session: Session to check

        Returns:
            True if session should be paused
        """
        if not session.resource_usage:
            return False

        # Pause if memory > 90% or CPU > 85%
        return (
            session.resource_usage.memory_percent > 90.0
            or session.resource_usage.cpu_percent > 85.0
        )


class SessionRecovery:
    """Handles session recovery from failures."""

    def __init__(
        self,
        session_storage: SessionStorage,
        checkpoint_manager: CheckpointManager | None = None,
    ):
        """
        Initialize session recovery.

        Args:
            session_storage: SessionStorage instance
            checkpoint_manager: CheckpointManager instance (creates default if not provided)
        """
        self.session_storage = session_storage
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

    def recover_session(self, session_id: str) -> AgentSession | None:
        """
        Recover session from disk.

        Args:
            session_id: Session ID to recover

        Returns:
            Recovered AgentSession or None if recovery failed
        """
        session = self.session_storage.load(session_id)

        if not session:
            logger.warning(f"Session {session_id} not found for recovery")
            return None

        # Validate session
        if not self._validate_session(session):
            logger.error(f"Session {session_id} failed validation")
            return None

        # Update session state
        session.state = SessionState.ACTIVE
        session.update_activity()

        logger.info(
            f"Recovered session {session_id} (duration: {session.duration_hours:.2f} hours)"
        )
        return session

    def _validate_session(self, session: AgentSession) -> bool:
        """
        Validate session integrity.

        Args:
            session: Session to validate

        Returns:
            True if session is valid
        """
        # Check if session has valid ID
        if not session.session_id or not session.agent_id:
            return False

        # Check if checkpoints are valid
        for checkpoint in session.checkpoints:
            if not checkpoint.validate():
                logger.warning(f"Invalid checkpoint in session {session.session_id}")
                return False

        return True

    def get_latest_checkpoint(self, session: AgentSession) -> TaskCheckpoint | None:
        """
        Get the latest checkpoint for a session.

        Args:
            session: Session to get checkpoint from

        Returns:
            Latest TaskCheckpoint or None
        """
        if not session.checkpoints:
            return None

        # Sort by checkpoint time (most recent first)
        sorted_checkpoints = sorted(
            session.checkpoints, key=lambda cp: cp.checkpoint_time, reverse=True
        )

        return sorted_checkpoints[0]


class SessionManager:
    """Manages long-running agent sessions."""

    def __init__(
        self,
        storage_dir: Path | None = None,
        checkpoint_manager: CheckpointManager | None = None,
        resource_monitor: ResourceMonitor | None = None,
        hardware_profile: HardwareProfile | None = None,
    ):
        """
        Initialize session manager.

        Args:
            storage_dir: Directory to store sessions
            checkpoint_manager: CheckpointManager instance
            resource_monitor: ResourceMonitor instance
            hardware_profile: Hardware profile for optimization
        """
        self.storage = SessionStorage(storage_dir)
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.monitor = SessionMonitor(resource_monitor)
        self.recovery = SessionRecovery(self.storage, self.checkpoint_manager)

        # Detect hardware profile if not provided
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.hardware_profile = hardware_profile

        # Active sessions in memory
        self._active_sessions: dict[str, AgentSession] = {}

    def create_session(
        self, agent_id: str, metadata: dict[str, Any] | None = None
    ) -> AgentSession:
        """
        Create a new session.

        Args:
            agent_id: Agent ID for this session
            metadata: Optional metadata

        Returns:
            Created AgentSession
        """
        session_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        session = AgentSession(
            session_id=session_id,
            agent_id=agent_id,
            start_time=now,
            last_activity=now,
            duration_hours=0.0,
            state=SessionState.ACTIVE,
            metadata=metadata or {},
        )

        # Check initial health
        session.health_status = self.monitor.check_health(session)

        # Save to disk
        self.storage.save(session)

        # Store in memory
        self._active_sessions[session_id] = session

        logger.info(f"Created session {session_id} for agent {agent_id}")
        return session

    def get_session(self, session_id: str) -> AgentSession | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            AgentSession if found, None otherwise
        """
        # Check in-memory cache first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Load from disk
        session = self.storage.load(session_id)
        if session:
            self._active_sessions[session_id] = session

        return session

    def update_session(self, session: AgentSession):
        """
        Update session state and save to disk.

        Args:
            session: Session to update
        """
        session.update_activity()

        # Check health
        session.health_status = self.monitor.check_health(session)

        # Check if should pause
        if session.state == SessionState.ACTIVE and self.monitor.should_pause(session):
            logger.warning(
                f"Pausing session {session.session_id} due to resource constraints"
            )
            session.state = SessionState.PAUSED

        # Save to disk
        self.storage.save(session)

        # Update in-memory cache
        self._active_sessions[session.session_id] = session

    def add_checkpoint(self, session_id: str, checkpoint: TaskCheckpoint):
        """
        Add checkpoint to session.

        Args:
            session_id: Session ID
            checkpoint: Checkpoint to add
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for checkpoint")
            return

        session.checkpoints.append(checkpoint)
        self.update_session(session)

        logger.debug(f"Added checkpoint to session {session_id}")

    def pause_session(self, session_id: str, reason: str | None = None):
        """
        Pause a session.

        Args:
            session_id: Session ID
            reason: Optional reason for pausing
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for pause")
            return

        session.state = SessionState.PAUSED
        if reason:
            session.metadata["pause_reason"] = reason

        self.update_session(session)
        logger.info(f"Paused session {session_id}: {reason or 'manual pause'}")

    def resume_session(self, session_id: str) -> AgentSession | None:
        """
        Resume a paused session.

        Args:
            session_id: Session ID

        Returns:
            Resumed AgentSession or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for resume")
            return None

        if session.state != SessionState.PAUSED:
            logger.warning(
                f"Session {session_id} is not paused (state: {session.state})"
            )
            return session

        session.state = SessionState.ACTIVE
        session.update_activity()
        self.update_session(session)

        logger.info(f"Resumed session {session_id}")
        return session

    def recover_session(self, session_id: str) -> AgentSession | None:
        """
        Recover a session from failure.

        Args:
            session_id: Session ID

        Returns:
            Recovered AgentSession or None if recovery failed
        """
        session = self.recovery.recover_session(session_id)

        if session:
            self._active_sessions[session_id] = session

        return session

    def list_sessions(self, state: SessionState | None = None) -> list[AgentSession]:
        """
        List all sessions.

        Args:
            state: Optional filter by state

        Returns:
            List of AgentSession
        """
        session_ids = self.storage.list_sessions(state)
        sessions = []

        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions.append(session)

        return sessions

    def get_active_sessions(self) -> list[AgentSession]:
        """Get all active sessions."""
        return self.list_sessions(SessionState.ACTIVE)

    def cleanup_old_sessions(self, max_age_hours: float = 168.0):  # 7 days default
        """
        Clean up old completed/failed sessions.

        Args:
            max_age_hours: Maximum age in hours for sessions to keep
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)

        for session in self.list_sessions():
            if session.state in (SessionState.COMPLETED, SessionState.FAILED):
                if session.last_activity < cutoff_time:
                    self.storage.delete(session.session_id)
                    if session.session_id in self._active_sessions:
                        del self._active_sessions[session.session_id]
                    logger.debug(f"Cleaned up old session {session.session_id}")
