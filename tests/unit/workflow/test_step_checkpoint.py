"""Tests for StepCheckpointManager."""

from datetime import datetime

import pytest

from tapps_agents.workflow.step_checkpoint import (
    CheckpointNotFoundError,
    StepCheckpoint,
    StepCheckpointManager,
)


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Create temporary state directory."""
    return tmp_path / ".tapps-agents" / "workflow-state"


@pytest.fixture
def checkpoint_manager(tmp_state_dir):
    """Create StepCheckpointManager instance."""
    return StepCheckpointManager(
        state_dir=tmp_state_dir,
        workflow_id="test-workflow-123",
    )


@pytest.fixture
def sample_checkpoint_data():
    """Create sample checkpoint data."""
    return {
        "workflow_id": "test-workflow-123",
        "step_id": "enhance",
        "step_number": 1,
        "step_name": "enhanced-prompt",
        "completed_at": datetime.now(),
        "step_output": {"enhanced_prompt": "Enhanced content"},
        "artifacts": {},
        "metadata": {},
    }


class TestStepCheckpoint:
    """Test StepCheckpoint data model."""

    def test_to_dict(self, sample_checkpoint_data):
        """Test checkpoint to dictionary conversion."""
        checkpoint = StepCheckpoint(**sample_checkpoint_data)
        data = checkpoint.to_dict()

        assert isinstance(data["completed_at"], str)  # ISO format
        assert data["workflow_id"] == "test-workflow-123"
        assert data["step_id"] == "enhance"

    def test_from_dict(self, sample_checkpoint_data):
        """Test checkpoint from dictionary creation."""
        data = sample_checkpoint_data.copy()
        data["completed_at"] = data["completed_at"].isoformat()

        checkpoint = StepCheckpoint.from_dict(data)

        assert isinstance(checkpoint.completed_at, datetime)
        assert checkpoint.workflow_id == "test-workflow-123"

    def test_checksum_calculation(self, sample_checkpoint_data):
        """Test checksum calculation."""
        checkpoint = StepCheckpoint(**sample_checkpoint_data)
        checkpoint.update_checksum()

        assert len(checkpoint.checksum) == 64  # SHA256 hex length
        assert checkpoint.validate()

    def test_checksum_validation(self, sample_checkpoint_data):
        """Test checksum validation."""
        checkpoint = StepCheckpoint(**sample_checkpoint_data)
        checkpoint.update_checksum()

        assert checkpoint.validate()

        # Tamper with data
        checkpoint.step_output["tampered"] = True
        assert not checkpoint.validate()


class TestStepCheckpointManager:
    """Test StepCheckpointManager."""

    def test_save_checkpoint(self, checkpoint_manager, sample_checkpoint_data):
        """Test saving checkpoint."""
        checkpoint_path = checkpoint_manager.save_checkpoint(
            step_id="enhance",
            step_number=1,
            step_output=sample_checkpoint_data["step_output"],
            artifacts={},
            step_name="enhanced-prompt",
        )

        assert checkpoint_path.exists()
        assert checkpoint_path.name == "step1-enhance.json"

    def test_load_checkpoint(self, checkpoint_manager, sample_checkpoint_data):
        """Test loading checkpoint."""
        # Save checkpoint first
        checkpoint_manager.save_checkpoint(
            step_id="enhance",
            step_number=1,
            step_output=sample_checkpoint_data["step_output"],
            artifacts={},
        )

        # Load checkpoint
        checkpoint = checkpoint_manager.load_checkpoint(
            step_id="enhance",
            step_number=1,
        )

        assert checkpoint.step_id == "enhance"
        assert checkpoint.step_number == 1
        assert checkpoint.validate()

    def test_load_checkpoint_not_found(self, checkpoint_manager):
        """Test loading non-existent checkpoint."""
        with pytest.raises(CheckpointNotFoundError):
            checkpoint_manager.load_checkpoint(step_id="nonexistent", step_number=999)

    def test_get_latest_checkpoint(self, checkpoint_manager):
        """Test getting latest checkpoint."""
        # Save multiple checkpoints
        for i in range(1, 4):
            checkpoint_manager.save_checkpoint(
                step_id=f"step{i}",
                step_number=i,
                step_output={"result": f"step{i}"},
                artifacts={},
            )

        latest = checkpoint_manager.get_latest_checkpoint()

        assert latest is not None
        assert latest.step_number == 3  # Latest step

    def test_get_latest_checkpoint_none(self, checkpoint_manager):
        """Test getting latest checkpoint when none exist."""
        latest = checkpoint_manager.get_latest_checkpoint()
        assert latest is None

    def test_list_checkpoints(self, checkpoint_manager):
        """Test listing all checkpoints."""
        # Save multiple checkpoints
        for i in range(1, 4):
            checkpoint_manager.save_checkpoint(
                step_id=f"step{i}",
                step_number=i,
                step_output={"result": f"step{i}"},
                artifacts={},
            )

        checkpoints = checkpoint_manager.list_checkpoints()

        assert len(checkpoints) == 3
        assert all(c.step_number == i + 1 for i, c in enumerate(checkpoints))
