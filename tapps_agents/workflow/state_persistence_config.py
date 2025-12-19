"""
State Persistence Configuration Management.

Epic 12: State Persistence and Resume - Story 12.6
Manages configuration for state persistence, checkpointing, and cleanup policies.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.config import StatePersistenceConfig, load_config

logger = logging.getLogger(__name__)

# Configuration version for migration
CONFIG_VERSION = "1.0"


class StatePersistenceConfigManager:
    """
    Manages state persistence configuration with validation, migration, and reload.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize configuration manager.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.config: StatePersistenceConfig | None = None
        self.config_version: str = CONFIG_VERSION
        self._config_file: Path | None = None
        self._file_watcher: Any | None = None  # For future file watching implementation
        self._load_configuration()  # Ignore return value on init - defaults are OK

    def _load_configuration(self) -> bool:
        """Load configuration from project config.
        
        Returns:
            True if config was loaded successfully, False if defaults were used or config is invalid
        """
        try:
            # Look for config file in project root
            config_path = self.project_root / ".tapps-agents" / "config.yaml"
            if config_path.exists():
                project_config = load_config(config_path)
            else:
                project_config = load_config()
            self.config = project_config.workflow.state_persistence
            
            # Validate immediately after loading - if invalid, use defaults
            # Note: We validate here to catch invalid values early
            if not self.validate_configuration():
                logger.warning(f"Loaded configuration is invalid (mode: {self.config.checkpoint.mode if self.config else 'None'}), using defaults")
                from ..core.config import StatePersistenceConfig
                self.config = StatePersistenceConfig()
                return False
            
            logger.info("State persistence configuration loaded")
            return True
        except Exception as e:
            logger.warning(f"Failed to load state persistence config: {e}, using defaults")
            from ..core.config import StatePersistenceConfig
            self.config = StatePersistenceConfig()
            return False

    def reload_configuration(self) -> bool:
        """
        Reload configuration from file.

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            old_config = self.config
            config_loaded = self._load_configuration()
            
            # If we fell back to defaults or validation failed, that's a failure for reload
            if not config_loaded:
                logger.error("Failed to load or validate configuration, reverting to previous")
                self.config = old_config
                return False
            
            logger.info("State persistence configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            if old_config:
                self.config = old_config
            return False

    def validate_configuration(self) -> bool:
        """
        Validate current configuration.

        Returns:
            True if configuration is valid
        """
        if self.config is None:
            return False
        
        # Validate checkpoint frequency mode
        valid_modes = ["every_step", "every_n_steps", "on_gates", "time_based", "manual"]
        if self.config.checkpoint.mode not in valid_modes:
            logger.error(f"Invalid checkpoint mode: {self.config.checkpoint.mode}")
            return False
        
        # Validate storage location is writable
        storage_path = self.project_root / self.config.storage_location
        try:
            storage_path.mkdir(parents=True, exist_ok=True)
            # Test write
            test_file = storage_path / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            logger.error(f"Storage location is not writable: {e}")
            return False
        
        # Validate cleanup schedule
        valid_schedules = ["daily", "weekly", "monthly", "on_startup", "manual"]
        if self.config.cleanup.cleanup_schedule not in valid_schedules:
            logger.error(f"Invalid cleanup schedule: {self.config.cleanup.cleanup_schedule}")
            return False
        
        return True

    def migrate_configuration(self, old_config: dict[str, Any]) -> StatePersistenceConfig:
        """
        Migrate old configuration format to new format.

        Args:
            old_config: Old configuration dictionary

        Returns:
            Migrated StatePersistenceConfig
        """
        from ..core.config import (
            CheckpointFrequencyConfig,
            StateCleanupPolicyConfig,
            StatePersistenceConfig,
        )

        # Extract checkpoint config
        checkpoint_mode = old_config.get("checkpoint_frequency", "every_step")
        checkpoint_interval = old_config.get("checkpoint_interval", 1)
        checkpoint_enabled = old_config.get("checkpoint_enabled", True)

        checkpoint_config = CheckpointFrequencyConfig(
            mode=checkpoint_mode,
            interval=checkpoint_interval,
            enabled=checkpoint_enabled,
        )

        # Extract cleanup config
        cleanup_enabled = old_config.get("cleanup_enabled", True)
        retention_days = old_config.get("retention_days")
        max_size_mb = old_config.get("max_size_mb")
        cleanup_schedule = old_config.get("cleanup_schedule", "daily")
        keep_latest = old_config.get("keep_latest", 10)

        cleanup_config = StateCleanupPolicyConfig(
            enabled=cleanup_enabled,
            retention_days=retention_days,
            max_size_mb=max_size_mb,
            cleanup_schedule=cleanup_schedule,
            keep_latest=keep_latest,
        )

        # Build full config
        return StatePersistenceConfig(
            enabled=old_config.get("persistence_enabled", True),
            storage_location=old_config.get("storage_location", ".tapps-agents/workflow-state"),
            format=old_config.get("format", "json"),
            compression=old_config.get("compression", False),
            checkpoint=checkpoint_config,
            cleanup=cleanup_config,
        )

    def get_storage_path(self) -> Path:
        """
        Get the storage path for workflow state.

        Returns:
            Path to state storage directory
        """
        if self.config is None:
            path = self.project_root / ".tapps-agents" / "workflow-state"
        else:
            path = self.project_root / self.config.storage_location
        
        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        return path

    def should_run_cleanup(self) -> bool:
        """
        Check if cleanup should run based on schedule.

        Returns:
            True if cleanup should run
        """
        if not self.config or not self.config.cleanup.enabled:
            return False

        schedule = self.config.cleanup.cleanup_schedule
        if schedule == "manual":
            return False
        if schedule == "on_startup":
            # This would be checked at startup, not here
            return False

        # For daily/weekly/monthly, we'd check last cleanup time
        # For now, return True if schedule is not manual/on_startup
        return schedule in ["daily", "weekly", "monthly"]

    def execute_cleanup(self) -> dict[str, Any]:
        """
        Execute state cleanup based on configured policies.

        Returns:
            Dictionary with cleanup results
        """
        if not self.config or not self.config.cleanup.enabled:
            return {"status": "disabled", "deleted": 0, "freed_mb": 0.0}

        storage_path = self.get_storage_path()
        if not storage_path.exists():
            return {"status": "no_storage", "deleted": 0, "freed_mb": 0.0}

        deleted_count = 0
        freed_bytes = 0

        # Get all state files
        state_files = list(storage_path.glob("*.json")) + list(storage_path.glob("*.json.gz"))
        state_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)  # Newest first

        # Always keep latest N states
        keep_count = self.config.cleanup.keep_latest
        files_to_keep = set(state_files[:keep_count])

        # Apply retention policy
        if self.config.cleanup.retention_days:
            cutoff_date = datetime.now() - timedelta(days=self.config.cleanup.retention_days)
            for state_file in state_files:
                if state_file in files_to_keep:
                    continue
                file_mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    try:
                        file_size = state_file.stat().st_size
                        state_file.unlink()
                        deleted_count += 1
                        freed_bytes += file_size
                        logger.info(f"Deleted old state file: {state_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {state_file}: {e}")

        # Apply size limit policy
        if self.config.cleanup.max_size_mb:
            max_size_bytes = self.config.cleanup.max_size_mb * 1024 * 1024
            total_size = sum(f.stat().st_size for f in state_files if f.exists())

            # Delete oldest files until under limit
            if total_size > max_size_bytes:
                for state_file in reversed(state_files):  # Oldest first
                    if state_file in files_to_keep:
                        continue
                    if total_size <= max_size_bytes:
                        break
                    try:
                        file_size = state_file.stat().st_size
                        state_file.unlink()
                        deleted_count += 1
                        freed_bytes += file_size
                        total_size -= file_size
                        logger.info(f"Deleted state file to free space: {state_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {state_file}: {e}")

        freed_mb = freed_bytes / (1024 * 1024)

        result = {
            "status": "success",
            "deleted": deleted_count,
            "freed_mb": round(freed_mb, 2),
            "remaining_files": len([f for f in state_files if f.exists()]),
        }

        logger.info(
            f"State cleanup completed: deleted {deleted_count} files, "
            f"freed {freed_mb:.2f} MB"
        )

        return result

    def get_config_summary(self) -> dict[str, Any]:
        """
        Get a summary of current configuration.

        Returns:
            Dictionary with configuration summary
        """
        if not self.config:
            return {"status": "no_config"}

        return {
            "persistence_enabled": self.config.enabled,
            "storage_location": str(self.get_storage_path()),
            "format": self.config.format,
            "compression": self.config.compression,
            "checkpoint": {
                "enabled": self.config.checkpoint.enabled,
                "mode": self.config.checkpoint.mode,
                "interval": self.config.checkpoint.interval,
            },
            "cleanup": {
                "enabled": self.config.cleanup.enabled,
                "retention_days": self.config.cleanup.retention_days,
                "max_size_mb": self.config.cleanup.max_size_mb,
                "cleanup_schedule": self.config.cleanup.cleanup_schedule,
                "keep_latest": self.config.cleanup.keep_latest,
            },
        }

