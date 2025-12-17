"""
Integration tests for state persistence and resume.

Epic 12: State Persistence and Resume - Story 12.7
Tests the integration between state manager, checkpoint manager, and workflow executor.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.workflow.checkpoint_manager import (
    CheckpointConfig,
    CheckpointFrequency,
    WorkflowCheckpointManager,
)
from tapps_agents.workflow.models import Artifact, WorkflowState, WorkflowStep
from tapps_agents.workflow.state_manager import AdvancedStateManager
from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager

pytestmark = pytest.mark.integration


class TestWorkflowResumeIntegration:
    """Integration tests for workflow resume capability."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create state manager instance."""
        storage_dir = temp_dir / "state"
        return AdvancedStateManager(storage_dir, compression=False)

    @pytest.fixture
    def checkpoint_manager(self):
        """Create checkpoint manager instance."""
        config = CheckpointConfig(frequency=CheckpointFrequency.EVERY_STEP)
        return WorkflowCheckpointManager(config=config)

    def test_checkpoint_creation_during_execution(
        self, state_manager, checkpoint_manager, temp_dir
    ):
        """Test checkpoint creation during workflow execution."""
        # Create initial workflow state
        workflow_state = WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            current_step="step-1",
            completed_steps=["step-0"],
            skipped_steps=[],
            artifacts={},
            variables={"progress": 25},
            status="running",
        )

        # Simulate step completion
        step = WorkflowStep(
            id="step-1",
            agent="implementer",
            action="implement",
            metadata={},
        )

        # Check if checkpoint should be created
        should_checkpoint = checkpoint_manager.should_checkpoint(step, workflow_state)
        assert should_checkpoint is True

        # Save state
        workflow_path = temp_dir / "workflow.yaml"
        state_path = state_manager.save_state(workflow_state, workflow_path)

        assert state_path.exists()

        # Record checkpoint
        checkpoint_manager.record_checkpoint(step.id)

        # Verify state can be loaded
        loaded_state, metadata = state_manager.load_state(
            workflow_id=workflow_state.workflow_id
        )

        assert loaded_state.workflow_id == workflow_state.workflow_id
        assert loaded_state.current_step == workflow_state.current_step
        assert loaded_state.variables == workflow_state.variables

    def test_state_persistence_across_restarts(self, state_manager, temp_dir):
        """Test state persistence across system restarts."""
        # Create and save initial state
        initial_state = WorkflowState(
            workflow_id="persistent-workflow",
            started_at=datetime.now(),
            current_step="step-2",
            completed_steps=["step-0", "step-1"],
            skipped_steps=[],
            artifacts={
                "output": Artifact(
                    path="output/file.txt",
                    type="file",
                    created_at=datetime.now(),
                )
            },
            variables={"key": "value", "counter": 2},
            status="running",
        )

        workflow_path = temp_dir / "workflow.yaml"
        state_manager.save_state(initial_state, workflow_path)

        # Simulate restart: create new state manager instance
        storage_dir = temp_dir / "state"
        new_state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Load persisted state
        loaded_state, metadata = new_state_manager.load_state(
            workflow_id=initial_state.workflow_id
        )

        # Verify state was persisted correctly
        assert loaded_state.workflow_id == initial_state.workflow_id
        assert loaded_state.current_step == initial_state.current_step
        assert loaded_state.completed_steps == initial_state.completed_steps
        assert loaded_state.variables == initial_state.variables
        assert len(loaded_state.artifacts) == len(initial_state.artifacts)

    def test_state_loading_and_continuation(self, state_manager, temp_dir):
        """Test loading state and continuing workflow execution."""
        # Save state at mid-point
        mid_state = WorkflowState(
            workflow_id="resumable-workflow",
            started_at=datetime.now(),
            current_step="step-3",
            completed_steps=["step-0", "step-1", "step-2"],
            skipped_steps=[],
            artifacts={},
            variables={"progress": 50},
            status="running",
        )

        workflow_path = temp_dir / "workflow.yaml"
        state_manager.save_state(mid_state, workflow_path)

        # Load state
        loaded_state, metadata = state_manager.load_state(
            workflow_id=mid_state.workflow_id
        )

        # Continue execution: complete next step
        loaded_state.completed_steps.append(loaded_state.current_step)
        loaded_state.current_step = "step-4"
        loaded_state.variables["progress"] = 60

        # Save updated state
        state_manager.save_state(loaded_state, workflow_path)

        # Verify continuation
        final_state, _ = state_manager.load_state(workflow_id=mid_state.workflow_id)
        assert "step-3" in final_state.completed_steps
        assert final_state.current_step == "step-4"
        assert final_state.variables["progress"] == 60

    def test_checkpoint_frequency_modes(self, state_manager, checkpoint_manager, temp_dir):
        """Test different checkpoint frequency modes."""
        workflow_state = WorkflowState(
            workflow_id="frequency-test",
            started_at=datetime.now(),
            current_step="step-1",
            completed_steps=["step-0"],
            skipped_steps=[],
            artifacts={},
            variables={},
            status="running",
        )

        step = WorkflowStep(id="step-1", agent="implementer", action="implement", metadata={})
        workflow_path = temp_dir / "workflow.yaml"

        # Test EVERY_STEP
        config = CheckpointConfig(frequency=CheckpointFrequency.EVERY_STEP)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(step, workflow_state) is True

        # Test EVERY_N_STEPS
        config = CheckpointConfig(
            frequency=CheckpointFrequency.EVERY_N_STEPS, interval=2
        )
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(step, workflow_state) is False  # Step 1
        assert manager.should_checkpoint(step, workflow_state) is True  # Step 2

        # Test ON_GATES
        config = CheckpointConfig(frequency=CheckpointFrequency.ON_GATES)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(step, workflow_state, is_gate_step=False) is False
        assert manager.should_checkpoint(step, workflow_state, is_gate_step=True) is True

        # Test MANUAL
        config = CheckpointConfig(frequency=CheckpointFrequency.MANUAL)
        manager = WorkflowCheckpointManager(config=config)
        assert manager.should_checkpoint(step, workflow_state) is False


class TestStatePersistenceConfigIntegration:
    """Integration tests for state persistence configuration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create config manager instance."""
        return StatePersistenceConfigManager(project_root=temp_dir)

    def test_config_manager_with_state_manager(self, config_manager, temp_dir):
        """Test config manager integration with state manager."""
        # Get storage path from config
        storage_path = config_manager.get_storage_path()

        # Create state manager using config storage path
        state_manager = AdvancedStateManager(storage_path, compression=False)

        # Save state
        workflow_state = WorkflowState(
            workflow_id="config-test",
            started_at=datetime.now(),
            status="running",
        )
        state_manager.save_state(workflow_state)

        # Verify state was saved in configured location
        assert storage_path.exists()
        state_files = list(storage_path.glob("*.json"))
        assert len(state_files) > 0

    def test_cleanup_policy_execution(self, config_manager, temp_dir):
        """Test cleanup policy execution with real state files."""
        storage_path = config_manager.get_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)

        # Create state manager
        state_manager = AdvancedStateManager(storage_path, compression=False)

        # Create multiple states
        for i in range(5):
            workflow_state = WorkflowState(
                workflow_id=f"workflow-{i}",
                started_at=datetime.now(),
                status="running",
            )
            state_manager.save_state(workflow_state)

        # Configure cleanup to keep only 2 latest
        config_manager.config.cleanup.enabled = True
        config_manager.config.cleanup.keep_latest = 2

        # Execute cleanup
        result = config_manager.execute_cleanup()

        # Verify cleanup results
        assert result["status"] == "success"
        # Should have deleted some files (keeping only 2)
        remaining = list(storage_path.glob("*.json"))
        assert len(remaining) <= 2

