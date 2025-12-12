"""
Advanced Analytics Dashboard

Provides comprehensive analytics and monitoring for agent performance, workflows, and system metrics.
Supports real-time metrics, historical trends, and performance analytics.
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for a single agent."""

    agent_id: str
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    total_duration: float = 0.0
    last_execution: datetime | None = None
    success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.last_execution:
            data["last_execution"] = self.last_execution.isoformat()
        return data


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""

    workflow_id: str
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0
    average_steps: float = 0.0
    last_execution: datetime | None = None
    success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.last_execution:
            data["last_execution"] = self.last_execution.isoformat()
        return data


@dataclass
class SystemMetrics:
    """System-wide metrics."""

    timestamp: datetime
    total_agents: int = 0
    active_workflows: int = 0
    completed_workflows_today: int = 0
    failed_workflows_today: int = 0
    average_workflow_duration: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class TrendData:
    """Historical trend data."""

    metric_name: str
    timestamps: list[str]
    values: list[float]
    unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AnalyticsCollector:
    """Collects and aggregates analytics data from various sources."""

    def __init__(self, analytics_dir: Path | None = None):
        """
        Initialize analytics collector.

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
    ):
        """Record an agent execution."""
        if timestamp is None:
            timestamp = datetime.now()

        record = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "duration": duration,
            "success": success,
            "timestamp": timestamp.isoformat(),
        }

        # Append to history
        history_file = (
            self.history_dir / f"agents-{timestamp.strftime('%Y-%m-%d')}.jsonl"
        )
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        logger.debug(f"Recorded agent execution: {agent_id}")

    def record_workflow_execution(
        self,
        workflow_id: str,
        workflow_name: str,
        duration: float,
        steps: int,
        success: bool,
        timestamp: datetime | None = None,
    ):
        """Record a workflow execution."""
        if timestamp is None:
            timestamp = datetime.now()

        record = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "duration": duration,
            "steps": steps,
            "success": success,
            "timestamp": timestamp.isoformat(),
        }

        # Append to history
        history_file = (
            self.history_dir / f"workflows-{timestamp.strftime('%Y-%m-%d')}.jsonl"
        )
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        logger.debug(f"Recorded workflow execution: {workflow_id}")

    def get_agent_metrics(
        self, agent_id: str | None = None, days: int = 30
    ) -> list[AgentPerformanceMetrics]:
        """
        Get agent performance metrics.

        Args:
            agent_id: Optional agent ID to filter by
            days: Number of days to look back

        Returns:
            List of AgentPerformanceMetrics
        """
        agent_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "durations": [],
                "last_execution": None,
            }
        )

        # Read history files
        for day_offset in range(days):
            date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            history_file = self.history_dir / f"agents-{date}.jsonl"

            if not history_file.exists():
                continue

            with open(history_file, encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line.strip())

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

                    exec_time = datetime.fromisoformat(record["timestamp"])
                    if (
                        agent_data[agent_key]["last_execution"] is None
                        or exec_time > agent_data[agent_key]["last_execution"]
                    ):
                        agent_data[agent_key]["last_execution"] = exec_time

        # Convert to metrics
        metrics = []
        for agent_id_key, data in agent_data.items():
            durations = data["durations"]
            total_duration = sum(durations)
            avg_duration = total_duration / len(durations) if durations else 0.0

            metrics.append(
                AgentPerformanceMetrics(
                    agent_id=agent_id_key,
                    agent_name=data["agent_name"],
                    total_executions=data["total"],
                    successful_executions=data["successful"],
                    failed_executions=data["failed"],
                    average_duration=avg_duration,
                    min_duration=min(durations) if durations else 0.0,
                    max_duration=max(durations) if durations else 0.0,
                    total_duration=total_duration,
                    last_execution=data["last_execution"],
                    success_rate=(
                        data["successful"] / data["total"] if data["total"] > 0 else 0.0
                    ),
                )
            )

        return metrics

    def get_workflow_metrics(
        self, workflow_id: str | None = None, days: int = 30
    ) -> list[WorkflowMetrics]:
        """
        Get workflow performance metrics.

        Args:
            workflow_id: Optional workflow ID to filter by
            days: Number of days to look back

        Returns:
            List of WorkflowMetrics
        """
        workflow_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "durations": [],
                "steps": [],
                "last_execution": None,
            }
        )

        # Read history files
        for day_offset in range(days):
            date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            history_file = self.history_dir / f"workflows-{date}.jsonl"

            if not history_file.exists():
                continue

            with open(history_file, encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line.strip())

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

                    exec_time = datetime.fromisoformat(record["timestamp"])
                    if (
                        workflow_data[workflow_key]["last_execution"] is None
                        or exec_time > workflow_data[workflow_key]["last_execution"]
                    ):
                        workflow_data[workflow_key]["last_execution"] = exec_time

        # Convert to metrics
        metrics = []
        for workflow_id_key, data in workflow_data.items():
            durations = data["durations"]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            avg_steps = (
                sum(data["steps"]) / len(data["steps"]) if data["steps"] else 0.0
            )

            metrics.append(
                WorkflowMetrics(
                    workflow_id=workflow_id_key,
                    workflow_name=data["workflow_name"],
                    total_executions=data["total"],
                    successful_executions=data["successful"],
                    failed_executions=data["failed"],
                    average_duration=avg_duration,
                    average_steps=avg_steps,
                    last_execution=data["last_execution"],
                    success_rate=(
                        data["successful"] / data["total"] if data["total"] > 0 else 0.0
                    ),
                )
            )

        return metrics

    def get_trends(
        self, metric_type: str, days: int = 30, interval: str = "day"
    ) -> list[TrendData]:
        """
        Get historical trend data.

        Args:
            metric_type: Type of metric ("agent_duration", "workflow_duration", "success_rate", etc.)
            days: Number of days to look back
            interval: Aggregation interval ("hour", "day", "week")

        Returns:
            List of TrendData
        """
        trends: dict[str, TrendData] = {}

        # Aggregate data by interval
        for day_offset in range(days):
            date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")

            if metric_type.startswith("agent_"):
                history_file = self.history_dir / f"agents-{date}.jsonl"
            elif metric_type.startswith("workflow_"):
                history_file = self.history_dir / f"workflows-{date}.jsonl"
            else:
                continue

            if not history_file.exists():
                continue

            with open(history_file, encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(record["timestamp"])

                    # Determine interval key
                    if interval == "hour":
                        interval_key = timestamp.strftime("%Y-%m-%d-%H")
                    elif interval == "day":
                        interval_key = timestamp.strftime("%Y-%m-%d")
                    elif interval == "week":
                        interval_key = timestamp.strftime("%Y-W%W")
                    else:
                        interval_key = timestamp.strftime("%Y-%m-%d")

                    # Extract metric value
                    if metric_type == "agent_duration":
                        value = record["duration"]
                        metric_name = "agent_duration"
                    elif metric_type == "workflow_duration":
                        value = record["duration"]
                        metric_name = "workflow_duration"
                    elif metric_type == "agent_success_rate":
                        value = 1.0 if record["success"] else 0.0
                        metric_name = "agent_success_rate"
                    elif metric_type == "workflow_success_rate":
                        value = 1.0 if record["success"] else 0.0
                        metric_name = "workflow_success_rate"
                    else:
                        continue

                    # Initialize trend if needed
                    if metric_name not in trends:
                        trends[metric_name] = TrendData(
                            metric_name=metric_name,
                            timestamps=[],
                            values=[],
                            unit="seconds" if "duration" in metric_name else "rate",
                        )

                    # Add to trend (aggregate by interval)
                    if interval_key not in [t for t in trends[metric_name].timestamps]:
                        trends[metric_name].timestamps.append(interval_key)
                        trends[metric_name].values.append(value)
                    else:
                        # Average with existing value
                        idx = trends[metric_name].timestamps.index(interval_key)
                        trends[metric_name].values[idx] = (
                            trends[metric_name].values[idx] + value
                        ) / 2

        return list(trends.values())

    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system-wide metrics.

        Returns:
            SystemMetrics instance
        """
        # Get agent metrics
        agent_metrics = self.get_agent_metrics(days=1)
        total_agents = len(agent_metrics)

        # Get workflow metrics
        workflow_metrics = self.get_workflow_metrics(days=1)
        completed_today = sum(
            1 for w in workflow_metrics if w.successful_executions > 0
        )
        failed_today = sum(1 for w in workflow_metrics if w.failed_executions > 0)
        active_workflows = len(
            [
                w
                for w in workflow_metrics
                if w.last_execution
                and (datetime.now() - w.last_execution).total_seconds() < 3600
            ]
        )

        avg_duration = (
            sum(w.average_duration for w in workflow_metrics) / len(workflow_metrics)
            if workflow_metrics
            else 0.0
        )

        # Try to get resource metrics if available
        try:
            from .resource_monitor import ResourceMonitor

            monitor = ResourceMonitor()
            resource_metrics = monitor.get_current_metrics()
            cpu_usage = resource_metrics.cpu_percent
            memory_usage = resource_metrics.memory_percent
            disk_usage = resource_metrics.disk_percent
        except Exception:
            cpu_usage = 0.0
            memory_usage = 0.0
            disk_usage = 0.0

        return SystemMetrics(
            timestamp=datetime.now(),
            total_agents=total_agents,
            active_workflows=active_workflows,
            completed_workflows_today=completed_today,
            failed_workflows_today=failed_today,
            average_workflow_duration=avg_duration,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
        )


class AnalyticsDashboard:
    """Main analytics dashboard interface."""

    def __init__(self, analytics_dir: Path | None = None):
        """
        Initialize analytics dashboard.

        Args:
            analytics_dir: Directory for analytics data
        """
        self.collector = AnalyticsCollector(analytics_dir)

    def get_dashboard_data(self) -> dict[str, Any]:
        """
        Get comprehensive dashboard data.

        Returns:
            Dictionary with all dashboard metrics
        """
        return {
            "system": self.collector.get_system_metrics().to_dict(),
            "agents": [m.to_dict() for m in self.collector.get_agent_metrics(days=30)],
            "workflows": [
                m.to_dict() for m in self.collector.get_workflow_metrics(days=30)
            ],
            "trends": {
                "agent_duration": [
                    t.to_dict()
                    for t in self.collector.get_trends("agent_duration", days=30)
                ],
                "workflow_duration": [
                    t.to_dict()
                    for t in self.collector.get_trends("workflow_duration", days=30)
                ],
                "agent_success_rate": [
                    t.to_dict()
                    for t in self.collector.get_trends("agent_success_rate", days=30)
                ],
                "workflow_success_rate": [
                    t.to_dict()
                    for t in self.collector.get_trends("workflow_success_rate", days=30)
                ],
            },
            "timestamp": datetime.now().isoformat(),
        }

    def get_agent_performance(
        self, agent_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get agent performance metrics."""
        return [
            m.to_dict() for m in self.collector.get_agent_metrics(agent_id=agent_id)
        ]

    def get_workflow_performance(
        self, workflow_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get workflow performance metrics."""
        return [
            m.to_dict()
            for m in self.collector.get_workflow_metrics(workflow_id=workflow_id)
        ]

    def get_trends(self, metric_type: str, days: int = 30) -> list[dict[str, Any]]:
        """Get trend data."""
        return [t.to_dict() for t in self.collector.get_trends(metric_type, days=days)]

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status."""
        return self.collector.get_system_metrics().to_dict()
