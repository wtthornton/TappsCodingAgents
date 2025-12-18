"""
Governance Health Check.

Checks governance safety and approval queue status.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from ..base import HealthCheck, HealthCheckResult


class GovernanceHealthCheck(HealthCheck):
    """Health check for governance safety and approval queue."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize governance health check.

        Args:
            project_root: Project root directory
        """
        super().__init__(name="governance", dependencies=["environment"])
        self.project_root = project_root or Path.cwd()
        self.approval_queue_dir = self.project_root / ".tapps-agents" / "approval_queue"

    def run(self) -> HealthCheckResult:
        """
        Run governance health check.

        Returns:
            HealthCheckResult with governance status
        """
        try:
            # Check approval queue
            approval_queue_exists = self.approval_queue_dir.exists()
            pending_approvals = []
            approval_lead_times = []

            if approval_queue_exists:
                # Count pending approvals
                for approval_file in self.approval_queue_dir.glob("*.json"):
                    try:
                        with open(approval_file, encoding="utf-8") as f:
                            approval_data = json.load(f)
                            if approval_data.get("status") == "pending":
                                pending_approvals.append(approval_data)
                                # Calculate lead time
                                queued_at_str = approval_data.get("queued_at")
                                if queued_at_str:
                                    try:
                                        queued_at = datetime.fromisoformat(
                                            queued_at_str.replace("Z", "+00:00")
                                        )
                                        lead_time = (datetime.now() - queued_at.replace(tzinfo=None)).days
                                        approval_lead_times.append(lead_time)
                                    except Exception:
                                        pass
                    except Exception:
                        # Skip invalid files
                        continue

            queue_size = len(pending_approvals)
            avg_lead_time = (
                sum(approval_lead_times) / len(approval_lead_times)
                if approval_lead_times
                else 0.0
            )
            max_lead_time = max(approval_lead_times) if approval_lead_times else 0.0

            # Calculate health score
            score = 100.0
            issues = []
            remediation = []

            # Check approval queue size
            if queue_size == 0:
                # Healthy - no pending approvals
                pass
            elif queue_size < 5:
                score -= 5.0
                issues.append(f"Small approval queue: {queue_size} pending")
            elif queue_size < 20:
                score -= 15.0
                issues.append(f"Growing approval queue: {queue_size} pending")
                remediation.append("Review and process approval queue: tapps-agents governance list")
            else:
                score -= 30.0
                issues.append(f"Large approval queue: {queue_size} pending")
                remediation.append("Urgent: Process approval queue to prevent KB stagnation")

            # Check approval lead time
            if avg_lead_time > 7:
                score -= 20.0
                issues.append(f"High average approval lead time: {avg_lead_time:.0f} days")
                remediation.append("Process approvals more frequently")
            elif avg_lead_time > 3:
                score -= 10.0
                issues.append(f"Moderate approval lead time: {avg_lead_time:.0f} days")

            if max_lead_time > 30:
                score -= 15.0
                issues.append(f"Very old pending approval: {max_lead_time:.0f} days")
                remediation.append("Review and process oldest approvals")

            # Note: Filtered content events would be tracked elsewhere
            # This is a simplified check focusing on approval queue

            # Determine status
            if score >= 85.0:
                status = "healthy"
            elif score >= 70.0:
                status = "degraded"
            else:
                status = "unhealthy"

            # Build message
            if queue_size == 0:
                message = "No pending approvals"
            else:
                message = f"Pending approvals: {queue_size} | Avg lead time: {avg_lead_time:.0f} days"

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=max(0.0, score),
                message=message,
                details={
                    "approval_queue_size": queue_size,
                    "average_lead_time_days": avg_lead_time,
                    "max_lead_time_days": max_lead_time,
                    "approval_queue_dir": str(self.approval_queue_dir),
                    "approval_queue_exists": approval_queue_exists,
                    "issues": issues,
                },
                remediation=remediation if remediation else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Governance check failed: {e}",
                details={"error": str(e), "approval_queue_dir": str(self.approval_queue_dir)},
                remediation=["Check approval queue directory permissions"],
            )

