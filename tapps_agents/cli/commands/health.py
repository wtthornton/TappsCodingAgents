"""
Health command handlers.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ...health.checks.automation import AutomationHealthCheck
from ...health.checks.environment import EnvironmentHealthCheck
from ...health.checks.execution import ExecutionHealthCheck
from ...health.checks.context7_cache import Context7CacheHealthCheck
from ...health.checks.knowledge_base import KnowledgeBaseHealthCheck
from ...health.checks.outcomes import OutcomeHealthCheck
from ...health.collector import HealthMetricsCollector
from ...health.dashboard import HealthDashboard
from ...health.orchestrator import HealthOrchestrator
from ...health.registry import HealthCheckRegistry
from ..feedback import get_feedback, ProgressTracker
from .common import format_json_output


def _usage_data_from_execution_metrics(project_root: Path) -> dict | None:
    """
    Build usage-like data from execution metrics when analytics is empty.

    Aggregates .tapps-agents/metrics/executions_*.jsonl by today (steps/workflows),
    by skill (agents), and by workflow_id (workflows). Returns same shape as
    AnalyticsDashboard.get_dashboard_data() for system/agents/workflows.
    """
    try:
        from ...workflow.execution_metrics import ExecutionMetricsCollector

        collector = ExecutionMetricsCollector(project_root=project_root)
        metrics = collector.get_metrics(limit=5000)
        if not metrics:
            return None

        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - timedelta(days=30)

        # Filter to last 30 days
        def parse_ts(ts: str) -> datetime:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))

        recent = [m for m in metrics if parse_ts(m.started_at) >= thirty_days_ago]
        if not recent:
            return None

        today_metrics = [m for m in recent if parse_ts(m.started_at) >= today_start]
        workflow_ids_today_success = {
            m.workflow_id for m in today_metrics if m.status == "success"
        }
        workflow_ids_today_failed = {
            m.workflow_id for m in today_metrics if m.status != "success"
        }
        completed_today = len(workflow_ids_today_success)
        failed_today = len(workflow_ids_today_failed)
        avg_duration = (
            sum(m.duration_ms for m in recent) / len(recent) / 1000.0
            if recent
            else 0.0
        )

        # Agents: by skill or command
        agent_counts: dict[str, list] = defaultdict(list)
        for m in recent:
            key = m.skill or m.command or "unknown"
            agent_counts[key].append(m)

        agents_list = []
        for name, ms in agent_counts.items():
            total = len(ms)
            success = sum(1 for m in ms if m.status == "success")
            agents_list.append(
                {
                    "agent_id": name,
                    "agent_name": name,
                    "total_executions": total,
                    "successful_executions": success,
                    "failed_executions": total - success,
                    "success_rate": success / total if total else 0.0,
                    "average_duration": sum(m.duration_ms for m in ms) / total / 1000.0
                    if total
                    else 0.0,
                }
            )

        # Workflows: by workflow_id
        wf_counts: dict[str, list] = defaultdict(list)
        for m in recent:
            wf_counts[m.workflow_id].append(m)

        workflows_list = []
        for wf_id, ms in wf_counts.items():
            total = len(ms)
            success = sum(1 for m in ms if m.status == "success")
            workflows_list.append(
                {
                    "workflow_id": wf_id,
                    "workflow_name": wf_id,
                    "total_executions": total,
                    "successful_executions": success,
                    "failed_executions": total - success,
                    "success_rate": success / total if total else 0.0,
                    "average_duration": sum(m.duration_ms for m in ms) / total / 1000.0
                    if total
                    else 0.0,
                }
            )

        # System: try cpu/mem/disk from ResourceMonitor
        cpu_usage = memory_usage = disk_usage = 0.0
        try:
            from ...core.resource_monitor import ResourceMonitor

            mon = ResourceMonitor()
            res = mon.get_current_metrics()
            cpu_usage = getattr(res, "cpu_percent", 0.0) or 0.0
            memory_usage = getattr(res, "memory_percent", 0.0) or 0.0
            disk_usage = getattr(res, "disk_percent", 0.0) or 0.0
        except Exception:
            pass

        return {
            "timestamp": now.isoformat(),
            "system": {
                "timestamp": now.isoformat(),
                "total_agents": len(agents_list),
                "active_workflows": 0,
                "completed_workflows_today": completed_today,
                "failed_workflows_today": failed_today,
                "average_workflow_duration": avg_duration,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
            },
            "agents": agents_list,
            "workflows": workflows_list,
        }
    except Exception:
        return None


def handle_health_check_command(
    check_name: str | None = None,
    output_format: str = "text",
    save: bool = True,
    project_root: Path | None = None,
) -> None:
    """
    Handle health check command.

    Args:
        check_name: Optional specific check to run
        output_format: Output format (json or text)
        save: Whether to save results to metrics storage
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()

    # Initialize registry and register all checks
    registry = HealthCheckRegistry()
    registry.register(EnvironmentHealthCheck(project_root=project_root))
    registry.register(AutomationHealthCheck(project_root=project_root))
    registry.register(ExecutionHealthCheck(project_root=project_root))
    registry.register(Context7CacheHealthCheck(project_root=project_root))
    registry.register(KnowledgeBaseHealthCheck(project_root=project_root))
    registry.register(OutcomeHealthCheck(project_root=project_root))

    # Initialize orchestrator
    metrics_collector = HealthMetricsCollector(project_root=project_root)
    orchestrator = HealthOrchestrator(
        registry=registry, metrics_collector=metrics_collector, project_root=project_root
    )

    # Run checks
    feedback = get_feedback()
    feedback.format_type = output_format
    operation_desc = f"Running health check: {check_name}" if check_name else "Running all health checks"
    feedback.start_operation("Health Check", operation_desc)
    
    if check_name:
        check_names = [check_name]
        feedback.running(f"Initializing check: {check_name}...", step=1, total_steps=3)
    else:
        check_names = None
        feedback.running("Discovering health checks...", step=1, total_steps=3)

    feedback.running("Executing health checks...", step=2, total_steps=3)
    results = orchestrator.run_all_checks(check_names=check_names, save_metrics=save)
    feedback.running("Collecting results...", step=3, total_steps=3)
    feedback.clear_progress()

    # Build summary
    summary = {}
    if results:
        healthy_count = sum(1 for r in results.values() if r and r.status == "healthy")
        total_count = len([r for r in results.values() if r])
        summary["checks_run"] = total_count
        summary["healthy"] = healthy_count
        summary["degraded"] = sum(1 for r in results.values() if r and r.status == "degraded")
        summary["unhealthy"] = sum(1 for r in results.values() if r and r.status == "unhealthy")

    # Format output
    if output_format == "json":
        output = {
            "checks": {
                name: {
                    "status": result.status,
                    "score": result.score,
                    "message": result.message,
                    "details": result.details,
                    "remediation": (
                        result.remediation
                        if isinstance(result.remediation, list)
                        else [result.remediation]
                        if result.remediation
                        else None
                    ),
                }
                for name, result in results.items()
                if result
            }
        }
        # Merge summary into output
        if summary:
            output = {**output, "summary": summary}
        feedback.output_result(output, message="Health checks completed")
    else:
        # Text output
        feedback.success("Health checks completed")
        warnings = []
        for name, result in sorted(results.items()):
            if not result:
                continue

            status_symbol = {
                "healthy": "[OK]",
                "degraded": "[WARN]",
                "unhealthy": "[FAIL]",
            }.get(result.status, "[?]")

            print(f"\n[{status_symbol}] {name.upper()}: {result.status} ({result.score:.1f}/100)")
            print(f"   {result.message}")
            
            if result.status != "healthy":
                warnings.append(f"{name}: {result.message}")

            if result.details:
                # Show key metrics
                key_metrics = []
                for key in [
                    "total_executions",
                    "success_rate",
                    "hit_rate",
                    "total_files",
                    "average_score",
                ]:
                    if key in result.details:
                        value = result.details[key]
                        if isinstance(value, float):
                            if key == "success_rate" or key == "hit_rate":
                                key_metrics.append(f"{key}: {value:.1f}%")
                            else:
                                key_metrics.append(f"{key}: {value:.1f}")
                        else:
                            key_metrics.append(f"{key}: {value}")

                if key_metrics:
                    print(f"   Metrics: {' | '.join(key_metrics)}")

            if result.remediation:
                if isinstance(result.remediation, list):
                    if len(result.remediation) > 0:
                        print(f"   Remediation: {result.remediation[0]}")
                elif isinstance(result.remediation, str):
                    print(f"   Remediation: {result.remediation}")
        
        if warnings:
            for warning_msg in warnings:
                feedback.warning(warning_msg)


def handle_health_dashboard_command(
    output_format: str = "text", project_root: Path | None = None
) -> None:
    """
    Handle health dashboard command.

    Args:
        output_format: Output format (json or text)
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()

    # Initialize registry and register all checks
    registry = HealthCheckRegistry()
    registry.register(EnvironmentHealthCheck(project_root=project_root))
    registry.register(AutomationHealthCheck(project_root=project_root))
    registry.register(ExecutionHealthCheck(project_root=project_root))
    registry.register(Context7CacheHealthCheck(project_root=project_root))
    registry.register(KnowledgeBaseHealthCheck(project_root=project_root))
    registry.register(OutcomeHealthCheck(project_root=project_root))

    # Initialize dashboard
    metrics_collector = HealthMetricsCollector(project_root=project_root)
    orchestrator = HealthOrchestrator(
        registry=registry, metrics_collector=metrics_collector, project_root=project_root
    )
    dashboard = HealthDashboard(orchestrator=orchestrator)

    # Render dashboard
    feedback = get_feedback()
    feedback.format_type = output_format
    feedback.start_operation("Health Dashboard", "Generating health dashboard visualization")
    feedback.running("Collecting health metrics...", step=1, total_steps=3)
    feedback.running("Generating dashboard...", step=2, total_steps=3)
    feedback.running("Rendering dashboard output...", step=3, total_steps=3)
    
    if output_format == "json":
        output = dashboard.render_json()
        feedback.clear_progress()
        feedback.output_result(output, message="Health dashboard generated")
    else:
        output = dashboard.render_text()
        feedback.clear_progress()
        feedback.success("Health dashboard generated")
        print(output)


def handle_health_metrics_command(
    check_name: str | None = None,
    status: str | None = None,
    days: int = 30,
    output_format: str = "text",
    project_root: Path | None = None,
) -> None:
    """
    Handle health metrics command.

    Args:
        check_name: Optional check name to filter
        status: Optional status to filter
        days: Number of days to look back
        output_format: Output format (json or text)
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()
    collector = HealthMetricsCollector(project_root=project_root)

    # Get metrics
    feedback = get_feedback()
    feedback.format_type = output_format
    operation_desc = f"Collecting metrics{f' for {check_name}' if check_name else ''}"
    feedback.start_operation("Health Metrics", operation_desc)
    feedback.running("Querying metrics database...", step=1, total_steps=3)
    
    metrics = collector.get_metrics(check_name=check_name, status=status, days=days, limit=1000)
    feedback.running("Calculating summary statistics...", step=2, total_steps=3)
    summary = collector.get_summary(days=days)
    feedback.running("Formatting results...", step=3, total_steps=3)
    feedback.clear_progress()

    if output_format == "json":
        output = {
            "summary": summary,
            "metrics": [m.to_dict() for m in metrics],
        }
        feedback.output_result(output, message="Health metrics retrieved")
    else:
        # Text output
        feedback.success("Health metrics retrieved")
        print(f"\nHealth Metrics Summary (last {days} days)")
        print("=" * 70)
        print(f"Total checks: {summary['total_checks']}")
        print(f"Average score: {summary['average_score']:.1f}/100")
        print(f"\nBy status:")
        for status_name, count in summary["by_status"].items():
            print(f"  {status_name}: {count}")

        if summary["by_check"]:
            print(f"\nBy check:")
            for check_name, check_data in summary["by_check"].items():
                print(f"  {check_name}:")
                print(f"    Count: {check_data['count']}")
                print(f"    Average score: {check_data['average_score']:.1f}/100")
                print(f"    Latest status: {check_data['latest_status']}")
                print(f"    Latest score: {check_data['latest_score']:.1f}/100")

        if metrics:
            print(f"\nRecent metrics (showing up to 10):")
            for metric in metrics[:10]:
                print(f"  {metric.check_name}: {metric.status} ({metric.score:.1f}/100) - {metric.timestamp}")


def handle_health_trends_command(
    check_name: str,
    days: int = 7,
    output_format: str = "text",
    project_root: Path | None = None,
) -> None:
    """
    Handle health trends command.

    Args:
        check_name: Check name to analyze trends for
        days: Number of days to analyze
        output_format: Output format (json or text)
        project_root: Project root directory
    """
    project_root = project_root or Path.cwd()
    collector = HealthMetricsCollector(project_root=project_root)

    # Get trends
    feedback = get_feedback()
    feedback.format_type = output_format
    feedback.start_operation("Health Trends", f"Analyzing health trends for {check_name}")
    feedback.running("Loading historical data...", step=1, total_steps=3)
    
    trends = collector.get_trends(check_name=check_name, days=days)
    feedback.running("Calculating trends...", step=2, total_steps=3)
    feedback.running("Generating trend report...", step=3, total_steps=3)
    feedback.clear_progress()

    if output_format == "json":
        output = {
            "check_name": check_name,
            "days": days,
            "trends": trends,
        }
        feedback.output_result(output, message="Health trends analyzed")
    else:
        # Text output
        feedback.success("Health trends analyzed")
        print(f"\nHealth Trends for '{check_name}' (last {days} days)")
        print("=" * 70)
        print(f"Direction: {trends['direction']}")
        print(f"Score change: {trends['score_change']:+.1f} points")

        if trends["status_changes"]:
            print(f"\nStatus changes:")
            for status, change in trends["status_changes"].items():
                if change != 0:
                    print(f"  {status}: {change:+d}")


def handle_health_usage_command(args: object) -> None:
    """
    Handle health usage subcommand (formerly analytics).
    Dispatches to dashboard, agents, workflows, trends, or system using AnalyticsDashboard.
    """
    from ...core.analytics_dashboard import AnalyticsDashboard

    dashboard = AnalyticsDashboard()
    sub = getattr(args, "usage_subcommand", "dashboard")
    if sub == "show":
        sub = "dashboard"
    fmt = getattr(args, "format", "text")

    if sub == "dashboard":
        data = dashboard.get_dashboard_data()
        if fmt == "json":
            format_json_output(data)
        else:
            print("\n" + "=" * 60)
            print("Usage / Analytics Dashboard")
            print("=" * 60)
            print(f"\nSystem Status (as of {data['timestamp']}):")
            sys_data = data["system"]
            print(f"  Total Agents: {sys_data['total_agents']}")
            print(f"  Active Workflows: {sys_data['active_workflows']}")
            print(f"  Completed Today: {sys_data['completed_workflows_today']}")
            print(f"  Failed Today: {sys_data['failed_workflows_today']}")
            print(f"  Avg Workflow Duration: {sys_data['average_workflow_duration']:.2f}s")
            print(f"  CPU Usage: {sys_data['cpu_usage']:.1f}%")
            print(f"  Memory Usage: {sys_data['memory_usage']:.1f}%")
            print(f"  Disk Usage: {sys_data['disk_usage']:.1f}%")
            print("\nAgent Performance (Top 10):")
            for agent in sorted(data["agents"], key=lambda x: x["total_executions"], reverse=True)[:10]:
                print(f"  {agent['agent_name']}: {agent['total_executions']} executions, "
                      f"{agent['success_rate']*100:.1f}% success, {agent['average_duration']:.2f}s avg")
            print("\nWorkflow Performance:")
            for wf in sorted(data["workflows"], key=lambda x: x["total_executions"], reverse=True)[:10]:
                print(f"  {wf['workflow_name']}: {wf['total_executions']} executions, "
                      f"{wf['success_rate']*100:.1f}% success")
    elif sub == "agents":
        metrics = dashboard.get_agent_performance(agent_id=getattr(args, "agent_id", None))
        if fmt == "json":
            format_json_output(metrics)
        else:
            for agent in metrics:
                print(f"{agent['agent_name']}: {agent['total_executions']} executions, "
                      f"{agent['success_rate']*100:.1f}% success")
    elif sub == "workflows":
        metrics = dashboard.get_workflow_performance(workflow_id=getattr(args, "workflow_id", None))
        if fmt == "json":
            format_json_output(metrics)
        else:
            for wf in metrics:
                print(f"{wf['workflow_name']}: {wf['total_executions']} executions, "
                      f"{wf['success_rate']*100:.1f}% success")
    elif sub == "trends":
        metric_type = getattr(args, "metric_type", "agent_duration")
        days = getattr(args, "days", 30)
        trends = dashboard.get_trends(metric_type, days=days)
        if fmt == "json":
            format_json_output(trends)
        else:
            for t in trends:
                print(f"{t['metric_name']}: {len(t['values'])} data points")
    elif sub == "system":
        status = dashboard.get_system_status()
        if fmt == "json":
            format_json_output(status)
        else:
            print(f"System Status (as of {status['timestamp']}):")
            print(f"  Total Agents: {status['total_agents']}")
            print(f"  Active Workflows: {status['active_workflows']}")
            print(f"  Completed Today: {status['completed_workflows_today']}")
            print(f"  Failed Today: {status['failed_workflows_today']}")


def handle_health_overview_command(
    output_format: str = "text",
    project_root: Path | None = None,
) -> None:
    """
    Single 1000-foot view: health checks + usage rolled up for all subsystems.

    Renders one easy-to-read report: overall health, each health check one line,
    then usage at a glance (system, top agents, top workflows).
    """
    from ...core.analytics_dashboard import AnalyticsDashboard

    project_root = project_root or Path.cwd()

    # 1. Health checks
    registry = HealthCheckRegistry()
    registry.register(EnvironmentHealthCheck(project_root=project_root))
    registry.register(AutomationHealthCheck(project_root=project_root))
    registry.register(ExecutionHealthCheck(project_root=project_root))
    registry.register(Context7CacheHealthCheck(project_root=project_root))
    registry.register(KnowledgeBaseHealthCheck(project_root=project_root))
    registry.register(OutcomeHealthCheck(project_root=project_root))
    metrics_collector = HealthMetricsCollector(project_root=project_root)
    orchestrator = HealthOrchestrator(
        registry=registry,
        metrics_collector=metrics_collector,
        project_root=project_root,
    )
    health_results = orchestrator.run_all_checks(save_metrics=True)
    overall = orchestrator.get_overall_health(health_results)

    # 2. Usage (best-effort; prefer analytics, fallback to execution metrics)
    usage_data = None
    try:
        usage_dashboard = AnalyticsDashboard()
        usage_data = usage_dashboard.get_dashboard_data()
    except Exception:
        pass
    # If analytics has no agent/workflow data, derive from execution metrics
    if usage_data:
        agents = usage_data.get("agents") or []
        workflows = usage_data.get("workflows") or []
        total_runs = sum(a.get("total_executions", 0) for a in agents) + sum(
            w.get("total_executions", 0) for w in workflows
        )
        if total_runs == 0:
            usage_data = _usage_data_from_execution_metrics(project_root) or usage_data
    else:
        usage_data = _usage_data_from_execution_metrics(project_root) or usage_data

    # 3. Build output
    feedback = get_feedback()
    feedback.format_type = output_format

    if output_format == "json":
        out = {
            "overview": {
                "overall_health": overall,
                "health_checks": {
                    name: {
                        "status": r.status,
                        "score": r.score,
                        "message": r.message,
                    }
                    for name, r in health_results.items()
                    if r
                },
            },
            "usage": usage_data,
        }
        format_json_output(out)
        return

    # Text: 1000-foot, great-looking, easy to read
    width = 72
    lines = []
    lines.append("")
    lines.append("=" * width)
    lines.append("  TAPPS-AGENTS  |  HEALTH + USAGE  |  1000-FOOT VIEW")
    lines.append("=" * width)
    lines.append("")

    # Overall health
    status_sym = {"healthy": "[OK] ", "degraded": "[WARN]", "unhealthy": "[FAIL]", "unknown": "[?]  "}
    sym = status_sym.get(overall["status"], "[?]  ")
    lines.append(f"  {sym}  Overall: {overall['status'].upper()}  ({overall['score']:.1f}/100)")
    lines.append("")

    # Subsystems (health checks) - one line each
    lines.append("  SUBSYSTEMS (health)")
    lines.append("  " + "-" * (width - 2))
    for name, result in sorted(health_results.items()):
        if not result:
            continue
        s = status_sym.get(result.status, "[?]  ")
        label = name.replace("_", " ").upper()
        lines.append(f"  {s}  {label}: {result.score:.1f}/100  |  {result.message[:50]}{'...' if len(result.message) > 50 else ''}")
    lines.append("")

    # Usage at a glance
    lines.append("  USAGE (agents & workflows)")
    lines.append("  " + "-" * (width - 2))
    if usage_data:
        sys_data = usage_data.get("system", {})
        lines.append(f"  Today: completed {sys_data.get('completed_workflows_today', 0)} workflows, failed {sys_data.get('failed_workflows_today', 0)}  |  active: {sys_data.get('active_workflows', 0)}")
        lines.append(f"  Avg workflow duration: {sys_data.get('average_workflow_duration', 0):.1f}s  |  CPU: {sys_data.get('cpu_usage', 0):.0f}%  Mem: {sys_data.get('memory_usage', 0):.0f}%  Disk: {sys_data.get('disk_usage', 0):.0f}%")
        agents = sorted(usage_data.get("agents", []), key=lambda x: x.get("total_executions", 0), reverse=True)[:5]
        if agents:
            lines.append("  Top agents (30d): " + "  |  ".join(f"{a.get('agent_name', '')}: {a.get('total_executions', 0)} runs ({a.get('success_rate', 0)*100:.0f}% ok)" for a in agents))
        workflows = sorted(usage_data.get("workflows", []), key=lambda x: x.get("total_executions", 0), reverse=True)[:5]
        if workflows:
            lines.append("  Top workflows (30d): " + "  |  ".join(f"{w.get('workflow_name', '')}: {w.get('total_executions', 0)} ({w.get('success_rate', 0)*100:.0f}% ok)" for w in workflows))
    else:
        lines.append("  (No usage data yet. Run agents/workflows to populate.)")
    lines.append("")
    lines.append("=" * width)
    lines.append("")

    feedback.clear_progress()
    print("\n".join(lines))

