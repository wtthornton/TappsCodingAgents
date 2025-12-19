"""
Health Metrics Data Models and Storage.

Defines data structures for health check metrics and provides storage utilities.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import HealthCheckResult


@dataclass
class HealthMetric:
    """Single health check metric record."""

    check_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    score: float  # 0-100
    timestamp: str  # ISO timestamp
    details: dict[str, Any]
    remediation: list[str] | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthMetric:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_health_check_result(
        cls, result: HealthCheckResult, timestamp: datetime | None = None
    ) -> HealthMetric:
        """
        Create HealthMetric from HealthCheckResult.

        Args:
            result: Health check result
            timestamp: Optional timestamp (defaults to now)

        Returns:
            HealthMetric instance
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Convert remediation to list if it's a string
        remediation_list = None
        if result.remediation:
            if isinstance(result.remediation, str):
                remediation_list = [result.remediation]
            elif isinstance(result.remediation, list):
                remediation_list = result.remediation

        return cls(
            check_name=result.name,
            status=result.status,
            score=result.score,
            timestamp=timestamp.isoformat(),
            details=result.details or {},
            remediation=remediation_list,
            message=result.message,
        )


def calculate_trend(
    metrics: list[HealthMetric], window_days: int = 7
) -> dict[str, Any]:
    """
    Calculate trend statistics for health metrics.

    Args:
        metrics: List of health metrics
        window_days: Number of days to analyze

    Returns:
        Dictionary with trend information:
        - direction: "improving", "stable", "degrading"
        - score_change: Change in score over window
        - status_changes: Changes in status counts
    """
    if not metrics:
        return {
            "direction": "unknown",
            "score_change": 0.0,
            "status_changes": {},
        }

    # Sort by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)

    # Get metrics within window
    cutoff_date = datetime.now(UTC)
    # Simple approximation - in production would parse timestamps
    recent_metrics = sorted_metrics[-window_days:] if len(sorted_metrics) > window_days else sorted_metrics

    if len(recent_metrics) < 2:
        return {
            "direction": "stable",
            "score_change": 0.0,
            "status_changes": {},
        }

    # Calculate score change
    first_scores = [m.score for m in recent_metrics[: len(recent_metrics) // 2]]
    last_scores = [m.score for m in recent_metrics[len(recent_metrics) // 2 :]]

    avg_first = sum(first_scores) / len(first_scores) if first_scores else 0.0
    avg_last = sum(last_scores) / len(last_scores) if last_scores else 0.0
    score_change = avg_last - avg_first

    # Determine direction
    if score_change > 5.0:
        direction = "improving"
    elif score_change < -5.0:
        direction = "degrading"
    else:
        direction = "stable"

    # Count status changes
    first_statuses = [m.status for m in recent_metrics[: len(recent_metrics) // 2]]
    last_statuses = [m.status for m in recent_metrics[len(recent_metrics) // 2 :]]

    status_counts_first = {}
    status_counts_last = {}

    for status in first_statuses:
        status_counts_first[status] = status_counts_first.get(status, 0) + 1
    for status in last_statuses:
        status_counts_last[status] = status_counts_last.get(status, 0) + 1

    status_changes = {
        status: status_counts_last.get(status, 0) - status_counts_first.get(status, 0)
        for status in set(list(status_counts_first.keys()) + list(status_counts_last.keys()))
    }

    return {
        "direction": direction,
        "score_change": score_change,
        "status_changes": status_changes,
    }

