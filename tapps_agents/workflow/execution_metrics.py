"""
Execution Metrics Collection for Background Agent Auto-Execution.

Collects and stores metrics about workflow step execution.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetric:
    """Single execution metric record. Plan 4.2: skill, gate_pass."""

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
    skill: str | None = None  # skill/agent name (plan 4.2)
    gate_pass: bool | None = None  # quality gate passed, when applicable (plan 4.2)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionMetric:
        """Create from dictionary. Filters to known fields for backward compatibility."""
        known = {
            "execution_id", "workflow_id", "step_id", "command", "status",
            "duration_ms", "started_at", "retry_count", "completed_at", "error_message",
            "skill", "gate_pass",
        }
        return cls(**{k: v for k, v in data.items() if k in known})


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
        self._write_lock = threading.Lock()

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
        *,
        skill: str | None = None,
        gate_pass: bool | None = None,
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
            skill=skill,
            gate_pass=gate_pass,
        )

        # Store to file
        self._store_metric(metric)

        # Dual-write to analytics (best-effort; does not block)
        try:
            from .analytics_dual_write import record_agent_execution_to_analytics

            agent_id = skill or command or "unknown"
            record_agent_execution_to_analytics(
                project_root=self.project_root,
                agent_id=agent_id,
                agent_name=agent_id,
                duration_seconds=duration_ms / 1000.0,
                success=(status == "success"),
                timestamp=completed_at,
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Analytics dual-write (agent) failed: %s", e)

        # Add to cache
        self._recent_metrics.append(metric)
        if len(self._recent_metrics) > self._max_cache_size:
            self._recent_metrics.pop(0)

        return metric

    def _store_metric(self, metric: ExecutionMetric) -> None:
        """Store metric to file."""
        try:
            # Use metric's started_at for file naming (not current time)
            try:
                metric_date = datetime.fromisoformat(
                    metric.started_at.replace("Z", "+00:00")
                )
                date_str = metric_date.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                date_str = datetime.now(UTC).strftime("%Y-%m-%d")

            metrics_file = self.metrics_dir / f"executions_{date_str}.jsonl"

            # Append to file (JSONL format, thread-safe)
            with self._write_lock, open(metrics_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(metric.to_dict()) + "\n")
                    f.flush()

        except Exception as e:
            logger.error("Failed to store metric: %s", e)

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
        seen_ids: set[str] = set()

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

            # Avoid duplicates
            if metric.execution_id in seen_ids:
                continue
            seen_ids.add(metric.execution_id)
            metrics.append(metric)

        # If we need more, search files
        if len(metrics) < limit:
            file_metrics = self._load_metrics_from_files(
                workflow_id=workflow_id,
                step_id=step_id,
                status=status,
                limit=limit - len(metrics),
                exclude_ids=seen_ids,
            )
            metrics.extend(file_metrics)

        return metrics[:limit]

    def _load_metrics_from_files(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        exclude_ids: set[str] | None = None,
    ) -> list[ExecutionMetric]:
        """Load metrics from files."""
        metrics: list[ExecutionMetric] = []
        exclude_ids = exclude_ids or set()

        # Get all metrics files, sorted by filename date (newest first)
        metrics_files = sorted(
            self.metrics_dir.glob("executions_*.jsonl"),
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

                            # Skip if already seen (from cache)
                            if metric.execution_id in exclude_ids:
                                continue

                            # Apply filters
                            if workflow_id and metric.workflow_id != workflow_id:
                                continue
                            if step_id and metric.step_id != step_id:
                                continue
                            if status and metric.status != status:
                                continue

                            metrics.append(metric)
                        except json.JSONDecodeError as e:
                            logger.warning("Corrupted JSON in %s: %s", metrics_file, e)
                            continue
                        except (KeyError, ValueError, TypeError):
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
        all_metrics = self.get_metrics(limit=10000)

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

    def get_summary_by_skill(
        self,
        limit: int = 1000,
    ) -> dict[str, dict[str, Any]]:
        """
        Get metrics summary grouped by skill (plan 4.2).

        Returns:
            Dict mapping skill name (or "unknown") to {
                total, success_count, success_rate, average_duration_ms,
                gate_pass_count, gate_pass_rate (only when gate_pass is recorded)
            }
        """
        all_metrics = self.get_metrics(limit=limit)
        by_skill: dict[str, list[ExecutionMetric]] = {}
        for m in all_metrics:
            k = m.skill if m.skill else "unknown"
            by_skill.setdefault(k, []).append(m)
        out: dict[str, dict[str, Any]] = {}
        for skill_name, ms in by_skill.items():
            total = len(ms)
            ok = sum(1 for x in ms if x.status == "success")
            dur = sum(x.duration_ms for x in ms)
            with_gate = [x for x in ms if x.gate_pass is not None]
            gate_ok = sum(1 for x in with_gate if x.gate_pass is True)
            rec: dict[str, Any] = {
                "total": total,
                "success_count": ok,
                "success_rate": ok / total if total else 0.0,
                "average_duration_ms": dur / total if total else 0.0,
            }
            if with_gate:
                rec["gate_pass_count"] = gate_ok
                rec["gate_pass_rate"] = gate_ok / len(with_gate) if with_gate else 0.0
            out[skill_name] = rec
        return out

    def cleanup_old_metrics(self, days_to_keep: int = 90) -> int:
        """Delete JSONL files older than retention period.

        Returns:
            Number of files deleted.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        deleted = 0
        for metrics_file in self.metrics_dir.glob("executions_*.jsonl"):
            try:
                date_str = metrics_file.stem.replace("executions_", "")
                if date_str < cutoff:
                    metrics_file.unlink()
                    deleted += 1
                    logger.info("Deleted old metrics file: %s", metrics_file.name)
            except (ValueError, OSError) as e:
                logger.warning("Could not delete %s: %s", metrics_file, e)
        return deleted

