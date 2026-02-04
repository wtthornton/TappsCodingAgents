"""
Learning Explainability System

Provides transparency and explainability for the agent learning system.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class DecisionLog:
    """Log entry for a learning decision."""

    decision_id: str
    timestamp: datetime
    decision_type: str
    reasoning: str
    sources: list[str]  # learned_experience, best_practice, etc.
    confidence: float
    outcome: Any
    context: dict[str, Any] = field(default_factory=dict)


class DecisionReasoningLogger:
    """Logs all learning decisions with full context."""

    def __init__(self):
        """Initialize decision reasoning logger."""
        self.decision_logs: list[DecisionLog] = []
        self.max_logs: int = 1000  # Limit to prevent memory issues

    def log_decision(
        self,
        decision_type: str,
        reasoning: str,
        sources: list[str],
        confidence: float,
        outcome: Any,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Log a decision with reasoning.

        Args:
            decision_type: Type of decision
            reasoning: Reasoning for the decision
            sources: List of sources used
            confidence: Confidence score (0.0-1.0)
            outcome: Decision outcome
            context: Optional context dictionary

        Returns:
            Decision ID
        """
        decision_id = str(uuid4())
        log_entry = DecisionLog(
            decision_id=decision_id,
            timestamp=datetime.now(UTC),
            decision_type=decision_type,
            reasoning=reasoning,
            sources=sources,
            confidence=confidence,
            outcome=outcome,
            context=context or {},
        )

        self.decision_logs.append(log_entry)

        # Limit log size
        if len(self.decision_logs) > self.max_logs:
            self.decision_logs = self.decision_logs[-self.max_logs :]

        logger.debug(f"Logged decision {decision_id}: {decision_type}")
        return decision_id

    def get_decision_history(
        self,
        decision_type: str | None = None,
        limit: int = 100,
        since: datetime | None = None,
    ) -> list[DecisionLog]:
        """
        Retrieve decision history.

        Args:
            decision_type: Optional filter by decision type
            limit: Maximum results
            since: Optional filter by timestamp

        Returns:
            List of decision logs
        """
        logs = self.decision_logs

        if decision_type:
            logs = [log for log in logs if log.decision_type == decision_type]

        if since:
            logs = [log for log in logs if log.timestamp >= since]

        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]

    def explain_decision(self, decision_id: str) -> dict[str, Any] | None:
        """
        Generate human-readable explanation for a decision.

        Args:
            decision_id: Decision identifier

        Returns:
            Explanation dictionary or None if not found
        """
        log = next((l for l in self.decision_logs if l.decision_id == decision_id), None)
        if not log:
            return None

        return {
            "decision_id": log.decision_id,
            "decision_type": log.decision_type,
            "timestamp": log.timestamp.isoformat(),
            "reasoning": log.reasoning,
            "sources": log.sources,
            "confidence": log.confidence,
            "outcome": log.outcome,
            "context": log.context,
            "explanation": (
                f"Decision '{log.decision_type}' was made with {log.confidence:.1%} confidence. "
                f"Reasoning: {log.reasoning}. "
                f"Sources: {', '.join(log.sources)}."
            ),
        }

    def get_decision_statistics(self) -> dict[str, Any]:
        """
        Get decision statistics.

        Returns:
            Dictionary with decision metrics
        """
        if not self.decision_logs:
            return {
                "total_decisions": 0,
                "by_type": {},
                "by_source": {},
                "average_confidence": 0.0,
            }

        stats: dict[str, Any] = {
            "total_decisions": len(self.decision_logs),
            "by_type": {},
            "by_source": {},
            "average_confidence": 0.0,
        }

        total_confidence = 0.0
        for log in self.decision_logs:
            # Count by type
            stats["by_type"][log.decision_type] = (
                stats["by_type"].get(log.decision_type, 0) + 1
            )

            # Count by source
            for source in log.sources:
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

            total_confidence += log.confidence

        stats["average_confidence"] = (
            total_confidence / len(self.decision_logs) if self.decision_logs else 0.0
        )

        return stats


class PatternSelectionExplainer:
    """Explains why patterns were selected."""

    def explain_pattern_selection(
        self,
        selected_patterns: list[Any],  # CodePattern
        context: str,
        pattern_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Explain why patterns were selected.

        Args:
            selected_patterns: List of selected patterns
            context: Context string
            pattern_type: Optional pattern type filter

        Returns:
            Explanation dictionary
        """
        if not selected_patterns:
            return {
                "selected_count": 0,
                "explanation": "No patterns selected for this context.",
                "patterns": [],
            }

        explanations = []
        for pattern in selected_patterns:
            relevance_score = self._calculate_relevance(pattern, context)
            explanations.append(
                {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "relevance_score": relevance_score,
                    "quality_score": pattern.quality_score,
                    "security_score": getattr(pattern, "security_score", 0.0),
                    "usage_count": pattern.usage_count,
                    "success_rate": pattern.success_rate,
                    "justification": (
                        f"Selected pattern '{pattern.pattern_id}' "
                        f"(type: {pattern.pattern_type}) "
                        f"with quality score {pattern.quality_score:.2f}, "
                        f"security score {getattr(pattern, 'security_score', 0.0):.2f}, "
                        f"and {pattern.usage_count} previous uses."
                    ),
                }
            )

        return {
            "selected_count": len(selected_patterns),
            "explanation": (
                f"Selected {len(selected_patterns)} pattern(s) "
                f"based on quality, security, and usage history."
            ),
            "patterns": explanations,
        }

    def explain_pattern_relevance(
        self, pattern: Any, context: str  # CodePattern
    ) -> dict[str, Any]:
        """
        Show relevance calculation for a pattern.

        Args:
            pattern: CodePattern instance
            context: Context string

        Returns:
            Relevance explanation
        """
        relevance = self._calculate_relevance(pattern, context)

        return {
            "pattern_id": pattern.pattern_id,
            "relevance_score": relevance,
            "factors": {
                "quality_score": pattern.quality_score,
                "security_score": getattr(pattern, "security_score", 0.0),
                "usage_count": pattern.usage_count,
                "success_rate": pattern.success_rate,
            },
            "explanation": (
                f"Pattern relevance: {relevance:.2f} "
                f"(quality: {pattern.quality_score:.2f}, "
                f"security: {getattr(pattern, 'security_score', 0.0):.2f}, "
                f"usage: {pattern.usage_count})"
            ),
        }

    def compare_patterns(
        self, patterns: list[Any]  # CodePattern
    ) -> dict[str, Any]:
        """
        Compare multiple patterns.

        Args:
            patterns: List of patterns to compare

        Returns:
            Comparison dictionary
        """
        if not patterns:
            return {"patterns": [], "comparison": "No patterns to compare."}

        comparisons = []
        for pattern in patterns:
            comparisons.append(
                {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "quality_score": pattern.quality_score,
                    "security_score": getattr(pattern, "security_score", 0.0),
                    "usage_count": pattern.usage_count,
                    "success_rate": pattern.success_rate,
                    "is_anti_pattern": getattr(pattern, "is_anti_pattern", False),
                }
            )

        # Sort by quality + security
        comparisons.sort(
            key=lambda x: (
                x["quality_score"] + x["security_score"],
                x["usage_count"],
            ),
            reverse=True,
        )

        return {
            "patterns": comparisons,
            "comparison": (
                f"Compared {len(patterns)} patterns. "
                f"Top pattern: {comparisons[0]['pattern_id']} "
                f"(quality: {comparisons[0]['quality_score']:.2f}, "
                f"security: {comparisons[0]['security_score']:.2f})"
            ),
        }

    def get_pattern_justification(
        self, pattern: Any, context: str  # CodePattern
    ) -> str:
        """
        Get human-readable justification for pattern selection.

        Args:
            pattern: CodePattern instance
            context: Context string

        Returns:
            Justification string
        """
        relevance = self._calculate_relevance(pattern, context)

        justification_parts = [
            f"Pattern '{pattern.pattern_id}' was selected because:",
            f"- High quality score ({pattern.quality_score:.2f})",
            f"- Security score: {getattr(pattern, 'security_score', 0.0):.2f}",
            f"- Successfully used {pattern.usage_count} time(s) with "
            f"{pattern.success_rate:.1%} success rate",
            f"- Relevance to context: {relevance:.2f}",
        ]

        if getattr(pattern, "is_anti_pattern", False):
            justification_parts.append(
                f"- WARNING: This is an anti-pattern with "
                f"{pattern.rejection_count} rejection(s)"
            )

        return " ".join(justification_parts)

    def _calculate_relevance(self, pattern: Any, context: str) -> float:  # CodePattern
        """
        Calculate relevance score for a pattern in a context.

        Args:
            pattern: CodePattern instance
            context: Context string

        Returns:
            Relevance score (0.0-1.0)
        """
        # Simple relevance calculation based on context matching
        # In production, might use more sophisticated NLP matching
        context_lower = context.lower()
        pattern_context_lower = pattern.context.lower()

        # Check if context keywords match pattern context
        relevance = 0.5  # Base relevance

        if any(word in pattern_context_lower for word in context_lower.split()):
            relevance += 0.3

        # Boost relevance based on quality and usage
        relevance += pattern.quality_score * 0.1
        relevance += min(pattern.usage_count / 10.0, 0.1)

        return min(1.0, relevance)


class LearningImpactReporter:
    """Generates learning impact reports."""

    def __init__(self):
        """Initialize learning impact reporter."""
        self.impact_history: list[dict[str, Any]] = []

    def generate_impact_report(
        self,
        capability_id: str,
        before_metrics: dict[str, float],
        after_metrics: dict[str, float],
        learning_session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate learning impact report.

        Args:
            capability_id: Capability identifier
            before_metrics: Metrics before learning
            after_metrics: Metrics after learning
            learning_session_id: Optional session identifier

        Returns:
            Impact report dictionary
        """
        improvements = {}
        for metric, after_value in after_metrics.items():
            before_value = before_metrics.get(metric, 0.0)
            improvement = after_value - before_value
            improvement_percent = (
                (improvement / before_value * 100) if before_value > 0 else 0.0
            )
            improvements[metric] = {
                "before": before_value,
                "after": after_value,
                "improvement": improvement,
                "improvement_percent": improvement_percent,
            }

        overall_improvement = sum(
            imp["improvement"] for imp in improvements.values()
        ) / len(improvements) if improvements else 0.0

        report = {
            "capability_id": capability_id,
            "learning_session_id": learning_session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "improvements": improvements,
            "overall_improvement": overall_improvement,
            "effectiveness": self._calculate_effectiveness(improvements),
        }

        self.impact_history.append(report)
        return report

    def track_improvement(
        self,
        capability_id: str,
        metric_name: str,
        before_value: float,
        after_value: float,
    ) -> dict[str, Any]:
        """
        Track improvement for a specific metric.

        Args:
            capability_id: Capability identifier
            metric_name: Metric name
            before_value: Value before learning
            after_value: Value after learning

        Returns:
            Improvement tracking dictionary
        """
        improvement = after_value - before_value
        improvement_percent = (
            (improvement / before_value * 100) if before_value > 0 else 0.0
        )

        return {
            "capability_id": capability_id,
            "metric": metric_name,
            "before": before_value,
            "after": after_value,
            "improvement": improvement,
            "improvement_percent": improvement_percent,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_learning_effectiveness(
        self, capability_id: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate learning effectiveness metrics.

        Args:
            capability_id: Optional filter by capability

        Returns:
            Effectiveness metrics
        """
        reports = self.impact_history
        if capability_id:
            reports = [r for r in reports if r["capability_id"] == capability_id]

        if not reports:
            return {
                "total_sessions": 0,
                "average_improvement": 0.0,
                "effectiveness_score": 0.0,
            }

        total_improvement = sum(r["overall_improvement"] for r in reports)
        average_improvement = total_improvement / len(reports)
        effectiveness_score = min(1.0, average_improvement * 10.0)  # Scale to 0-1

        return {
            "total_sessions": len(reports),
            "average_improvement": average_improvement,
            "effectiveness_score": effectiveness_score,
            "improvement_trend": "positive" if average_improvement > 0 else "negative",
        }

    def export_report(
        self, report: dict[str, Any], format: str = "markdown"
    ) -> str:
        """
        Export report to specified format.

        Args:
            report: Report dictionary
            format: Export format (markdown or json)

        Returns:
            Exported report string
        """
        if format == "json":
            import json

            return json.dumps(report, indent=2)

        # Markdown format
        lines = [
            "# Learning Impact Report",
            "",
            f"**Capability**: {report['capability_id']}",
            f"**Timestamp**: {report['timestamp']}",
            f"**Overall Improvement**: {report['overall_improvement']:.2f}",
            f"**Effectiveness**: {report['effectiveness']:.2f}",
            "",
            "## Improvements",
            "",
        ]

        for metric, data in report["improvements"].items():
            lines.append(f"### {metric}")
            lines.append(f"- Before: {data['before']:.2f}")
            lines.append(f"- After: {data['after']:.2f}")
            lines.append(f"- Improvement: {data['improvement']:.2f} ({data['improvement_percent']:.1f}%)")
            lines.append("")

        return "\n".join(lines)

    def _calculate_effectiveness(
        self, improvements: dict[str, dict[str, Any]]
    ) -> float:
        """
        Calculate overall effectiveness score.

        Args:
            improvements: Dictionary of improvements

        Returns:
            Effectiveness score (0.0-1.0)
        """
        if not improvements:
            return 0.0

        # Weighted average of improvements
        total_weight = 0.0
        weighted_sum = 0.0

        for _metric, data in improvements.items():
            # Weight by improvement magnitude
            weight = abs(data["improvement"])
            total_weight += weight
            weighted_sum += data["improvement"] * weight

        if total_weight == 0:
            return 0.0

        effectiveness = weighted_sum / total_weight
        # Normalize to 0-1
        return max(0.0, min(1.0, (effectiveness + 1.0) / 2.0))

