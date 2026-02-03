"""
Outcome Health Check.

Checks quality trends and improvement metrics.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from ...workflow.analytics_dashboard_cursor import CursorAnalyticsAccessor
from ...workflow.review_artifact import ReviewArtifact
from ..base import HealthCheck, HealthCheckResult


class OutcomeHealthCheck(HealthCheck):
    """Health check for quality trends and outcomes."""

    def __init__(self, project_root: Path | None = None, reports_dir: Path | None = None):
        """
        Initialize outcome health check.

        Args:
            project_root: Project root directory
            reports_dir: Reports directory (defaults to .tapps-agents/reports)
        """
        super().__init__(name="outcomes", dependencies=["environment", "execution"])
        self.project_root = project_root or Path.cwd()
        self.reports_dir = reports_dir or (self.project_root / ".tapps-agents" / "reports")
        self.accessor = CursorAnalyticsAccessor()

    def _compute_outcomes_from_execution_metrics(self, days: int = 30) -> dict:
        """
        Compute outcomes from execution metrics when review artifacts don't exist.

        Args:
            days: Number of days to look back for metrics

        Returns:
            Dictionary with review_executions_count, success_rate, and gate_pass_rate
        """
        try:
            from datetime import UTC
            from ...workflow.execution_metrics import ExecutionMetricsCollector
            import logging

            collector = ExecutionMetricsCollector(project_root=self.project_root)

            # Get metrics with reasonable limit (5000 max for ~30 days of heavy usage)
            MAX_METRICS_TO_SCAN = 5000
            all_metrics = collector.get_metrics(limit=MAX_METRICS_TO_SCAN)

            # Log warning if we hit the limit
            if len(all_metrics) >= MAX_METRICS_TO_SCAN:
                logging.getLogger(__name__).warning(
                    "Hit metrics scan limit (%d); results may be incomplete",
                    MAX_METRICS_TO_SCAN
                )

            # Filter for review executions within the last N days (timezone-aware)
            cutoff_date = datetime.now(UTC) - timedelta(days=days)
            review_metrics = []
            for m in all_metrics:
                # Parse timestamp and ensure timezone-aware comparison
                try:
                    ts = datetime.fromisoformat(m.started_at.replace("Z", "+00:00"))
                    # Convert naive datetime to UTC if needed
                    if ts.tzinfo is None:
                        from datetime import UTC
                        ts = ts.replace(tzinfo=UTC)

                    if ts >= cutoff_date:
                        if m.command == "review" or (m.skill and "reviewer" in (m.skill or "").lower()):
                            review_metrics.append(m)
                except (ValueError, AttributeError):
                    # Skip metrics with invalid timestamps
                    continue

            if not review_metrics:
                return {
                    "review_executions_count": 0,
                    "success_rate": 0.0,
                    "gate_pass_rate": None,
                }

            total = len(review_metrics)
            success_count = sum(1 for m in review_metrics if m.status == "success")
            success_rate = (success_count / total * 100) if total > 0 else 0.0

            # Calculate gate pass rate (only for metrics that have gate_pass field)
            gate_pass_metrics = [m for m in review_metrics if m.gate_pass is not None]
            if gate_pass_metrics:
                gate_pass_count = sum(1 for m in gate_pass_metrics if m.gate_pass is True)
                gate_pass_rate = (gate_pass_count / len(gate_pass_metrics) * 100)
            else:
                gate_pass_rate = None

            return {
                "review_executions_count": total,
                "success_rate": success_rate,
                "gate_pass_rate": gate_pass_rate,
            }

        except Exception as e:
            # If fallback fails, log and return empty result
            import logging
            logging.getLogger(__name__).debug(
                "Failed to compute outcomes from execution metrics: %s", e
            )
            return {
                "review_executions_count": 0,
                "success_rate": 0.0,
                "gate_pass_rate": None,
            }

    def run(self) -> HealthCheckResult:
        """
        Run outcome health check.

        Returns:
            HealthCheckResult with outcome trends
        """
        try:
            # Get analytics data for trends
            dashboard_data = self.accessor.get_dashboard_data()
            agents_data = dashboard_data.get("agents", [])
            workflows_data = dashboard_data.get("workflows", [])

            # Look for review artifacts in reports directory
            review_artifacts = []
            if self.reports_dir.exists():
                for artifact_file in self.reports_dir.rglob("review_*.json"):
                    try:
                        with open(artifact_file, encoding="utf-8") as f:
                            data = json.load(f)
                            artifact = ReviewArtifact.from_dict(data)
                            if artifact.overall_score is not None:
                                review_artifacts.append(artifact)
                    except Exception:
                        continue

            # Calculate trends from review artifacts
            score_trend = "unknown"
            avg_score = 0.0
            score_change = 0.0

            if review_artifacts:
                # Sort by timestamp
                review_artifacts.sort(key=lambda a: a.timestamp)

                # Get recent artifacts (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_artifacts = [
                    a
                    for a in review_artifacts
                    if datetime.fromisoformat(a.timestamp.replace("Z", "+00:00")) >= thirty_days_ago
                ]

                if recent_artifacts:
                    scores = [a.overall_score for a in recent_artifacts if a.overall_score is not None]
                    if scores:
                        avg_score = sum(scores) / len(scores)

                        # Calculate trend (compare first half to second half)
                        if len(scores) >= 4:
                            first_half = scores[: len(scores) // 2]
                            second_half = scores[len(scores) // 2 :]
                            first_avg = sum(first_half) / len(first_half)
                            second_avg = sum(second_half) / len(second_half)
                            score_change = second_avg - first_avg

                            if score_change > 5.0:
                                score_trend = "improving"
                            elif score_change < -5.0:
                                score_trend = "degrading"
                            else:
                                score_trend = "stable"

            # Count quality improvement workflows
            quality_workflows = [
                w
                for w in workflows_data
                if "quality" in w.get("workflow_name", "").lower()
                or "improve" in w.get("workflow_name", "").lower()
            ]
            improvement_cycles = len(quality_workflows)

            # Calculate health score
            score = 100.0
            issues = []
            remediation = []

            # Check if we have any data; if not, try fallback to execution metrics (review steps)
            if not review_artifacts and not agents_data:
                # Fallback: derive outcomes from execution metrics (review steps, gate_pass)
                import logging
                fallback_data = self._compute_outcomes_from_execution_metrics(days=30)

                if fallback_data["review_executions_count"] > 0:
                    total = fallback_data["review_executions_count"]
                    success_rate = fallback_data["success_rate"]
                    gate_pass_rate = fallback_data["gate_pass_rate"]

                    # Calculate score: 60 base + 10 if success_rate ≥80% + 5 if gate_pass_rate ≥70%
                    fallback_score = 60.0
                    if success_rate >= 80.0:
                        fallback_score += 10.0
                    if gate_pass_rate is not None and gate_pass_rate >= 70.0:
                        fallback_score += 5.0

                    # Build message
                    gate_msg = f"{gate_pass_rate:.0f}% passed gate" if gate_pass_rate is not None else "no gate data"
                    message = (
                        f"Outcomes derived from execution metrics: {total} review steps, "
                        f"{gate_msg}"
                    )

                    logging.getLogger(__name__).info(
                        "Outcomes fallback activated: %d review executions processed", total
                    )

                    return HealthCheckResult(
                        name=self.name,
                        status="degraded",
                        score=fallback_score,
                        message=message,
                        details={
                            "average_score": 0.0,
                            "score_trend": "unknown",
                            "score_change": 0.0,
                            "review_artifacts_count": 0,
                            "improvement_cycles": 0,
                            "reports_dir": str(self.reports_dir),
                            "fallback_used": True,
                            "fallback_source": "execution_metrics",
                            "review_executions_count": total,
                            "success_rate": success_rate,
                            "gate_pass_rate": gate_pass_rate,
                            "issues": [],
                        },
                        remediation=[
                            "Run reviewer agent or quality workflows to generate review artifacts"
                        ],
                    )

                score = 50.0
                issues.append("No quality metrics available")
                remediation.append("Run reviewer agent or quality workflows to generate metrics")
            else:
                # Check score trend
                if score_trend == "degrading":
                    score -= 20.0
                    issues.append(f"Quality scores declining: {score_change:.1f} point change")
                    remediation.append("Investigate recent code changes causing quality decline")
                elif score_trend == "improving":
                    # Bonus for improvement
                    score = min(100.0, score + 5.0)

                # Check average score
                if avg_score > 0:
                    if avg_score < 60.0:
                        score -= 30.0
                        issues.append(f"Low average quality score: {avg_score:.1f}/100")
                        remediation.append("Run quality improvement workflows")
                    elif avg_score < 75.0:
                        score -= 15.0
                        issues.append(f"Moderate quality score: {avg_score:.1f}/100")

                # Check improvement activity
                if improvement_cycles == 0:
                    score -= 10.0
                    issues.append("No quality improvement workflows run")
                    remediation.append("Run quality workflows to improve code quality")

            # Determine status
            if score >= 85.0:
                status = "healthy"
            elif score >= 70.0:
                status = "degraded"
            else:
                status = "unhealthy"

            # Build message
            message_parts = []
            if avg_score > 0:
                message_parts.append(f"Avg score: {avg_score:.1f}")
            if score_trend != "unknown":
                message_parts.append(f"Trend: {score_trend}")
            if improvement_cycles > 0:
                message_parts.append(f"Improvements: {improvement_cycles}")
            if not message_parts:
                message = "No outcome data available"
            else:
                message = " | ".join(message_parts)

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=max(0.0, score),
                message=message,
                details={
                    "average_score": avg_score,
                    "score_trend": score_trend,
                    "score_change": score_change,
                    "review_artifacts_count": len(review_artifacts),
                    "improvement_cycles": improvement_cycles,
                    "reports_dir": str(self.reports_dir),
                    "issues": issues,
                },
                remediation=remediation if remediation else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Outcome check failed: {e}",
                details={"error": str(e), "reports_dir": str(self.reports_dir)},
                remediation=["Check reports directory and analytics access"],
            )

