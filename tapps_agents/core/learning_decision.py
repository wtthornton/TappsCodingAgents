"""
Learning Decision Engine

Combines learned experience and best practices to make intelligent decisions
for the learning system.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .best_practice_consultant import BestPracticeAdvice, BestPracticeConsultant
from .learning_confidence import LearningConfidenceCalculator

logger = logging.getLogger(__name__)


class DecisionSource(Enum):
    """Source of the decision."""

    LEARNED_EXPERIENCE = "learned_experience"
    BEST_PRACTICE = "best_practice"
    COMBINED = "combined"
    DEFAULT = "default"


@dataclass
class DecisionResult:
    """Result of a learning decision."""

    value: Any
    source: DecisionSource
    confidence: float
    reasoning: str
    should_proceed: bool
    learned_confidence: float | None = None
    best_practice_confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningDecision:
    """Complete learning decision with all context."""

    decision_type: str
    result: DecisionResult
    learned_data: dict[str, Any]
    best_practice_advice: BestPracticeAdvice | None = None
    context: dict[str, Any] = field(default_factory=dict)


class LearningDecisionEngine:
    """
    Makes learning decisions by combining learned experience and best practices.

    Implements the "Guided Autonomy" pattern:
    - Prioritizes learned experience when high confidence
    - Falls back to best practices when learned confidence is low
    - Uses defaults when both sources are insufficient
    """

    # Decision thresholds
    LEARNED_HIGH_CONFIDENCE = 0.8
    BEST_PRACTICE_HIGH_CONFIDENCE = 0.7
    LEARNED_MODERATE_CONFIDENCE = 0.6
    DEFAULT_CONFIDENCE = 0.5

    # Minimum confidence to proceed
    MIN_PROCEED_CONFIDENCE = 0.5

    def __init__(
        self,
        capability_registry: Any,  # CapabilityRegistry
        best_practice_consultant: BestPracticeConsultant | None,
        confidence_calculator: LearningConfidenceCalculator | None = None,
    ):
        """
        Initialize learning decision engine.

        Args:
            capability_registry: CapabilityRegistry instance
            best_practice_consultant: BestPracticeConsultant instance (optional)
            confidence_calculator: LearningConfidenceCalculator instance (optional)
        """
        self.capability_registry = capability_registry
        self.best_practice_consultant = best_practice_consultant
        self.confidence_calculator = (
            confidence_calculator or LearningConfidenceCalculator()
        )
        self._decision_count = 0
        self._decision_metrics: dict[str, list[DecisionResult]] = {}

    async def make_decision(
        self,
        decision_type: str,
        learned_data: dict[str, Any],
        context: dict[str, Any],
        default_value: Any = None,
    ) -> LearningDecision:
        """
        Make a learning decision combining learned experience and best practices.

        Decision Logic:
        1. Calculate learned experience confidence
        2. Consult best practices (if available)
        3. Apply decision logic to choose value
        4. Return decision result

        Args:
            decision_type: Type of decision (e.g., "quality_threshold")
            learned_data: Dictionary with learned experience metrics
            context: Context dictionary for decision
            default_value: Default value if both sources insufficient

        Returns:
            LearningDecision with result and metadata
        """
        self._decision_count += 1

        logger.debug(
            f"Making decision: {decision_type} "
            f"(learned_data keys: {list(learned_data.keys())})"
        )

        # Calculate learned experience confidence
        learned_confidence = self._calculate_learned_confidence(learned_data)
        learned_value = learned_data.get("value") or default_value

        # Get best practice advice (if consultant available)
        best_practice_advice = None
        if self.best_practice_consultant:
            try:
                best_practice_advice = (
                    await self.best_practice_consultant.consult_best_practices(
                        decision_type=decision_type, context=context
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to consult best practices: {e}")

        # Calculate best practice confidence
        best_practice_confidence = None
        best_practice_value = None
        if best_practice_advice:
            best_practice_confidence = best_practice_advice.confidence
            # Extract value from advice (may need parsing based on decision type)
            best_practice_value = self._extract_value_from_advice(
                best_practice_advice.advice, decision_type
            )

        # Apply decision logic
        result = self._apply_decision_logic(
            learned_confidence=learned_confidence,
            best_practice_confidence=best_practice_confidence,
            learned_value=learned_value,
            best_practice_value=best_practice_value,
            default_value=default_value,
            decision_type=decision_type,
        )

        # Track metrics
        if decision_type not in self._decision_metrics:
            self._decision_metrics[decision_type] = []
        self._decision_metrics[decision_type].append(result)

        return LearningDecision(
            decision_type=decision_type,
            result=result,
            learned_data=learned_data,
            best_practice_advice=best_practice_advice,
            context=context,
        )

    def _calculate_learned_confidence(self, learned_data: dict[str, Any]) -> float:
        """
        Calculate confidence from learned experience data.

        Args:
            learned_data: Dictionary with learned experience metrics

        Returns:
            Confidence score (0.0-1.0)
        """
        # Extract metrics
        usage_count = learned_data.get("usage_count", 0)
        success_rate = learned_data.get("success_rate", 0.0)
        quality_score = learned_data.get("quality_score", 0.0)
        context_relevance = learned_data.get("context_relevance", 1.0)

        # Calculate confidence
        confidence = self.confidence_calculator.calculate_learned_confidence(
            usage_count=usage_count,
            success_rate=success_rate,
            quality_score=quality_score,
            context_relevance=context_relevance,
        )

        return confidence

    def _extract_value_from_advice(self, advice: str, decision_type: str) -> Any:
        """
        Extract value from best practice advice text.

        This is a simple implementation - in production, might use
        structured output or parsing based on decision type.

        Args:
            advice: Advice text from expert
            decision_type: Type of decision

        Returns:
            Extracted value (may be None if extraction fails)
        """
        # For now, return the advice text itself
        # In production, might parse structured values like thresholds, etc.
        return advice

    def _apply_decision_logic(
        self,
        learned_confidence: float,
        best_practice_confidence: float | None,
        learned_value: Any,
        best_practice_value: Any,
        default_value: Any,
        decision_type: str,
    ) -> DecisionResult:
        """
        Apply decision logic to choose value from available sources.

        Priority:
        1. Learned experience (confidence >= 0.8)
        2. Best practice (confidence >= 0.7)
        3. Moderate learned experience (confidence >= 0.6)
        4. Best practice fallback
        5. Default

        Args:
            learned_confidence: Confidence from learned experience
            best_practice_confidence: Confidence from best practices
            learned_value: Value from learned experience
            best_practice_value: Value from best practices
            default_value: Default value
            decision_type: Type of decision

        Returns:
            DecisionResult with chosen value and reasoning
        """
        # Priority 1: High confidence learned experience
        if learned_confidence >= self.LEARNED_HIGH_CONFIDENCE:
            return DecisionResult(
                value=learned_value,
                source=DecisionSource.LEARNED_EXPERIENCE,
                confidence=learned_confidence,
                reasoning=(
                    f"High confidence from learned experience "
                    f"(confidence={learned_confidence:.3f})"
                ),
                should_proceed=True,
                learned_confidence=learned_confidence,
                best_practice_confidence=best_practice_confidence,
            )

        # Priority 2: High confidence best practice
        if (
            best_practice_confidence is not None
            and best_practice_confidence >= self.BEST_PRACTICE_HIGH_CONFIDENCE
        ):
            return DecisionResult(
                value=best_practice_value,
                source=DecisionSource.BEST_PRACTICE,
                confidence=best_practice_confidence,
                reasoning=(
                    f"High confidence from best practices "
                    f"(confidence={best_practice_confidence:.3f})"
                ),
                should_proceed=True,
                learned_confidence=learned_confidence,
                best_practice_confidence=best_practice_confidence,
            )

        # Priority 3: Moderate learned experience
        if learned_confidence >= self.LEARNED_MODERATE_CONFIDENCE:
            return DecisionResult(
                value=learned_value,
                source=DecisionSource.LEARNED_EXPERIENCE,
                confidence=learned_confidence,
                reasoning=(
                    f"Moderate confidence from learned experience "
                    f"(confidence={learned_confidence:.3f})"
                ),
                should_proceed=learned_confidence >= self.MIN_PROCEED_CONFIDENCE,
                learned_confidence=learned_confidence,
                best_practice_confidence=best_practice_confidence,
            )

        # Priority 4: Best practice fallback
        if best_practice_confidence is not None:
            return DecisionResult(
                value=best_practice_value,
                source=DecisionSource.BEST_PRACTICE,
                confidence=best_practice_confidence,
                reasoning=(
                    f"Using best practice as fallback "
                    f"(confidence={best_practice_confidence:.3f}, "
                    f"learned_confidence={learned_confidence:.3f})"
                ),
                should_proceed=best_practice_confidence >= self.MIN_PROCEED_CONFIDENCE,
                learned_confidence=learned_confidence,
                best_practice_confidence=best_practice_confidence,
            )

        # Priority 5: Default
        return DecisionResult(
            value=default_value,
            source=DecisionSource.DEFAULT,
            confidence=self.DEFAULT_CONFIDENCE,
            reasoning=(
                f"No sufficient confidence from either source "
                f"(learned={learned_confidence:.3f}, "
                f"best_practice={best_practice_confidence})"
            ),
            should_proceed=False,
            learned_confidence=learned_confidence,
            best_practice_confidence=best_practice_confidence,
        )

    def get_decision_statistics(self) -> dict[str, Any]:
        """
        Get decision statistics.

        Returns:
            Dictionary with decision statistics
        """
        stats: dict[str, Any] = {
            "total_decisions": self._decision_count,
            "by_type": {},
            "by_source": {},
        }

        # Count by type and source
        for decision_type, results in self._decision_metrics.items():
            stats["by_type"][decision_type] = len(results)

            for result in results:
                source = result.source.value
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        return stats

    def get_cache_statistics(self) -> dict[str, Any] | None:
        """
        Get cache statistics from best practice consultant.

        Returns:
            Cache statistics if consultant available, None otherwise
        """
        if self.best_practice_consultant:
            return self.best_practice_consultant.get_cache_statistics()
        return None
