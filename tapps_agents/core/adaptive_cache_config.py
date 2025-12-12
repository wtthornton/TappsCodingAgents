"""
Adaptive Cache Configuration - Dynamically adjusts cache settings based on resource usage.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .hardware_profiler import (
    CacheOptimizationProfile,
    HardwareProfile,
    HardwareProfiler,
)
from .resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveCacheSettings:
    """Current adaptive cache settings."""

    # Tiered Context settings
    tier1_ttl: int
    tier2_ttl: int
    tier3_ttl: int
    max_in_memory_entries: int
    hybrid_mode: bool
    compression_enabled: bool

    # Context7 KB settings
    max_cache_size_mb: int
    pre_populate: bool
    auto_refresh: bool

    # RAG Knowledge settings
    index_on_startup: bool
    max_knowledge_files: int

    # Adaptive behavior flags
    background_indexing_enabled: bool
    cache_warming_enabled: bool
    emergency_cleanup_active: bool

    # Adaptive control settings (derived from hardware profile)
    # Context7 best practice: make new adaptive knobs backward-compatible with safe defaults,
    # then allow hardware profiles to override them (see UnifiedCache initialization).
    resource_check_interval: int = 60
    emergency_cleanup_threshold: float = 0.80  # Memory usage % to trigger cleanup

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ConfigurationChange:
    """Record of a configuration change."""

    timestamp: str
    reason: str
    old_settings: dict[str, Any]
    new_settings: dict[str, Any]
    resource_metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AdaptiveCacheConfig:
    """
    Dynamically adjusts cache configuration based on resource usage.

    Monitors CPU, memory, and disk usage and adjusts cache settings
    to maintain optimal performance under resource constraints.
    """

    def __init__(
        self,
        resource_monitor: ResourceMonitor | None = None,
        hardware_profiler: HardwareProfiler | None = None,
        hardware_profile: HardwareProfile | None = None,
        check_interval: int = 60,
        enable_logging: bool = True,
    ):
        """
        Initialize adaptive cache configuration.

        Args:
            resource_monitor: ResourceMonitor instance (creates default if not provided)
            hardware_profiler: HardwareProfiler instance (creates default if not provided)
            check_interval: Interval in seconds between resource checks
            enable_logging: Whether to log configuration changes
        """
        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.hardware_profiler = hardware_profiler or HardwareProfiler()
        self.check_interval = check_interval
        self.enable_logging = enable_logging

        # Get base optimization profile from hardware
        self.hardware_profile = (
            hardware_profile or self.hardware_profiler.detect_profile()
        )
        self.base_profile = self.hardware_profiler.get_optimization_profile(
            self.hardware_profile
        )

        # Current adaptive settings (initialized from base profile)
        self.current_settings = self._create_settings_from_profile(self.base_profile)

        # Track configuration changes
        self.config_changes: list[ConfigurationChange] = []
        self.last_check_time: datetime | None = None

        # Thresholds for adaptive behavior
        self.memory_warning_threshold = 80.0  # % memory usage
        self.memory_critical_threshold = 90.0
        self.memory_low_threshold = 60.0

        self.cpu_warning_threshold = 70.0  # % CPU usage
        self.cpu_critical_threshold = 85.0

        self.disk_warning_threshold = 80.0  # % disk usage
        self.disk_critical_threshold = 90.0
        self.disk_free_warning_threshold = 20.0  # % free disk
        self.disk_free_critical_threshold = 10.0

    def _create_settings_from_profile(
        self, profile: CacheOptimizationProfile
    ) -> AdaptiveCacheSettings:
        """Create adaptive settings from optimization profile."""
        return AdaptiveCacheSettings(
            tier1_ttl=profile.tier1_ttl,
            tier2_ttl=profile.tier2_ttl,
            tier3_ttl=profile.tier3_ttl,
            max_in_memory_entries=profile.max_in_memory_entries,
            hybrid_mode=profile.hybrid_mode,
            compression_enabled=profile.compression_enabled,
            max_cache_size_mb=profile.max_cache_size_mb,
            pre_populate=profile.pre_populate,
            auto_refresh=profile.auto_refresh,
            index_on_startup=profile.index_on_startup,
            max_knowledge_files=profile.max_knowledge_files,
            background_indexing_enabled=True,
            cache_warming_enabled=True,
            emergency_cleanup_active=False,
            resource_check_interval=profile.resource_check_interval,
            emergency_cleanup_threshold=profile.emergency_cleanup_threshold,
        )

    def check_and_adjust(self) -> bool:
        """
        Check resource usage and adjust configuration if needed.

        Returns:
            True if configuration was adjusted
        """
        # Check if enough time has passed since last check
        now = datetime.now(timezone.utc)
        if self.last_check_time:
            elapsed = (now - self.last_check_time).total_seconds()
            if elapsed < self.check_interval:
                return False

        # Get current resource metrics
        metrics = self.resource_monitor.get_current_metrics()
        self.last_check_time = now

        # Store old settings
        old_settings = self.current_settings.to_dict()
        adjusted = False
        reasons = []

        # Adjust based on memory pressure
        if metrics.memory_percent > self.memory_critical_threshold:
            # Critical memory pressure - disable in-memory cache, enable compression
            if self.current_settings.max_in_memory_entries > 0:
                self.current_settings.max_in_memory_entries = 0
                self.current_settings.hybrid_mode = False
                adjusted = True
                reasons.append(
                    f"Critical memory pressure ({metrics.memory_percent:.1f}%)"
                )

            if not self.current_settings.compression_enabled:
                self.current_settings.compression_enabled = True
                adjusted = True
                reasons.append("Enabled compression due to memory pressure")

        elif metrics.memory_percent > self.memory_warning_threshold:
            # Warning memory pressure - reduce in-memory cache size
            if self.current_settings.max_in_memory_entries > 0:
                # Reduce to 50% of base profile
                base_entries = self.base_profile.max_in_memory_entries
                new_entries = max(10, int(base_entries * 0.5))
                if self.current_settings.max_in_memory_entries != new_entries:
                    self.current_settings.max_in_memory_entries = new_entries
                    adjusted = True
                    reasons.append(
                        f"Reduced in-memory cache due to memory pressure ({metrics.memory_percent:.1f}%)"
                    )

        elif metrics.memory_percent < self.memory_low_threshold:
            # Low memory usage - restore to base profile
            if (
                self.current_settings.max_in_memory_entries
                < self.base_profile.max_in_memory_entries
            ):
                self.current_settings.max_in_memory_entries = (
                    self.base_profile.max_in_memory_entries
                )
                self.current_settings.hybrid_mode = self.base_profile.hybrid_mode
                adjusted = True
                reasons.append(
                    f"Restored cache settings (memory usage {metrics.memory_percent:.1f}%)"
                )

        # Adjust based on CPU pressure
        if metrics.cpu_percent > self.cpu_critical_threshold:
            # Critical CPU pressure - disable background operations
            if self.current_settings.background_indexing_enabled:
                self.current_settings.background_indexing_enabled = False
                adjusted = True
                reasons.append(
                    f"Disabled background indexing (CPU {metrics.cpu_percent:.1f}%)"
                )

            if self.current_settings.cache_warming_enabled:
                self.current_settings.cache_warming_enabled = False
                adjusted = True
                reasons.append("Disabled cache warming due to CPU pressure")

            # Increase TTL to reduce refresh frequency
            if self.current_settings.tier1_ttl < self.base_profile.tier1_ttl * 1.5:
                self.current_settings.tier1_ttl = int(self.base_profile.tier1_ttl * 1.5)
                self.current_settings.tier2_ttl = int(self.base_profile.tier2_ttl * 1.5)
                self.current_settings.tier3_ttl = int(self.base_profile.tier3_ttl * 1.5)
                adjusted = True
                reasons.append("Increased TTL to reduce refresh frequency")

        elif metrics.cpu_percent > self.cpu_warning_threshold:
            # Warning CPU pressure - reduce background operations
            if self.current_settings.background_indexing_enabled:
                self.current_settings.background_indexing_enabled = False
                adjusted = True
                reasons.append(
                    f"Disabled background indexing (CPU {metrics.cpu_percent:.1f}%)"
                )

        elif metrics.cpu_percent < 50.0:
            # Low CPU usage - restore background operations
            if not self.current_settings.background_indexing_enabled:
                self.current_settings.background_indexing_enabled = True
                adjusted = True
                reasons.append("Restored background indexing (CPU usage low)")

            if not self.current_settings.cache_warming_enabled:
                self.current_settings.cache_warming_enabled = True
                adjusted = True
                reasons.append("Restored cache warming")

            # Restore TTL to base values
            if self.current_settings.tier1_ttl != self.base_profile.tier1_ttl:
                self.current_settings.tier1_ttl = self.base_profile.tier1_ttl
                self.current_settings.tier2_ttl = self.base_profile.tier2_ttl
                self.current_settings.tier3_ttl = self.base_profile.tier3_ttl
                adjusted = True
                reasons.append("Restored TTL to base values")

        # Adjust based on disk space
        disk_free_percent = 100.0 - metrics.disk_percent
        if disk_free_percent < self.disk_free_critical_threshold:
            # Critical disk space - emergency cleanup, disable cache growth
            if not self.current_settings.emergency_cleanup_active:
                self.current_settings.emergency_cleanup_active = True
                adjusted = True
                reasons.append(
                    f"Emergency cleanup activated (disk {disk_free_percent:.1f}% free)"
                )

            # Reduce max cache size
            if (
                self.current_settings.max_cache_size_mb
                > self.base_profile.max_cache_size_mb * 0.5
            ):
                self.current_settings.max_cache_size_mb = int(
                    self.base_profile.max_cache_size_mb * 0.5
                )
                adjusted = True
                reasons.append("Reduced max cache size due to disk pressure")

            # Enable compression
            if not self.current_settings.compression_enabled:
                self.current_settings.compression_enabled = True
                adjusted = True
                reasons.append("Enabled compression due to disk pressure")

        elif disk_free_percent < self.disk_free_warning_threshold:
            # Warning disk space - aggressive cleanup, reduce cache size
            if (
                self.current_settings.max_cache_size_mb
                > self.base_profile.max_cache_size_mb * 0.75
            ):
                self.current_settings.max_cache_size_mb = int(
                    self.base_profile.max_cache_size_mb * 0.75
                )
                adjusted = True
                reasons.append(
                    f"Reduced cache size (disk {disk_free_percent:.1f}% free)"
                )

        elif disk_free_percent > 30.0:
            # Plenty of disk space - restore settings
            if self.current_settings.emergency_cleanup_active:
                self.current_settings.emergency_cleanup_active = False
                adjusted = True
                reasons.append("Deactivated emergency cleanup (disk space available)")

            if (
                self.current_settings.max_cache_size_mb
                < self.base_profile.max_cache_size_mb
            ):
                self.current_settings.max_cache_size_mb = (
                    self.base_profile.max_cache_size_mb
                )
                adjusted = True
                reasons.append("Restored max cache size")

        # Log configuration change if adjusted
        if adjusted:
            new_settings = self.current_settings.to_dict()
            change = ConfigurationChange(
                timestamp=now.isoformat(),
                reason="; ".join(reasons),
                old_settings=old_settings,
                new_settings=new_settings,
                resource_metrics={
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "disk_percent": metrics.disk_percent,
                    "disk_free_percent": disk_free_percent,
                },
            )
            self.config_changes.append(change)

            # Keep only last 100 changes
            if len(self.config_changes) > 100:
                self.config_changes = self.config_changes[-100:]

            if self.enable_logging:
                logger.info(
                    f"Adaptive cache configuration adjusted: {change.reason}. "
                    f"CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_percent:.1f}%, "
                    f"Disk: {disk_free_percent:.1f}% free"
                )

        return adjusted

    def get_current_settings(self) -> AdaptiveCacheSettings:
        """Get current adaptive cache settings."""
        return self.current_settings

    def get_recent_changes(self, count: int = 10) -> list[ConfigurationChange]:
        """
        Get recent configuration changes.

        Args:
            count: Number of changes to return

        Returns:
            List of recent configuration changes
        """
        return self.config_changes[-count:]

    def reset_to_base_profile(self):
        """Reset settings to base hardware profile."""
        old_settings = self.current_settings.to_dict()
        self.current_settings = self._create_settings_from_profile(self.base_profile)
        new_settings = self.current_settings.to_dict()

        change = ConfigurationChange(
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason="Manual reset to base profile",
            old_settings=old_settings,
            new_settings=new_settings,
            resource_metrics={},
        )
        self.config_changes.append(change)

        if self.enable_logging:
            logger.info("Adaptive cache configuration reset to base profile")

    def get_status(self) -> dict[str, Any]:
        """
        Get current status of adaptive configuration.

        Returns:
            Dictionary with status information
        """
        metrics = self.resource_monitor.get_current_metrics()
        disk_free_percent = 100.0 - metrics.disk_percent

        return {
            "hardware_profile": self.hardware_profile.value,
            "current_settings": self.current_settings.to_dict(),
            "base_profile": {
                "tier1_ttl": self.base_profile.tier1_ttl,
                "tier2_ttl": self.base_profile.tier2_ttl,
                "tier3_ttl": self.base_profile.tier3_ttl,
                "max_in_memory_entries": self.base_profile.max_in_memory_entries,
                "max_cache_size_mb": self.base_profile.max_cache_size_mb,
            },
            "resource_metrics": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_percent": metrics.disk_percent,
                "disk_free_percent": disk_free_percent,
            },
            "adaptive_behavior": {
                "memory_pressure": metrics.memory_percent
                > self.memory_warning_threshold,
                "cpu_pressure": metrics.cpu_percent > self.cpu_warning_threshold,
                "disk_pressure": disk_free_percent < self.disk_free_warning_threshold,
                "emergency_cleanup": self.current_settings.emergency_cleanup_active,
            },
            "total_changes": len(self.config_changes),
            "last_check": (
                self.last_check_time.isoformat() if self.last_check_time else None
            ),
        }
