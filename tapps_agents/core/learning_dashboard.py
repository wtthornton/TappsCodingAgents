"""
Learning Dashboard

Provides aggregated metrics and dashboard data for the learning system.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class LearningDashboard:
    """Aggregates learning metrics and provides dashboard data."""

    def __init__(
        self,
        capability_registry: Any,  # CapabilityRegistry
        pattern_extractor: Any | None = None,  # PatternExtractor
        anti_pattern_extractor: Any | None = None,  # AntiPatternExtractor
        decision_logger: Any | None = None,  # DecisionReasoningLogger
        impact_reporter: Any | None = None,  # LearningImpactReporter
    ):
        """
        Initialize learning dashboard.

        Args:
            capability_registry: CapabilityRegistry instance
            pattern_extractor: Optional PatternExtractor instance
            anti_pattern_extractor: Optional AntiPatternExtractor instance
            decision_logger: Optional DecisionReasoningLogger instance
            impact_reporter: Optional LearningImpactReporter instance
        """
        self.capability_registry = capability_registry
        self.pattern_extractor = pattern_extractor
        self.anti_pattern_extractor = anti_pattern_extractor
        self.decision_logger = decision_logger
        self.impact_reporter = impact_reporter

    def get_capability_metrics(
        self, capability_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get capability performance metrics.

        Args:
            capability_id: Optional filter by capability

        Returns:
            Capability metrics dictionary
        """
        if capability_id:
            metric = self.capability_registry.get_capability(capability_id)
            if not metric:
                return {"capability_id": capability_id, "found": False}

            return {
                "capability_id": capability_id,
                "found": True,
                "usage_count": metric.usage_count,
                "success_rate": metric.success_rate,
                "quality_score": metric.quality_score,
                "average_duration": metric.average_duration,
                "last_used": metric.last_used.isoformat() if metric.last_used else None,
            }

        # Get all capabilities
        all_capabilities = self.capability_registry.get_all_capabilities()
        return {
            "total_capabilities": len(all_capabilities),
            "capabilities": [
                {
                    "capability_id": cap_id,
                    "usage_count": metric.usage_count,
                    "success_rate": metric.success_rate,
                    "quality_score": metric.quality_score,
                    "average_duration": metric.average_duration,
                }
                for cap_id, metric in all_capabilities.items()
            ],
        }

    def get_learning_trends(
        self, days: int = 30, capability_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get learning trend data.

        Args:
            days: Number of days to look back
            capability_id: Optional filter by capability

        Returns:
            Trend data dictionary
        """
        # This would typically query historical data
        # For now, return current metrics as trends
        metrics = self.get_capability_metrics(capability_id=capability_id)

        return {
            "period_days": days,
            "capability_id": capability_id,
            "trends": {
                "success_rate": metrics.get("success_rate", 0.0) if capability_id else 0.0,
                "quality_score": metrics.get("quality_score", 0.0) if capability_id else 0.0,
                "usage_count": metrics.get("usage_count", 0) if capability_id else 0,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_pattern_statistics(self) -> dict[str, Any]:
        """
        Get pattern statistics.

        Returns:
            Pattern statistics dictionary
        """
        pattern_count = 0
        anti_pattern_count = 0
        pattern_types: dict[str, int] = {}

        if self.pattern_extractor:
            pattern_count = len(self.pattern_extractor.patterns)
            for pattern in self.pattern_extractor.patterns.values():
                pattern_types[pattern.pattern_type] = (
                    pattern_types.get(pattern.pattern_type, 0) + 1
                )

        if self.anti_pattern_extractor:
            anti_pattern_count = len(self.anti_pattern_extractor.anti_patterns)
            for pattern in self.anti_pattern_extractor.anti_patterns.values():
                pattern_types[pattern.pattern_type] = (
                    pattern_types.get(pattern.pattern_type, 0) + 1
                )

        return {
            "total_patterns": pattern_count,
            "total_anti_patterns": anti_pattern_count,
            "patterns_by_type": pattern_types,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_security_metrics(self) -> dict[str, Any]:
        """
        Get security learning metrics.

        Returns:
            Security metrics dictionary
        """
        secure_patterns = 0
        insecure_patterns = 0
        average_security_score = 0.0

        if self.pattern_extractor:
            for pattern in self.pattern_extractor.patterns.values():
                security_score = getattr(pattern, "security_score", 0.0)
                if security_score >= 7.0:
                    secure_patterns += 1
                else:
                    insecure_patterns += 1
                average_security_score += security_score

            if self.pattern_extractor.patterns:
                average_security_score /= len(self.pattern_extractor.patterns)

        return {
            "secure_patterns": secure_patterns,
            "insecure_patterns": insecure_patterns,
            "average_security_score": average_security_score,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_failure_analysis(
        self, failure_mode_analyzer: Any | None = None  # FailureModeAnalyzer
    ) -> dict[str, Any]:
        """
        Get failure analysis data.

        Args:
            failure_mode_analyzer: Optional FailureModeAnalyzer instance

        Returns:
            Failure analysis dictionary
        """
        if not failure_mode_analyzer:
            return {
                "common_failure_modes": [],
                "total_failures": 0,
            }

        common_modes = failure_mode_analyzer.get_common_failure_modes(limit=10)
        total_failures = sum(mode["count"] for mode in common_modes)

        return {
            "common_failure_modes": common_modes,
            "total_failures": total_failures,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_dashboard_data(
        self,
        capability_id: str | None = None,
        include_trends: bool = True,
        include_failures: bool = True,
        failure_mode_analyzer: Any | None = None,
    ) -> dict[str, Any]:
        """
        Get complete dashboard data.

        Args:
            capability_id: Optional filter by capability
            include_trends: Include trend data
            include_failures: Include failure analysis
            failure_mode_analyzer: Optional FailureModeAnalyzer instance

        Returns:
            Complete dashboard data dictionary
        """
        dashboard: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "capability_metrics": self.get_capability_metrics(capability_id=capability_id),
            "pattern_statistics": self.get_pattern_statistics(),
            "security_metrics": self.get_security_metrics(),
        }

        if include_trends:
            dashboard["learning_trends"] = self.get_learning_trends(
                capability_id=capability_id
            )

        if include_failures:
            dashboard["failure_analysis"] = self.get_failure_analysis(
                failure_mode_analyzer=failure_mode_analyzer
            )

        if self.decision_logger:
            dashboard["decision_statistics"] = self.decision_logger.get_decision_statistics()

        if self.impact_reporter:
            dashboard["learning_effectiveness"] = self.impact_reporter.get_learning_effectiveness(
                capability_id=capability_id
            )

        return dashboard

