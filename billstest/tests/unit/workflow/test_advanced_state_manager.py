"""
Tests for Advanced Workflow State Manager.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.workflow.models import WorkflowState
from tapps_agents.workflow.state_manager import (
    CURRENT_STATE_VERSION,
    AdvancedStateManager,
    StateMigrator,
    StateValidator,
)


class TestStateValidator:
    """Tests for StateValidator."""

    def test_calculate_checksum(self):
        """Test checksum calculation."""
        state_data = {
            "workflow_id": "test-workflow",
            "current_step": "step1",
            "completed_steps": ["step0"],
            "skipped_steps": [],
            "status": "running",
            "variables": {"key": "value"},
        }

        checksum = StateValidator.calculate_checksum(state_data)
        assert len(checksum) == 64  # SHA256 hex digest
        assert isinstance(checksum, str)

        # Same data should produce same checksum
        checksum2 = StateValidator.calculate_checksum(state_data)
        assert checksum == checksum2

    def test_validate_state_valid(self):
        """Test validation of valid state."""
        state_data = {
            "workflow_id": "test-workflow",
            "started_at": datetime.now().isoformat(),
            "current_step": "step1",
            "completed_steps": ["step0"],
            "skipped_steps": [],
            "status": "running",
            "variables": {},
        }

        is_valid, error = StateValidator.validate_state(state_data)
        assert is_valid
        assert error is None

    def test_validate_state_missing_field(self):
        """Test validation fails for missing required field."""
        state_data = {
            "workflow_id": "test-workflow",
            # Missing started_at
            "status": "running",
        }

        is_valid, error = StateValidator.validate_state(state_data)
        assert not is_valid
        assert "Missing required field" in error

    def test_validate_state_invalid_status(self):
        """Test validation fails for invalid status."""
        state_data = {
            "workflow_id": "test-workflow",
            "started_at": datetime.now().isoformat(),
            "status": "invalid_status",
        }

        is_valid, error = StateValidator.validate_state(state_data)
        assert not is_valid
        assert "Invalid status" in error

    def test_validate_state_checksum_mismatch(self):
        """Test validation fails for checksum mismatch."""
        state_data = {
            "workflow_id": "test-workflow",
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        expected_checksum = "wrong_checksum"
        is_valid, error = StateValidator.validate_state(state_data, expected_checksum)
        assert not is_valid
        assert "Checksum mismatch" in error


class TestStateMigrator:
    """Tests for StateMigrator."""

    def test_migrate_same_version(self):
        """Test migration with same version does nothing."""
        state_data = {"workflow_id": "test", "status": "running"}
        migrated = StateMigrator.migrate_state(state_data, "2.0", "2.0")
        assert migrated == state_data

    def test_migrate_1_0_to_2_0(self):
        """Test migration from version 1.0 to 2.0."""
        state_data = {
            "workflow_id": "test",
            "started_at": datetime.now().isoformat(),
            "status": "running",
            # Missing fields that should be added
        }

        migrated = StateMigrator.migrate_state(state_data, "1.0", "2.0")

        assert "skipped_steps" in migrated
        assert "artifacts" in migrated
        assert "variables" in migrated
        assert migrated["skipped_steps"] == []
        assert migrated["artifacts"] == {}
        assert migrated["variables"] == {}


class TestAdvancedStateManager:
    """Tests for AdvancedStateManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create state manager instance."""
        return AdvancedStateManager(temp_dir / "state", compression=False)

    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        return WorkflowState(
            workflow_id="test-workflow",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=["step0"],
            skipped_steps=[],
            artifacts={},
            variables={"key": "value"},
            status="running",
        )

    def test_save_state(self, state_manager, sample_state, temp_dir):
        """Test saving state."""
        workflow_path = temp_dir / "workflow.yaml"
        state_path = state_manager.save_state(sample_state, workflow_path)

        assert state_path.exists()
        assert state_path.suffix == ".json"

        # Check metadata was created
        metadata_path = temp_dir / "state" / f"{sample_state.workflow_id}.meta.json"
        assert metadata_path.exists()

        # Check last pointer was created
        last_path = temp_dir / "state" / "last.json"
        assert last_path.exists()

        # Check history was created
        history_files = list((temp_dir / "state" / "history").glob("*.json"))
        assert len(history_files) > 0

    def test_load_state(self, state_manager, sample_state, temp_dir):
        """Test loading state."""
        workflow_path = temp_dir / "workflow.yaml"

        # Save state
        state_manager.save_state(sample_state, workflow_path)

        # Load state
        loaded_state, metadata = state_manager.load_state(
            workflow_id=sample_state.workflow_id
        )

        assert loaded_state.workflow_id == sample_state.workflow_id
        assert loaded_state.current_step == sample_state.current_step
        assert loaded_state.completed_steps == sample_state.completed_steps
        assert loaded_state.status == sample_state.status
        assert metadata.version == CURRENT_STATE_VERSION

    def test_load_last_state(self, state_manager, sample_state, temp_dir):
        """Test loading last state."""
        workflow_path = temp_dir / "workflow.yaml"

        # Save state
        state_manager.save_state(sample_state, workflow_path)

        # Load last state
        loaded_state, metadata = state_manager.load_state()

        assert loaded_state.workflow_id == sample_state.workflow_id
        assert metadata.workflow_id == sample_state.workflow_id

    def test_list_states(self, state_manager, temp_dir):
        """Test listing states."""
        # Save multiple states
        for i in range(3):
            state = WorkflowState(
                workflow_id=f"workflow-{i}",
                started_at=datetime.now(),
                status="running",
            )
            state_manager.save_state(state)

        # List all states
        states = state_manager.list_states()
        assert len(states) >= 3

        # List states for specific workflow
        workflow_states = state_manager.list_states(workflow_id="workflow-0")
        assert len(workflow_states) > 0
        assert all(s.get("workflow_id") == "workflow-0" for s in workflow_states)

    def test_state_validation_on_load(self, state_manager, sample_state, temp_dir):
        """Test state validation when loading."""
        workflow_path = temp_dir / "workflow.yaml"

        # Save state
        state_manager.save_state(sample_state, workflow_path)

        # Load with validation
        loaded_state, metadata = state_manager.load_state(validate=True)
        assert loaded_state.workflow_id == sample_state.workflow_id

    def test_compression(self, temp_dir):
        """Test state compression."""
        compressed_manager = AdvancedStateManager(temp_dir / "state", compression=True)
        state = WorkflowState(
            workflow_id="test",
            started_at=datetime.now(),
            status="running",
        )

        state_path = compressed_manager.save_state(state)
        assert state_path.suffix == ".gz" or state_path.name.endswith(".gz")

        # Load compressed state
        loaded_state, metadata = compressed_manager.load_state(workflow_id="test")
        assert loaded_state.workflow_id == "test"
        assert metadata.compression is True
