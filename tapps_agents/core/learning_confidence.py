"""
Learning Confidence Calculator

Calculates confidence scores for learning system decisions, combining
learned experience and best practices consultation results.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LearnedExperienceMetrics:
    """Metrics for learned experience confidence calculation."""

    usage_count: int
    success_rate: float
    quality_score: float
    sample_size: int = 10


@dataclass
class ConfidenceFactors:
    """Factors used in confidence calculation."""

    learned_confidence: float
    best_practice_confidence: float | None = None
    context_relevance: float = 1.0
    sample_size_factor: float = 0.0


class LearningConfidenceCalculator:
    """
    Calculates confidence scores for learning system decisions.

    Uses weighted algorithms similar to expert confidence calculation,
    but adapted for learned experience metrics.
    """

    # Weight factors for learned experience confidence
    WEIGHT_SUCCESS_RATE = 0.4  # Success rate (40%)
    WEIGHT_QUALITY_SCORE = 0.3  # Quality score (30%)
    WEIGHT_SAMPLE_SIZE = 0.2  # Sample size (20%)
    WEIGHT_CONTEXT_RELEVANCE = 0.1  # Context relevance (10%)

    # Weight factors for combined confidence
    WEIGHT_LEARNED_HIGH = 0.7  # When learned confidence is high (>= 0.8)
    WEIGHT_BEST_PRACTICE_HIGH = 0.7  # When best practice confidence is high (>= 0.7)
    WEIGHT_EQUAL = 0.5  # When both are moderate

    # Minimum sample size for reliable confidence
    MIN_SAMPLE_SIZE = 5

    @staticmethod
    def calculate_learned_confidence(
        usage_count: int,
        success_rate: float,
        quality_score: float,
        context_relevance: float = 1.0,
        min_sample_size: int = 5,
    ) -> float:
        """
        Calculate confidence from learned experience metrics.

        Formula:
        learned_confidence = (
            success_rate * 0.4 +           # Success rate (40%)
            quality_score * 0.3 +          # Quality score (30%)
            min(usage_count / 100, 1.0) * 0.2 +  # Sample size (20%)
            context_relevance * 0.1        # Context match (10%)
        )

        Args:
            usage_count: Number of times this has been used
            success_rate: Success rate (0.0-1.0)
            quality_score: Quality score (0.0-1.0)
            context_relevance: How relevant to current context (0.0-1.0)
            min_sample_size: Minimum sample size for reliable confidence

        Returns:
            Confidence score (0.0-1.0)
        """
        # Normalize inputs
        success_rate = max(0.0, min(1.0, success_rate))
        quality_score = max(0.0, min(1.0, quality_score))
        context_relevance = max(0.0, min(1.0, context_relevance))

        # Calculate sample size factor
        # More usage = higher confidence, but with diminishing returns
        if usage_count < min_sample_size:
            # Low sample size reduces confidence
            sample_size_factor = (usage_count / min_sample_size) * 0.5
        else:
            # Normalize to 0-1 range with diminishing returns
            sample_size_factor = min(1.0, usage_count / 100.0)

        # Calculate weighted confidence
        confidence = (
            success_rate * LearningConfidenceCalculator.WEIGHT_SUCCESS_RATE
            + quality_score * LearningConfidenceCalculator.WEIGHT_QUALITY_SCORE
            + sample_size_factor * LearningConfidenceCalculator.WEIGHT_SAMPLE_SIZE
            + context_relevance * LearningConfidenceCalculator.WEIGHT_CONTEXT_RELEVANCE
        )

        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        logger.debug(
            f"Calculated learned confidence: {confidence:.3f} "
            f"(usage={usage_count}, success={success_rate:.3f}, "
            f"quality={quality_score:.3f}, context={context_relevance:.3f})"
        )

        return confidence

    @staticmethod
    def calculate_best_practice_confidence(
        expert_consultation: Any,  # ConsultationResult from expert registry
    ) -> float:
        """
        Calculate confidence from best practices consultation.

        Uses the confidence score from expert consultation directly,
        as it already incorporates multiple factors (agreement, RAG quality, etc.).

        Args:
            expert_consultation: ConsultationResult from expert registry

        Returns:
            Confidence score (0.0-1.0)
        """
        if not expert_consultation:
            return 0.0

        # Use the confidence from expert consultation
        confidence = getattr(expert_consultation, "confidence", 0.0)

        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        logger.debug(f"Best practice confidence: {confidence:.3f}")

        return confidence

    @staticmethod
    def combine_confidence(
        learned_confidence: float,
        best_practice_confidence: float | None,
        context_factors: dict[str, float] | None = None,
    ) -> float:
        """
        Combine multiple confidence sources into a single score.

        Strategy:
        - If learned confidence is high (>= 0.8): Weight learned 70%, best practice 30%
        - If best practice confidence is high (>= 0.7): Weight learned 30%, best practice 70%
        - Otherwise: Equal weighting (50/50)

        Args:
            learned_confidence: Confidence from learned experience (0.0-1.0)
            best_practice_confidence: Confidence from best practices (0.0-1.0 or None)
            context_factors: Optional context factors for adjustment

        Returns:
            Combined confidence score (0.0-1.0)
        """
        # Normalize learned confidence
        learned_confidence = max(0.0, min(1.0, learned_confidence))

        # If no best practice confidence, return learned
        if best_practice_confidence is None:
            return learned_confidence

        # Normalize best practice confidence
        best_practice_confidence = max(0.0, min(1.0, best_practice_confidence))

        # Determine weighting strategy
        if learned_confidence >= 0.8:
            # High learned confidence: prioritize learned experience
            combined = (
                learned_confidence * LearningConfidenceCalculator.WEIGHT_LEARNED_HIGH
                + best_practice_confidence
                * (1.0 - LearningConfidenceCalculator.WEIGHT_LEARNED_HIGH)
            )
            logger.debug(
                f"Combined confidence (learned priority): {combined:.3f} "
                f"(learned={learned_confidence:.3f}, best_practice={best_practice_confidence:.3f})"
            )
        elif best_practice_confidence >= 0.7:
            # High best practice confidence: prioritize best practices
            combined = (
                learned_confidence
                * (1.0 - LearningConfidenceCalculator.WEIGHT_BEST_PRACTICE_HIGH)
                + best_practice_confidence
                * LearningConfidenceCalculator.WEIGHT_BEST_PRACTICE_HIGH
            )
            logger.debug(
                f"Combined confidence (best practice priority): {combined:.3f} "
                f"(learned={learned_confidence:.3f}, best_practice={best_practice_confidence:.3f})"
            )
        else:
            # Moderate confidence: equal weighting
            combined = (
                learned_confidence * LearningConfidenceCalculator.WEIGHT_EQUAL
                + best_practice_confidence * LearningConfidenceCalculator.WEIGHT_EQUAL
            )
            logger.debug(
                f"Combined confidence (equal weight): {combined:.3f} "
                f"(learned={learned_confidence:.3f}, best_practice={best_practice_confidence:.3f})"
            )

        # Apply context factors if provided
        if context_factors:
            context_adjustment = context_factors.get("relevance", 1.0)
            combined = combined * max(0.0, min(1.0, context_adjustment))

        # Ensure confidence is between 0 and 1
        combined = max(0.0, min(1.0, combined))

        return combined

    @staticmethod
    def calculate_from_metrics(metrics: LearnedExperienceMetrics) -> float:
        """
        Calculate confidence from LearnedExperienceMetrics.

        Args:
            metrics: LearnedExperienceMetrics instance

        Returns:
            Confidence score (0.0-1.0)
        """
        return LearningConfidenceCalculator.calculate_learned_confidence(
            usage_count=metrics.usage_count,
            success_rate=metrics.success_rate,
            quality_score=metrics.quality_score,
            context_relevance=1.0,  # Default context relevance
            min_sample_size=metrics.sample_size,
        )
