"""
Enhanced Analytics Dashboard and Access Layer

High-quality enhancements to analytics collection and reporting:
- Date range filtering
- Enhanced aggregation methods
- Performance optimizations
- Better error handling
- Metrics validation
- Query optimization
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    """Date range for filtering metrics."""
    
    start: datetime | None = None
    end: datetime | None = None
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within range."""
        if self.start and timestamp < self.start:
            return False
        if self.end and timestamp > self.end:
            return False
        return True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
        }


class EnhancedAnalyticsCollector:
    """
    Enhanced analytics collector with improved performance and filtering.
    
    Features:
    - Date range filtering
    - Enhanced aggregation
    - Performance optimizations
    - Better error handling
    """

    def __init__(self, analytics_dir: Path | None = None):
        """
        Initialize enhanced analytics collector.

        Args:
            analytics_dir: Directory to store analytics data (defaults to .tapps-agents/analytics)
        """
        if analytics_dir is None:
            analytics_dir = Path(".tapps-agents/analytics")

        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.analytics_dir / "metrics.json"
        self.history_dir = self.analytics_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def record_agent_execution(
        self,
        agent_id: str,
        agent_name: str,
        duration: float,
        success: bool,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Record an agent execution with enhanced error handling.
        
        Args:
            agent_id: Agent identifier
            agent_name: Agent name
            duration: Execution duration in seconds
            success: Whether execution was successful
            timestamp: Execution timestamp (defaults to now)
            metadata: Optional metadata dictionary
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Validate inputs
        if duration < 0:
            logger.warning(f"Negative duration for agent {agent_id}: {duration}")
            duration = 0.0

        record = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "duration": duration,
            "success": success,
            "timestamp": timestamp.isoformat(),
            "metadata": metadata or {},
        }

        # Append to history with error handling
        try:
            history_file = (
                self.history_dir / f"agents-{timestamp.strftime('%Y-%m-%d')}.jsonl"
            )
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Recorded agent execution: {agent_id}")
        except Exception as e:
            logger.error(f"Failed to record agent execution {agent_id}: {e}", exc_info=True)

    def record_workflow_execution(
        self,
        workflow_id: str,
        workflow_name: str,
        duration: float,
        steps: int,
        success: bool,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Record a workflow execution with enhanced error handling.
        
        Args:
            workflow_id: Workflow identifier
            workflow_name: Workflow name
            duration: Execution duration in seconds
            steps: Number of steps executed
            success: Whether execution was successful
            timestamp: Execution timestamp (defaults to now)
            metadata: Optional metadata dictionary
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Validate inputs
        if duration < 0:
            logger.warning(f"Negative duration for workflow {workflow_id}: {duration}")
            duration = 0.0
        if steps < 0:
            logger.warning(f"Negative steps for workflow {workflow_id}: {steps}")
            steps = 0

        record = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "duration": duration,
            "steps": steps,
            "success": success,
            "timestamp": timestamp.isoformat(),
            "metadata": metadata or {},
        }

        # Append to history with error handling
        try:
            history_file = (
                self.history_dir / f"workflows-{timestamp.strftime('%Y-%m-%d')}.jsonl"
            )
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Recorded workflow execution: {workflow_id}")
        except Exception as e:
            logger.error(f"Failed to record workflow execution {workflow_id}: {e}", exc_info=True)

    def get_agent_metrics(
        self,
        agent_id: str | None = None,
        days: int = 30,
        date_range: DateRange | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get agent performance metrics with date range filtering.

        Args:
            agent_id: Optional agent ID to filter by
            days: Number of days to look back (ignored if date_range provided)
            date_range: Optional date range filter

        Returns:
            List of agent metrics dictionaries
        """
        # Use date_range if provided, otherwise calculate from days
        if date_range:
            start_date = date_range.start
            end_date = date_range.end
        else:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

        agent_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "durations": [],
                "last_execution": None,
                "agent_name": None,
            }
        )

        # Calculate date range for file filtering
        current_date = start_date
        files_processed = 0
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            history_file = self.history_dir / f"agents-{date_str}.jsonl"

            if history_file.exists():
                try:
                    with open(history_file, encoding="utf-8") as f:
                        for line in f:
                            try:
                                record = json.loads(line.strip())
                                
                                # Parse timestamp
                                record_timestamp = datetime.fromisoformat(
                                    record["timestamp"].replace("Z", "+00:00")
                                )
                                
                                # Apply date range filter
                                if date_range and not date_range.contains(record_timestamp):
                                    continue
                                
                                # Apply agent filter
                                if agent_id and record["agent_id"] != agent_id:
                                    continue

                                agent_key = record["agent_id"]
                                agent_data[agent_key]["agent_name"] = record.get(
                                    "agent_name", agent_key
                                )
                                agent_data[agent_key]["total"] += 1

                                if record["success"]:
                                    agent_data[agent_key]["successful"] += 1
                                else:
                                    agent_data[agent_key]["failed"] += 1

                                agent_data[agent_key]["durations"].append(record["duration"])

                                if (
                                    agent_data[agent_key]["last_execution"] is None
                                    or record_timestamp > agent_data[agent_key]["last_execution"]
                                ):
                                    agent_data[agent_key]["last_execution"] = record_timestamp
                            
                            except Exception as e:
                                logger.debug(f"Failed to parse agent record: {e}")
                                continue
                    
                    files_processed += 1
                except Exception as e:
                    logger.warning(f"Failed to read {history_file}: {e}")

            current_date += timedelta(days=1)

        # Convert to metrics
        metrics = []
        for agent_id_key, data in agent_data.items():
            durations = data["durations"]
            total_duration = sum(durations)
            avg_duration = total_duration / len(durations) if durations else 0.0

            metrics.append({
                "agent_id": agent_id_key,
                "agent_name": data["agent_name"] or agent_id_key,
                "total_executions": data["total"],
                "successful_executions": data["successful"],
                "failed_executions": data["failed"],
                "average_duration": avg_duration,
                "min_duration": min(durations) if durations else 0.0,
                "max_duration": max(durations) if durations else 0.0,
                "total_duration": total_duration,
                "last_execution": data["last_execution"].isoformat() if data["last_execution"] else None,
                "success_rate": (
                    data["successful"] / data["total"] if data["total"] > 0 else 0.0
                ),
            })

        return metrics

    def get_workflow_metrics(
        self,
        workflow_id: str | None = None,
        days: int = 30,
        date_range: DateRange | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get workflow performance metrics with date range filtering.

        Args:
            workflow_id: Optional workflow ID to filter by
            days: Number of days to look back (ignored if date_range provided)
            date_range: Optional date range filter

        Returns:
            List of workflow metrics dictionaries
        """
        # Use date_range if provided, otherwise calculate from days
        if date_range:
            start_date = date_range.start
            end_date = date_range.end
        else:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

        workflow_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "durations": [],
                "steps": [],
                "last_execution": None,
                "workflow_name": None,
            }
        )

        # Calculate date range for file filtering
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            history_file = self.history_dir / f"workflows-{date_str}.jsonl"

            if history_file.exists():
                try:
                    with open(history_file, encoding="utf-8") as f:
                        for line in f:
                            try:
                                record = json.loads(line.strip())
                                
                                # Parse timestamp
                                record_timestamp = datetime.fromisoformat(
                                    record["timestamp"].replace("Z", "+00:00")
                                )
                                
                                # Apply date range filter
                                if date_range and not date_range.contains(record_timestamp):
                                    continue
                                
                                # Apply workflow filter
                                if workflow_id and record["workflow_id"] != workflow_id:
                                    continue

                                workflow_key = record["workflow_id"]
                                workflow_data[workflow_key]["workflow_name"] = record.get(
                                    "workflow_name", workflow_key
                                )
                                workflow_data[workflow_key]["total"] += 1

                                if record["success"]:
                                    workflow_data[workflow_key]["successful"] += 1
                                else:
                                    workflow_data[workflow_key]["failed"] += 1

                                workflow_data[workflow_key]["durations"].append(record["duration"])
                                workflow_data[workflow_key]["steps"].append(record["steps"])

                                if (
                                    workflow_data[workflow_key]["last_execution"] is None
                                    or record_timestamp > workflow_data[workflow_key]["last_execution"]
                                ):
                                    workflow_data[workflow_key]["last_execution"] = record_timestamp
                            
                            except Exception as e:
                                logger.debug(f"Failed to parse workflow record: {e}")
                                continue
                except Exception as e:
                    logger.warning(f"Failed to read {history_file}: {e}")

            current_date += timedelta(days=1)

        # Convert to metrics
        metrics = []
        for workflow_id_key, data in workflow_data.items():
            durations = data["durations"]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            avg_steps = (
                sum(data["steps"]) / len(data["steps"]) if data["steps"] else 0.0
            )

            metrics.append({
                "workflow_id": workflow_id_key,
                "workflow_name": data["workflow_name"] or workflow_id_key,
                "total_executions": data["total"],
                "successful_executions": data["successful"],
                "failed_executions": data["failed"],
                "average_duration": avg_duration,
                "average_steps": avg_steps,
                "last_execution": data["last_execution"].isoformat() if data["last_execution"] else None,
                "success_rate": (
                    data["successful"] / data["total"] if data["total"] > 0 else 0.0
                ),
            })

        return metrics


class MetricsAggregator:
    """
    Enhanced metrics aggregation with multiple aggregation types.
    
    Supports:
    - Summary statistics
    - Percentiles
    - Time-series aggregation
    - Grouped aggregation
    """

    @staticmethod
    def aggregate(
        metrics: list[dict[str, Any]],
        aggregation_type: str = "summary",
        group_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate metrics with enhanced options.

        Args:
            metrics: List of metric dictionaries
            aggregation_type: Type of aggregation (summary, percentiles, time_series)
            group_by: Optional field to group by (e.g., "agent_id", "workflow_id")

        Returns:
            Aggregated metrics dictionary
        """
        if not metrics:
            return {"count": 0}

        if group_by:
            return MetricsAggregator._grouped_aggregate(metrics, aggregation_type, group_by)

        if aggregation_type == "summary":
            return MetricsAggregator._summary_aggregate(metrics)
        elif aggregation_type == "percentiles":
            return MetricsAggregator._percentile_aggregate(metrics)
        elif aggregation_type == "time_series":
            return MetricsAggregator._time_series_aggregate(metrics)
        else:
            return {"count": len(metrics)}

    @staticmethod
    def _summary_aggregate(metrics: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate summary statistics."""
        total_executions = sum(m.get("total_executions", 0) for m in metrics)
        total_successful = sum(m.get("successful_executions", 0) for m in metrics)
        total_failed = sum(m.get("failed_executions", 0) for m in metrics)

        durations = []
        for m in metrics:
            if "average_duration" in m:
                durations.append(m["average_duration"])

        durations_sorted = sorted(durations) if durations else []
        
        return {
            "count": len(metrics),
            "total_executions": total_executions,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": (
                total_successful / total_executions if total_executions > 0 else 0.0
            ),
            "average_duration": sum(durations) / len(durations) if durations else 0.0,
            "median_duration": (
                durations_sorted[len(durations_sorted) // 2]
                if durations_sorted
                else 0.0
            ),
            "min_duration": min(durations) if durations else 0.0,
            "max_duration": max(durations) if durations else 0.0,
            "p25_duration": (
                durations_sorted[len(durations_sorted) // 4]
                if len(durations_sorted) >= 4
                else 0.0
            ),
            "p75_duration": (
                durations_sorted[len(durations_sorted) * 3 // 4]
                if len(durations_sorted) >= 4
                else 0.0
            ),
            "p95_duration": (
                durations_sorted[int(len(durations_sorted) * 0.95)]
                if len(durations_sorted) >= 20
                else 0.0
            ),
        }

    @staticmethod
    def _percentile_aggregate(metrics: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate percentile statistics."""
        durations = []
        success_rates = []
        
        for m in metrics:
            if "average_duration" in m:
                durations.append(m["average_duration"])
            if "success_rate" in m:
                success_rates.append(m["success_rate"])

        durations_sorted = sorted(durations) if durations else []
        success_rates_sorted = sorted(success_rates) if success_rates else []

        def percentile(data: list[float], p: float) -> float:
            """Calculate percentile."""
            if not data:
                return 0.0
            idx = int(len(data) * p)
            return data[min(idx, len(data) - 1)]

        return {
            "count": len(metrics),
            "duration_percentiles": {
                "p50": percentile(durations_sorted, 0.50),
                "p75": percentile(durations_sorted, 0.75),
                "p90": percentile(durations_sorted, 0.90),
                "p95": percentile(durations_sorted, 0.95),
                "p99": percentile(durations_sorted, 0.99),
            },
            "success_rate_percentiles": {
                "p50": percentile(success_rates_sorted, 0.50),
                "p75": percentile(success_rates_sorted, 0.75),
                "p90": percentile(success_rates_sorted, 0.90),
                "p95": percentile(success_rates_sorted, 0.95),
                "p99": percentile(success_rates_sorted, 0.99),
            },
        }

    @staticmethod
    def _time_series_aggregate(metrics: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate metrics by time intervals."""
        # Group by day
        by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
        
        for m in metrics:
            if "last_execution" in m and m["last_execution"]:
                try:
                    exec_time = datetime.fromisoformat(m["last_execution"].replace("Z", "+00:00"))
                    day_key = exec_time.strftime("%Y-%m-%d")
                    by_day[day_key].append(m)
                except Exception:
                    continue

        time_series = []
        for day, day_metrics in sorted(by_day.items()):
            summary = MetricsAggregator._summary_aggregate(day_metrics)
            time_series.append({
                "date": day,
                **summary,
            })

        return {
            "count": len(metrics),
            "time_series": time_series,
            "days": len(time_series),
        }

    @staticmethod
    def _grouped_aggregate(
        metrics: list[dict[str, Any]],
        aggregation_type: str,
        group_by: str,
    ) -> dict[str, Any]:
        """Aggregate metrics grouped by a field."""
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        
        for m in metrics:
            group_key = m.get(group_by, "unknown")
            groups[group_key].append(m)

        grouped_results = {}
        for group_key, group_metrics in groups.items():
            grouped_results[group_key] = MetricsAggregator.aggregate(
                group_metrics, aggregation_type
            )

        return {
            "count": len(metrics),
            "groups": len(groups),
            "grouped": grouped_results,
        }
