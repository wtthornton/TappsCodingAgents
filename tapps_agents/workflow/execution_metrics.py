"""
Execution Metrics Collection for Background Agent Auto-Execution.

Collects and stores metrics about workflow step execution.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetric:
    """Single execution metric record."""

    execution_id: str
    workflow_id: str
    step_id: str
    command: str
    status: str  # "success", "failed", "timeout", "cancelled"
    duration_ms: float
    started_at: str  # ISO timestamp
    retry_count: int = 0
    completed_at: str | None = None  # ISO timestamp
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionMetric:
        """Create from dictionary."""
        return cls(**data)


class ExecutionMetricsCollector:
    """Collects and stores execution metrics."""

    def __init__(self, metrics_dir: Path | None = None, project_root: Path | None = None):
        """
        Initialize metrics collector.

        Args:
            metrics_dir: Directory to store metrics (defaults to .tapps-agents/metrics)
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.metrics_dir = metrics_dir or (self.project_root / ".tapps-agents" / "metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for recent metrics
        self._recent_metrics: list[ExecutionMetric] = []
        self._max_cache_size = 100

    def record_execution(
        self,
        workflow_id: str,
        step_id: str,
        command: str,
        status: str,
        duration_ms: float,
        retry_count: int = 0,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> ExecutionMetric:
        """
        Record an execution metric.

        Args:
            workflow_id: Workflow identifier
            step_id: Step identifier
            command: Command that was executed
            status: Execution status
            duration_ms: Execution duration in milliseconds
            retry_count: Number of retries
            started_at: Start timestamp (defaults to now)
            completed_at: Completion timestamp (defaults to now)
            error_message: Error message if failed

        Returns:
            Created ExecutionMetric
        """
        execution_id = str(uuid4())
        started_at = started_at or datetime.now(UTC)
        completed_at = completed_at or datetime.now(UTC)

        metric = ExecutionMetric(
            execution_id=execution_id,
            workflow_id=workflow_id,
            step_id=step_id,
            command=command,
            status=status,
            duration_ms=duration_ms,
            retry_count=retry_count,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat() if completed_at else None,
            error_message=error_message,
        )

        # Store to file
        self._store_metric(metric)

        # Add to cache
        self._recent_metrics.append(metric)
        if len(self._recent_metrics) > self._max_cache_size:
            self._recent_metrics.pop(0)

        return metric

    def _store_metric(self, metric: ExecutionMetric) -> None:
        """Store metric to file."""
        try:
            # Store in daily files for easier management
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")
            metrics_file = self.metrics_dir / f"executions_{date_str}.jsonl"

            # Append to file (JSONL format)
            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metric.to_dict()) + "\n")

        except Exception as e:
            logger.error(f"Failed to store metric: {e}")

    def get_metrics(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionMetric]:
        """
        Get execution metrics with optional filtering.

        Args:
            workflow_id: Filter by workflow ID
            step_id: Filter by step ID
            status: Filter by status
            limit: Maximum number of metrics to return

        Returns:
            List of ExecutionMetric instances
        """
        metrics: list[ExecutionMetric] = []

        # Search recent cache first
        for metric in reversed(self._recent_metrics):
            if len(metrics) >= limit:
                break

            if workflow_id and metric.workflow_id != workflow_id:
                continue
            if step_id and metric.step_id != step_id:
                continue
            if status and metric.status != status:
                continue

            metrics.append(metric)

        # If we need more, search files
        if len(metrics) < limit:
            metrics.extend(
                self._load_metrics_from_files(
                    workflow_id=workflow_id,
                    step_id=step_id,
                    status=status,
                    limit=limit - len(metrics),
                )
            )

        return metrics[:limit]

    def _load_metrics_from_files(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionMetric]:
        """Load metrics from files."""
        metrics: list[ExecutionMetric] = []

        # Get all metrics files, sorted by date (newest first)
        metrics_files = sorted(
            self.metrics_dir.glob("executions_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for metrics_file in metrics_files:
            if len(metrics) >= limit:
                break

            try:
                with open(metrics_file, encoding="utf-8") as f:
                    # Read lines in reverse (newest first)
                    lines = f.readlines()
                    for line in reversed(lines):
                        if len(metrics) >= limit:
                            break

                        try:
                            data = json.loads(line.strip())
                            metric = ExecutionMetric.from_dict(data)

                            # Apply filters
                            if workflow_id and metric.workflow_id != workflow_id:
                                continue
                            if step_id and metric.step_id != step_id:
                                continue
                            if status and metric.status != status:
                                continue

                            metrics.append(metric)
                        except Exception:
                            continue

            except Exception as e:
                logger.warning(f"Failed to load metrics from {metrics_file}: {e}")

        return metrics

    def get_summary(self) -> dict[str, Any]:
        """
        Get metrics summary.

        Returns:
            Dictionary with summary statistics
        """
        all_metrics = self.get_metrics(limit=1000)

        if not all_metrics:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "total_retries": 0,
            }

        total = len(all_metrics)
        successful = sum(1 for m in all_metrics if m.status == "success")
        total_duration = sum(m.duration_ms for m in all_metrics)
        total_retries = sum(m.retry_count for m in all_metrics)

        return {
            "total_executions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_duration_ms": total_duration / total if total > 0 else 0.0,
            "total_retries": total_retries,
            "by_status": {
                status: sum(1 for m in all_metrics if m.status == status)
                for status in ["success", "failed", "timeout", "cancelled"]
            },
        }

