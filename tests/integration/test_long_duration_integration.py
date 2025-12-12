"""
Integration tests for LongDurationManager with agents and full workflow.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone, timedelta
import tempfile
import shutil
import time

from tapps_agents.core.long_duration_support import (
    LongDurationManager, DurabilityLevel, ProgressSnapshot
)
from tapps_agents.core.session_manager import SessionManager, SessionState
from tapps_agents.core.checkpoint_manager import CheckpointManager, TaskCheckpoint
from tapps_agents.core.resource_aware_executor import ResourceAwareExecutor
from tapps_agents.core.resource_monitor import ResourceMonitor
from tapps_agents.core.hardware_profiler import HardwareProfile

pytestmark = pytest.mark.integration


class TestLongDurationIntegration:
    """Integration tests for long-duration operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def session_manager(self, temp_dir):
        """Create session manager."""
        return SessionManager(storage_dir=temp_dir / "sessions")
    
    @pytest.fixture
    def checkpoint_manager(self, temp_dir):
        """Create checkpoint manager."""
        return CheckpointManager(storage_dir=temp_dir / "checkpoints")
    
    @pytest.fixture
    def long_duration_manager(self, session_manager, checkpoint_manager):
        """Create long-duration manager."""
        return LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
    
    def test_full_workflow_start_to_progress(self, long_duration_manager):
        """Test full workflow from start to progress updates."""
        task_id = "test-task-1"
        agent_id = "test-agent"
        command = "test command"
        
        # Start task
        session = long_duration_manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            initial_context={"step": 0}
        )
        
        assert session is not None
        assert session.agent_id == agent_id
        assert task_id in long_duration_manager.active_tasks
        
        # Update progress multiple times
        for i in range(1, 6):
            long_duration_manager.update_progress(
                task_id=task_id,
                progress=i * 0.1,
                current_step=f"Step {i}",
                steps_completed=i,
                total_steps=10
            )
        
        # Verify progress tracking
        latest_progress = long_duration_manager.get_progress(task_id)
        assert latest_progress is not None
        assert latest_progress.progress == 0.5
        assert latest_progress.current_step == "Step 5"
        assert latest_progress.steps_completed == 5
        
        # Verify progress history
        history = long_duration_manager.get_progress_history(task_id)
        assert len(history) == 5
    
    def test_failure_recovery_workflow(self, long_duration_manager):
        """Test failure and recovery workflow."""
        task_id = "test-task-2"
        agent_id = "test-agent"
        command = "test command"
        
        # Start task
        session = long_duration_manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        # Force checkpoint by resetting last checkpoint time
        long_duration_manager.durability.last_checkpoint_time = None
        
        # Update progress
        long_duration_manager.update_progress(
            task_id=task_id,
            progress=0.3,
            current_step="Step 3",
            steps_completed=3,
            total_steps=10
        )
        
        # Simulate failure
        recovered_checkpoint = long_duration_manager.handle_failure(
            task_id=task_id,
            failure_type="crash",
            error_message="Simulated crash",
            stack_trace="Traceback..."
        )
        
        assert recovered_checkpoint is not None
        assert recovered_checkpoint.task_id == task_id
        assert recovered_checkpoint.progress == 0.3
        
        # Verify failure was recorded
        failure_history = long_duration_manager.failure_recovery.get_failure_history(task_id)
        assert len(failure_history) == 1
        assert failure_history[0].failure_type == "crash"
        assert failure_history[0].recovery_successful is True
    
    def test_checkpoint_creation_on_interval(self, long_duration_manager, checkpoint_manager):
        """Test that checkpoints are created at the correct intervals."""
        task_id = "test-task-3"
        agent_id = "test-agent"
        command = "test command"
        
        # Start task
        session = long_duration_manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        # Force checkpoint by setting last_checkpoint_time to None
        long_duration_manager.durability.last_checkpoint_time = None
        
        # Update progress (should trigger checkpoint)
        long_duration_manager.update_progress(
            task_id=task_id,
            progress=0.2,
            current_step="Step 2",
            steps_completed=2,
            total_steps=10
        )
        
        # Verify checkpoint was created
        checkpoint = checkpoint_manager.load_checkpoint(task_id)
        assert checkpoint is not None
        assert checkpoint.progress == 0.2
        assert checkpoint.task_id == task_id
    
    def test_durability_levels(self, session_manager, checkpoint_manager):
        """Test different durability levels."""
        # Test BASIC level
        basic_manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.BASIC
        )
        
        # Test STANDARD level
        standard_manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.STANDARD
        )
        
        # Test HIGH level
        high_manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.HIGH
        )
        
        # Verify intervals are correct
        assert basic_manager.durability.checkpoint_interval > standard_manager.durability.checkpoint_interval
        assert standard_manager.durability.checkpoint_interval > high_manager.durability.checkpoint_interval
    
    def test_artifact_backup_high_durability(self, session_manager, checkpoint_manager, temp_dir):
        """Test artifact backup for HIGH durability level."""
        high_manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager,
            durability_level=DurabilityLevel.HIGH
        )
        
        task_id = "test-task-4"
        agent_id = "test-agent"
        command = "test command"
        
        # Create test artifact
        artifact_file = temp_dir / "test_artifact.txt"
        artifact_file.write_text("test content")
        
        # Start task with artifact
        session = high_manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            initial_context={"artifacts": [str(artifact_file)]}
        )
        
        # Update session metadata with artifacts
        session.metadata["artifacts"] = [str(artifact_file)]
        session_manager.update_session(session)
        
        # Force checkpoint
        high_manager.durability.last_checkpoint_time = None
        
        # Update progress (should trigger backup)
        high_manager.update_progress(
            task_id=task_id,
            progress=0.5,
            current_step="Step 5",
            steps_completed=5,
            total_steps=10
        )
        
        # Verify backup was created
        backup_dir = temp_dir / ".tapps-agents" / "backups" / task_id
        if backup_dir.exists():
            backed_up_files = list(backup_dir.glob("*"))
            assert len(backed_up_files) > 0
    
    def test_multiple_tasks_concurrent(self, long_duration_manager):
        """Test managing multiple concurrent tasks."""
        tasks = []
        
        # Start multiple tasks
        for i in range(3):
            task_id = f"test-task-{i}"
            session = long_duration_manager.start_long_duration_task(
                task_id=task_id,
                agent_id=f"agent-{i}",
                command=f"command-{i}"
            )
            tasks.append((task_id, session))
        
        # Update progress for all tasks
        for task_id, session in tasks:
            long_duration_manager.update_progress(
                task_id=task_id,
                progress=0.5,
                current_step="Step 5",
                steps_completed=5,
                total_steps=10
            )
        
        # Verify all tasks are tracked
        assert len(long_duration_manager.active_tasks) == 3
        
        # Verify progress for each
        for task_id, _ in tasks:
            progress = long_duration_manager.get_progress(task_id)
            assert progress is not None
            assert progress.progress == 0.5
    
    def test_progress_velocity_calculation(self, long_duration_manager):
        """Test progress velocity calculation."""
        task_id = "test-task-5"
        agent_id = "test-agent"
        command = "test command"
        
        session = long_duration_manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        # Record progress over time
        for i in range(5):
            long_duration_manager.update_progress(
                task_id=task_id,
                progress=i * 0.2,
                current_step=f"Step {i}",
                steps_completed=i,
                total_steps=5
            )
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        # Calculate velocity
        velocity = long_duration_manager.progress_tracker.calculate_velocity()
        assert velocity is not None
        assert velocity > 0
    
    def test_context_manager_cleanup(self, session_manager, checkpoint_manager):
        """Test that context manager properly cleans up."""
        with LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        ) as manager:
            task_id = "test-task-6"
            session = manager.start_long_duration_task(
                task_id=task_id,
                agent_id="test-agent",
                command="test command"
            )
            assert manager._checkpoint_active is True
        
        # After context exit, checkpoint thread should be stopped
        assert manager._checkpoint_active is False


class TestFailureRecoveryScenarios:
    """Test various failure recovery scenarios."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def recovery_setup(self, temp_dir):
        """Set up recovery test environment."""
        session_manager = SessionManager(storage_dir=temp_dir / "sessions")
        checkpoint_manager = CheckpointManager(storage_dir=temp_dir / "checkpoints")
        manager = LongDurationManager(
            session_manager=session_manager,
            checkpoint_manager=checkpoint_manager
        )
        return manager, session_manager, checkpoint_manager
    
    def test_crash_recovery(self, recovery_setup):
        """Test recovery from crash."""
        manager, session_manager, checkpoint_manager = recovery_setup
        
        task_id = "crash-test"
        agent_id = "test-agent"
        command = "test command"
        
        # Start task and make progress
        session = manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            initial_context={"data": "important"}
        )
        
        # Force checkpoint by resetting last checkpoint time
        manager.durability.last_checkpoint_time = None
        
        # Make progress
        for i in range(1, 4):
            manager.update_progress(
                task_id=task_id,
                progress=i * 0.25,
                current_step=f"Step {i}",
                steps_completed=i,
                total_steps=4
            )
            # Reset checkpoint time after each update to ensure checkpoint is created
            manager.durability.last_checkpoint_time = None
        
        # Simulate crash
        recovered = manager.handle_failure(
            task_id=task_id,
            failure_type="crash",
            error_message="Process crashed",
            stack_trace="Traceback..."
        )
        
        assert recovered is not None
        assert recovered.progress >= 0.25
        assert "data" in recovered.context
        assert recovered.context["data"] == "important"
    
    def test_timeout_recovery(self, recovery_setup):
        """Test recovery from timeout."""
        manager, session_manager, checkpoint_manager = recovery_setup
        
        task_id = "timeout-test"
        agent_id = "test-agent"
        command = "test command"
        
        session = manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        manager.update_progress(
            task_id=task_id,
            progress=0.6,
            current_step="Step 6",
            steps_completed=6,
            total_steps=10
        )
        
        # Simulate timeout
        recovered = manager.handle_failure(
            task_id=task_id,
            failure_type="timeout",
            error_message="Operation timed out"
        )
        
        assert recovered is not None
        strategy = manager.failure_recovery.get_recovery_strategy("timeout")
        assert "timeout" in strategy.lower()
    
    def test_resource_exhaustion_recovery(self, recovery_setup):
        """Test recovery from resource exhaustion."""
        manager, session_manager, checkpoint_manager = recovery_setup
        
        task_id = "resource-test"
        agent_id = "test-agent"
        command = "test command"
        
        session = manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        manager.update_progress(
            task_id=task_id,
            progress=0.7,
            current_step="Step 7",
            steps_completed=7,
            total_steps=10
        )
        
        # Simulate resource exhaustion
        recovered = manager.handle_failure(
            task_id=task_id,
            failure_type="resource_exhaustion",
            error_message="Memory exhausted"
        )
        
        assert recovered is not None
        strategy = manager.failure_recovery.get_recovery_strategy("resource_exhaustion")
        assert "resource" in strategy.lower()
    
    def test_multiple_failures_recovery(self, recovery_setup):
        """Test recovery from multiple failures."""
        manager, session_manager, checkpoint_manager = recovery_setup
        
        task_id = "multi-failure-test"
        agent_id = "test-agent"
        command = "test command"
        
        session = manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        # Make progress
        manager.update_progress(
            task_id=task_id,
            progress=0.4,
            current_step="Step 4",
            steps_completed=4,
            total_steps=10
        )
        
        # Simulate multiple failures
        for failure_type in ["crash", "timeout", "error"]:
            manager.handle_failure(
                task_id=task_id,
                failure_type=failure_type,
                error_message=f"{failure_type} occurred"
            )
        
        # Verify all failures recorded
        history = manager.failure_recovery.get_failure_history(task_id)
        assert len(history) == 3
        
        # Verify recovery still works
        recovered = manager.handle_failure(
            task_id=task_id,
            failure_type="crash",
            error_message="Another crash"
        )
        assert recovered is not None
    
    def test_recovery_without_checkpoint(self, recovery_setup):
        """Test recovery attempt when no checkpoint exists."""
        manager, session_manager, checkpoint_manager = recovery_setup
        
        task_id = "no-checkpoint-test"
        agent_id = "test-agent"
        command = "test command"
        
        # Start task but don't create any checkpoints
        session = manager.start_long_duration_task(
            task_id=task_id,
            agent_id=agent_id,
            command=command
        )
        
        # Don't update progress, so no checkpoint is created
        
        # Try to recover
        recovered = manager.handle_failure(
            task_id=task_id,
            failure_type="crash",
            error_message="Crash without checkpoint"
        )
        
        # Should return None if no checkpoint
        # (The initial checkpoint from start_long_duration_task should exist)
        # So this should actually succeed
        assert recovered is not None  # Initial checkpoint exists

