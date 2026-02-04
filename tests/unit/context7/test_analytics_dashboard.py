"""
Unit tests for Context7 Analytics Dashboard.

Tests dashboard metrics collection, skill usage tracking, and performance monitoring.
"""

from unittest.mock import MagicMock

import pytest

from tapps_agents.context7.analytics_dashboard import (
    AnalyticsDashboard,
    DashboardMetrics,
    SkillUsageMetrics,
)

pytestmark = pytest.mark.unit


class TestSkillUsageMetrics:
    """Tests for SkillUsageMetrics dataclass."""

    def test_skill_usage_metrics_init(self):
        """Test SkillUsageMetrics initialization."""
        metrics = SkillUsageMetrics(
            skill_name="test_skill",
            total_lookups=100,
            cache_hits=80,
            cache_misses=20
        )
        
        assert metrics.skill_name == "test_skill"
        assert metrics.total_lookups == 100
        assert metrics.cache_hits == 80
        assert metrics.cache_misses == 20

    def test_skill_usage_metrics_to_dict(self):
        """Test SkillUsageMetrics.to_dict()."""
        metrics = SkillUsageMetrics(
            skill_name="test_skill",
            total_lookups=100
        )
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result["skill_name"] == "test_skill"
        assert result["total_lookups"] == 100


class TestDashboardMetrics:
    """Tests for DashboardMetrics dataclass."""

    def test_dashboard_metrics_init(self):
        """Test DashboardMetrics initialization."""
        metrics = DashboardMetrics(
            timestamp="2024-01-01T00:00:00",
            overall_metrics={},
            skill_usage=[],
            top_libraries=[],
            cache_health={},
            performance_trends={}
        )
        
        assert metrics.timestamp == "2024-01-01T00:00:00"
        assert isinstance(metrics.overall_metrics, dict)

    def test_dashboard_metrics_to_dict(self):
        """Test DashboardMetrics.to_dict()."""
        metrics = DashboardMetrics(
            timestamp="2024-01-01T00:00:00",
            overall_metrics={"total": 100},
            skill_usage=[],
            top_libraries=[],
            cache_health={},
            performance_trends={}
        )
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result["timestamp"] == "2024-01-01T00:00:00"


class TestAnalyticsDashboard:
    """Tests for AnalyticsDashboard class."""

    def test_analytics_dashboard_init(self, tmp_path):
        """Test AnalyticsDashboard initialization."""
        mock_analytics = MagicMock()
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_metadata = MagicMock()
        
        dashboard = AnalyticsDashboard(
            analytics=mock_analytics,
            cache_structure=mock_cache_structure,
            metadata_manager=mock_metadata,
            dashboard_dir=tmp_path / "dashboard"
        )
        
        assert dashboard.analytics == mock_analytics
        assert dashboard.dashboard_dir.exists()

    def test_analytics_dashboard_load_skill_usage(self, tmp_path):
        """Test AnalyticsDashboard loads skill usage from file."""
        mock_analytics = MagicMock()
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_metadata = MagicMock()
        
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir(parents=True)
        skill_usage_file = dashboard_dir / "skill-usage.json"
        skill_usage_file.write_text('{"test_skill": {"skill_name": "test_skill", "total_lookups": 100}}')
        
        dashboard = AnalyticsDashboard(
            analytics=mock_analytics,
            cache_structure=mock_cache_structure,
            metadata_manager=mock_metadata,
            dashboard_dir=dashboard_dir
        )
        
        assert "test_skill" in dashboard._skill_usage

    def test_analytics_dashboard_load_skill_usage_missing_file(self, tmp_path):
        """Test AnalyticsDashboard handles missing skill usage file."""
        mock_analytics = MagicMock()
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_metadata = MagicMock()
        
        dashboard = AnalyticsDashboard(
            analytics=mock_analytics,
            cache_structure=mock_cache_structure,
            metadata_manager=mock_metadata,
            dashboard_dir=tmp_path / "dashboard"
        )
        
        assert dashboard._skill_usage == {}

    def test_analytics_dashboard_record_skill_usage(self, tmp_path):
        """Test AnalyticsDashboard records skill usage."""
        mock_analytics = MagicMock()
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_metadata = MagicMock()
        
        dashboard = AnalyticsDashboard(
            analytics=mock_analytics,
            cache_structure=mock_cache_structure,
            metadata_manager=mock_metadata,
            dashboard_dir=tmp_path / "dashboard"
        )
        
        dashboard.record_skill_usage(
            skill_name="test_skill",
            cache_hit=True,
            response_time_ms=50.0
        )
        
        assert "test_skill" in dashboard._skill_usage
        assert dashboard._skill_usage["test_skill"].total_lookups == 1
        assert dashboard._skill_usage["test_skill"].cache_hits == 1

    def test_analytics_dashboard_get_dashboard_metrics(self, tmp_path):
        """Test AnalyticsDashboard.get_dashboard_metrics()."""
        mock_analytics = MagicMock()
        mock_analytics.get_overall_metrics.return_value = {"total": 100}
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_metadata = MagicMock()
        mock_metadata.get_top_libraries.return_value = []
        
        dashboard = AnalyticsDashboard(
            analytics=mock_analytics,
            cache_structure=mock_cache_structure,
            metadata_manager=mock_metadata,
            dashboard_dir=tmp_path / "dashboard"
        )
        
        metrics = dashboard.get_dashboard_metrics()
        
        assert isinstance(metrics, DashboardMetrics)
        assert "timestamp" in metrics.to_dict()

    def test_analytics_dashboard_save_skill_usage(self, tmp_path):
        """Test AnalyticsDashboard saves skill usage to file."""
        mock_analytics = MagicMock()
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_metadata = MagicMock()
        
        dashboard = AnalyticsDashboard(
            analytics=mock_analytics,
            cache_structure=mock_cache_structure,
            metadata_manager=mock_metadata,
            dashboard_dir=tmp_path / "dashboard"
        )
        
        dashboard.record_skill_usage("test_skill", cache_hit=True)
        dashboard._save_skill_usage()
        
        assert dashboard.skill_usage_file.exists()
        assert dashboard.skill_usage_file.read_text()

