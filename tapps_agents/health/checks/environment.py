"""
Environment Health Check.

Extends the doctor command to provide health check results.
"""

from __future__ import annotations

from pathlib import Path

from ...core.doctor import collect_doctor_report
from ..base import HealthCheck, HealthCheckResult


class EnvironmentHealthCheck(HealthCheck):
    """Health check for environment readiness."""

    def __init__(self, project_root: Path | None = None, config_path: Path | None = None):
        """
        Initialize environment health check.

        Args:
            project_root: Project root directory
            config_path: Path to config file
        """
        super().__init__(name="environment", dependencies=[])
        self.project_root = project_root
        self.config_path = config_path

    def run(self) -> HealthCheckResult:
        """
        Run environment health check.

        Returns:
            HealthCheckResult with environment status
        """
        try:
            report = collect_doctor_report(
                project_root=self.project_root, config_path=self.config_path
            )

            findings = report.get("findings", [])
            if not findings:
                return HealthCheckResult(
                    name=self.name,
                    status="unhealthy",
                    score=0.0,
                    message="No environment findings available",
                    details={"report": report},
                )

            # Count findings by severity
            ok_count = sum(1 for f in findings if f.get("severity") == "ok")
            warn_count = sum(1 for f in findings if f.get("severity") == "warn")
            error_count = sum(1 for f in findings if f.get("severity") == "error")

            total = len(findings)

            # Calculate score (0-100)
            # OK = 100 points, WARN = 50 points, ERROR = 0 points
            score = ((ok_count * 100) + (warn_count * 50) + (error_count * 0)) / total if total > 0 else 0.0

            # Determine status
            if error_count > 0:
                status = "unhealthy"
            elif warn_count > 0:
                status = "degraded"
            else:
                status = "healthy"

            # Get top 3 remediation actions
            remediation_actions = []
            for finding in findings:
                if finding.get("severity") in ("error", "warn") and finding.get("remediation"):
                    remediation_actions.append(finding["remediation"])
                    if len(remediation_actions) >= 3:
                        break

            # Build message
            message_parts = []
            if error_count > 0:
                message_parts.append(f"{error_count} error(s)")
            if warn_count > 0:
                message_parts.append(f"{warn_count} warning(s)")
            if ok_count > 0:
                message_parts.append(f"{ok_count} check(s) passed")

            message = f"Environment check: {', '.join(message_parts)}"

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=score,
                message=message,
                details={
                    "findings_count": total,
                    "ok": ok_count,
                    "warn": warn_count,
                    "error": error_count,
                    "policy": report.get("policy", {}),
                    "targets": report.get("targets", {}),
                    "features": report.get("features", {}),
                },
                remediation=remediation_actions if remediation_actions else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Environment check failed: {e}",
                details={"error": str(e)},
                remediation=["Run 'tapps-agents doctor' to diagnose environment issues"],
            )

