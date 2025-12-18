"""
Automation Health Check.

Checks background agent configuration and file system access.
"""

from __future__ import annotations

from pathlib import Path

from ...workflow.health_checker import HealthChecker
from ..base import HealthCheck, HealthCheckResult


class AutomationHealthCheck(HealthCheck):
    """Health check for background agent automation."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize automation health check.

        Args:
            project_root: Project root directory
        """
        super().__init__(name="automation", dependencies=["environment"])
        self.project_root = project_root or Path.cwd()
        self.health_checker = HealthChecker(project_root=project_root)

    def run(self) -> HealthCheckResult:
        """
        Run automation health check.

        Returns:
            HealthCheckResult with automation status
        """
        try:
            # Run all background agent health checks
            results = self.health_checker.check_all()

            if not results:
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    score=50.0,
                    message="No automation health checks available",
                    details={},
                )

            # Count statuses
            healthy_count = sum(1 for r in results if r.status == "healthy")
            degraded_count = sum(1 for r in results if r.status == "degraded")
            unhealthy_count = sum(1 for r in results if r.status == "unhealthy")
            total = len(results)

            # Calculate score (0-100)
            # Healthy = 100 points, Degraded = 50 points, Unhealthy = 0 points
            score = ((healthy_count * 100) + (degraded_count * 50) + (unhealthy_count * 0)) / total if total > 0 else 0.0

            # Determine overall status
            if unhealthy_count > 0:
                status = "unhealthy"
            elif degraded_count > 0:
                status = "degraded"
            else:
                status = "healthy"

            # Build message
            message_parts = []
            if healthy_count > 0:
                message_parts.append(f"{healthy_count} healthy")
            if degraded_count > 0:
                message_parts.append(f"{degraded_count} degraded")
            if unhealthy_count > 0:
                message_parts.append(f"{unhealthy_count} unhealthy")

            message = f"Automation checks: {', '.join(message_parts)}" if message_parts else "No checks run"

            # Collect remediation actions
            remediation = []
            for result in results:
                if result.status != "healthy" and result.message:
                    # Extract actionable remediation from message
                    if "configuration" in result.name.lower():
                        remediation.append("Check .cursor/background-agents.yaml configuration")
                    elif "file_system" in result.name.lower():
                        remediation.append("Check .tapps-agents/ directory permissions")
                    elif "status_file" in result.name.lower():
                        remediation.append("Check .cursor/ directory permissions for status files")
                    elif "command_file" in result.name.lower():
                        remediation.append("Check .cursor/ directory permissions for command files")

            # Get overall status from health checker
            overall_status = self.health_checker.get_overall_status()

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=score,
                message=message,
                details={
                    "overall_status": overall_status,
                    "healthy": healthy_count,
                    "degraded": degraded_count,
                    "unhealthy": unhealthy_count,
                    "total_checks": total,
                    "checks": [
                        {
                            "name": r.name,
                            "status": r.status,
                            "message": r.message,
                        }
                        for r in results
                    ],
                },
                remediation=list(set(remediation))[:3] if remediation else None,  # Top 3 unique
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Automation check failed: {e}",
                details={"error": str(e)},
                remediation=["Check background agent configuration and file permissions"],
            )

