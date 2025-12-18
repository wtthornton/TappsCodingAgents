"""
Health command handlers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ...health.checks.automation import AutomationHealthCheck
from ...health.checks.environment import EnvironmentHealthCheck
from ...health.checks.execution import ExecutionHealthCheck
from ...health.checks.context7_cache import Context7CacheHealthCheck
from ...health.checks.knowledge_base import KnowledgeBaseHealthCheck
from ...health.checks.governance import GovernanceHealthCheck
from ...health.checks.outcomes import OutcomeHealthCheck
from ...health.collector import HealthMetricsCollector
from ...health.dashboard import HealthDashboard
from ...health.orchestrator import HealthOrchestrator
from ...health.registry import HealthCheckRegistry
from .common import format_json_output


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
    registry.register(GovernanceHealthCheck(project_root=project_root))
    registry.register(OutcomeHealthCheck(project_root=project_root))

    # Initialize orchestrator
    metrics_collector = HealthMetricsCollector(project_root=project_root)
    orchestrator = HealthOrchestrator(
        registry=registry, metrics_collector=metrics_collector, project_root=project_root
    )

    # Run checks
    if check_name:
        check_names = [check_name]
    else:
        check_names = None

    results = orchestrator.run_all_checks(check_names=check_names, save_metrics=save)

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
        print(json.dumps(output, indent=2))
    else:
        # Text output
        for name, result in sorted(results.items()):
            if not result:
                continue

            status_symbol = {
                "healthy": "[✓]",
                "degraded": "[⚠]",
                "unhealthy": "[✗]",
            }.get(result.status, "[?]")

            print(f"\n{status_symbol} {name.upper()}: {result.status} ({result.score:.1f}/100)")
            print(f"   {result.message}")

            if result.details:
                # Show key metrics
                key_metrics = []
                for key in [
                    "total_executions",
                    "success_rate",
                    "hit_rate",
                    "total_files",
                    "approval_queue_size",
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
    registry.register(GovernanceHealthCheck(project_root=project_root))
    registry.register(OutcomeHealthCheck(project_root=project_root))

    # Initialize dashboard
    metrics_collector = HealthMetricsCollector(project_root=project_root)
    orchestrator = HealthOrchestrator(
        registry=registry, metrics_collector=metrics_collector, project_root=project_root
    )
    dashboard = HealthDashboard(orchestrator=orchestrator)

    # Render dashboard
    if output_format == "json":
        output = dashboard.render_json()
        print(json.dumps(output, indent=2))
    else:
        output = dashboard.render_text()
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
    metrics = collector.get_metrics(check_name=check_name, status=status, days=days, limit=1000)
    summary = collector.get_summary(days=days)

    if output_format == "json":
        output = {
            "summary": summary,
            "metrics": [m.to_dict() for m in metrics],
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
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
    trends = collector.get_trends(check_name=check_name, days=days)

    if output_format == "json":
        output = {
            "check_name": check_name,
            "days": days,
            "trends": trends,
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
        print(f"\nHealth Trends for '{check_name}' (last {days} days)")
        print("=" * 70)
        print(f"Direction: {trends['direction']}")
        print(f"Score change: {trends['score_change']:+.1f} points")

        if trends["status_changes"]:
            print(f"\nStatus changes:")
            for status, change in trends["status_changes"].items():
                if change != 0:
                    print(f"  {status}: {change:+d}")

