"""
Unit tests for Checkpoint Manager.
"""

import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tapps_agents.core.checkpoint_manager import (
    CheckpointManager,
    CheckpointStorage,
    TaskCheckpoint,
)
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.task_state import TaskState, TaskStateManager


class TestTaskCheckpoint:
    """Tests for TaskCheckpoint dataclass."""

    def test_checkpoint_creation(self):
        """Test checkpoint creation."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
        )

        assert checkpoint.task_id == "test-task"
        assert checkpoint.agent_id == "test-agent"
        assert checkpoint.progress == 0.5

    def test_checkpoint_checksum(self):
        """Test checksum calculation."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
        )

        checksum = checkpoint.calculate_checksum()
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex length

    def test_checkpoint_validation(self):
        """Test checkpoint validation."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
        )

        checkpoint.checksum = checkpoint.calculate_checksum()
        assert checkpoint.validate()

        # Tampered checkpoint should fail
        checkpoint.checksum = "invalid"
        assert not checkpoint.validate()

    def test_checkpoint_serialization(self):
        """Test checkpoint serialization."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
            context={"key": "value"},
            artifacts=["file1.txt", "file2.txt"],
        )

        data = checkpoint.to_dict()
        assert data["task_id"] == "test-task"
        assert data["progress"] == 0.5
        assert "checkpoint_time" in data

        restored = TaskCheckpoint.from_dict(data)
        assert restored.task_id == checkpoint.task_id
        assert restored.progress == checkpoint.progress


class TestCheckpointStorage:
    """Tests for CheckpointStorage."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_storage_initialization(self, temp_dir):
        """Test storage initialization."""
        storage = CheckpointStorage(temp_dir, HardwareProfile.WORKSTATION)
        assert storage.storage_dir == temp_dir
        assert storage.hardware_profile == HardwareProfile.WORKSTATION

    def test_save_and_load_checkpoint(self, temp_dir):
        """Test saving and loading checkpoint."""
        storage = CheckpointStorage(temp_dir, HardwareProfile.WORKSTATION)

        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
            context={"key": "value"},
        )

        # Save checkpoint
        saved_path = storage.save(checkpoint)
        assert saved_path.exists()

        # Load checkpoint
        loaded = storage.load("test-task")
        assert loaded is not None
        assert loaded.task_id == checkpoint.task_id
        assert loaded.progress == checkpoint.progress
        assert loaded.context == checkpoint.context

    def test_compressed_storage(self, temp_dir):
        """Test compressed storage for NUC."""
        storage = CheckpointStorage(temp_dir, HardwareProfile.NUC)
        assert storage.compression_enabled

        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
        )

        saved_path = storage.save(checkpoint)
        assert saved_path.suffix == ".gz"
        assert saved_path.exists()

        loaded = storage.load("test-task")
        assert loaded is not None
        assert loaded.task_id == checkpoint.task_id

    def test_list_checkpoints(self, temp_dir):
        """Test listing checkpoints."""
        storage = CheckpointStorage(temp_dir, HardwareProfile.WORKSTATION)

        # Create multiple checkpoints
        for i in range(3):
            checkpoint = TaskCheckpoint(
                task_id=f"task-{i}",
                agent_id="test-agent",
                command="test command",
                state="running",
                progress=0.5,
                checkpoint_time=datetime.now(UTC),
            )
            storage.save(checkpoint)

        task_ids = storage.list_checkpoints()
        assert len(task_ids) == 3
        assert "task-0" in task_ids
        assert "task-1" in task_ids
        assert "task-2" in task_ids

    def test_delete_checkpoint(self, temp_dir):
        """Test deleting checkpoint."""
        storage = CheckpointStorage(temp_dir, HardwareProfile.WORKSTATION)

        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="running",
            progress=0.5,
            checkpoint_time=datetime.now(UTC),
        )

        storage.save(checkpoint)
        assert storage.load("test-task") is not None

        deleted = storage.delete("test-task")
        assert deleted
        assert storage.load("test-task") is None


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_manager_initialization(self, temp_dir):
        """Test manager initialization."""
        manager = CheckpointManager(storage_dir=temp_dir)
        assert manager.storage.storage_dir == temp_dir
        assert manager.checkpoint_interval > 0

    def test_hardware_aware_intervals(self, temp_dir):
        """Test hardware-aware checkpoint intervals."""
        nuc_manager = CheckpointManager(
            storage_dir=temp_dir, hardware_profile=HardwareProfile.NUC
        )
        assert nuc_manager.checkpoint_interval == 30

        workstation_manager = CheckpointManager(
            storage_dir=temp_dir, hardware_profile=HardwareProfile.WORKSTATION
        )
        assert workstation_manager.checkpoint_interval == 120

    def test_should_checkpoint(self, temp_dir):
        """Test should_checkpoint logic."""
        manager = CheckpointManager(storage_dir=temp_dir, checkpoint_interval=1)

        # First check should return True
        assert manager.should_checkpoint("test-task")

        # Immediate second check should return False
        import time

        time.sleep(0.1)
        assert not manager.should_checkpoint("test-task")

    def test_create_checkpoint(self, temp_dir):
        """Test creating checkpoint."""
        manager = CheckpointManager(storage_dir=temp_dir)
        state_manager = TaskStateManager("test-task")
        state_manager.transition(TaskState.RUNNING)

        checkpoint = manager.create_checkpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state_manager=state_manager,
            progress=0.5,
            context={"key": "value"},
            artifacts=["file1.txt"],
        )

        assert checkpoint.task_id == "test-task"
        assert checkpoint.progress == 0.5
        assert checkpoint.checksum is not None

        # Verify saved
        loaded = manager.load_checkpoint("test-task")
        assert loaded is not None
        assert loaded.task_id == checkpoint.task_id

    def test_list_checkpoints(self, temp_dir):
        """Test listing checkpoints."""
        manager = CheckpointManager(storage_dir=temp_dir)

        # Create multiple checkpoints
        for i in range(3):
            state_manager = TaskStateManager(f"task-{i}")
            state_manager.transition(TaskState.RUNNING)
            manager.create_checkpoint(
                task_id=f"task-{i}",
                agent_id="test-agent",
                command="test command",
                state_manager=state_manager,
                progress=0.5,
            )

        task_ids = manager.list_checkpoints()
        assert len(task_ids) == 3
