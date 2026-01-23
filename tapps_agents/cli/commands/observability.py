"""
Observability command handlers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ...workflow.event_log import WorkflowEventLog
from ...workflow.execution_metrics import ExecutionMetricsCollector
from ...workflow.observability_dashboard import ObservabilityDashboard
from ...workflow.graph_visualizer import GraphVisualizer
from ..feedback import get_feedback
from .common import format_json_output


def handle_observability_dashboard_command(
    workflow_id: str | None = None,
    output_format: str = "text",
    output_file: Path | None = None,
    project_root: Path | None = None,
) -> None:
    """
    Handle observability dashboard command.

    Args:
        workflow_id: Optional workflow ID (if None, shows all workflows)
        output_format: Output format (json, text, html)
        output_file: Optional output file path
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()
    feedback = get_feedback()
    feedback.format_type = output_format

    # Initialize components
    events_dir = project_root / ".tapps-agents" / "workflow-state" / "events"
    event_log = WorkflowEventLog(events_dir=events_dir)
    
    metrics_dir = project_root / ".tapps-agents" / "metrics"
    metrics_collector = ExecutionMetricsCollector(metrics_dir=metrics_dir, project_root=project_root)

    # Create dashboard
    dashboard = ObservabilityDashboard(
        project_root=project_root,
        event_log=event_log,
        metrics_collector=metrics_collector,
    )

    feedback.start_operation("Observability Dashboard", f"Generating dashboard for {workflow_id or 'all workflows'}")
    
    try:
        dashboard_data = dashboard.generate_dashboard(workflow_id=workflow_id)
        feedback.clear_progress()

        # Format output
        if output_format == "json":
            output = json.dumps(dashboard_data, indent=2, default=str)
            if output_file:
                output_file.write_text(output, encoding="utf-8")
                feedback.success(f"Dashboard saved to {output_file}")
            else:
                print(output)
        elif output_format == "html":
            if not workflow_id:
                feedback.error("HTML output requires --workflow-id", exit_code=2)
                return
            
            # Generate HTML with graph
            if output_file is None:
                output_file = project_root / ".tapps-agents" / "observability" / f"{workflow_id}_dashboard.html"
            
            try:
                graph = dashboard.graph_generator.generate_graph(workflow_id)
                GraphVisualizer.generate_html_view(graph, output_file)
                feedback.success(f"HTML dashboard saved to {output_file}")
            except Exception as e:
                feedback.error(f"Failed to generate HTML dashboard: {e}", exit_code=1)
        else:
            # Text format
            output_lines = [
                "=" * 60,
                f"Observability Dashboard: {workflow_id or 'All Workflows'}",
                "=" * 60,
                "",
            ]

            if workflow_id:
                # Single workflow
                trace = dashboard_data.get("trace", {})
                if trace:
                    output_lines.extend([
                        f"Workflow ID: {workflow_id}",
                        f"Started: {trace.get('started_at', 'N/A')}",
                        f"Ended: {trace.get('ended_at', 'N/A')}",
                        f"Total Steps: {len(trace.get('steps', []))}",
                        "",
                    ])

                metrics = dashboard_data.get("metrics", {})
                if metrics:
                    output_lines.extend([
                        "Metrics:",
                        f"  Total Executions: {metrics.get('total_executions', 0)}",
                        f"  Total Duration: {metrics.get('total_duration_ms', 0):.0f}ms",
                        f"  Avg Duration: {metrics.get('avg_duration_ms', 0):.0f}ms",
                        "",
                    ])

                correlation = dashboard_data.get("correlation", {})
                if correlation.get("bottleneck"):
                    bottleneck = correlation["bottleneck"]
                    output_lines.extend([
                        "Bottleneck:",
                        f"  Step: {bottleneck.get('step_id')}",
                        f"  Duration: {bottleneck.get('duration_ms', 0):.0f}ms",
                        "",
                    ])

                graph_info = dashboard_data.get("graph", {})
                if graph_info:
                    output_lines.extend([
                        "Execution Graph:",
                        f"  Nodes: {graph_info.get('nodes', 0)}",
                        f"  Edges: {graph_info.get('edges', 0)}",
                        "",
                    ])
            else:
                # Overview
                summary = dashboard_data.get("summary", {})
                if summary:
                    output_lines.extend([
                        "Summary:",
                        f"  Total Workflows: {summary.get('total_workflows', 0)}",
                        f"  Completed: {summary.get('completed', 0)}",
                        f"  Failed: {summary.get('failed', 0)}",
                        f"  In Progress: {summary.get('in_progress', 0)}",
                        f"  Total Steps: {summary.get('total_steps', 0)}",
                        "",
                    ])

                workflows = dashboard_data.get("workflows", [])
                if workflows:
                    output_lines.append("Workflows:")
                    for wf in workflows[:10]:  # Show first 10
                        wf_id = wf.get("workflow_id", "unknown")
                        trace = wf.get("trace", {})
                        steps = trace.get("steps", [])
                        output_lines.append(f"  - {wf_id}: {len(steps)} steps")
                    
                    if len(workflows) > 10:
                        output_lines.append(f"  ... and {len(workflows) - 10} more")

            output = "\n".join(output_lines)
            
            if output_file:
                output_file.write_text(output, encoding="utf-8")
                feedback.success(f"Dashboard saved to {output_file}")
            else:
                print(output)

    except Exception as e:
        feedback.error(f"Failed to generate dashboard: {e}", exit_code=1)
        if output_format == "json":
            print(json.dumps({"error": str(e)}, indent=2))


def handle_observability_graph_command(
    workflow_id: str,
    output_format: str = "dot",
    output_file: Path | None = None,
    project_root: Path | None = None,
) -> None:
    """
    Handle observability graph command.

    Args:
        workflow_id: Workflow ID (required)
        output_format: Output format (dot, mermaid, html, summary)
        output_file: Optional output file path
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()
    feedback = get_feedback()

    # Initialize components
    events_dir = project_root / ".tapps-agents" / "workflow-state" / "events"
    event_log = WorkflowEventLog(events_dir=events_dir)
    
    from ...workflow.execution_graph import ExecutionGraphGenerator
    generator = ExecutionGraphGenerator(event_log=event_log)

    feedback.start_operation("Execution Graph", f"Generating graph for {workflow_id}")
    
    try:
        graph = generator.generate_graph(workflow_id)
        feedback.clear_progress()

        # Determine output file
        if output_file is None:
            output_dir = project_root / ".tapps-agents" / "observability" / "graphs"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            ext_map = {
                "dot": ".dot",
                "mermaid": ".mmd",
                "html": ".html",
                "summary": ".txt",
            }
            ext = ext_map.get(output_format, ".txt")
            output_file = output_dir / f"{workflow_id}{ext}"

        # Generate output
        if output_format == "dot":
            generator.save_dot(graph, output_file)
            feedback.success(f"DOT graph saved to {output_file}")
        elif output_format == "mermaid":
            generator.save_mermaid(graph, output_file)
            feedback.success(f"Mermaid graph saved to {output_file}")
        elif output_format == "html":
            GraphVisualizer.generate_html_view(graph, output_file)
            feedback.success(f"HTML graph saved to {output_file}")
        elif output_format == "summary":
            GraphVisualizer.save_summary(graph, output_file)
            feedback.success(f"Graph summary saved to {output_file}")
        else:
            feedback.error(f"Unknown output format: {output_format}", exit_code=2)

    except Exception as e:
        feedback.error(f"Failed to generate graph: {e}", exit_code=1)


def handle_observability_otel_command(
    workflow_id: str,
    output_file: Path | None = None,
    project_root: Path | None = None,
) -> None:
    """
    Handle observability OpenTelemetry export command.

    Args:
        workflow_id: Workflow ID (required)
        output_file: Optional output file path
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()
    feedback = get_feedback()

    # Initialize components
    events_dir = project_root / ".tapps-agents" / "workflow-state" / "events"
    event_log = WorkflowEventLog(events_dir=events_dir)
    
    metrics_dir = project_root / ".tapps-agents" / "metrics"
    metrics_collector = ExecutionMetricsCollector(metrics_dir=metrics_dir, project_root=project_root)

    dashboard = ObservabilityDashboard(
        project_root=project_root,
        event_log=event_log,
        metrics_collector=metrics_collector,
    )

    feedback.start_operation("OpenTelemetry Export", f"Exporting trace for {workflow_id}")
    
    try:
        otel_trace = dashboard.export_otel_trace(workflow_id)
        feedback.clear_progress()

        # Determine output file
        if output_file is None:
            output_dir = project_root / ".tapps-agents" / "observability" / "otel"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{workflow_id}_trace.json"

        # Save OpenTelemetry trace
        output_file.write_text(
            json.dumps(otel_trace, indent=2, default=str), encoding="utf-8"
        )
        feedback.success(f"OpenTelemetry trace saved to {output_file}")

    except Exception as e:
        feedback.error(f"Failed to export OpenTelemetry trace: {e}", exit_code=1)
