"""
Unit tests for auto-execution configuration management.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tapps_agents.workflow.auto_execution_config import (
    AutoExecutionConfig,
    AutoExecutionConfigManager,
    FeatureFlags,
    PollingConfig,
    RetryConfig,
)


def test_retry_config_defaults():
    """Test RetryConfig defaults."""
    retry = RetryConfig()
    assert retry.enabled is True
    assert retry.max_attempts == 3
    assert retry.backoff_multiplier == 2.0
    assert retry.initial_delay_seconds == 1.0


def test_polling_config_defaults():
    """Test PollingConfig defaults."""
    polling = PollingConfig()
    assert polling.enabled is True
    assert polling.interval_seconds == 5.0
    assert polling.timeout_seconds == 3600.0


def test_feature_flags_defaults():
    """Test FeatureFlags defaults."""
    flags = FeatureFlags()
    assert flags.artifact_detection is True
    assert flags.status_tracking is True
    assert flags.error_handling is True
    assert flags.metrics_collection is True
    assert flags.audit_logging is True


def test_auto_execution_config_defaults():
    """Test AutoExecutionConfig defaults."""
    config = AutoExecutionConfig()
    assert config.enabled is False
    assert isinstance(config.retry, RetryConfig)
    assert isinstance(config.polling, PollingConfig)
    assert isinstance(config.features, FeatureFlags)
    assert config.version == "1.0"


def test_auto_execution_config_to_dict():
    """Test AutoExecutionConfig serialization."""
    config = AutoExecutionConfig(enabled=True)
    data = config.to_dict()
    assert data["enabled"] is True
    assert "retry" in data
    assert "polling" in data
    assert "features" in data
    assert data["version"] == "1.0"


def test_auto_execution_config_from_dict():
    """Test AutoExecutionConfig deserialization."""
    data = {
        "enabled": True,
        "retry": {"enabled": False, "max_attempts": 5},
        "polling": {"interval_seconds": 10.0},
        "features": {"artifact_detection": False},
        "version": "1.0",
    }
    config = AutoExecutionConfig.from_dict(data)
    assert config.enabled is True
    assert config.retry.enabled is False
    assert config.retry.max_attempts == 5
    assert config.polling.interval_seconds == 10.0
    assert config.features.artifact_detection is False


def test_config_manager_load_defaults(tmp_path: Path):
    """Test loading defaults when config file doesn't exist."""
    manager = AutoExecutionConfigManager(config_path=tmp_path / "nonexistent.yaml")
    config = manager.load()
    assert config.enabled is False
    assert config.version == "1.0"


def test_config_manager_load_existing(tmp_path: Path):
    """Test loading existing configuration."""
    config_path = tmp_path / "config.yaml"
    config_data = {
        "auto_execution": {
            "enabled": True,
            "retry": {"max_attempts": 5},
            "polling": {"interval_seconds": 2.0},
            "version": "1.0",
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    manager = AutoExecutionConfigManager(config_path=config_path)
    config = manager.load()
    assert config.enabled is True
    assert config.retry.max_attempts == 5
    assert config.polling.interval_seconds == 2.0


def test_config_manager_save(tmp_path: Path):
    """Test saving configuration."""
    config_path = tmp_path / "config.yaml"
    manager = AutoExecutionConfigManager(config_path=config_path)
    config = AutoExecutionConfig(enabled=True)
    manager.save(config)

    assert config_path.exists()
    with open(config_path) as f:
        data = yaml.safe_load(f)
        assert data["auto_execution"]["enabled"] is True


def test_config_manager_validate_valid():
    """Test validation of valid configuration."""
    manager = AutoExecutionConfigManager()
    config = AutoExecutionConfig(
        enabled=True,
        polling=PollingConfig(interval_seconds=5.0, timeout_seconds=3600.0),
    )
    # Should not raise
    manager.validate(config)


def test_config_manager_validate_invalid():
    """Test validation of invalid configuration."""
    manager = AutoExecutionConfigManager()
    config = AutoExecutionConfig(
        enabled=True,
        polling=PollingConfig(interval_seconds=-1.0),  # Invalid
    )
    with pytest.raises(ValueError, match="polling.interval_seconds"):
        manager.validate(config)


def test_config_manager_reload(tmp_path: Path):
    """Test configuration reload."""
    config_path = tmp_path / "config.yaml"
    manager = AutoExecutionConfigManager(config_path=config_path)

    # Initial config
    config1 = AutoExecutionConfig(enabled=False)
    manager.save(config1)
    loaded1 = manager.load()
    assert loaded1.enabled is False

    # Update config file directly
    config_data = {"auto_execution": {"enabled": True, "version": "1.0"}}
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    # Reload
    loaded2 = manager.reload()
    assert loaded2.enabled is True


def test_config_manager_get_feature_flag():
    """Test feature flag evaluation."""
    manager = AutoExecutionConfigManager()
    config = AutoExecutionConfig(
        features=FeatureFlags(artifact_detection=True, status_tracking=False)
    )
    manager._config = config

    assert manager.get_feature_flag("artifact_detection") is True
    assert manager.get_feature_flag("status_tracking") is False


def test_config_manager_get_feature_flag_workflow_override():
    """Test feature flag with workflow override."""
    manager = AutoExecutionConfigManager()
    config = AutoExecutionConfig(features=FeatureFlags(artifact_detection=False))
    manager._config = config

    workflow_override = {
        "auto_execution": {
            "features": {"artifact_detection": True}  # Override
        }
    }

    assert manager.get_feature_flag("artifact_detection", workflow_override) is True


def test_config_migration(tmp_path: Path):
    """Test configuration migration."""
    config_path = tmp_path / "config.yaml"
    # Old version config
    config_data = {
        "auto_execution": {
            "enabled": True,
            "version": "0.0",  # Old version
        }
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    manager = AutoExecutionConfigManager(config_path=config_path)
    config = manager.load()
    # Should be migrated to version 1.0
    assert config.version == "1.0"
    assert config.enabled is True

