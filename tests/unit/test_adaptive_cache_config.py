"""
Unit tests for AdaptiveCacheConfig.
"""

from unittest.mock import Mock

import pytest

from tapps_agents.core.adaptive_cache_config import (
    AdaptiveCacheConfig,
    AdaptiveCacheSettings,
    ConfigurationChange,
)
from tapps_agents.core.resource_monitor import ResourceMetrics

pytestmark = pytest.mark.unit


class TestAdaptiveCacheConfig:
    """Test AdaptiveCacheConfig functionality."""

    def test_initialization(self):
        """Test AdaptiveCacheConfig initialization."""
        config = AdaptiveCacheConfig(enable_logging=False)

        assert config.resource_monitor is not None
        assert config.hardware_profiler is not None
        assert config.current_settings is not None
        assert config.hardware_profile is not None

    def test_create_settings_from_profile(self):
        """Test creating settings from optimization profile."""
        config = AdaptiveCacheConfig(enable_logging=False)

        profile = config.base_profile
        settings = config._create_settings_from_profile(profile)

        assert isinstance(settings, AdaptiveCacheSettings)
        assert settings.tier1_ttl == profile.tier1_ttl
        assert settings.max_in_memory_entries == profile.max_in_memory_entries

    def test_check_and_adjust_memory_critical(self):
        """Test adjustment for critical memory pressure."""
        config = AdaptiveCacheConfig(enable_logging=False)

        # Mock resource monitor to return high memory usage
        mock_metrics = ResourceMetrics(
            timestamp="2025-12-11T10:00:00Z",
            cpu_percent=30.0,
            memory_percent=95.0,  # Critical
            memory_used_mb=1000.0,
            memory_available_mb=100.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        config.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)

        # Initial settings should have in-memory cache
        initial_entries = config.current_settings.max_in_memory_entries
        assert initial_entries > 0

        # Check and adjust
        adjusted = config.check_and_adjust()

        assert adjusted is True
        assert config.current_settings.max_in_memory_entries == 0
        assert config.current_settings.hybrid_mode is False
        assert config.current_settings.compression_enabled is True
        assert len(config.config_changes) > 0

    def test_check_and_adjust_cpu_critical(self):
        """Test adjustment for critical CPU pressure."""
        config = AdaptiveCacheConfig(enable_logging=False)

        # Mock resource monitor to return high CPU usage
        mock_metrics = ResourceMetrics(
            timestamp="2025-12-11T10:00:00Z",
            cpu_percent=90.0,  # Critical
            memory_percent=50.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        config.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)

        # Initial settings should have background indexing enabled
        assert config.current_settings.background_indexing_enabled is True

        # Check and adjust
        adjusted = config.check_and_adjust()

        assert adjusted is True
        assert config.current_settings.background_indexing_enabled is False
        assert config.current_settings.cache_warming_enabled is False
        assert config.current_settings.tier1_ttl > config.base_profile.tier1_ttl

    def test_check_and_adjust_disk_critical(self):
        """Test adjustment for critical disk space."""
        config = AdaptiveCacheConfig(enable_logging=False)

        # Mock resource monitor to return low disk space
        mock_metrics = ResourceMetrics(
            timestamp="2025-12-11T10:00:00Z",
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_percent=95.0,  # Only 5% free (critical)
            disk_used_gb=190.0,
            disk_free_gb=10.0,
        )
        config.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)

        # Check and adjust
        adjusted = config.check_and_adjust()

        assert adjusted is True
        assert config.current_settings.emergency_cleanup_active is True
        assert config.current_settings.compression_enabled is True
        assert (
            config.current_settings.max_cache_size_mb
            < config.base_profile.max_cache_size_mb
        )

    def test_check_and_adjust_no_change(self):
        """Test that no adjustment is made when resources are normal."""
        config = AdaptiveCacheConfig(enable_logging=False)

        # Mock resource monitor to return normal usage
        mock_metrics = ResourceMetrics(
            timestamp="2025-12-11T10:00:00Z",
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        config.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)

        # Store initial settings
        initial_settings = config.current_settings.to_dict()

        # Check and adjust
        adjusted = config.check_and_adjust()

        # Should not adjust under normal conditions
        assert adjusted is False
        assert config.current_settings.to_dict() == initial_settings

    def test_reset_to_base_profile(self):
        """Test resetting to base profile."""
        config = AdaptiveCacheConfig(enable_logging=False)

        # Modify settings
        config.current_settings.max_in_memory_entries = 0
        config.current_settings.compression_enabled = True

        # Reset
        config.reset_to_base_profile()

        # Should match base profile
        assert (
            config.current_settings.max_in_memory_entries
            == config.base_profile.max_in_memory_entries
        )
        assert (
            config.current_settings.compression_enabled
            == config.base_profile.compression_enabled
        )
        assert len(config.config_changes) > 0

    def test_get_status(self):
        """Test getting status."""
        config = AdaptiveCacheConfig(enable_logging=False)

        status = config.get_status()

        assert "hardware_profile" in status
        assert "current_settings" in status
        assert "base_profile" in status
        assert "resource_metrics" in status
        assert "adaptive_behavior" in status
        assert status["hardware_profile"] == config.hardware_profile.value

    def test_get_recent_changes(self):
        """Test getting recent configuration changes."""
        config = AdaptiveCacheConfig(enable_logging=False)

        # Force a change
        mock_metrics = ResourceMetrics(
            timestamp="2025-12-11T10:00:00Z",
            cpu_percent=95.0,
            memory_percent=50.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_free_gb=100.0,
        )
        config.resource_monitor.get_current_metrics = Mock(return_value=mock_metrics)
        config.check_and_adjust()

        changes = config.get_recent_changes(count=5)

        assert len(changes) > 0
        assert isinstance(changes[0], ConfigurationChange)
        assert "reason" in changes[0].to_dict()


class TestAdaptiveCacheSettings:
    """Test AdaptiveCacheSettings."""

    def test_to_dict(self):
        """Test converting settings to dictionary."""
        settings = AdaptiveCacheSettings(
            tier1_ttl=300,
            tier2_ttl=120,
            tier3_ttl=60,
            max_in_memory_entries=100,
            hybrid_mode=True,
            compression_enabled=False,
            max_cache_size_mb=200,
            pre_populate=True,
            auto_refresh=True,
            index_on_startup=True,
            max_knowledge_files=1000,
            background_indexing_enabled=True,
            cache_warming_enabled=True,
            emergency_cleanup_active=False,
        )

        data = settings.to_dict()

        assert isinstance(data, dict)
        assert data["tier1_ttl"] == 300
        assert data["max_in_memory_entries"] == 100
        assert data["hybrid_mode"] is True
