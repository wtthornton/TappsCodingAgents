"""
Unit tests for LongDurationManager and related components.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone, timedelta
import tempfile
import shutil

from tapps_agents.core.long_duration_support import (
    LongDurationManager, DurabilityGuarantee, FailureRecovery, ProgressTracker,
    DurabilityLevel, ProgressSnapshot, FailureRecord
)
from tapps_agents.core.session_manager import SessionManager, SessionState
from tapps_agents.core.checkpoint_manager import CheckpointManager, TaskCheckpoint
from tapps_agents.core.hardware_profiler import HardwareProfile

pytestmark = pytest.mark.unit


class TestProgressTracker:
    """Test ProgressTracker functionality."""
    
    def test_record_progress(self):
        """Test recording progress."""
        tracker = ProgressTracker()
        
        snapshot = tracker.record_progress(
            progress=0.5,
            current_step="Step 5",
            steps_completed=5,
            total_steps=10
        )
        
        assert snapshot.progress == 0.5
        assert snapshot.current_step == "Step 5"
        assert snapshot.steps_completed == 5
        assert snapshot.total_steps == 10
        assert len(tracker.snapshots) == 1
    
    def test_get_latest_progress(self):
        """Test getting latest progress."""
        tracker = ProgressTracker()
        
        tracker.record_progress(0.3, "Step 3", 3, 10)
        tracker.record_progress(0.5, "Step 5", 5, 10)
        
        latest = tracker.get_latest_progress()
        assert latest is not None
        assert latest.progress == 0.5
        assert latest.current_step == "Step 5"
    
    def test_get_progress_history(self):
        """Test getting progress history."""
        tracker = ProgressTracker()
        
        tracker.record_progress(0.2, "Step 2", 2, 10)
        tracker.record_progress(0.4, "Step 4", 4, 10)
        tracker.record_progress(0.6, "Step 6", 6, 10)
        
        history = tracker.get_progress_history()
        assert len(history) == 3
        
        # Test with time limit
        history_recent = tracker.get_progress_history(hours=1.0)
        assert len(history_recent) == 3
    
    def test_calculate_velocity(self):
        """Test calculating progress velocity."""
        tracker = ProgressTracker()
        
        # Need at least 2 snapshots
        tracker.record_progress(0.0, "Step 0", 0, 10)
        tracker.record_progress(0.5, "Step 5", 5, 10)
        
        velocity = tracker.calculate_velocity()
        assert velocity is not None
        assert velocity > 0
    
    def test_calculate_velocity_insufficient_data(self):
        """Test velocity calculation with insufficient data."""
        tracker = ProgressTracker()
        
        tracker.record_progress(0.5, "Step 5", 5, 10)
        
        velocity = tracker.calculate_velocity()
        assert velocity is None


class TestDurabilityGuarantee:
    """Test DurabilityGuarantee functionality."""
    
    def test_initialization(self):
        """Test initialization."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        durability = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
        
        assert durability.durability_level == DurabilityLevel.STANDARD
        assert durability.checkpoint_interval > 0
    
    def test_checkpoint_interval_by_level(self):
        """Test checkpoint intervals by durability level."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        basic = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.BASIC
        )
        standard = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
        high = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.HIGH
        )
        
        # HIGH should have shorter interval than STANDARD, which should be shorter than BASIC
        assert high.checkpoint_interval < standard.checkpoint_interval
        assert standard.checkpoint_interval < basic.checkpoint_interval
    
    def test_should_checkpoint(self):
        """Test should_checkpoint logic."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        durability = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
        
        # Should checkpoint if never checkpointed
        assert durability.should_checkpoint() is True
        
        # Should not checkpoint immediately after creating one
        durability.last_checkpoint_time = datetime.now(timezone.utc)
        assert durability.should_checkpoint() is False
    
    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint_manager.create_checkpoint.return_value = checkpoint
        
        durability = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
        
        created = durability.create_checkpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5
        )
        
        assert created == checkpoint
        assert durability.checkpoint_count == 1
        assert durability.last_checkpoint_time is not None
    
    def test_backup_artifacts_high_durability(self):
        """Test artifact backup for HIGH durability."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        durability = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.HIGH
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test artifact
            artifact_file = Path(tmpdir) / "test.txt"
            artifact_file.write_text("test content")
            
            backup_dir = Path(tmpdir) / "backup"
            backed_up = durability.backup_artifacts([str(artifact_file)], backup_dir)
            
            assert len(backed_up) == 1
            assert (backup_dir / "test.txt").exists()
    
    def test_backup_artifacts_lower_durability(self):
        """Test that artifacts are not backed up for lower durability levels."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        durability = DurabilityGuarantee(
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_file = Path(tmpdir) / "test.txt"
            artifact_file.write_text("test content")
            
            backup_dir = Path(tmpdir) / "backup"
            backed_up = durability.backup_artifacts([str(artifact_file)], backup_dir)
            
            assert len(backed_up) == 0


class TestFailureRecovery:
    """Test FailureRecovery functionality."""
    
    def test_initialization(self):
        """Test initialization."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        assert recovery.checkpoint_manager is checkpoint_manager
        assert len(recovery.failure_history) == 0
    
    def test_record_failure(self):
        """Test recording a failure."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint_manager.list_checkpoints.return_value = []
        
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        failure = recovery.record_failure(
            failure_type="crash",
            error_message="Test error",
            task_id="test-task"
        )
        
        assert failure.failure_type == "crash"
        assert failure.error_message == "Test error"
        assert len(recovery.failure_history) == 1
    
    def test_record_failure_with_checkpoint(self):
        """Test recording failure when checkpoint is available."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint_manager.list_checkpoints.return_value = [checkpoint]
        
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        failure = recovery.record_failure(
            failure_type="crash",
            error_message="Test error",
            task_id="test-task"
        )
        
        assert failure.checkpoint_available is True
    
    def test_recover_from_checkpoint(self):
        """Test recovering from checkpoint."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint.calculate_checksum()
        checkpoint.checksum = checkpoint.calculate_checksum()
        checkpoint_manager.list_checkpoints.return_value = [checkpoint]
        
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        recovered = recovery.recover_from_checkpoint(
            task_id="test-task",
            agent_id="test-agent"
        )
        
        assert recovered is not None
        assert recovered.task_id == "test-task"
    
    def test_recover_from_checkpoint_no_checkpoints(self):
        """Test recovery when no checkpoints available."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint_manager.list_checkpoints.return_value = []
        
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        recovered = recovery.recover_from_checkpoint(task_id="test-task")
        
        assert recovered is None
    
    def test_get_recovery_strategy(self):
        """Test getting recovery strategy."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        strategy = recovery.get_recovery_strategy("crash")
        assert "checkpoint" in strategy.lower()
        
        strategy = recovery.get_recovery_strategy("timeout")
        assert "timeout" in strategy.lower()
    
    def test_get_failure_history(self):
        """Test getting failure history."""
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint_manager.list_checkpoints.return_value = []
        
        recovery = FailureRecovery(checkpoint_manager=checkpoint_manager)
        
        recovery.record_failure("crash", "Error 1", task_id="task1")
        recovery.record_failure("timeout", "Error 2", task_id="task2")
        
        history = recovery.get_failure_history()
        assert len(history) == 2
        
        # Test filtering by task_id
        history_task1 = recovery.get_failure_history(task_id="task1")
        assert len(history_task1) == 1


class TestLongDurationManager:
    """Test LongDurationManager functionality."""
    
    def test_initialization(self):
        """Test initialization."""
        session_manager = Mock(spec=SessionManager)
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        assert manager.session_manager is session_manager
        assert manager.checkpoint_manager is checkpoint_manager
        assert manager.durability is not None
        assert manager.failure_recovery is not None
        assert manager.progress_tracker is not None
    
    def test_start_long_duration_task(self):
        """Test starting a long-duration task."""
        session_manager = Mock(spec=SessionManager)
        session = Mock()
        session.session_id = "session-1"
        session.agent_id = "agent-1"
        session.state = SessionState.ACTIVE
        session.metadata = {"command": "test command"}
        session_manager.create_session.return_value = session
        
        checkpoint_manager = Mock(spec=CheckpointManager)
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="agent-1",
            command="test command",
            state="running",
            progress=0.0,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint_manager.create_checkpoint.return_value = checkpoint
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        created_session = manager.start_long_duration_task(
            task_id="test-task",
            agent_id="agent-1",
            command="test command"
        )
        
        assert created_session == session
        assert "test-task" in manager.active_tasks
        session_manager.create_session.assert_called_once()
        checkpoint_manager.create_checkpoint.assert_called()
    
    def test_update_progress(self):
        """Test updating progress."""
        session_manager = Mock(spec=SessionManager)
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        session = Mock()
        session.session_id = "session-1"
        session.agent_id = "agent-1"
        session.state = SessionState.ACTIVE
        session.metadata = {"command": "test command", "artifacts": []}
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        manager.active_tasks["test-task"] = session
        
        # Mock should_checkpoint to return True
        manager.durability.last_checkpoint_time = None
        
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="agent-1",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint_manager.create_checkpoint.return_value = checkpoint
        
        manager.update_progress(
            task_id="test-task",
            progress=0.5,
            current_step="Step 5",
            steps_completed=5,
            total_steps=10
        )
        
        latest = manager.progress_tracker.get_latest_progress()
        assert latest is not None
        assert latest.progress == 0.5
    
    def test_handle_failure(self):
        """Test handling a failure."""
        session_manager = Mock(spec=SessionManager)
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        session = Mock()
        session.session_id = "session-1"
        session.agent_id = "agent-1"
        session.state = SessionState.ACTIVE
        session.metadata = {}
        
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="agent-1",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint.calculate_checksum()
        checkpoint.checksum = checkpoint.calculate_checksum()
        checkpoint_manager.list_checkpoints.return_value = [checkpoint]
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        manager.active_tasks["test-task"] = session
        
        recovered = manager.handle_failure(
            task_id="test-task",
            failure_type="crash",
            error_message="Test error"
        )
        
        assert recovered is not None
        assert len(manager.failure_recovery.failure_history) == 1
    
    def test_get_progress(self):
        """Test getting progress."""
        session_manager = Mock(spec=SessionManager)
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        manager.progress_tracker.record_progress(
            progress=0.6,
            current_step="Step 6",
            steps_completed=6,
            total_steps=10
        )
        
        progress = manager.get_progress("test-task")
        assert progress is not None
        assert progress.progress == 0.6
    
    def test_stop(self):
        """Test stopping the manager."""
        session_manager = Mock(spec=SessionManager)
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        manager._checkpoint_active = True
        manager.stop()
        
        assert manager._checkpoint_active is False
    
    def test_context_manager(self):
        """Test manager as context manager."""
        session_manager = Mock(spec=SessionManager)
        checkpoint_manager = Mock(spec=CheckpointManager)
        
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        
        # Start a task to activate checkpoint thread
        session = Mock()
        session.session_id = "session-1"
        session.agent_id = "agent-1"
        session.state = SessionState.ACTIVE
        session.metadata = {"command": "test command"}
        session_manager.create_session.return_value = session
        
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="agent-1",
            command="test command",
            state="running",
            progress=0.0,
            checkpoint_time=datetime.now(timezone.utc)
        )
        checkpoint_manager.create_checkpoint.return_value = checkpoint
        
        with manager:
            manager.start_long_duration_task("test-task", "agent-1", "test command")
            assert manager._checkpoint_active is True
        
        assert manager._checkpoint_active is False

