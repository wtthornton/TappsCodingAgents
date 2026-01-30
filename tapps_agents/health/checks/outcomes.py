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
                try:
                    from ...workflow.execution_metrics import ExecutionMetricsCollector

                    collector = ExecutionMetricsCollector(project_root=self.project_root)
                    exec_metrics = collector.get_metrics(limit=2000)
                    review_metrics = [
                        m
                        for m in exec_metrics
                        if m.command == "review"
                        or (m.skill and "review" in (m.skill or "").lower())
                    ]
                    if review_metrics:
                        total = len(review_metrics)
                        success = sum(1 for m in review_metrics if m.status == "success")
                        gate_passed = sum(
                            1 for m in review_metrics if getattr(m, "gate_pass", False)
                        )
                        gate_rate = (gate_passed / total * 100) if total else 0.0
                        success_rate = (success / total * 100) if total else 0.0
                        derived_score = 50.0 + min(25.0, success_rate / 4.0 + gate_rate / 4.0)
                        return HealthCheckResult(
                            name=self.name,
                            status="degraded",
                            score=min(75.0, derived_score),
                            message=(
                                f"Outcomes derived from execution metrics: {total} review steps, "
                                f"{gate_rate:.0f}% passed gate"
                            ),
                            details={
                                "average_score": 0.0,
                                "score_trend": "unknown",
                                "score_change": 0.0,
                                "review_artifacts_count": 0,
                                "improvement_cycles": 0,
                                "reports_dir": str(self.reports_dir),
                                "review_steps_from_execution_metrics": total,
                                "gate_pass_rate": gate_rate,
                                "success_rate": success_rate,
                                "issues": [],
                            },
                            remediation=[
                                "Run reviewer agent or quality workflows to generate metrics"
                            ],
                        )
                except Exception:
                    pass
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

