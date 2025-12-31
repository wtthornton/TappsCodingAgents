"""
Quality Analyzer - Analyzes code quality metrics and issues.
"""

from typing import Any


class QualityAnalyzer:
    """
    Analyzes code quality metrics and issues.
    
    Tracks:
    - Quality scores from reviewer agent
    - Quality issues (syntax errors, test failures)
    - Quality trends over time
    """

    def analyze_quality(
        self,
        quality_data: dict[str, Any] | None = None,
        workflow_state: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze code quality metrics.
        
        Args:
            quality_data: Quality scores from reviewer agent (if available)
            workflow_state: Workflow state (may contain quality data)
        
        Returns:
            Dictionary with quality analysis
        """
        # Collect quality scores
        scores = self._collect_scores(quality_data, workflow_state)
        
        # Identify issues
        issues = self.identify_issues(scores)
        
        # Track trends (if historical data available)
        trends = self.track_trends(scores) if self._has_historical_data() else {}
        
        return {
            "scores": scores,
            "issues": issues,
            "trends": trends,
            "recommendations": self._generate_recommendations(scores, issues)
        }

    def _collect_scores(
        self,
        quality_data: dict[str, Any] | None,
        workflow_state: dict[str, Any] | None
    ) -> dict[str, float]:
        """Collect quality scores from available sources."""
        scores = {}
        
        # From quality_data
        if quality_data:
            overall = quality_data.get("overall_score", 0.0)
            scores["overall"] = overall
            scores_by_metric = quality_data.get("scores_by_metric", {})
            scores.update(scores_by_metric)
        
        # From workflow state
        if workflow_state:
            quality_scores = workflow_state.get("quality_scores", {})
            if quality_scores:
                scores.update(quality_scores)
        
        return scores

    def identify_issues(
        self,
        scores: dict[str, float],
        thresholds: dict[str, float] | None = None
    ) -> list[dict]:
        """
        Identify quality issues below thresholds.
        
        Returns:
            List of issue dictionaries
        """
        if thresholds is None:
            thresholds = {
                "overall": 70.0,
                "complexity": 7.0,
                "security": 7.0,
                "maintainability": 7.0,
            }
        
        issues = []
        
        for metric, score in scores.items():
            threshold = thresholds.get(metric, thresholds.get("overall", 70.0))
            if score < threshold:
                severity = "high" if score < threshold * 0.8 else "medium"
                issues.append({
                    "metric": metric,
                    "score": score,
                    "threshold": threshold,
                    "severity": severity,
                    "recommendation": f"Improve {metric} score from {score:.1f} to at least {threshold:.1f}",
                })
        
        return issues

    def track_trends(self, historical_data: list[dict]) -> dict[str, str]:
        """
        Track quality trends over time.
        
        Returns:
            Dictionary with trend indicators
        """
        # Simplified trend analysis
        # In a full implementation, this would analyze historical data
        return {
            "overall": "stable",  # "improving", "declining", "stable"
        }

    def _has_historical_data(self) -> bool:
        """Check if historical data is available."""
        # Simplified: always return False for now
        # In a full implementation, this would check for historical evaluation files
        return False

    def _generate_recommendations(
        self,
        scores: dict[str, float],
        issues: list[dict]
    ) -> list[dict]:
        """Generate recommendations based on quality analysis."""
        recommendations = []
        
        # Add issue-based recommendations
        recommendations.extend(issues)
        
        # Add overall score recommendation
        overall = scores.get("overall", 0.0)
        if overall < 70.0:
            recommendations.append({
                "type": "quality",
                "description": f"Overall quality score is {overall:.1f}/100 (below 70 threshold)",
                "impact": "high",
                "recommendation": "Focus on improving code quality across all metrics",
            })
        
        return recommendations
