"""
Unit tests for SessionManager.
"""

import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from tapps_agents.core.checkpoint_manager import TaskCheckpoint
from tapps_agents.core.resource_monitor import ResourceMetrics
from tapps_agents.core.session_manager import (
    AgentSession,
    HealthStatus,
    SessionManager,
    SessionMonitor,
    SessionRecovery,
    SessionState,
    SessionStorage,
)

pytestmark = pytest.mark.unit


class TestAgentSession:
    """Test AgentSession dataclass."""

    def test_create_session(self):
        """Test creating a session."""
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=0.0,
            state=SessionState.ACTIVE,
        )

        assert session.session_id == "test-session"
        assert session.agent_id == "test-agent"
        assert session.state == SessionState.ACTIVE

    def test_update_duration(self):
        """Test updating duration."""
        start = datetime.now(UTC) - timedelta(hours=2)
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=start,
            last_activity=start,
            duration_hours=0.0,
            state=SessionState.ACTIVE,
        )

        session.update_duration()

        assert session.duration_hours > 1.9
        assert session.duration_hours < 2.1

    def test_to_dict_from_dict(self):
        """Test serialization and deserialization."""
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=1.5,
            state=SessionState.ACTIVE,
            metadata={"key": "value"},
        )

        data = session.to_dict()
        restored = AgentSession.from_dict(data)

        assert restored.session_id == session.session_id
        assert restored.agent_id == session.agent_id
        assert restored.state == session.state
        assert restored.metadata == session.metadata


class TestSessionStorage:
    """Test SessionStorage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage = SessionStorage(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load(self):
        """Test saving and loading sessions."""
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=0.0,
            state=SessionState.ACTIVE,
        )

        # Save
        saved_path = self.storage.save(session)
        assert saved_path.exists()

        # Load
        loaded = self.storage.load("test-session")
        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.agent_id == session.agent_id

    def test_list_sessions(self):
        """Test listing sessions."""
        # Create multiple sessions
        for i in range(3):
            session = AgentSession(
                session_id=f"session-{i}",
                agent_id="test-agent",
                start_time=datetime.now(UTC),
                last_activity=datetime.now(UTC),
                duration_hours=0.0,
                state=SessionState.ACTIVE if i < 2 else SessionState.PAUSED,
            )
            self.storage.save(session)

        # List all
        all_sessions = self.storage.list_sessions()
        assert len(all_sessions) == 3

        # List active only
        active_sessions = self.storage.list_sessions(SessionState.ACTIVE)
        assert len(active_sessions) == 2

    def test_delete(self):
        """Test deleting sessions."""
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=0.0,
            state=SessionState.ACTIVE,
        )

        self.storage.save(session)
        assert self.storage.load("test-session") is not None

        # Delete
        result = self.storage.delete("test-session")
        assert result is True
        assert self.storage.load("test-session") is None


class TestSessionMonitor:
    """Test SessionMonitor."""

    def test_check_health_healthy(self):
        """Test health check for healthy session."""
        monitor = SessionMonitor()

        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=1.0,
            state=SessionState.ACTIVE,
        )

        # Mock resource monitor to return healthy metrics
        mock_metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=1000.0,
            memory_available_mb=1000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        monitor.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)

        health = monitor.check_health(session)

        assert health == HealthStatus.HEALTHY
        assert session.resource_usage is not None

    def test_check_health_critical(self):
        """Test health check for critical session."""
        monitor = SessionMonitor()

        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC) - timedelta(hours=2),  # Stale
            duration_hours=1.0,
            state=SessionState.ACTIVE,
        )

        health = monitor.check_health(session)

        assert health == HealthStatus.CRITICAL

    def test_should_pause(self):
        """Test should_pause logic."""
        monitor = SessionMonitor()

        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=1.0,
            state=SessionState.ACTIVE,
        )

        # High memory usage
        mock_metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=30.0,
            memory_percent=95.0,  # Critical
            memory_used_mb=1900.0,
            memory_available_mb=100.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        monitor.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)
        monitor.check_health(session)

        assert monitor.should_pause(session) is True


class TestSessionRecovery:
    """Test SessionRecovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage = SessionStorage(self.temp_dir)
        self.recovery = SessionRecovery(self.storage)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_recover_session(self):
        """Test session recovery."""
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=1.0,
            state=SessionState.PAUSED,
        )

        self.storage.save(session)

        recovered = self.recovery.recover_session("test-session")

        assert recovered is not None
        assert recovered.session_id == session.session_id
        assert recovered.state == SessionState.ACTIVE

    def test_get_latest_checkpoint(self):
        """Test getting latest checkpoint."""
        session = AgentSession(
            session_id="test-session",
            agent_id="test-agent",
            start_time=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            duration_hours=1.0,
            state=SessionState.ACTIVE,
        )

        # Add checkpoints
        checkpoint1 = TaskCheckpoint(
            task_id="task-1",
            agent_id="test-agent",
            command="test",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC) - timedelta(minutes=10),
        )
        checkpoint2 = TaskCheckpoint(
            task_id="task-2",
            agent_id="test-agent",
            command="test",
            state="running",
            progress=0.8,
            checkpoint_time=datetime.now(UTC) - timedelta(minutes=5),
        )

        session.checkpoints = [checkpoint1, checkpoint2]

        latest = self.recovery.get_latest_checkpoint(session)

        assert latest is not None
        assert latest.progress == 0.8


class TestSessionManager:
    """Test SessionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = SessionManager(storage_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_session(self):
        """Test creating a session."""
        session = self.manager.create_session("test-agent", {"key": "value"})

        assert session is not None
        assert session.agent_id == "test-agent"
        assert session.state == SessionState.ACTIVE
        assert session.metadata["key"] == "value"

    def test_get_session(self):
        """Test getting a session."""
        created = self.manager.create_session("test-agent")
        session_id = created.session_id

        retrieved = self.manager.get_session(session_id)

        assert retrieved is not None
        assert retrieved.session_id == session_id

    def test_update_session(self):
        """Test updating a session."""
        session = self.manager.create_session("test-agent")

        # Mock resource monitor
        mock_metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=1000.0,
            memory_available_mb=1000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        self.manager.monitor.resource_monitor.get_current_metrics = Mock(
            return_value=mock_metrics
        )

        self.manager.update_session(session)

        # Session should be saved
        loaded = self.manager.get_session(session.session_id)
        assert loaded is not None

    def test_pause_and_resume(self):
        """Test pausing and resuming a session."""
        session = self.manager.create_session("test-agent")

        # Mock resource monitor to prevent auto-pausing
        mock_metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=30.0,  # Low CPU to prevent auto-pause
            memory_percent=50.0,
            memory_used_mb=1000.0,
            memory_available_mb=1000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        self.manager.monitor.resource_monitor.get_current_metrics = Mock(
            return_value=mock_metrics
        )
        self.manager.monitor.should_pause = Mock(return_value=False)

        # Pause
        self.manager.pause_session(session.session_id, "test reason")
        paused = self.manager.get_session(session.session_id)
        assert paused.state == SessionState.PAUSED
        assert paused.metadata["pause_reason"] == "test reason"

        # Resume
        resumed = self.manager.resume_session(session.session_id)
        assert resumed is not None
        # Verify the resumed session has ACTIVE state
        assert resumed.state == SessionState.ACTIVE
        # Also verify by getting the session again
        resumed_check = self.manager.get_session(session.session_id)
        assert resumed_check.state == SessionState.ACTIVE

    def test_add_checkpoint(self):
        """Test adding checkpoint to session."""
        session = self.manager.create_session("test-agent")

        checkpoint = TaskCheckpoint(
            task_id="task-1",
            agent_id="test-agent",
            command="test",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
        )

        self.manager.add_checkpoint(session.session_id, checkpoint)

        updated = self.manager.get_session(session.session_id)
        assert len(updated.checkpoints) == 1
        assert updated.checkpoints[0].task_id == "task-1"

    def test_list_sessions(self):
        """Test listing sessions."""
        # Create multiple sessions
        self.manager.create_session("agent-1")
        session2 = self.manager.create_session("agent-2")
        self.manager.pause_session(session2.session_id)

        # List all
        all_sessions = self.manager.list_sessions()
        assert len(all_sessions) >= 2

        # List active only
        active = self.manager.get_active_sessions()
        assert len(active) >= 1

    def test_cleanup_old_sessions(self):
        """Test cleaning up old sessions."""
        # Create old completed session
        old_time = datetime.now(UTC) - timedelta(days=10)
        session = AgentSession(
            session_id="old-session",
            agent_id="test-agent",
            start_time=old_time,
            last_activity=old_time,
            duration_hours=1.0,
            state=SessionState.COMPLETED,
        )
        self.manager.storage.save(session)

        # Cleanup
        self.manager.cleanup_old_sessions(max_age_hours=168.0)  # 7 days

        # Should be deleted
        assert self.manager.get_session("old-session") is None
