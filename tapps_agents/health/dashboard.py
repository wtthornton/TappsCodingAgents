"""
Health Dashboard Renderer.

Renders health status in a user-friendly dashboard format.
"""

from __future__ import annotations

from typing import Any

from .base import HealthCheckResult
from .orchestrator import HealthOrchestrator


class HealthDashboard:
    """Renders health status dashboard."""

    def __init__(self, orchestrator: HealthOrchestrator | None = None):
        """
        Initialize health dashboard.

        Args:
            orchestrator: Health orchestrator instance
        """
        self.orchestrator = orchestrator or HealthOrchestrator()

    def render_text(self, results: dict[str, HealthCheckResult] | None = None) -> str:
        """
        Render health dashboard as text.

        Args:
            results: Optional check results (runs all checks if None)

        Returns:
            Formatted text dashboard
        """
        if results is None:
            results = self.orchestrator.run_all_checks(save_metrics=True)

        overall = self.orchestrator.get_overall_health(results)

        lines = []
        lines.append("=" * 70)
        lines.append("TAPPS-AGENTS HEALTH DASHBOARD")
        lines.append("=" * 70)
        lines.append("")

        # Overall status
        status_emoji = {
            "healthy": "✓",
            "degraded": "⚠",
            "unhealthy": "✗",
            "unknown": "?",
        }
        emoji = status_emoji.get(overall["status"], "?")
        lines.append(f"{emoji} Overall Health: {overall['status'].upper()} ({overall['score']:.1f}/100)")
        lines.append("")

        # Individual checks
        lines.append("Health Checks:")
        lines.append("-" * 70)

        for name, result in sorted(results.items()):
            if not result:
                continue

            status_symbol = {
                "healthy": "[✓]",
                "degraded": "[⚠]",
                "unhealthy": "[✗]",
            }.get(result.status, "[?]")

            lines.append(f"{status_symbol} {name.upper()}: {result.status} ({result.score:.1f}/100)")
            lines.append(f"    {result.message}")
            if result.details:
                # Show key details
                key_details = []
                for key in ["total_executions", "success_rate", "hit_rate", "total_files", "approval_queue_size"]:
                    if key in result.details:
                        value = result.details[key]
                        if isinstance(value, float):
                            key_details.append(f"{key}: {value:.1f}")
                        else:
                            key_details.append(f"{key}: {value}")
                if key_details:
                    lines.append(f"    Details: {' | '.join(key_details)}")

        lines.append("")

        # Remediation actions
        if overall.get("remediation"):
            lines.append("Top Remediation Actions:")
            lines.append("-" * 70)
            for i, action in enumerate(overall["remediation"], 1):
                lines.append(f"{i}. {action}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)

    def render_json(self, results: dict[str, HealthCheckResult] | None = None) -> dict[str, Any]:
        """
        Render health dashboard as JSON.

        Args:
            results: Optional check results (runs all checks if None)

        Returns:
            Dictionary with health dashboard data
        """
        if results is None:
            results = self.orchestrator.run_all_checks(save_metrics=True)

        overall = self.orchestrator.get_overall_health(results)

        return {
            "overall": overall,
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
            },
        }

