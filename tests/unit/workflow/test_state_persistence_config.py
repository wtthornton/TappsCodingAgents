"""
Unit tests for State Persistence Configuration Manager.

Epic 12: State Persistence and Resume - Story 12.7
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

from tapps_agents.core.config import (
    StatePersistenceConfig,
)
from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager

pytestmark = pytest.mark.unit


class TestStatePersistenceConfigManager:
    """Tests for StatePersistenceConfigManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create a test config file."""
        config_path = temp_dir / ".tapps-agents" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_path

    @pytest.fixture
    def manager(self, temp_dir):
        """Create StatePersistenceConfigManager instance."""
        return StatePersistenceConfigManager(project_root=temp_dir)

    def test_initialization_with_defaults(self, manager):
        """Test manager initialization with default config."""
        assert manager.config is not None
        assert manager.config.enabled is True
        assert manager.config.storage_location == ".tapps-agents/workflow-state"

    def test_get_storage_path(self, manager, temp_dir):
        """Test getting storage path."""
        storage_path = manager.get_storage_path()
        assert storage_path == temp_dir / ".tapps-agents" / "workflow-state"
        assert storage_path.exists()

    def test_get_storage_path_custom_location(self, temp_dir):
        """Test getting storage path with custom location."""
        custom_config = StatePersistenceConfig(
            storage_location="custom/state/location"
        )
        manager = StatePersistenceConfigManager(project_root=temp_dir)
        manager.config = custom_config

        storage_path = manager.get_storage_path()
        assert storage_path == temp_dir / "custom" / "state" / "location"
        assert storage_path.exists()

    def test_validate_configuration_valid(self, manager):
        """Test validation of valid configuration."""
        assert manager.validate_configuration() is True

    def test_validate_configuration_invalid_mode(self, manager):
        """Test validation fails for invalid checkpoint mode."""
        manager.config.checkpoint.mode = "invalid_mode"
        assert manager.validate_configuration() is False

    def test_validate_configuration_invalid_schedule(self, manager):
        """Test validation fails for invalid cleanup schedule."""
        manager.config.cleanup.cleanup_schedule = "invalid_schedule"
        assert manager.validate_configuration() is False

    def test_validate_configuration_unwritable_storage(self, manager, temp_dir):
        """Test validation fails for unwritable storage location."""
        # Create a file where storage should be
        storage_path = temp_dir / ".tapps-agents" / "workflow-state"
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text("not a directory")

        manager.config.storage_location = ".tapps-agents/workflow-state"
        assert manager.validate_configuration() is False

    def test_reload_configuration_success(self, manager, config_file):
        """Test successful configuration reload."""
        # Create initial config
        initial_config = {
            "workflow": {
                "state_persistence": {
                    "enabled": True,
                    "storage_location": ".tapps-agents/workflow-state",
                    "checkpoint": {"mode": "every_step", "enabled": True},
                    "cleanup": {"enabled": True, "cleanup_schedule": "daily"},
                }
            }
        }
        config_file.write_text(yaml.dump(initial_config))

        # Reload should succeed
        result = manager.reload_configuration()
        assert result is True

    def test_reload_configuration_invalid(self, manager, config_file):
        """Test reload fails for invalid configuration."""
        # Create invalid config
        invalid_config = {
            "workflow": {
                "state_persistence": {
                    "checkpoint": {"mode": "invalid_mode"},
                }
            }
        }
        config_file.write_text(yaml.dump(invalid_config))

        # Reload should fail and revert
        old_config = manager.config
        result = manager.reload_configuration()
        assert result is False
        assert manager.config == old_config

    def test_migrate_configuration(self, manager):
        """Test configuration migration from old format."""
        old_config = {
            "persistence_enabled": True,
            "storage_location": "old/location",
            "checkpoint_frequency": "every_n_steps",
            "checkpoint_interval": 5,
            "checkpoint_enabled": True,
            "cleanup_enabled": True,
            "retention_days": 30,
            "max_size_mb": 100,
            "cleanup_schedule": "weekly",
            "keep_latest": 5,
        }

        migrated = manager.migrate_configuration(old_config)

        assert migrated.enabled is True
        assert migrated.storage_location == "old/location"
        assert migrated.checkpoint.mode == "every_n_steps"
        assert migrated.checkpoint.interval == 5
        assert migrated.cleanup.retention_days == 30
        assert migrated.cleanup.max_size_mb == 100
        assert migrated.cleanup.cleanup_schedule == "weekly"
        assert migrated.cleanup.keep_latest == 5

    def test_should_run_cleanup_daily(self, manager):
        """Test should_run_cleanup for daily schedule."""
        manager.config.cleanup.enabled = True
        manager.config.cleanup.cleanup_schedule = "daily"
        assert manager.should_run_cleanup() is True

    def test_should_run_cleanup_manual(self, manager):
        """Test should_run_cleanup for manual schedule."""
        manager.config.cleanup.enabled = True
        manager.config.cleanup.cleanup_schedule = "manual"
        assert manager.should_run_cleanup() is False

    def test_should_run_cleanup_disabled(self, manager):
        """Test should_run_cleanup when disabled."""
        manager.config.cleanup.enabled = False
        assert manager.should_run_cleanup() is False

    def test_execute_cleanup_disabled(self, manager):
        """Test cleanup execution when disabled."""
        manager.config.cleanup.enabled = False
        result = manager.execute_cleanup()
        assert result["status"] == "disabled"
        assert result["deleted"] == 0

    def test_execute_cleanup_no_storage(self, manager):
        """Test cleanup execution when storage doesn't exist."""
        manager.config.cleanup.enabled = True
        manager.config.storage_location = "nonexistent/path"
        result = manager.execute_cleanup()
        assert result["status"] == "no_storage"

    def test_execute_cleanup_retention_policy(self, manager, temp_dir):
        """Test cleanup execution with retention policy."""
        storage_path = manager.get_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)

        # Create old state files
        old_file = storage_path / "old-state.json"
        old_file.write_text('{"workflow_id": "old", "saved_at": "2020-01-01T00:00:00"}')
        # Make file appear old
        old_time = (datetime.now() - timedelta(days=31)).timestamp()
        old_file.touch()
        import os
        os.utime(old_file, (old_time, old_time))

        # Create recent state file
        recent_file = storage_path / "recent-state.json"
        recent_file.write_text('{"workflow_id": "recent", "saved_at": "2025-01-27T00:00:00"}')

        manager.config.cleanup.enabled = True
        manager.config.cleanup.retention_days = 30
        manager.config.cleanup.keep_latest = 1

        result = manager.execute_cleanup()

        assert result["status"] == "success"
        assert result["deleted"] >= 1
        assert not old_file.exists() or recent_file.exists()

    def test_execute_cleanup_max_size_policy(self, manager, temp_dir):
        """Test cleanup execution with max size policy."""
        storage_path = manager.get_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)

        # Create large state files
        for i in range(3):
            state_file = storage_path / f"state-{i}.json"
            # Create a file larger than 1MB
            state_file.write_text("x" * (2 * 1024 * 1024))  # 2MB

        manager.config.cleanup.enabled = True
        manager.config.cleanup.max_size_mb = 2  # 2MB limit
        manager.config.cleanup.keep_latest = 1

        result = manager.execute_cleanup()

        assert result["status"] == "success"
        assert result["deleted"] >= 1
        # Verify total size is under limit
        total_size = sum(f.stat().st_size for f in storage_path.glob("*.json"))
        assert total_size <= 2 * 1024 * 1024

    def test_execute_cleanup_keep_latest(self, manager, temp_dir):
        """Test cleanup execution keeps latest N states."""
        storage_path = manager.get_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)

        # Create multiple state files
        for i in range(5):
            state_file = storage_path / f"state-{i}.json"
            state_file.write_text(f'{{"workflow_id": "workflow-{i}"}}')
            # Stagger modification times
            import time
            time.sleep(0.01)

        manager.config.cleanup.enabled = True
        manager.config.cleanup.keep_latest = 2

        manager.execute_cleanup()

        # Should keep at least 2 files
        remaining = list(storage_path.glob("*.json"))
        assert len(remaining) >= 2

    def test_get_config_summary(self, manager):
        """Test getting configuration summary."""
        summary = manager.get_config_summary()

        assert "persistence_enabled" in summary
        assert "storage_location" in summary
        assert "format" in summary
        assert "checkpoint" in summary
        assert "cleanup" in summary
        assert summary["checkpoint"]["mode"] == manager.config.checkpoint.mode

    def test_get_config_summary_no_config(self, temp_dir):
        """Test getting config summary when config is None."""
        manager = StatePersistenceConfigManager(project_root=temp_dir)
        manager.config = None
        summary = manager.get_config_summary()
        assert summary["status"] == "no_config"

