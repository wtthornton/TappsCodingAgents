"""
Health Metrics Collector.

Collects and stores health check metrics for trend analysis.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .metrics import HealthMetric, calculate_trend

logger = logging.getLogger(__name__)


class HealthMetricsCollector:
    """Collects and stores health check metrics."""

    def __init__(self, metrics_dir: Path | None = None, project_root: Path | None = None):
        """
        Initialize health metrics collector.

        Args:
            metrics_dir: Directory to store metrics (defaults to .tapps-agents/health/metrics)
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.metrics_dir = metrics_dir or (self.project_root / ".tapps-agents" / "health" / "metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for recent metrics
        self._recent_metrics: list[HealthMetric] = []
        self._max_cache_size = 100

    def record_metric(self, metric: HealthMetric) -> None:
        """
        Record a health metric.

        Args:
            metric: Health metric to record
        """
        # Store to file
        self._store_metric(metric)

        # Add to cache
        self._recent_metrics.append(metric)
        if len(self._recent_metrics) > self._max_cache_size:
            self._recent_metrics.pop(0)

    def record_health_check_result(self, result: Any, timestamp: datetime | None = None) -> HealthMetric:
        """
        Record a health check result as a metric.

        Args:
            result: HealthCheckResult instance
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Created HealthMetric
        """
        metric = HealthMetric.from_health_check_result(result, timestamp)
        self.record_metric(metric)
        return metric

    def _store_metric(self, metric: HealthMetric) -> None:
        """Store metric to file."""
        try:
            # Store in daily files for easier management
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")
            metrics_file = self.metrics_dir / f"health_{date_str}.jsonl"

            # Append to file (JSONL format)
            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metric.to_dict()) + "\n")

        except Exception as e:
            logger.error(f"Failed to store health metric: {e}")

    def get_metrics(
        self,
        check_name: str | None = None,
        status: str | None = None,
        days: int = 30,
        limit: int = 1000,
    ) -> list[HealthMetric]:
        """
        Get health metrics with optional filtering.

        Args:
            check_name: Filter by check name
            status: Filter by status (healthy, degraded, unhealthy)
            days: Number of days to look back
            limit: Maximum number of metrics to return

        Returns:
            List of HealthMetric instances
        """
        metrics: list[HealthMetric] = []

        # Search recent cache first
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        for metric in reversed(self._recent_metrics):
            if len(metrics) >= limit:
                break

            try:
                metric_date = datetime.fromisoformat(metric.timestamp.replace("Z", "+00:00"))
                if metric_date < cutoff_date:
                    continue
            except Exception:
                # If timestamp parsing fails, include it anyway
                pass

            if check_name and metric.check_name != check_name:
                continue
            if status and metric.status != status:
                continue

            metrics.append(metric)

        # If we need more, search files
        if len(metrics) < limit:
            metrics.extend(
                self._load_metrics_from_files(
                    check_name=check_name,
                    status=status,
                    days=days,
                    limit=limit - len(metrics),
                )
            )

        return metrics[:limit]

    def _load_metrics_from_files(
        self,
        check_name: str | None = None,
        status: str | None = None,
        days: int = 30,
        limit: int = 1000,
    ) -> list[HealthMetric]:
        """Load metrics from files."""
        metrics: list[HealthMetric] = []

        # Get all metrics files, sorted by date (newest first)
        metrics_files = sorted(
            self.metrics_dir.glob("health_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        for metrics_file in metrics_files:
            if len(metrics) >= limit:
                break

            # Check if file is within date range
            try:
                file_date_str = metrics_file.stem.replace("health_", "")
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                if file_date < cutoff_date:
                    continue
            except Exception:
                # If date parsing fails, include file anyway
                pass

            try:
                with open(metrics_file, encoding="utf-8") as f:
                    # Read lines in reverse (newest first)
                    lines = f.readlines()
                    for line in reversed(lines):
                        if len(metrics) >= limit:
                            break

                        try:
                            data = json.loads(line.strip())
                            metric = HealthMetric.from_dict(data)

                            # Check date range
                            try:
                                metric_date = datetime.fromisoformat(metric.timestamp.replace("Z", "+00:00"))
                                if metric_date < cutoff_date:
                                    continue
                            except Exception:
                                pass

                            # Apply filters
                            if check_name and metric.check_name != check_name:
                                continue
                            if status and metric.status != status:
                                continue

                            metrics.append(metric)
                        except Exception:
                            continue

            except Exception as e:
                logger.warning(f"Failed to load metrics from {metrics_file}: {e}")

        return metrics

    def get_summary(self, days: int = 30) -> dict[str, Any]:
        """
        Get health metrics summary.

        Args:
            days: Number of days to include in summary

        Returns:
            Dictionary with summary statistics
        """
        all_metrics = self.get_metrics(days=days, limit=10000)

        if not all_metrics:
            return {
                "total_checks": 0,
                "average_score": 0.0,
                "by_status": {},
                "by_check": {},
            }

        # Calculate overall statistics
        total = len(all_metrics)
        total_score = sum(m.score for m in all_metrics)
        avg_score = total_score / total if total > 0 else 0.0

        # Count by status
        by_status = {}
        for metric in all_metrics:
            by_status[metric.status] = by_status.get(metric.status, 0) + 1

        # Count by check name
        by_check = {}
        for metric in all_metrics:
            if metric.check_name not in by_check:
                by_check[metric.check_name] = {
                    "count": 0,
                    "total_score": 0.0,
                    "latest_status": metric.status,
                    "latest_score": metric.score,
                }
            by_check[metric.check_name]["count"] += 1
            by_check[metric.check_name]["total_score"] += metric.score
            # Update latest if this metric is more recent
            by_check[metric.check_name]["latest_status"] = metric.status
            by_check[metric.check_name]["latest_score"] = metric.score

        # Calculate averages for each check
        for check_name in by_check:
            count = by_check[check_name]["count"]
            by_check[check_name]["average_score"] = (
                by_check[check_name]["total_score"] / count if count > 0 else 0.0
            )
            del by_check[check_name]["total_score"]

        return {
            "total_checks": total,
            "average_score": avg_score,
            "by_status": by_status,
            "by_check": by_check,
        }

    def get_trends(self, check_name: str, days: int = 7) -> dict[str, Any]:
        """
        Get trend analysis for a specific check.

        Args:
            check_name: Name of the check to analyze
            days: Number of days to analyze

        Returns:
            Dictionary with trend information
        """
        metrics = self.get_metrics(check_name=check_name, days=days, limit=1000)
        return calculate_trend(metrics, window_days=days)

