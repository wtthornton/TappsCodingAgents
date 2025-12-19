"""
KB Usage Analytics Dashboard

Provides analytics dashboard functionality for Context7 KB usage in Skills.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .analytics import Analytics
from .cache_structure import CacheStructure
from .metadata import MetadataManager


@dataclass
class SkillUsageMetrics:
    """Metrics for Skill usage of Context7 KB."""

    skill_name: str
    total_lookups: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    libraries_accessed: list[str] = field(default_factory=list)
    avg_response_time_ms: float = 0.0
    last_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DashboardMetrics:
    """Complete dashboard metrics."""

    timestamp: str
    overall_metrics: dict[str, Any]
    skill_usage: list[dict[str, Any]]
    top_libraries: list[dict[str, Any]]
    cache_health: dict[str, Any]
    performance_trends: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AnalyticsDashboard:
    """Analytics dashboard for KB usage in Skills."""

    def __init__(
        self,
        analytics: Analytics,
        cache_structure: CacheStructure,
        metadata_manager: MetadataManager,
        dashboard_dir: Path | None = None,
    ):
        """
        Initialize analytics dashboard.

        Args:
            analytics: Analytics instance
            cache_structure: CacheStructure instance
            metadata_manager: MetadataManager instance
            dashboard_dir: Directory for dashboard data (default: cache_root/dashboard)
        """
        self.analytics = analytics
        self.cache_structure = cache_structure
        self.metadata_manager = metadata_manager

        if dashboard_dir is None:
            dashboard_dir = cache_structure.cache_root / "dashboard"

        self.dashboard_dir = Path(dashboard_dir)
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

        self.skill_usage_file = self.dashboard_dir / "skill-usage.json"
        self._skill_usage: dict[str, SkillUsageMetrics] = {}
        self._load_skill_usage()

    def _load_skill_usage(self):
        """Load skill usage data from file."""
        if not self.skill_usage_file.exists():
            return

        try:
            with open(self.skill_usage_file) as f:
                data = json.load(f)
                for skill_name, metrics_data in data.items():
                    self._skill_usage[skill_name] = SkillUsageMetrics(**metrics_data)
        except Exception:
            self._skill_usage = {}

    def _save_skill_usage(self):
        """Save skill usage data to file."""
        data = {
            skill_name: metrics.to_dict()
            for skill_name, metrics in self._skill_usage.items()
        }

        with open(self.skill_usage_file, "w") as f:
            json.dump(data, f, indent=2)

    def record_skill_lookup(
        self,
        skill_name: str,
        library: str,
        cache_hit: bool,
        response_time_ms: float = 0.0,
    ):
        """
        Record a lookup from a Skill.

        Args:
            skill_name: Name of the Skill
            library: Library that was looked up
            cache_hit: Whether it was a cache hit
            response_time_ms: Response time in milliseconds
        """
        if skill_name not in self._skill_usage:
            self._skill_usage[skill_name] = SkillUsageMetrics(
                skill_name=skill_name, last_used=datetime.now(UTC).isoformat()
            )

        metrics = self._skill_usage[skill_name]
        metrics.total_lookups += 1

        if cache_hit:
            metrics.cache_hits += 1
        else:
            metrics.cache_misses += 1

        if library not in metrics.libraries_accessed:
            metrics.libraries_accessed.append(library)

        # Update average response time
        if response_time_ms > 0:
            if metrics.avg_response_time_ms == 0:
                metrics.avg_response_time_ms = response_time_ms
            else:
                # Running average
                metrics.avg_response_time_ms = (
                    metrics.avg_response_time_ms * (metrics.total_lookups - 1)
                    + response_time_ms
                ) / metrics.total_lookups

        metrics.last_used = datetime.now(UTC).isoformat()
        self._save_skill_usage()

    def record_skill_api_call(self, skill_name: str):
        """Record an API call from a Skill."""
        if skill_name not in self._skill_usage:
            self._skill_usage[skill_name] = SkillUsageMetrics(
                skill_name=skill_name, last_used=datetime.now(UTC).isoformat()
            )

        self._skill_usage[skill_name].api_calls += 1
        self._save_skill_usage()

    def get_skill_metrics(self, skill_name: str) -> SkillUsageMetrics | None:
        """Get metrics for a specific Skill."""
        return self._skill_usage.get(skill_name)

    def get_all_skill_metrics(self) -> list[SkillUsageMetrics]:
        """Get metrics for all Skills."""
        return list(self._skill_usage.values())

    def get_dashboard_metrics(self) -> DashboardMetrics:
        """
        Get complete dashboard metrics.

        Returns:
            DashboardMetrics with all analytics data
        """
        # Overall cache metrics
        cache_metrics = self.analytics.get_cache_metrics()

        # Skill usage metrics
        skill_usage = [m.to_dict() for m in self.get_all_skill_metrics()]

        # Top libraries
        top_libraries = [m.to_dict() for m in self.analytics.get_top_libraries(10)]

        # Cache health
        hit_rate = cache_metrics.hit_rate
        cache_health = {
            "status": "healthy" if hit_rate >= 70 else "needs_attention",
            "hit_rate": hit_rate,
            "total_entries": cache_metrics.total_entries,
            "total_libraries": cache_metrics.total_libraries,
            "cache_size_mb": cache_metrics.total_size_bytes / (1024 * 1024),
            "avg_response_time_ms": cache_metrics.avg_response_time_ms,
        }

        # Performance trends (simplified - would need historical data)
        performance_trends = {
            "cache_hits_trend": "increasing",  # Would calculate from historical data
            "response_time_trend": "stable",
            "api_calls_trend": "decreasing",
        }

        return DashboardMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            overall_metrics=cache_metrics.to_dict(),
            skill_usage=skill_usage,
            top_libraries=top_libraries,
            cache_health=cache_health,
            performance_trends=performance_trends,
        )

    def export_dashboard_json(self, output_file: Path | None = None) -> Path:
        """
        Export dashboard metrics to JSON file.

        Args:
            output_file: Output file path (default: dashboard_dir/dashboard-{timestamp}.json)

        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            output_file = self.dashboard_dir / f"dashboard-{timestamp}.json"

        output_file = Path(output_file)
        metrics = self.get_dashboard_metrics()

        with open(output_file, "w") as f:
            json.dump(metrics.to_dict(), f, indent=2)

        return output_file

    def generate_dashboard_report(self) -> str:
        """
        Generate a text report of dashboard metrics.

        Returns:
            Formatted report string
        """
        metrics = self.get_dashboard_metrics()

        report = []
        report.append("=" * 60)
        report.append("Context7 KB Usage Analytics Dashboard")
        report.append("=" * 60)
        report.append(f"Generated: {metrics.timestamp}")
        report.append("")

        # Overall Metrics
        report.append("Overall Cache Metrics:")
        report.append("-" * 60)
        overall = metrics.overall_metrics
        report.append(f"  Total Entries: {overall.get('total_entries', 0)}")
        report.append(f"  Total Libraries: {overall.get('total_libraries', 0)}")
        report.append(f"  Cache Hits: {overall.get('cache_hits', 0)}")
        report.append(f"  Cache Misses: {overall.get('cache_misses', 0)}")
        report.append(f"  Hit Rate: {overall.get('hit_rate', 0):.1f}%")
        report.append(f"  API Calls: {overall.get('api_calls', 0)}")
        report.append(
            f"  Avg Response Time: {overall.get('avg_response_time_ms', 0):.2f} ms"
        )
        report.append("")

        # Cache Health
        report.append("Cache Health:")
        report.append("-" * 60)
        health = metrics.cache_health
        report.append(f"  Status: {health.get('status', 'unknown')}")
        report.append(f"  Hit Rate: {health.get('hit_rate', 0):.1f}%")
        report.append(f"  Cache Size: {health.get('cache_size_mb', 0):.2f} MB")
        report.append("")

        # Skill Usage
        report.append("Skill Usage:")
        report.append("-" * 60)
        for skill in metrics.skill_usage:
            report.append(f"  {skill.get('skill_name', 'unknown')}:")
            report.append(f"    Total Lookups: {skill.get('total_lookups', 0)}")
            report.append(f"    Cache Hits: {skill.get('cache_hits', 0)}")
            report.append(f"    Cache Misses: {skill.get('cache_misses', 0)}")
            report.append(f"    Libraries: {len(skill.get('libraries_accessed', []))}")
            report.append("")

        # Top Libraries
        report.append("Top Libraries by Usage:")
        report.append("-" * 60)
        for i, lib in enumerate(metrics.top_libraries[:10], 1):
            report.append(
                f"  {i}. {lib.get('library', 'unknown')}: {lib.get('cache_hits', 0)} hits"
            )

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)
