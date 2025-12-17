"""
Unit tests for Workflow Checkpoint Manager.

Epic 12: State Persistence and Resume - Story 12.7
"""

import time
from datetime import datetime

import pytest

from tapps_agents.workflow.checkpoint_manager import (
    CheckpointConfig,
    CheckpointFrequency,
    WorkflowCheckpointManager,
)
from tapps_agents.workflow.models import WorkflowState, WorkflowStep

pytestmark = pytest.mark.unit


class TestCheckpointConfig:
    """Tests for CheckpointConfig dataclass."""

    def test_default_config(self):
        """Test default checkpoint configuration."""
        config = CheckpointConfig()
        assert config.frequency == CheckpointFrequency.EVERY_STEP
        assert config.interval == 1
        assert config.enabled is True

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "frequency": "every_n_steps",
            "interval": 5,
            "enabled": False,
        }
        config = CheckpointConfig.from_dict(data)
        assert config.frequency == CheckpointFrequency.EVERY_N_STEPS
        assert config.interval == 5
        assert config.enabled is False

    def test_from_dict_invalid_frequency(self):
        """Test from_dict with invalid frequency defaults to EVERY_STEP."""
        data = {"frequency": "invalid"}
        config = CheckpointConfig.from_dict(data)
        assert config.frequency == CheckpointFrequency.EVERY_STEP

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = CheckpointConfig(
            frequency=CheckpointFrequency.ON_GATES,
            interval=3,
            enabled=True,
        )
        data = config.to_dict()
        assert data["frequency"] == "on_gates"
        assert data["interval"] == 3
        assert data["enabled"] is True


class TestWorkflowCheckpointManager:
    """Tests for WorkflowCheckpointManager."""

    @pytest.fixture
    def sample_step(self):
        """Create a sample workflow step."""
        return WorkflowStep(
            id="step-1",
            agent="implementer",
            action="implement",
            metadata={},
        )

    @pytest.fixture
    def sample_state(self):
        """Create a sample workflow state."""
        return WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            current_step="step-1",
            completed_steps=["step-0"],
            skipped_steps=[],
            artifacts={},
            variables={},
            status="running",
        )

    def test_initialization_default(self):
        """Test manager initialization with default config."""
        manager = WorkflowCheckpointManager()
        assert manager.config.frequency == CheckpointFrequency.EVERY_STEP
        assert manager.step_count == 0

    def test_initialization_custom_config(self):
        """Test manager initialization with custom config."""
        config = CheckpointConfig(frequency=CheckpointFrequency.ON_GATES)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.config.frequency == CheckpointFrequency.ON_GATES

    def test_should_checkpoint_disabled(self, sample_step, sample_state):
        """Test should_checkpoint returns False when disabled."""
        config = CheckpointConfig(enabled=False)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(sample_step, sample_state) is False

    def test_should_checkpoint_every_step(self, sample_step, sample_state):
        """Test should_checkpoint for EVERY_STEP frequency."""
        config = CheckpointConfig(frequency=CheckpointFrequency.EVERY_STEP)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(sample_step, sample_state) is True

    def test_should_checkpoint_manual(self, sample_step, sample_state):
        """Test should_checkpoint returns False for MANUAL frequency."""
        config = CheckpointConfig(frequency=CheckpointFrequency.MANUAL)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(sample_step, sample_state) is False

    def test_should_checkpoint_on_gates(self, sample_step, sample_state):
        """Test should_checkpoint for ON_GATES frequency."""
        config = CheckpointConfig(frequency=CheckpointFrequency.ON_GATES)
        manager = WorkflowCheckpointManager(config=config)

        # Should checkpoint on gate step
        assert manager.should_checkpoint(sample_step, sample_state, is_gate_step=True) is True

        # Should not checkpoint on non-gate step
        assert manager.should_checkpoint(sample_step, sample_state, is_gate_step=False) is False

    def test_should_checkpoint_every_n_steps(self, sample_step, sample_state):
        """Test should_checkpoint for EVERY_N_STEPS frequency."""
        config = CheckpointConfig(
            frequency=CheckpointFrequency.EVERY_N_STEPS,
            interval=3,
        )
        manager = WorkflowCheckpointManager(config=config)

        # Step 1: should not checkpoint (1 % 3 != 0)
        assert manager.should_checkpoint(sample_step, sample_state) is False

        # Step 2: should not checkpoint (2 % 3 != 0)
        assert manager.should_checkpoint(sample_step, sample_state) is False

        # Step 3: should checkpoint (3 % 3 == 0)
        assert manager.should_checkpoint(sample_step, sample_state) is True

    def test_should_checkpoint_time_based(self, sample_step, sample_state):
        """Test should_checkpoint for TIME_BASED frequency."""
        config = CheckpointConfig(
            frequency=CheckpointFrequency.TIME_BASED,
            interval=1,  # 1 second
        )
        manager = WorkflowCheckpointManager(config=config)

        # First checkpoint should be allowed
        assert manager.should_checkpoint(sample_step, sample_state) is True

        # Record checkpoint
        manager.record_checkpoint("step-1")

        # Immediate second check should not checkpoint
        assert manager.should_checkpoint(sample_step, sample_state) is False

        # Wait for interval
        time.sleep(1.1)

        # Should checkpoint after interval
        assert manager.should_checkpoint(sample_step, sample_state) is True

    def test_record_checkpoint(self):
        """Test recording checkpoint."""
        manager = WorkflowCheckpointManager()
        manager.record_checkpoint("step-1")

        assert manager.last_checkpoint_time is not None
        assert manager.last_checkpoint_step == "step-1"

    def test_get_checkpoint_metadata(self, sample_state, sample_step):
        """Test getting checkpoint metadata."""
        manager = WorkflowCheckpointManager()
        manager.step_count = 5

        metadata = manager.get_checkpoint_metadata(sample_state, sample_step)

        assert "checkpoint_time" in metadata
        assert metadata["step_count"] == 5
        assert metadata["current_step"] == "step-1"
        assert metadata["completed_steps"] == 1
        assert metadata["skipped_steps"] == 0
        assert "progress_percentage" in metadata
        assert metadata["workflow_status"] == "running"
        assert metadata["trigger_step_id"] == "step-1"
        assert metadata["trigger_step_agent"] == "implementer"
        assert metadata["trigger_step_action"] == "implement"

    def test_get_checkpoint_metadata_no_step(self, sample_state):
        """Test getting checkpoint metadata without step."""
        manager = WorkflowCheckpointManager()
        metadata = manager.get_checkpoint_metadata(sample_state)

        assert "checkpoint_time" in metadata
        assert "trigger_step_id" not in metadata
        assert "trigger_step_agent" not in metadata

    def test_get_checkpoint_metadata_progress_calculation(self, sample_state):
        """Test progress calculation in metadata."""
        manager = WorkflowCheckpointManager()

        # State with 3 completed steps
        sample_state.completed_steps = ["step-0", "step-1", "step-2"]
        sample_state.current_step = "step-3"

        metadata = manager.get_checkpoint_metadata(sample_state)

        assert metadata["completed_steps"] == 3
        assert "progress_percentage" in metadata
        assert 0 <= metadata["progress_percentage"] <= 100

    def test_step_count_increment(self, sample_step, sample_state):
        """Test that step_count increments on each should_checkpoint call."""
        manager = WorkflowCheckpointManager()

        initial_count = manager.step_count
        manager.should_checkpoint(sample_step, sample_state)
        assert manager.step_count == initial_count + 1

        manager.should_checkpoint(sample_step, sample_state)
        assert manager.step_count == initial_count + 2

