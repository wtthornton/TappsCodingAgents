"""
Enhanced Metrics Collection and Reporting

High-quality enhancements to TappsCodingAgents metrics capture and reporting:
- Thread-safe operations
- Data validation
- Date range filtering
- Batch operations
- Performance optimizations
- Metrics retention policies
- Enhanced error handling
"""

from __future__ import annotations

import json
import logging
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Valid status values
VALID_STATUSES = {"success", "failed", "timeout", "cancelled", "running"}


@dataclass
class ExecutionMetric:
    """Single execution metric record with validation. Plan 4.2: skill, gate_pass."""

    execution_id: str
    workflow_id: str
    step_id: str
    command: str
    status: str  # "success", "failed", "timeout", "cancelled", "running"
    duration_ms: float
    started_at: str  # ISO timestamp
    retry_count: int = 0
    completed_at: str | None = None  # ISO timestamp
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    skill: str | None = None  # skill/agent name (plan 4.2)
    gate_pass: bool | None = None  # quality gate passed, when applicable (plan 4.2)

    def __post_init__(self):
        """Validate metric data after initialization."""
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {VALID_STATUSES}")
        if self.duration_ms < 0:
            raise ValueError(f"Duration cannot be negative: {self.duration_ms}")
        if self.retry_count < 0:
            raise ValueError(f"Retry count cannot be negative: {self.retry_count}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionMetric:
        """Create from dictionary with validation. Filters to known fields for backward compatibility."""
        required = {"execution_id", "workflow_id", "step_id", "command", "status", "duration_ms", "started_at"}
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        known = required | {"retry_count", "completed_at", "error_message", "metadata", "skill", "gate_pass"}
        return cls(**{k: v for k, v in data.items() if k in known})

    def validate(self) -> list[str]:
        """
        Validate metric data and return list of validation errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if self.status not in VALID_STATUSES:
            errors.append(f"Invalid status: {self.status}")
        
        if self.duration_ms < 0:
            errors.append(f"Negative duration: {self.duration_ms}")
        
        if self.retry_count < 0:
            errors.append(f"Negative retry count: {self.retry_count}")
        
        # Validate timestamps
        try:
            datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            errors.append(f"Invalid started_at timestamp: {e}")
        
        if self.completed_at:
            try:
                datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                errors.append(f"Invalid completed_at timestamp: {e}")
        
        return errors


class EnhancedExecutionMetricsCollector:
    """
    Enhanced execution metrics collector with thread safety, validation, and performance optimizations.
    
    Features:
    - Thread-safe operations with locking
    - Data validation before storage
    - Date range filtering
    - Batch operations
    - Write buffering for performance
    - Metrics retention policies
    - Enhanced error handling
    """

    def __init__(
        self,
        metrics_dir: Path | None = None,
        project_root: Path | None = None,
        max_cache_size: int = 1000,
        write_buffer_size: int = 10,
        retention_days: int | None = None,
        enable_validation: bool = True,
    ):
        """
        Initialize enhanced metrics collector.

        Args:
            metrics_dir: Directory to store metrics (defaults to .tapps-agents/metrics)
            project_root: Project root directory (defaults to current directory)
            max_cache_size: Maximum number of metrics to keep in memory cache
            write_buffer_size: Number of metrics to buffer before writing (0 = immediate write)
            retention_days: Number of days to retain metrics (None = no automatic cleanup)
            enable_validation: Whether to validate metrics before storing
        """
        self.project_root = project_root or Path.cwd()
        self.metrics_dir = metrics_dir or (self.project_root / ".tapps-agents" / "metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_cache_size = max_cache_size
        self.write_buffer_size = write_buffer_size
        self.retention_days = retention_days
        self.enable_validation = enable_validation

        # Thread-safe in-memory cache
        self._recent_metrics: list[ExecutionMetric] = []
        self._write_buffer: list[ExecutionMetric] = []
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Statistics
        self._stats = {
            "total_recorded": 0,
            "total_failed": 0,
            "validation_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

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
        metadata: dict[str, Any] | None = None,
        *,
        skill: str | None = None,
        gate_pass: bool | None = None,
    ) -> ExecutionMetric:
        """
        Record an execution metric with validation and thread safety.

        Args:
            workflow_id: Workflow identifier
            step_id: Step identifier
            command: Command that was executed
            status: Execution status (must be in VALID_STATUSES)
            duration_ms: Execution duration in milliseconds
            retry_count: Number of retries
            started_at: Start timestamp (defaults to now)
            completed_at: Completion timestamp (defaults to now)
            error_message: Error message if failed
            metadata: Optional metadata dictionary

        Returns:
            Created ExecutionMetric

        Raises:
            ValueError: If validation fails
        """
        execution_id = str(uuid4())
        started_at = started_at or datetime.now(UTC)
        completed_at = completed_at or datetime.now(UTC)

        try:
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
                metadata=metadata or {},
                skill=skill,
                gate_pass=gate_pass,
            )

            # Validate if enabled
            if self.enable_validation:
                validation_errors = metric.validate()
                if validation_errors:
                    self._stats["validation_errors"] += 1
                    error_msg = f"Validation failed: {', '.join(validation_errors)}"
                    logger.warning(error_msg)
                    raise ValueError(error_msg)

            # Thread-safe storage
            with self._lock:
                # Add to write buffer
                self._write_buffer.append(metric)
                
                # Flush buffer if it reaches threshold
                if len(self._write_buffer) >= self.write_buffer_size:
                    self._flush_buffer()
                
                # Add to cache
                self._recent_metrics.append(metric)
                if len(self._recent_metrics) > self.max_cache_size:
                    self._recent_metrics.pop(0)
                
                self._stats["total_recorded"] += 1

            # Dual-write to analytics (best-effort; does not block)
            try:
                from .analytics_dual_write import record_agent_execution_to_analytics

                agent_id = skill or command or "unknown"
                ts = None
                if metric.completed_at:
                    try:
                        ts = datetime.fromisoformat(
                            metric.completed_at.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass
                record_agent_execution_to_analytics(
                    project_root=self.project_root,
                    agent_id=agent_id,
                    agent_name=agent_id,
                    duration_seconds=duration_ms / 1000.0,
                    success=(status == "success"),
                    timestamp=ts,
                )
            except Exception as e:  # pylint: disable=broad-except
                logger.debug("Analytics dual-write (agent) failed: %s", e)

            return metric

        except Exception as e:
            self._stats["total_failed"] += 1
            logger.error(f"Failed to record execution metric: {e}", exc_info=True)
            raise

    def record_batch(
        self,
        metrics: list[dict[str, Any]],
    ) -> list[ExecutionMetric]:
        """
        Record multiple execution metrics in batch.

        Args:
            metrics: List of metric dictionaries

        Returns:
            List of created ExecutionMetric instances
        """
        recorded = []
        errors = []
        
        for metric_data in metrics:
            try:
                metric = self.record_execution(**metric_data)
                recorded.append(metric)
            except Exception as e:
                errors.append((metric_data.get("workflow_id", "unknown"), str(e)))
                logger.warning(f"Failed to record batch metric: {e}")
        
        if errors:
            logger.warning(f"Batch recording completed with {len(errors)} errors out of {len(metrics)}")
        
        return recorded

    def _flush_buffer(self) -> None:
        """Flush write buffer to disk (thread-safe)."""
        if not self._write_buffer:
            return
        
        # Copy buffer and clear it
        buffer_copy = self._write_buffer.copy()
        self._write_buffer.clear()
        
        # Write all metrics in batch
        try:
            # Group by date for efficient writing
            by_date: dict[str, list[ExecutionMetric]] = defaultdict(list)
            for metric in buffer_copy:
                # Extract date from started_at timestamp
                try:
                    metric_date = datetime.fromisoformat(
                        metric.started_at.replace("Z", "+00:00")
                    ).strftime("%Y-%m-%d")
                    by_date[metric_date].append(metric)
                except Exception as e:
                    logger.warning(f"Failed to extract date from metric {metric.execution_id}: {e}")
                    # Fallback to current date
                    metric_date = datetime.now(UTC).strftime("%Y-%m-%d")
                    by_date[metric_date].append(metric)
            
            # Write each date's metrics
            for date_str, date_metrics in by_date.items():
                metrics_file = self.metrics_dir / f"executions_{date_str}.jsonl"
                try:
                    with open(metrics_file, "a", encoding="utf-8") as f:
                        for metric in date_metrics:
                            f.write(json.dumps(metric.to_dict(), ensure_ascii=False) + "\n")
                except Exception as e:
                    logger.error(f"Failed to write metrics to {metrics_file}: {e}")
                    # Re-add failed metrics to buffer for retry
                    self._write_buffer.extend(date_metrics)
        
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {e}", exc_info=True)
            # Re-add all metrics to buffer for retry
            self._write_buffer.extend(buffer_copy)

    def flush(self) -> None:
        """Manually flush write buffer."""
        with self._lock:
            self._flush_buffer()

    def get_metrics(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionMetric]:
        """
        Get execution metrics with enhanced filtering options.

        Args:
            workflow_id: Filter by workflow ID
            step_id: Filter by step ID
            status: Filter by status
            start_date: Filter metrics from this date onwards
            end_date: Filter metrics up to this date
            limit: Maximum number of metrics to return
            offset: Number of metrics to skip (for pagination)

        Returns:
            List of ExecutionMetric instances
        """
        with self._lock:
            metrics: list[ExecutionMetric] = []
            seen_ids: set[str] = set()

            # Search recent cache first
            for metric in reversed(self._recent_metrics):
                if len(metrics) >= limit + offset:
                    break

                # Apply filters
                if workflow_id and metric.workflow_id != workflow_id:
                    continue
                if step_id and metric.step_id != step_id:
                    continue
                if status and metric.status != status:
                    continue
                
                # Date range filtering
                if start_date or end_date:
                    try:
                        metric_date = datetime.fromisoformat(
                            metric.started_at.replace("Z", "+00:00")
                        )
                        if start_date and metric_date < start_date:
                            continue
                        if end_date and metric_date > end_date:
                            continue
                    except Exception:
                        # Skip if date parsing fails
                        continue

                # Avoid duplicates
                if metric.execution_id in seen_ids:
                    continue
                seen_ids.add(metric.execution_id)
                
                metrics.append(metric)
                self._stats["cache_hits"] += 1

            # If we need more, search files
            if len(metrics) < limit + offset:
                needed = limit + offset - len(metrics)
                file_metrics = self._load_metrics_from_files(
                    workflow_id=workflow_id,
                    step_id=step_id,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    limit=needed,
                    exclude_ids=seen_ids,
                )
                metrics.extend(file_metrics)
                self._stats["cache_misses"] += len(file_metrics)

            # Apply pagination
            return metrics[offset:offset + limit]

    def _load_metrics_from_files(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        exclude_ids: set[str] | None = None,
    ) -> list[ExecutionMetric]:
        """Load metrics from files with date range filtering."""
        metrics: list[ExecutionMetric] = []
        exclude_ids = exclude_ids or set()

        # Determine date range for file filtering
        if start_date:
            start_date_str = start_date.strftime("%Y-%m-%d")
        else:
            start_date_str = None
        
        if end_date:
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            end_date_str = None

        # Get metrics files, filtered by date range if specified
        all_files = sorted(
            self.metrics_dir.glob("executions_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        
        # Filter files by date range
        metrics_files = []
        for metrics_file in all_files:
            if len(metrics) >= limit:
                break
            
            # Extract date from filename
            try:
                file_date_str = metrics_file.stem.split("_")[-1]  # executions_YYYY-MM-DD
                if start_date_str and file_date_str < start_date_str:
                    continue
                if end_date_str and file_date_str > end_date_str:
                    continue
                metrics_files.append(metrics_file)
            except Exception:
                # Include file if date extraction fails
                metrics_files.append(metrics_file)

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
                            
                            # Date range filtering (more precise than file-level)
                            if start_date or end_date:
                                try:
                                    metric_date = datetime.fromisoformat(
                                        metric.started_at.replace("Z", "+00:00")
                                    )
                                    if start_date and metric_date < start_date:
                                        continue
                                    if end_date and metric_date > end_date:
                                        continue
                                except Exception:
                                    continue

                            metrics.append(metric)
                        except Exception as e:
                            logger.debug(f"Failed to parse metric line: {e}")
                            continue

            except Exception as e:
                logger.warning(f"Failed to load metrics from {metrics_file}: {e}")

        return metrics

    def get_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get metrics summary with optional date range filtering.

        Args:
            start_date: Start date for summary calculation
            end_date: End date for summary calculation

        Returns:
            Dictionary with summary statistics
        """
        all_metrics = self.get_metrics(
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Large limit for summary
        )

        if not all_metrics:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "median_duration_ms": 0.0,
                "min_duration_ms": 0.0,
                "max_duration_ms": 0.0,
                "total_retries": 0,
                "by_status": {status: 0 for status in VALID_STATUSES},
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
            }

        durations = [m.duration_ms for m in all_metrics]
        durations_sorted = sorted(durations)
        
        total = len(all_metrics)
        successful = sum(1 for m in all_metrics if m.status == "success")
        total_duration = sum(durations)
        total_retries = sum(m.retry_count for m in all_metrics)
        
        # Calculate median
        median_duration = (
            durations_sorted[len(durations_sorted) // 2]
            if durations_sorted
            else 0.0
        )

        return {
            "total_executions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_duration_ms": total_duration / total if total > 0 else 0.0,
            "median_duration_ms": median_duration,
            "min_duration_ms": min(durations) if durations else 0.0,
            "max_duration_ms": max(durations) if durations else 0.0,
            "total_retries": total_retries,
            "by_status": {
                status: sum(1 for m in all_metrics if m.status == status)
                for status in VALID_STATUSES
            },
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "stats": self._stats.copy(),
        }

    def get_summary_by_skill(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 10000,
    ) -> dict[str, dict[str, Any]]:
        """
        Get metrics summary grouped by skill (plan 4.2).

        Returns:
            Dict mapping skill name (or "unknown") to {
                total, success_count, success_rate, average_duration_ms,
                gate_pass_count, gate_pass_rate (only when gate_pass is recorded)
            }
        """
        all_metrics = self.get_metrics(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
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

    def cleanup_old_metrics(self, days_to_keep: int | None = None) -> int:
        """
        Clean up metrics older than retention period.

        Args:
            days_to_keep: Number of days to keep (uses retention_days if None)

        Returns:
            Number of files deleted
        """
        retention = days_to_keep or self.retention_days
        if retention is None:
            logger.debug("No retention policy configured, skipping cleanup")
            return 0

        cutoff_date = datetime.now(UTC) - timedelta(days=retention)
        cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")

        deleted_count = 0
        for metrics_file in self.metrics_dir.glob("executions_*.jsonl"):
            try:
                # Extract date from filename
                file_date_str = metrics_file.stem.split("_")[-1]
                if file_date_str < cutoff_date_str:
                    metrics_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old metrics file: {metrics_file}")
            except Exception as e:
                logger.warning(f"Failed to process file {metrics_file} for cleanup: {e}")

        return deleted_count

    def get_stats(self) -> dict[str, Any]:
        """Get collector statistics."""
        return {
            **self._stats,
            "cache_size": len(self._recent_metrics),
            "buffer_size": len(self._write_buffer),
        }
