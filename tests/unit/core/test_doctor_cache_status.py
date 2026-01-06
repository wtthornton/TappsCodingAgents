"""
Tests for Context7 cache status checks in doctor command.

Tests the _check_context7_cache_status() function with various scenarios:
- Context7 disabled
- Cache directory missing/not writable
- Cache empty
- Cache populated
- Import errors
- Metrics calculation errors
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.doctor import DoctorFinding, _check_context7_cache_status

pytestmark = pytest.mark.unit


class TestContext7CacheStatusDisabled:
    """Test Context7 cache status when Context7 is disabled."""

    def test_context7_disabled(self, tmp_path):
        """Test that disabled Context7 returns 'ok' finding."""
        config = Mock(spec=ProjectConfig)
        config.context7 = None

        result = _check_context7_cache_status(config, tmp_path)

        assert result is not None
        assert result.severity == "ok"
        assert result.code == "CONTEXT7_CACHE"
        assert "Disabled" in result.message
        assert result.remediation is None

    def test_context7_enabled_false(self, tmp_path):
        """Test that Context7 enabled=False returns 'ok' finding."""
        config = Mock(spec=ProjectConfig)
        config.context7 = Mock()
        config.context7.enabled = False

        result = _check_context7_cache_status(config, tmp_path)

        assert result is not None
        assert result.severity == "ok"
        assert result.code == "CONTEXT7_CACHE"
        assert "Disabled" in result.message


class TestContext7CacheStatusDirectoryIssues:
    """Test Context7 cache status with directory access issues."""

    def test_cache_directory_missing(self, tmp_path):
        """Test when cache directory doesn't exist."""
        config = Mock(spec=ProjectConfig)
        config.context7 = Mock()
        config.context7.enabled = True
        config.context7.knowledge_base = None

        # The function will try to import Context7 components
        # Since directory doesn't exist, it should return a warning
        result = _check_context7_cache_status(config, tmp_path)

        # Should return warning about directory not accessible
        assert result is not None
        assert result.severity == "warn"
        assert result.code == "CONTEXT7_CACHE"
        assert "not accessible" in result.message or "Directory" in result.message
        assert result.remediation is not None

    def test_cache_directory_with_custom_location(self, tmp_path):
        """Test cache directory with custom knowledge_base location."""
        config = Mock(spec=ProjectConfig)
        config.context7 = Mock()
        config.context7.enabled = True
        config.context7.knowledge_base = Mock()
        config.context7.knowledge_base.location = "custom/cache/location"

        # Create the custom cache directory
        cache_dir = tmp_path / "custom" / "cache" / "location"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Mock the Analytics.get_cache_metrics to return populated cache
        with patch("tapps_agents.context7.analytics.Analytics") as mock_analytics_class:
            mock_analytics_instance = Mock()
            mock_metrics = Mock()
            mock_metrics.total_entries = 10
            mock_metrics.total_libraries = 2
            mock_analytics_instance.get_cache_metrics.return_value = mock_metrics
            mock_analytics_class.return_value = mock_analytics_instance

            result = _check_context7_cache_status(config, tmp_path)

        # Should return ok with entry count
        assert result is not None
        assert result.severity == "ok"
        assert "10 entries" in result.message
        assert "2 libraries" in result.message


class TestContext7CacheStatusEmpty:
    """Test Context7 cache status when cache is empty."""

    def test_cache_empty(self, tmp_path):
        """Test when cache directory exists but is empty."""
        config = Mock(spec=ProjectConfig)
        config.context7 = Mock()
        config.context7.enabled = True
        config.context7.knowledge_base = None

        # Create cache directory
        cache_dir = tmp_path / ".tapps-agents" / "kb" / "context7-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create empty index file to simulate empty cache
        index_file = cache_dir / ".index.yaml"
        index_file.write_text("version: 1.0\nlast_updated: null\ntotal_entries: 0\nlibraries: {}\n", encoding="utf-8")

        result = _check_context7_cache_status(config, tmp_path)

        assert result is not None
        assert result.severity == "warn"
        assert result.code == "CONTEXT7_CACHE"
        assert "Empty" in result.message or "0 entries" in result.message
        assert result.remediation is not None
        assert "pre-population" in result.remediation or "prepopulate" in result.remediation


class TestContext7CacheStatusPopulated:
    """Test Context7 cache status when cache is populated."""

    def test_cache_populated(self, tmp_path):
        """Test when cache has entries."""
        config = Mock(spec=ProjectConfig)
        config.context7 = Mock()
        config.context7.enabled = True
        config.context7.knowledge_base = None

        # Create cache directory with mock data
        cache_dir = tmp_path / ".tapps-agents" / "kb" / "context7-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create index file with entries
        index_file = cache_dir / ".index.yaml"
        index_file.write_text(
            "version: 1.0\nlast_updated: '2024-01-01T00:00:00Z'\ntotal_entries: 25\nlibraries:\n  fastapi:\n    topics: {}\n",
            encoding="utf-8",
        )

        # Mock Analytics to return populated metrics
        with patch("tapps_agents.context7.analytics.Analytics") as mock_analytics_class:
            mock_analytics_instance = Mock()
            mock_metrics = Mock()
            mock_metrics.total_entries = 25
            mock_metrics.total_libraries = 5
            mock_analytics_instance.get_cache_metrics.return_value = mock_metrics
            mock_analytics_class.return_value = mock_analytics_instance

            result = _check_context7_cache_status(config, tmp_path)

        assert result is not None
        assert result.severity == "ok"
        assert result.code == "CONTEXT7_CACHE"
        assert "25 entries" in result.message
        assert "5 libraries" in result.message
        assert result.remediation is None


class TestContext7CacheStatusMetricsErrors:
    """Test Context7 cache status with metrics calculation errors."""

    def test_metrics_calculation_error(self, tmp_path):
        """Test when metrics calculation fails."""
        config = Mock(spec=ProjectConfig)
        config.context7 = Mock()
        config.context7.enabled = True
        config.context7.knowledge_base = None

        # Create cache directory
        cache_dir = tmp_path / ".tapps-agents" / "kb" / "context7-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Mock Analytics to raise exception during metrics calculation
        with patch("tapps_agents.context7.analytics.Analytics") as mock_analytics_class:
            mock_analytics_instance = Mock()
            mock_analytics_instance.get_cache_metrics.side_effect = Exception("Metrics error")
            mock_analytics_class.return_value = mock_analytics_instance

            result = _check_context7_cache_status(config, tmp_path)

        assert result is not None
        assert result.severity == "warn"
        assert result.code == "CONTEXT7_CACHE"
        assert "metrics unavailable" in result.message or "Accessible" in result.message
        assert result.remediation is not None


class TestContext7CacheStatusIntegration:
    """Integration tests for cache status in collect_doctor_report."""

    def test_cache_status_included_in_report(self, tmp_path):
        """Test that cache status is included in doctor report."""
        from tapps_agents.core.doctor import collect_doctor_report

        # Create a minimal config file
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
tooling:
  targets:
    python: "3.13"
  policy:
    external_tools_mode: "soft"
context7:
  enabled: true
  knowledge_base:
    location: ".tapps-agents/kb/context7-cache"
""",
            encoding="utf-8",
        )

        # Create cache directory
        cache_dir = tmp_path / ".tapps-agents" / "kb" / "context7-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        with patch("tapps_agents.core.config.load_config") as mock_load_config:
            from tapps_agents.core.config import ProjectConfig

            mock_config = Mock(spec=ProjectConfig)
            mock_config.tooling = Mock()
            mock_config.tooling.targets = Mock()
            mock_config.tooling.targets.python = "3.13"
            mock_config.tooling.policy = Mock()
            mock_config.tooling.policy.external_tools_mode = "soft"
            mock_config.tooling.policy.mypy_staged = False
            mock_config.tooling.policy.mypy_stage_paths = []
            mock_config.context7 = Mock()
            mock_config.context7.enabled = True
            mock_config.context7.knowledge_base = Mock()
            mock_config.context7.knowledge_base.location = ".tapps-agents/kb/context7-cache"
            mock_config.quality_tools = None

            mock_load_config.return_value = mock_config

            report = collect_doctor_report(project_root=tmp_path)

        findings = report.get("findings", [])
        cache_findings = [f for f in findings if f.get("code") == "CONTEXT7_CACHE"]

        assert len(cache_findings) > 0, "Context7 cache status should be in findings"
        assert cache_findings[0]["code"] == "CONTEXT7_CACHE"
