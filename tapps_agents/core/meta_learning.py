"""
Meta-Learning System

Enables the learning system to learn about its own learning effectiveness
and optimize learning parameters autonomously.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Learning strategy types."""

    CONSERVATIVE = "conservative"  # High thresholds, slow learning
    BALANCED = "balanced"  # Medium thresholds, moderate learning
    AGGRESSIVE = "aggressive"  # Low thresholds, fast learning
    ADAPTIVE = "adaptive"  # Dynamic based on effectiveness


@dataclass
class LearningSession:
    """Represents a learning session."""

    session_id: str
    timestamp: datetime
    capability_id: str
    before_metrics: dict[str, float]
    after_metrics: dict[str, float]
    improvement_percent: float
    strategies_used: list[str]
    effectiveness_score: float


class LearningEffectivenessTracker:
    """Tracks learning effectiveness over time."""

    def __init__(self):
        """Initialize effectiveness tracker."""
        self.sessions: list[LearningSession] = []
        self.max_sessions: int = 1000  # Limit to prevent memory issues

    def track_effectiveness(
        self,
        capability_id: str,
        before_metrics: dict[str, float],
        after_metrics: dict[str, float],
        strategies_used: list[str] | None = None,
    ) -> LearningSession:
        """
        Track learning session effectiveness.

        Args:
            capability_id: Capability identifier
            before_metrics: Metrics before learning
            after_metrics: Metrics after learning
            strategies_used: Optional list of strategies used

        Returns:
            LearningSession instance
        """
        # Calculate improvement
        improvements = {}
        for metric, after_value in after_metrics.items():
            before_value = before_metrics.get(metric, 0.0)
            if before_value > 0:
                improvement = ((after_value - before_value) / before_value) * 100
            else:
                improvement = 100.0 if after_value > 0 else 0.0
            improvements[metric] = improvement

        # Average improvement percent
        improvement_percent = (
            sum(improvements.values()) / len(improvements) if improvements else 0.0
        )

        # Calculate effectiveness score (0.0-1.0)
        effectiveness_score = min(1.0, max(0.0, improvement_percent / 100.0))

        session = LearningSession(
            session_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            capability_id=capability_id,
            before_metrics=before_metrics.copy(),
            after_metrics=after_metrics.copy(),
            improvement_percent=improvement_percent,
            strategies_used=strategies_used or [],
            effectiveness_score=effectiveness_score,
        )

        self.sessions.append(session)

        # Limit session count
        if len(self.sessions) > self.max_sessions:
            self.sessions = self.sessions[-self.max_sessions :]

        logger.debug(
            f"Tracked learning session {session.session_id}: "
            f"effectiveness={effectiveness_score:.2f}"
        )

        return session

    def calculate_improvement_rate(
        self, capability_id: str | None = None, days: int = 30
    ) -> dict[str, Any]:
        """
        Calculate improvement rate over time.

        Args:
            capability_id: Optional filter by capability
            days: Number of days to look back

        Returns:
            Improvement rate metrics
        """
        sessions = self.sessions
        if capability_id:
            sessions = [s for s in sessions if s.capability_id == capability_id]

        # Filter by time
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        sessions = [s for s in sessions if s.timestamp >= cutoff_date]

        if not sessions:
            return {
                "sessions_count": 0,
                "average_improvement": 0.0,
                "improvement_rate": 0.0,
            }

        total_improvement = sum(s.improvement_percent for s in sessions)
        average_improvement = total_improvement / len(sessions)

        # Calculate rate (improvement per session)
        improvement_rate = average_improvement

        return {
            "sessions_count": len(sessions),
            "average_improvement": average_improvement,
            "improvement_rate": improvement_rate,
            "period_days": days,
        }

    def get_effective_strategies(
        self, capability_id: str | None = None
    ) -> dict[str, float]:
        """
        Identify effective learning strategies.

        Args:
            capability_id: Optional filter by capability

        Returns:
            Dictionary mapping strategy to effectiveness score
        """
        sessions = self.sessions
        if capability_id:
            sessions = [s for s in sessions if s.capability_id == capability_id]

        strategy_effectiveness: dict[str, list[float]] = {}
        for session in sessions:
            for strategy in session.strategies_used:
                if strategy not in strategy_effectiveness:
                    strategy_effectiveness[strategy] = []
                strategy_effectiveness[strategy].append(session.effectiveness_score)

        # Calculate average effectiveness per strategy
        result = {}
        for strategy, scores in strategy_effectiveness.items():
            result[strategy] = sum(scores) / len(scores) if scores else 0.0

        return result

    def get_learning_roi(
        self, capability_id: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate return on learning investment.

        Args:
            capability_id: Optional filter by capability

        Returns:
            ROI metrics
        """
        sessions = self.sessions
        if capability_id:
            sessions = [s for s in sessions if s.capability_id == capability_id]

        if not sessions:
            return {
                "total_sessions": 0,
                "total_improvement": 0.0,
                "roi_score": 0.0,
            }

        total_improvement = sum(s.improvement_percent for s in sessions)
        average_effectiveness = sum(s.effectiveness_score for s in sessions) / len(
            sessions
        )

        # ROI = average effectiveness * number of sessions
        roi_score = average_effectiveness * len(sessions)

        return {
            "total_sessions": len(sessions),
            "total_improvement": total_improvement,
            "average_effectiveness": average_effectiveness,
            "roi_score": roi_score,
        }


class LearningSelfAssessor:
    """Assesses learning quality and identifies gaps."""

    def __init__(self):
        """Initialize self-assessor."""
        self.assessments: list[dict[str, Any]] = []

    def assess_learning_quality(
        self,
        pattern_count: int,
        anti_pattern_count: int,
        average_quality: float,
        average_security: float,
    ) -> dict[str, Any]:
        """
        Assess overall learning quality.

        Args:
            pattern_count: Number of learned patterns
            anti_pattern_count: Number of anti-patterns
            average_quality: Average pattern quality score
            average_security: Average pattern security score

        Returns:
            Quality assessment dictionary
        """
        quality_score = 0.0

        # Pattern diversity (more patterns = better, but not too many)
        if pattern_count > 0:
            diversity_score = min(1.0, pattern_count / 100.0)  # Normalize to 0-1
            quality_score += diversity_score * 0.2

        # Quality score
        quality_score += average_quality * 0.4

        # Security score
        quality_score += (average_security / 10.0) * 0.3

        # Anti-pattern awareness (having anti-patterns is good for learning)
        if anti_pattern_count > 0:
            awareness_score = min(1.0, anti_pattern_count / 50.0)
            quality_score += awareness_score * 0.1

        quality_score = min(1.0, quality_score)

        assessment = {
            "quality_score": quality_score,
            "pattern_count": pattern_count,
            "anti_pattern_count": anti_pattern_count,
            "average_quality": average_quality,
            "average_security": average_security,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.assessments.append(assessment)
        return assessment

    def evaluate_pattern_quality(
        self, patterns: list[Any]  # CodePattern
    ) -> dict[str, Any]:
        """
        Evaluate pattern library quality.

        Args:
            patterns: List of patterns to evaluate

        Returns:
            Quality evaluation dictionary
        """
        if not patterns:
            return {
                "total_patterns": 0,
                "average_quality": 0.0,
                "average_security": 0.0,
                "quality_score": 0.0,
            }

        total_quality = sum(p.quality_score for p in patterns)
        total_security = sum(getattr(p, "security_score", 0.0) for p in patterns)

        average_quality = total_quality / len(patterns)
        average_security = total_security / len(patterns)

        # Quality score combines quality and security
        quality_score = (average_quality + (average_security / 10.0)) / 2.0

        return {
            "total_patterns": len(patterns),
            "average_quality": average_quality,
            "average_security": average_security,
            "quality_score": quality_score,
        }

    def identify_learning_gaps(
        self,
        capability_metrics: dict[str, Any],
        pattern_statistics: dict[str, Any],
    ) -> list[str]:
        """
        Identify areas needing improvement.

        Args:
            capability_metrics: Capability performance metrics
            pattern_statistics: Pattern library statistics

        Returns:
            List of identified gaps
        """
        gaps = []

        # Check pattern coverage
        pattern_count = pattern_statistics.get("total_patterns", 0)
        if pattern_count < 10:
            gaps.append("Low pattern coverage - need more learned patterns")

        # Check quality
        avg_quality = pattern_statistics.get("average_quality", 0.0)
        if avg_quality < 0.7:
            gaps.append("Low average pattern quality - improve code quality")

        # Check security
        avg_security = pattern_statistics.get("average_security", 0.0)
        if avg_security < 7.0:
            gaps.append("Low average security score - improve security practices")

        # Check capability performance
        if isinstance(capability_metrics, dict):
            success_rate = capability_metrics.get("success_rate", 1.0)
            if success_rate < 0.8:
                gaps.append("Low success rate - improve task execution")

        return gaps

    def suggest_improvements(
        self, assessment: dict[str, Any]
    ) -> list[str]:
        """
        Suggest how to improve learning.

        Args:
            assessment: Quality assessment dictionary

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        quality_score = assessment.get("quality_score", 0.0)
        if quality_score < 0.7:
            suggestions.append(
                "Increase learning intensity to capture more patterns"
            )
            suggestions.append("Focus on high-quality code examples")

        pattern_count = assessment.get("pattern_count", 0)
        if pattern_count < 20:
            suggestions.append("Learn from more successful tasks")

        avg_security = assessment.get("average_security", 0.0)
        if avg_security < 7.0:
            suggestions.append("Improve security scanning and filtering")

        return suggestions


class AdaptiveLearningRate:
    """Adjusts learning intensity based on effectiveness."""

    def __init__(self, base_rate: float = 0.7):
        """
        Initialize adaptive learning rate.

        Args:
            base_rate: Base learning rate (default: 0.7)
        """
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.effectiveness_history: list[float] = []

    def calculate_optimal_rate(
        self, recent_effectiveness: list[float]
    ) -> float:
        """
        Calculate optimal learning rate based on effectiveness.

        Args:
            recent_effectiveness: List of recent effectiveness scores

        Returns:
            Optimal learning rate (0.0-1.0)
        """
        if not recent_effectiveness:
            return self.base_rate

        avg_effectiveness = sum(recent_effectiveness) / len(recent_effectiveness)

        # If effectiveness is high, increase rate
        # If effectiveness is low, decrease rate
        if avg_effectiveness > 0.8:
            # High effectiveness - can be more aggressive
            optimal_rate = min(1.0, self.base_rate + 0.2)
        elif avg_effectiveness > 0.6:
            # Good effectiveness - maintain current rate
            optimal_rate = self.base_rate
        elif avg_effectiveness > 0.4:
            # Moderate effectiveness - slightly reduce
            optimal_rate = max(0.5, self.base_rate - 0.1)
        else:
            # Low effectiveness - be conservative
            optimal_rate = max(0.3, self.base_rate - 0.3)

        self.current_rate = optimal_rate
        return optimal_rate

    def adjust_learning_intensity(
        self, effectiveness_score: float
    ) -> dict[str, Any]:
        """
        Adjust learning intensity dynamically.

        Args:
            effectiveness_score: Current effectiveness score

        Returns:
            Adjustment result dictionary
        """
        self.effectiveness_history.append(effectiveness_score)

        # Keep only recent history (last 10)
        if len(self.effectiveness_history) > 10:
            self.effectiveness_history = self.effectiveness_history[-10:]

        # Calculate optimal rate
        optimal_rate = self.calculate_optimal_rate(self.effectiveness_history)

        return {
            "previous_rate": self.current_rate,
            "new_rate": optimal_rate,
            "effectiveness": effectiveness_score,
            "adjustment": optimal_rate - self.current_rate,
        }

    def optimize_thresholds(
        self,
        current_threshold: float,
        success_rate: float,
        quality_score: float,
    ) -> float:
        """
        Optimize quality thresholds based on performance.

        Args:
            current_threshold: Current quality threshold
            success_rate: Current success rate
            quality_score: Current quality score

        Returns:
            Optimized threshold
        """
        # If success rate is high and quality is good, can lower threshold slightly
        if success_rate > 0.9 and quality_score > 0.8:
            return max(0.6, current_threshold - 0.05)

        # If success rate is low, raise threshold
        if success_rate < 0.7:
            return min(0.9, current_threshold + 0.05)

        # Otherwise, maintain current threshold
        return current_threshold

    def balance_exploration(
        self, exploration_rate: float = 0.1
    ) -> dict[str, float]:
        """
        Balance exploration vs exploitation.

        Args:
            exploration_rate: Desired exploration rate

        Returns:
            Balanced rates dictionary
        """
        # Adjust based on current effectiveness
        if self.effectiveness_history:
            avg_effectiveness = sum(self.effectiveness_history) / len(
                self.effectiveness_history
            )

            # High effectiveness = more exploitation
            # Low effectiveness = more exploration
            if avg_effectiveness > 0.7:
                exploration_rate = max(0.05, exploration_rate - 0.02)
            elif avg_effectiveness < 0.5:
                exploration_rate = min(0.2, exploration_rate + 0.02)

        return {
            "exploration_rate": exploration_rate,
            "exploitation_rate": 1.0 - exploration_rate,
        }


class LearningStrategySelector:
    """Selects optimal learning strategy."""

    def __init__(self):
        """Initialize strategy selector."""
        self.strategy_performance: dict[str, list[float]] = {}

    def select_strategy(
        self,
        capability_id: str,
        current_effectiveness: float,
        hardware_profile: str | None = None,
    ) -> LearningStrategy:
        """
        Select best strategy for context.

        Args:
            capability_id: Capability identifier
            current_effectiveness: Current learning effectiveness
            hardware_profile: Optional hardware profile

        Returns:
            Selected learning strategy
        """
        # If effectiveness is high, can be more aggressive
        if current_effectiveness > 0.8:
            return LearningStrategy.AGGRESSIVE

        # If effectiveness is moderate, use balanced
        if current_effectiveness > 0.6:
            return LearningStrategy.BALANCED

        # If effectiveness is low or hardware is constrained, be conservative
        if hardware_profile == "nuc" or current_effectiveness < 0.4:
            return LearningStrategy.CONSERVATIVE

        # Default to adaptive
        return LearningStrategy.ADAPTIVE

    def test_strategy(
        self, strategy: LearningStrategy, effectiveness: float
    ) -> dict[str, Any]:
        """
        Test strategy effectiveness.

        Args:
            strategy: Strategy to test
            effectiveness: Effectiveness score

        Returns:
            Test result dictionary
        """
        strategy_name = strategy.value
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = []

        self.strategy_performance[strategy_name].append(effectiveness)

        # Keep only recent performance (last 20)
        if len(self.strategy_performance[strategy_name]) > 20:
            self.strategy_performance[strategy_name] = self.strategy_performance[
                strategy_name
            ][-20:]

        avg_effectiveness = (
            sum(self.strategy_performance[strategy_name])
            / len(self.strategy_performance[strategy_name])
            if self.strategy_performance[strategy_name]
            else 0.0
        )

        return {
            "strategy": strategy_name,
            "effectiveness": effectiveness,
            "average_effectiveness": avg_effectiveness,
            "test_count": len(self.strategy_performance[strategy_name]),
        }

    def switch_strategy(
        self,
        current_strategy: LearningStrategy,
        new_strategy: LearningStrategy,
    ) -> dict[str, Any]:
        """
        Switch to a better strategy.

        Args:
            current_strategy: Current strategy
            new_strategy: New strategy to switch to

        Returns:
            Switch result dictionary
        """
        current_perf = self.strategy_performance.get(current_strategy.value, [])
        new_perf = self.strategy_performance.get(new_strategy.value, [])

        current_avg = (
            sum(current_perf) / len(current_perf) if current_perf else 0.0
        )
        new_avg = sum(new_perf) / len(new_perf) if new_perf else 0.0

        return {
            "switched": new_avg > current_avg,
            "current_strategy": current_strategy.value,
            "new_strategy": new_strategy.value,
            "current_avg": current_avg,
            "new_avg": new_avg,
        }

    def optimize_strategy(
        self, strategy: LearningStrategy, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            strategy: Strategy to optimize
            parameters: Current parameters

        Returns:
            Optimized parameters
        """
        # Simple optimization - adjust thresholds based on strategy
        optimized = parameters.copy()

        if strategy == LearningStrategy.CONSERVATIVE:
            optimized["quality_threshold"] = max(
                0.8, parameters.get("quality_threshold", 0.7)
            )
            optimized["security_threshold"] = max(
                8.0, parameters.get("security_threshold", 7.0)
            )
        elif strategy == LearningStrategy.AGGRESSIVE:
            optimized["quality_threshold"] = min(
                0.6, parameters.get("quality_threshold", 0.7)
            )
            optimized["security_threshold"] = min(
                6.0, parameters.get("security_threshold", 7.0)
            )
        elif strategy == LearningStrategy.BALANCED:
            optimized["quality_threshold"] = 0.7
            optimized["security_threshold"] = 7.0

        return optimized

