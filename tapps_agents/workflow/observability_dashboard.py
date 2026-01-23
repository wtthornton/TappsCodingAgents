"""
Observability Dashboard

Correlates metrics, traces, and logs for comprehensive workflow observability.
Supports OpenTelemetry export for integration with external tools.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .event_log import WorkflowEventLog
from .execution_graph import ExecutionGraph, ExecutionGraphGenerator
from .execution_metrics import ExecutionMetricsCollector, ExecutionMetric
from .exceptions import (
    DashboardGenerationError,
    OpenTelemetryExportError,
)
from ..core.exceptions import WorkflowNotFoundError

logger = logging.getLogger(__name__)


class ObservabilityDashboard:
    """Observability dashboard that correlates metrics, traces, and logs."""

    def __init__(
        self,
        project_root: Path | None = None,
        event_log: WorkflowEventLog | None = None,
        metrics_collector: ExecutionMetricsCollector | None = None,
    ):
        """
        Initialize observability dashboard.

        Args:
            project_root: Project root directory
            event_log: Optional WorkflowEventLog instance
            metrics_collector: Optional ExecutionMetricsCollector instance
        """
        self.project_root = project_root or Path.cwd()
        self.event_log = event_log
        self.metrics_collector = metrics_collector
        self.graph_generator = ExecutionGraphGenerator(event_log=event_log)

    def generate_dashboard(
        self, workflow_id: str | None = None
    ) -> dict[str, Any]:
        """
        Generate comprehensive dashboard data.

        Args:
            workflow_id: Optional workflow ID (if None, shows all workflows)

        Returns:
            Dashboard data dictionary

        Raises:
            ValueError: If workflow_id format is invalid
            DashboardGenerationError: If dashboard generation fails
        """
        # Validate workflow_id format if provided
        if workflow_id is not None:
            if not isinstance(workflow_id, str) or not workflow_id.strip():
                raise ValueError("workflow_id must be a non-empty string")

        try:
            dashboard: dict[str, Any] = {
                "generated_at": datetime.now(UTC).isoformat() + "Z",
                "workflow_id": workflow_id,
            }

            if workflow_id:
                # Single workflow dashboard
                dashboard.update(self._generate_workflow_dashboard(workflow_id))
            else:
                # Multi-workflow overview
                dashboard.update(self._generate_overview_dashboard())

            return dashboard
        except (ValueError, WorkflowNotFoundError):
            # Re-raise validation errors
            raise
        except Exception as e:
            raise DashboardGenerationError(f"Failed to generate dashboard: {e}") from e

    def _generate_workflow_dashboard(self, workflow_id: str) -> dict[str, Any]:
        """
        Generate dashboard for a single workflow with graceful degradation.

        Args:
            workflow_id: Workflow ID

        Returns:
            Dashboard data dictionary with available data (partial if some sources unavailable)
        """
        dashboard: dict[str, Any] = {}

        # Get execution trace if available
        trace = None
        if self.event_log:
            try:
                trace = self.event_log.get_execution_trace(workflow_id)
                dashboard["trace"] = trace
            except (FileNotFoundError, KeyError) as e:
                dashboard["trace_error"] = f"Trace not found: {e}"
                logger.warning(f"Trace not found for workflow {workflow_id}: {e}")
            except Exception as e:
                dashboard["trace_error"] = f"Failed to load trace: {e}"
                logger.warning(f"Failed to load trace for workflow {workflow_id}: {e}")

        # Generate execution graph if trace available
        if trace and self.graph_generator:
            try:
                graph = self.graph_generator.generate_graph(workflow_id)
                dashboard["graph"] = {
                    "nodes": len(graph.nodes),
                    "edges": len(graph.edges),
                    "dot": graph.to_dot(),
                    "mermaid": graph.to_mermaid(),
                }
            except Exception as e:
                dashboard["graph_error"] = str(e)
                logger.warning(f"Failed to generate graph for workflow {workflow_id}: {e}")

        # Get events if event_log available
        if self.event_log:
            try:
                events = self.event_log.read_events(workflow_id)
                dashboard["events"] = {
                    "total": len(events),
                    "by_type": self._count_events_by_type(events),
                }
            except Exception as e:
                dashboard["events_error"] = str(e)
                logger.warning(f"Failed to read events for workflow {workflow_id}: {e}")

        # Get metrics if metrics_collector available
        if self.metrics_collector:
            try:
                metrics = self.metrics_collector.get_metrics(
                    workflow_id=workflow_id, limit=1000
                )
                dashboard["metrics"] = self._aggregate_metrics(metrics)
            except Exception as e:
                dashboard["metrics_error"] = str(e)
                logger.warning(f"Failed to get metrics for workflow {workflow_id}: {e}")

        # Correlate data if both trace and metrics available
        if trace and dashboard.get("metrics"):
            try:
                dashboard["correlation"] = self._correlate_data(
                    workflow_id, trace, dashboard["metrics"]
                )
            except Exception as e:
                dashboard["correlation_error"] = str(e)
                logger.warning(f"Failed to correlate data for workflow {workflow_id}: {e}")

        return dashboard

    def _generate_overview_dashboard(self) -> dict[str, Any]:
        """Generate overview dashboard for all workflows."""
        dashboard: dict[str, Any] = {
            "workflows": [],
            "summary": {},
        }

        # Find all workflow event files
        if self.event_log:
            events_dir = self.event_log.events_dir
            if events_dir.exists():
                event_files = list(events_dir.glob("*.events.jsonl"))
                workflow_ids = [
                    f.stem.replace(".events", "") for f in event_files
                ]

                for wf_id in workflow_ids:
                    try:
                        wf_data = self._generate_workflow_dashboard(wf_id)
                        wf_data["workflow_id"] = wf_id
                        dashboard["workflows"].append(wf_data)
                    except Exception as e:
                        dashboard["workflows"].append(
                            {"workflow_id": wf_id, "error": str(e)}
                        )

                # Generate summary
                dashboard["summary"] = self._generate_summary(
                    dashboard["workflows"]
                )

        return dashboard

    def _count_events_by_type(self, events: list[Any]) -> dict[str, int]:
        """Count events by type."""
        counts: dict[str, int] = {}
        for event in events:
            event_type = event.event_type if hasattr(event, "event_type") else str(event.get("event_type", "unknown"))
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    def _aggregate_metrics(
        self, metrics: list[ExecutionMetric]
    ) -> dict[str, Any]:
        """Aggregate metrics data."""
        if not metrics:
            return {}

        total_duration = sum(m.duration_ms for m in metrics if m.duration_ms)
        avg_duration = total_duration / len(metrics) if metrics else 0

        status_counts: dict[str, int] = {}
        for metric in metrics:
            status = metric.status or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_executions": len(metrics),
            "total_duration_ms": total_duration,
            "avg_duration_ms": avg_duration,
            "status_counts": status_counts,
            "retry_count": sum(m.retry_count for m in metrics),
        }

    def _correlate_data(
        self,
        workflow_id: str,
        trace: dict[str, Any] | None,
        metrics: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Correlate trace and metrics data."""
        correlation: dict[str, Any] = {}

        if trace and metrics:
            # Match steps with metrics
            steps = trace.get("steps", [])
            step_metrics: dict[str, list[dict[str, Any]]] = {}

            if self.metrics_collector:
                all_metrics = self.metrics_collector.get_metrics(
                    workflow_id=workflow_id, limit=1000
                )

                for step in steps:
                    step_id = step.get("step_id")
                    if step_id:
                        step_metrics[step_id] = [
                            asdict(m)
                            for m in all_metrics
                            if m.step_id == step_id
                        ]

            correlation["step_metrics"] = step_metrics

            # Identify bottlenecks
            if steps:
                durations = [
                    s.get("duration_ms", 0) for s in steps if s.get("duration_ms")
                ]
                if durations:
                    max_duration = max(durations)
                    bottleneck_step = next(
                        (
                            s
                            for s in steps
                            if s.get("duration_ms") == max_duration
                        ),
                        None,
                    )
                    if bottleneck_step:
                        correlation["bottleneck"] = {
                            "step_id": bottleneck_step.get("step_id"),
                            "duration_ms": max_duration,
                        }

        return correlation

    def _generate_summary(self, workflows: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate summary statistics."""
        total_workflows = len(workflows)
        completed = sum(
            1
            for wf in workflows
            if wf.get("trace", {}).get("ended_at") is not None
        )
        failed = sum(
            1
            for wf in workflows
            if any(
                step.get("status") == "failed"
                for step in wf.get("trace", {}).get("steps", [])
            )
        )

        total_steps = sum(
            len(wf.get("trace", {}).get("steps", [])) for wf in workflows
        )

        return {
            "total_workflows": total_workflows,
            "completed": completed,
            "failed": failed,
            "in_progress": total_workflows - completed,
            "total_steps": total_steps,
        }

    def export_otel_trace(self, workflow_id: str) -> dict[str, Any]:
        """
        Export workflow trace to OpenTelemetry format.

        Args:
            workflow_id: Workflow ID

        Returns:
            OpenTelemetry trace dictionary

        Raises:
            ValueError: If workflow_id is invalid
            OpenTelemetryExportError: If export fails
        """
        # Validate inputs
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")

        if not self.event_log:
            raise ValueError("WorkflowEventLog required for OpenTelemetry export")

        try:
            trace = self.event_log.get_execution_trace(workflow_id)
        except FileNotFoundError as e:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found") from e
        except Exception as e:
            raise OpenTelemetryExportError(f"Failed to load trace for workflow {workflow_id}: {e}") from e

        if not trace or not isinstance(trace, dict):
            raise OpenTelemetryExportError(f"Invalid trace structure for workflow {workflow_id}")

        if not trace.get("steps"):
            raise OpenTelemetryExportError(f"Workflow {workflow_id} has no steps to export")
        
        # Convert to OpenTelemetry format
        try:
            otel_trace = {
                "resourceSpans": [
                    {
                        "resource": {
                            "attributes": [
                                {"key": "service.name", "value": {"stringValue": "tapps-agents"}},
                                {"key": "workflow.id", "value": {"stringValue": workflow_id}},
                            ]
                        },
                        "scopeSpans": [
                            {
                                "spans": self._convert_steps_to_spans(trace.get("steps", [])),
                            }
                        ],
                    }
                ]
            }

            return otel_trace
        except Exception as e:
            raise OpenTelemetryExportError(f"Failed to convert trace to OpenTelemetry format: {e}") from e

    def _convert_steps_to_spans(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert workflow steps to OpenTelemetry spans."""
        spans = []
        
        for step in steps:
            span = {
                "traceId": step.get("step_id", ""),
                "spanId": step.get("step_id", ""),
                "name": f"{step.get('agent', 'unknown')}.{step.get('action', 'unknown')}",
                "startTimeUnixNano": self._iso_to_nanos(step.get("started_at")),
                "endTimeUnixNano": self._iso_to_nanos(step.get("ended_at")),
                "attributes": [
                    {"key": "step.id", "value": {"stringValue": step.get("step_id", "")}},
                    {"key": "agent", "value": {"stringValue": step.get("agent", "")}},
                    {"key": "action", "value": {"stringValue": step.get("action", "")}},
                    {"key": "status", "value": {"stringValue": step.get("status", "")}},
                ],
                "status": {
                    "code": 1 if step.get("status") == "failed" else 2,
                },
            }
            
            if step.get("duration_ms"):
                span["attributes"].append({
                    "key": "duration.ms",
                    "value": {"doubleValue": step.get("duration_ms")},
                })
            
            if step.get("error"):
                span["status"]["message"] = step.get("error")
            
            spans.append(span)
        
        return spans

    def _iso_to_nanos(self, iso_str: str | None) -> int:
        """Convert ISO timestamp to nanoseconds."""
        if not iso_str:
            return 0
        
        try:
            # Remove Z and parse
            dt_str = iso_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            # Convert to nanoseconds since epoch
            return int(dt.timestamp() * 1_000_000_000)
        except Exception:
            return 0

    def save_dashboard(
        self, dashboard: dict[str, Any], output_path: Path
    ) -> None:
        """
        Save dashboard data to JSON file.

        Args:
            dashboard: Dashboard data dictionary
            output_path: Output file path

        Raises:
            ValueError: If dashboard or output_path is invalid
            OSError: If file cannot be written
        """
        if not dashboard:
            raise ValueError("Dashboard data required")

        if not output_path:
            raise ValueError("Output path required")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create directory for {output_path}: {e}") from e

        try:
            output_path.write_text(
                json.dumps(dashboard, indent=2, default=str), encoding="utf-8"
            )
        except OSError as e:
            raise OSError(f"Cannot write dashboard file to {output_path}: {e}") from e
        except Exception as e:
            raise DashboardGenerationError(f"Failed to save dashboard: {e}") from e
