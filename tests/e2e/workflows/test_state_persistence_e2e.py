"""
End-to-end tests for state persistence and resume.

Epic 12: State Persistence and Resume - Story 12.7
Tests complete workflows with state persistence, recovery, and versioning.
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tapps_agents.workflow.checkpoint_manager import (
    CheckpointConfig,
    CheckpointFrequency,
    WorkflowCheckpointManager,
)
from tapps_agents.workflow.models import WorkflowState
from tapps_agents.workflow.state_manager import AdvancedStateManager
from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager
from tests.fixtures.state_persistence_fixtures import (
    create_corrupted_state_file,
    create_old_version_state_file,
)

pytestmark = pytest.mark.e2e


class TestCompleteWorkflowWithCheckpoints:
    """E2E tests for complete workflow execution with checkpoints."""

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
        """Create checkpoint manager with every step frequency."""
        config = CheckpointConfig(frequency=CheckpointFrequency.EVERY_STEP)
        return WorkflowCheckpointManager(config=config)

    def test_complete_workflow_with_checkpoints(
        self, state_manager, checkpoint_manager, temp_dir
    ):
        """Test complete workflow execution with checkpoints at each step."""
        workflow_path = temp_dir / "workflow.yaml"
        workflow_path.write_text("# Test workflow")

        # Simulate workflow execution with multiple steps
        steps = ["step-0", "step-1", "step-2", "step-3", "step-4"]
        checkpoints_created = []

        for i, step_id in enumerate(steps):
            # Create state for current step
            workflow_state = WorkflowState(
                workflow_id="e2e-workflow",
                started_at=datetime.now(),
                current_step=step_id if i < len(steps) - 1 else None,
                completed_steps=steps[:i],
                skipped_steps=[],
                artifacts={},
                variables={"step_count": i},
                status="running" if i < len(steps) - 1 else "completed",
            )

            # Checkpoint at each step
            if checkpoint_manager.should_checkpoint(None, workflow_state):
                state_manager.save_state(workflow_state, workflow_path)
                checkpoints_created.append(step_id)

        # Verify checkpoints were created
        assert len(checkpoints_created) > 0

        # Verify final state
        final_state, metadata = state_manager.load_state(workflow_id="e2e-workflow")
        assert final_state.status == "completed"
        assert len(final_state.completed_steps) == len(steps) - 1


class TestWorkflowResumeAfterInterruption:
    """E2E tests for workflow resume after interruption."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_workflow_resume_after_interruption(self, temp_dir):
        """Test resuming workflow after interruption."""
        storage_dir = temp_dir / "state"
        state_manager = AdvancedStateManager(storage_dir, compression=False)
        workflow_path = temp_dir / "workflow.yaml"

        # Simulate workflow execution that gets interrupted
        interrupted_state = WorkflowState(
            workflow_id="interrupted-workflow",
            started_at=datetime.now(),
            current_step="step-3",
            completed_steps=["step-0", "step-1", "step-2"],
            skipped_steps=[],
            artifacts={
                "output1": {"path": "output/file1.txt"},
                "output2": {"path": "output/file2.txt"},
            },
            variables={"progress": 60, "data": "important"},
            status="running",
        )

        # Save state before interruption
        state_manager.save_state(interrupted_state, workflow_path)

        # Simulate system restart: create new managers
        new_state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Resume workflow
        resumed_state, metadata = new_state_manager.load_state(
            workflow_id="interrupted-workflow"
        )

        # Verify state was restored
        assert resumed_state.workflow_id == interrupted_state.workflow_id
        assert resumed_state.current_step == interrupted_state.current_step
        assert resumed_state.completed_steps == interrupted_state.completed_steps
        assert resumed_state.variables == interrupted_state.variables

        # Continue execution from checkpoint
        resumed_state.completed_steps.append(resumed_state.current_step)
        resumed_state.current_step = "step-4"
        resumed_state.variables["progress"] = 80

        # Save continued state
        new_state_manager.save_state(resumed_state, workflow_path)

        # Verify continuation
        final_state, _ = new_state_manager.load_state(workflow_id="interrupted-workflow")
        assert "step-3" in final_state.completed_steps
        assert final_state.current_step == "step-4"
        assert final_state.variables["progress"] == 80


class TestStateVersioningAndMigration:
    """E2E tests for state versioning and migration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_state_versioning_and_migration(self, temp_dir):
        """Test state versioning and migration from old format."""
        storage_dir = temp_dir / "state"
        state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Create old version state file
        old_state_file = create_old_version_state_file(
            storage_dir, workflow_id="old-version-workflow", version="1.0"
        )

        # Load old version state (should trigger migration)
        loaded_state, metadata = state_manager.load_state(
            state_file=old_state_file
        )

        # Verify migration occurred
        assert metadata.version == "2.0"  # Should be migrated to current version

        # Verify migrated fields exist
        assert hasattr(loaded_state, "skipped_steps")
        assert hasattr(loaded_state, "artifacts")
        assert hasattr(loaded_state, "variables")

        # Verify migrated fields have default values
        assert loaded_state.skipped_steps == []
        assert loaded_state.artifacts == {}
        assert loaded_state.variables == {}

        # Save migrated state
        workflow_path = temp_dir / "workflow.yaml"
        new_state_file = state_manager.save_state(loaded_state, workflow_path)

        # Verify new state file has current version
        new_loaded_state, new_metadata = state_manager.load_state(
            state_file=new_state_file
        )
        assert new_metadata.version == "2.0"


class TestStateRecoveryFromCorruption:
    """E2E tests for state recovery from corruption."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_state_recovery_from_corruption(self, temp_dir):
        """Test recovery from corrupted state file."""
        storage_dir = temp_dir / "state"
        state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Create corrupted state file
        corrupted_file = create_corrupted_state_file(
            storage_dir, corruption_type="invalid_json"
        )

        # Attempt to load corrupted state
        # Should handle gracefully (either recover or raise appropriate error)
        try:
            loaded_state, metadata = state_manager.load_state(state_file=corrupted_file)
            # If recovery succeeds, verify state is valid
            assert loaded_state is not None
        except Exception as e:
            # If recovery fails, should raise clear error
            assert "corrupt" in str(e).lower() or "invalid" in str(e).lower()

    def test_state_recovery_from_missing_fields(self, temp_dir):
        """Test recovery from state file with missing required fields."""
        storage_dir = temp_dir / "state"
        state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Create state file with missing fields
        corrupted_file = create_corrupted_state_file(
            storage_dir, corruption_type="missing_fields"
        )

        # Attempt to load
        try:
            loaded_state, metadata = state_manager.load_state(state_file=corrupted_file)
            # If recovery succeeds, missing fields should have defaults
            assert loaded_state is not None
        except Exception as e:
            # Should raise validation error
            assert "missing" in str(e).lower() or "required" in str(e).lower()


class TestStateCleanupE2E:
    """E2E tests for state cleanup policies."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_state_cleanup_retention_policy(self, temp_dir):
        """Test state cleanup with retention policy."""
        storage_dir = temp_dir / "state"
        config_manager = StatePersistenceConfigManager(project_root=temp_dir)
        state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Create old state files
        old_time = datetime.now() - timedelta(days=31)
        old_state = WorkflowState(
            workflow_id="old-workflow",
            started_at=old_time,
            status="completed",
        )
        state_manager.save_state(old_state)

        # Make file appear old
        state_files = list(storage_dir.glob("*.json"))
        if state_files:
            old_time_stamp = old_time.timestamp()
            import os
            os.utime(state_files[0], (old_time_stamp, old_time_stamp))

        # Create recent state
        recent_state = WorkflowState(
            workflow_id="recent-workflow",
            started_at=datetime.now(),
            status="running",
        )
        state_manager.save_state(recent_state)

        # Configure cleanup with 30-day retention
        config_manager.config.cleanup.enabled = True
        config_manager.config.cleanup.retention_days = 30
        config_manager.config.cleanup.keep_latest = 1

        # Execute cleanup
        result = config_manager.execute_cleanup()

        # Verify cleanup results
        assert result["status"] == "success"
        assert result["deleted"] >= 1

        # Verify recent state is kept
        remaining = list(storage_dir.glob("*.json"))
        assert len(remaining) >= 1

    def test_state_cleanup_size_limit(self, temp_dir):
        """Test state cleanup with size limit policy."""
        storage_dir = temp_dir / "state"
        config_manager = StatePersistenceConfigManager(project_root=temp_dir)
        state_manager = AdvancedStateManager(storage_dir, compression=False)

        # Create multiple large state files
        for i in range(3):
            state = WorkflowState(
                workflow_id=f"large-workflow-{i}",
                started_at=datetime.now(),
                status="running",
                variables={f"key{j}": "x" * 1000 for j in range(100)},  # Large variables
            )
            state_manager.save_state(state)

        # Configure cleanup with 1MB limit
        config_manager.config.cleanup.enabled = True
        config_manager.config.cleanup.max_size_mb = 1
        config_manager.config.cleanup.keep_latest = 1

        # Execute cleanup
        result = config_manager.execute_cleanup()

        # Verify cleanup occurred
        assert result["status"] == "success"
        assert result["freed_mb"] > 0

        # Verify total size is under limit
        total_size = sum(f.stat().st_size for f in storage_dir.glob("*.json"))
        assert total_size <= 1 * 1024 * 1024  # 1MB

