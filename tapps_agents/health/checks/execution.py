"""
Execution Health Check.

Checks workflow execution reliability and performance.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from ...workflow.execution_metrics import ExecutionMetricsCollector
from ..base import HealthCheck, HealthCheckResult


class ExecutionHealthCheck(HealthCheck):
    """Health check for workflow execution reliability."""

    def __init__(self, project_root: Path | None = None, metrics_dir: Path | None = None):
        """
        Initialize execution health check.

        Args:
            project_root: Project root directory
            metrics_dir: Metrics directory
        """
        super().__init__(name="execution", dependencies=["environment"])
        self.project_root = project_root
        self.metrics_dir = metrics_dir
        self.collector = ExecutionMetricsCollector(
            metrics_dir=metrics_dir, project_root=project_root
        )

    def run(self) -> HealthCheckResult:
        """
        Run execution health check.

        Returns:
            HealthCheckResult with execution status
        """
        try:
            # Get metrics for last 30 days
            metrics = self.collector.get_metrics(limit=10000)

            if not metrics:
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    score=50.0,
                    message="No execution metrics available - workflows may not have run yet",
                    details={"total_executions": 0},
                    remediation=["Run a workflow to generate execution metrics"],
                )

            # Filter to last 7 and 30 days
            now = datetime.now(UTC)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)

            metrics_7d = [
                m
                for m in metrics
                if datetime.fromisoformat(m.started_at.replace("Z", "+00:00")) >= seven_days_ago
            ]
            metrics_30d = [
                m
                for m in metrics
                if datetime.fromisoformat(m.started_at.replace("Z", "+00:00")) >= thirty_days_ago
            ]

            # Calculate success rate (use 7-day window, fallback to 30-day, then all)
            target_window = metrics_7d if metrics_7d else (metrics_30d if metrics_30d else metrics)
            total = len(target_window)
            successful = sum(1 for m in target_window if m.status == "success")
            success_rate = (successful / total * 100) if total > 0 else 0.0

            # Calculate duration statistics
            durations = [m.duration_ms for m in target_window]
            durations_sorted = sorted(durations)
            median_duration = (
                durations_sorted[len(durations_sorted) // 2] if durations_sorted else 0.0
            )
            p95_duration = (
                durations_sorted[int(len(durations_sorted) * 0.95)]
                if len(durations_sorted) > 0
                else 0.0
            )

            # Calculate retry rate
            total_retries = sum(m.retry_count for m in target_window)
            retry_rate = (total_retries / total) if total > 0 else 0.0

            # Categorize errors
            error_categories: dict[str, int] = {}
            for m in target_window:
                if m.status != "success" and m.error_message:
                    error_msg = m.error_message.lower()
                    if "tool" in error_msg or "command not found" in error_msg:
                        category = "tool_missing"
                    elif "config" in error_msg or "configuration" in error_msg:
                        category = "config_invalid"
                    elif "model" in error_msg or "api" in error_msg or "key" in error_msg:
                        category = "model_unavailable"
                    elif "timeout" in error_msg:
                        category = "timeout"
                    elif "permission" in error_msg or "access" in error_msg:
                        category = "permission_denied"
                    else:
                        category = "other"
                    error_categories[category] = error_categories.get(category, 0) + 1

            # Determine status based on success rate
            if success_rate >= 95.0:
                status = "healthy"
                score = 100.0 - max(0, (100 - success_rate) * 2)
            elif success_rate >= 85.0:
                status = "degraded"
                score = 70.0 + ((success_rate - 85.0) / 10.0 * 15.0)
            else:
                status = "unhealthy"
                score = max(0, success_rate * 0.7)

            # Build message
            message = (
                f"Success rate: {success_rate:.1f}% ({successful}/{total} workflows)"
                f" | Median duration: {median_duration:.0f}ms"
            )

            # Build remediation actions
            remediation = []
            if success_rate < 95.0:
                remediation.append("Success rate below target (95%) - investigate failures")
            if error_categories:
                top_error = max(error_categories.items(), key=lambda x: x[1])
                remediation.append(
                    f"Top error category: {top_error[0]} ({top_error[1]} occurrences)"
                )
            if retry_rate > 0.1:
                remediation.append(f"High retry rate: {retry_rate:.2f} - check system stability")

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=score,
                message=message,
                details={
                    "total_executions": total,
                    "success_rate": success_rate,
                    "successful": successful,
                    "failed": total - successful,
                    "median_duration_ms": median_duration,
                    "p95_duration_ms": p95_duration,
                    "retry_rate": retry_rate,
                    "error_categories": error_categories,
                    "window_days": 7 if metrics_7d else (30 if metrics_30d else None),
                },
                remediation=remediation if remediation else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Execution check failed: {e}",
                details={"error": str(e)},
                remediation=["Check execution metrics directory permissions"],
            )

