"""
Learning export command handlers
"""
import sys
from pathlib import Path
from typing import Any

from ...core.learning_export import LearningDataExporter
from ...core.learning_dashboard import LearningDashboard
from ...core.capability_registry import CapabilityRegistry
from ...core.analytics_dashboard import AnalyticsDashboard
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from .common import check_result_error, format_json_output


def handle_learning_command(args: object) -> None:
    """Handle learning CLI commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "text")
    feedback.format_type = output_format

    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("learning")
        feedback.output_result(help_text)
        return

    if command == "export":
        handle_learning_export(args)
    elif command == "dashboard":
        handle_learning_dashboard(args)
    elif command == "submit":
        feedback.output_result(
            {
                "error": "Submit command not yet implemented. "
                "Export your data and submit manually via GitHub issue."
            }
        )
    else:
        feedback.output_result({"error": f"Unknown command: {command}"})


def handle_learning_export(args: object) -> None:
    """Handle 'learning export' command."""
    feedback = get_feedback()
    output_path = getattr(args, "output", None)
    anonymize = not getattr(args, "no_anonymize", False)
    compress = getattr(args, "compress", False)
    format_type = getattr(args, "format", "json")
    yes = getattr(args, "yes", False)

    # Confirm with user unless --yes flag
    if not yes and anonymize:
        feedback.output_result(
            {
                "message": "This will export learning data. "
                "Data will be anonymized for privacy. "
                "Use --yes to skip this confirmation."
            }
        )
        # In interactive mode, would prompt here
        # For now, proceed with export

    try:
        # Initialize exporter
        exporter = LearningDataExporter(project_root=Path.cwd())

        # Export data
        export_path = exporter.export(
            output_path=Path(output_path) if output_path else None,
            anonymize=anonymize,
            compress=compress,
            format=format_type,
        )

        result = {
            "success": True,
            "export_path": str(export_path),
            "anonymized": anonymize,
            "compressed": compress,
            "message": f"Learning data exported to {export_path}",
        }

        if format_type == "json":
            feedback.output_result(result)
        else:
            feedback.output_result(
                f"✓ Learning data exported successfully\n"
                f"  Path: {export_path}\n"
                f"  Anonymized: {anonymize}\n"
                f"  Compressed: {compress}"
            )

    except Exception as e:
        error_result = {"error": str(e), "success": False}
        check_result_error(error_result)
        feedback.output_result(error_result)
        sys.exit(1)


def handle_learning_dashboard(args: object) -> None:
    """Handle 'learning dashboard' command."""
    feedback = get_feedback()
    capability_id = getattr(args, "capability", None)
    format_type = getattr(args, "format", "text")
    include_trends = getattr(args, "include_trends", False)
    include_failures = getattr(args, "include_failures", False)

    try:
        # Initialize components
        registry = CapabilityRegistry()
        dashboard = LearningDashboard(capability_registry=registry)

        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data(
            capability_id=capability_id,
            include_trends=include_trends,
            include_failures=include_failures,
        )

        if format_type == "json":
            feedback.output_result(dashboard_data)
        else:
            # Format as text
            lines = []
            lines.append("Learning System Dashboard")
            lines.append("=" * 50)

            # Capability metrics
            if "capability_metrics" in dashboard_data:
                metrics = dashboard_data["capability_metrics"]
                lines.append("\nCapability Metrics:")
                if isinstance(metrics, dict):
                    total = metrics.get("total_capabilities", 0)
                    lines.append(f"  Total capabilities: {total}")
                    if "capabilities" in metrics:
                        for cap in metrics["capabilities"][:10]:  # Show first 10
                            cap_id = cap.get("capability_id", "unknown")
                            success = cap.get("success_rate", 0.0)
                            quality = cap.get("quality_score", 0.0)
                            lines.append(
                                f"  - {cap_id}: success={success:.2f}, quality={quality:.2f}"
                            )

            # Pattern statistics
            if "pattern_statistics" in dashboard_data:
                stats = dashboard_data["pattern_statistics"]
                lines.append("\nPattern Statistics:")
                if isinstance(stats, dict):
                    total = stats.get("total_patterns", 0)
                    anti = stats.get("total_anti_patterns", 0)
                    lines.append(f"  Total patterns: {total}")
                    lines.append(f"  Anti-patterns: {anti}")

            # Security metrics
            if "security_metrics" in dashboard_data:
                security = dashboard_data["security_metrics"]
                lines.append("\nSecurity Metrics:")
                if isinstance(security, dict):
                    avg_score = security.get("average_security_score", 0.0)
                    lines.append(f"  Average security score: {avg_score:.2f}/10")

            feedback.output_result("\n".join(lines))

    except Exception as e:
        error_result = {"error": str(e), "success": False}
        check_result_error(error_result)
        feedback.output_result(error_result)
        sys.exit(1)
