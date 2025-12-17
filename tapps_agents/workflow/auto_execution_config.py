"""
Auto-Execution Configuration Management.

Provides configuration management, feature flags, validation, migration,
and runtime reload for Background Agent auto-execution.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Configuration version for migration tracking
CONFIG_VERSION = "1.0"


@dataclass
class RetryConfig:
    """Retry configuration for auto-execution."""

    enabled: bool = True
    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    initial_delay_seconds: float = 1.0


@dataclass
class PollingConfig:
    """Polling configuration for auto-execution."""

    enabled: bool = True
    interval_seconds: float = 5.0
    timeout_seconds: float = 3600.0


@dataclass
class FeatureFlags:
    """Feature flags for auto-execution features."""

    artifact_detection: bool = True
    status_tracking: bool = True
    error_handling: bool = True
    metrics_collection: bool = True
    audit_logging: bool = True


@dataclass
class AutoExecutionConfig:
    """Configuration for Background Agent auto-execution."""

    enabled: bool = False
    retry: RetryConfig = field(default_factory=RetryConfig)
    polling: PollingConfig = field(default_factory=PollingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    version: str = CONFIG_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "retry": {
                "enabled": self.retry.enabled,
                "max_attempts": self.retry.max_attempts,
                "backoff_multiplier": self.retry.backoff_multiplier,
                "initial_delay_seconds": self.retry.initial_delay_seconds,
            },
            "polling": {
                "enabled": self.polling.enabled,
                "interval_seconds": self.polling.interval_seconds,
                "timeout_seconds": self.polling.timeout_seconds,
            },
            "features": {
                "artifact_detection": self.features.artifact_detection,
                "status_tracking": self.features.status_tracking,
                "error_handling": self.features.error_handling,
                "metrics_collection": self.features.metrics_collection,
                "audit_logging": self.features.audit_logging,
            },
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoExecutionConfig:
        """Create from dictionary."""
        retry_data = data.get("retry", {})
        polling_data = data.get("polling", {})
        features_data = data.get("features", {})

        return cls(
            enabled=data.get("enabled", False),
            retry=RetryConfig(
                enabled=retry_data.get("enabled", True),
                max_attempts=retry_data.get("max_attempts", 3),
                backoff_multiplier=retry_data.get("backoff_multiplier", 2.0),
                initial_delay_seconds=retry_data.get("initial_delay_seconds", 1.0),
            ),
            polling=PollingConfig(
                enabled=polling_data.get("enabled", True),
                interval_seconds=polling_data.get("interval_seconds", 5.0),
                timeout_seconds=polling_data.get("timeout_seconds", 3600.0),
            ),
            features=FeatureFlags(
                artifact_detection=features_data.get("artifact_detection", True),
                status_tracking=features_data.get("status_tracking", True),
                error_handling=features_data.get("error_handling", True),
                metrics_collection=features_data.get("metrics_collection", True),
                audit_logging=features_data.get("audit_logging", True),
            ),
            version=data.get("version", CONFIG_VERSION),
        )


class AutoExecutionConfigManager:
    """Manages auto-execution configuration with validation, migration, and reload."""

    def __init__(self, config_path: Path | None = None, project_root: Path | None = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (defaults to .tapps-agents/config.yaml)
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / ".tapps-agents"
        self.config_path = config_path or (self.config_dir / "auto_execution_config.yaml")

        # Cache for configuration
        self._config: AutoExecutionConfig | None = None
        self._config_file_mtime: float | None = None

    def load(self, validate: bool = True) -> AutoExecutionConfig:
        """
        Load configuration from file.

        Args:
            validate: If True, validate configuration after loading

        Returns:
            AutoExecutionConfig instance

        Raises:
            ValueError: If configuration is invalid
        """
        # Check if config file exists
        if not self.config_path.exists():
            logger.info(f"Configuration file not found at {self.config_path}, using defaults")
            self._config = AutoExecutionConfig()
            return self._config

        # Check if file has changed (for reload detection)
        current_mtime = self.config_path.stat().st_mtime
        if (
            self._config is not None
            and self._config_file_mtime == current_mtime
        ):
            return self._config

        # Load configuration
        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Extract auto_execution section
            auto_exec_data = data.get("auto_execution", {})

            # Check version and migrate if needed
            version = auto_exec_data.get("version", "0.0")
            if version != CONFIG_VERSION:
                logger.info(f"Migrating configuration from version {version} to {CONFIG_VERSION}")
                auto_exec_data = self._migrate_config(auto_exec_data, version)

            # Create config from data
            self._config = AutoExecutionConfig.from_dict(auto_exec_data)
            self._config_file_mtime = current_mtime

            # Validate if requested
            if validate:
                self.validate(self._config)

            logger.info(f"Loaded auto-execution configuration from {self.config_path}")
            return self._config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return defaults on error
            self._config = AutoExecutionConfig()
            return self._config

    def save(self, config: AutoExecutionConfig | None = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save (uses cached config if None)
        """
        config = config or self._config or AutoExecutionConfig()

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing config to preserve other sections
        existing_data: dict[str, Any] = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    existing_data = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Update auto_execution section
        existing_data["auto_execution"] = config.to_dict()

        # Save to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)

        # Update cache
        self._config = config
        if self.config_path.exists():
            self._config_file_mtime = self.config_path.stat().st_mtime

        logger.info(f"Saved auto-execution configuration to {self.config_path}")

    def validate(self, config: AutoExecutionConfig | None = None) -> None:
        """
        Validate configuration.

        Args:
            config: Configuration to validate (uses cached config if None)

        Raises:
            ValueError: If configuration is invalid
        """
        config = config or self._config or AutoExecutionConfig()

        errors: list[str] = []

        # Validate retry configuration
        if config.retry.max_attempts < 1:
            errors.append("retry.max_attempts must be >= 1")
        if config.retry.backoff_multiplier < 1.0:
            errors.append("retry.backoff_multiplier must be >= 1.0")
        if config.retry.initial_delay_seconds < 0:
            errors.append("retry.initial_delay_seconds must be >= 0")

        # Validate polling configuration
        if config.polling.interval_seconds <= 0:
            errors.append("polling.interval_seconds must be > 0")
        if config.polling.timeout_seconds <= 0:
            errors.append("polling.timeout_seconds must be > 0")
        if config.polling.timeout_seconds < config.polling.interval_seconds:
            errors.append("polling.timeout_seconds must be >= polling.interval_seconds")

        # Validate feature flag combinations
        if config.enabled and not config.polling.enabled:
            errors.append("polling must be enabled when auto_execution is enabled")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    def reload(self) -> AutoExecutionConfig:
        """
        Reload configuration from file.

        Returns:
            Reloaded AutoExecutionConfig instance

        Raises:
            ValueError: If reloaded configuration is invalid
        """
        # Clear cache to force reload
        self._config = None
        self._config_file_mtime = None

        # Load and validate
        return self.load(validate=True)

    def _migrate_config(self, data: dict[str, Any], from_version: str) -> dict[str, Any]:
        """
        Migrate configuration from old version to current version.

        Args:
            data: Configuration data from old version
            from_version: Version of the configuration

        Returns:
            Migrated configuration data
        """
        # For now, just ensure version is set
        # Future migrations can be added here
        if from_version == "0.0" or from_version < CONFIG_VERSION:
            # Migration from pre-versioned config
            # Ensure all required fields are present
            migrated = {
                "enabled": data.get("enabled", False),
                "retry": data.get("retry", {}),
                "polling": data.get("polling", {}),
                "features": data.get("features", {}),
                "version": CONFIG_VERSION,
            }
            return migrated

        return data

    def get_feature_flag(self, flag_name: str, workflow_override: dict[str, Any] | None = None) -> bool:
        """
        Get feature flag value with workflow override support.

        Args:
            flag_name: Name of the feature flag
            workflow_override: Optional workflow-level override

        Returns:
            Feature flag value
        """
        config = self.load()

        # Check workflow override first
        if workflow_override and "auto_execution" in workflow_override:
            workflow_config = workflow_override["auto_execution"]
            if isinstance(workflow_config, dict) and "features" in workflow_config:
                workflow_features = workflow_config["features"]
                if isinstance(workflow_features, dict) and flag_name in workflow_features:
                    return bool(workflow_features[flag_name])

        # Fall back to global config
        if hasattr(config.features, flag_name):
            return getattr(config.features, flag_name)

        # Default to False for unknown flags
        logger.warning(f"Unknown feature flag: {flag_name}")
        return False

