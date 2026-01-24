"""
Adaptive Scoring Engine

Adjusts scoring weights based on outcome analysis to maximize first-pass success.
"""

import logging
from typing import Any

from .outcome_tracker import CodeOutcome, OutcomeTracker

logger = logging.getLogger(__name__)


class AdaptiveScoringEngine:
    """
    Adjusts scoring weights based on outcome analysis.
    
    Analyzes correlation between scores and first-pass success,
    then adjusts weights to emphasize predictive metrics.
    """

    # Learning rate for weight adjustments (0.0-1.0)
    DEFAULT_LEARNING_RATE = 0.1

    # Minimum outcomes needed for adjustment
    MIN_OUTCOMES_FOR_ADJUSTMENT = 10

    def __init__(
        self,
        outcome_tracker: OutcomeTracker | None = None,
        learning_rate: float = DEFAULT_LEARNING_RATE,
    ):
        """
        Initialize adaptive scoring engine.

        Args:
            outcome_tracker: OutcomeTracker instance
            learning_rate: Learning rate for weight adjustments (0.0-1.0)
        """
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.learning_rate = learning_rate

    async def adjust_weights(
        self,
        outcomes: list[CodeOutcome] | None = None,
        current_weights: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """
        Adjust weights to maximize first-pass success.

        Args:
            outcomes: List of CodeOutcome objects (if None, loads from tracker)
            current_weights: Current weight configuration

        Returns:
            Adjusted weights dictionary
        """
        # Load outcomes if not provided
        if outcomes is None:
            outcomes = self.outcome_tracker.load_outcomes(limit=1000)

        if len(outcomes) < self.MIN_OUTCOMES_FOR_ADJUSTMENT:
            logger.info(
                f"Insufficient outcomes ({len(outcomes)}) for weight adjustment. "
                f"Need at least {self.MIN_OUTCOMES_FOR_ADJUSTMENT}."
            )
            return current_weights or self._get_default_weights()

        # Use current weights or defaults
        if current_weights is None:
            current_weights = self._get_default_weights()

        # Analyze correlation between scores and outcomes
        correlations = self._calculate_correlations(outcomes)

        # Calculate optimal weights
        optimal_weights = self._calculate_optimal_weights(
            correlations, current_weights
        )

        # Apply gradual adjustment (learning rate)
        adjusted_weights = self._apply_learning_rate(
            current_weights, optimal_weights
        )

        # Normalize to ensure sum = 1.0
        adjusted_weights = self._normalize_weights(adjusted_weights)

        logger.info(f"Adjusted scoring weights: {adjusted_weights}")
        return adjusted_weights

    def _calculate_correlations(
        self, outcomes: list[CodeOutcome]
    ) -> dict[str, float]:
        """
        Calculate correlation between each metric and first-pass success.

        Returns:
            Dictionary mapping metric names to correlation scores (-1.0 to 1.0)
        """
        correlations: dict[str, float] = {}

        # Metrics to analyze
        metrics = [
            "complexity_score",
            "security_score",
            "maintainability_score",
            "test_coverage_score",
            "performance_score",
            "structure_score",
            "devex_score",
        ]

        for metric in metrics:
            # Collect metric values and success flags
            metric_values: list[float] = []
            success_flags: list[bool] = []

            for outcome in outcomes:
                # Use initial scores (before iterations)
                if metric in outcome.initial_scores:
                    score = outcome.initial_scores[metric]
                    # Normalize to 0-1 range (assuming 0-10 scale)
                    normalized = min(1.0, score / 10.0) if score <= 10.0 else min(1.0, score / 100.0)
                    metric_values.append(normalized)
                    success_flags.append(outcome.first_pass_success)

            if len(metric_values) >= 5:  # Need at least 5 data points
                correlation = self._pearson_correlation(metric_values, success_flags)
                correlations[metric] = correlation
            else:
                correlations[metric] = 0.0

        return correlations

    def _pearson_correlation(
        self, x: list[float], y: list[bool]
    ) -> float:
        """
        Calculate Pearson correlation coefficient.

        Args:
            x: Metric values (0-1)
            y: Success flags (boolean)

        Returns:
            Correlation coefficient (-1.0 to 1.0)
        """
        if len(x) != len(y):
            return 0.0

        # Convert boolean to float
        y_float = [1.0 if v else 0.0 for v in y]

        n = len(x)
        if n < 2:
            return 0.0

        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y_float) / n

        # Calculate correlation
        numerator = sum((x[i] - mean_x) * (y_float[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y_float[i] - mean_y) ** 2 for i in range(n))

        if denominator_x == 0 or denominator_y == 0:
            return 0.0

        correlation = numerator / ((denominator_x * denominator_y) ** 0.5)
        return max(-1.0, min(1.0, correlation))  # Clamp to [-1, 1]

    def _calculate_optimal_weights(
        self,
        correlations: dict[str, float],
        current_weights: dict[str, float],
    ) -> dict[str, float]:
        """
        Calculate optimal weights based on correlations.

        Higher correlation = higher weight (more predictive).
        """
        # Map metric names to weight keys
        metric_to_weight = {
            "complexity_score": "complexity",
            "security_score": "security",
            "maintainability_score": "maintainability",
            "test_coverage_score": "test_coverage",
            "performance_score": "performance",
            "structure_score": "structure",
            "devex_score": "devex",
        }

        optimal_weights: dict[str, float] = {}

        # Convert correlations to positive weights
        # Negative correlations become small weights
        # Positive correlations become larger weights
        positive_correlations = {
            metric: max(0.0, corr) for metric, corr in correlations.items()
        }

        # Normalize positive correlations to sum to 1.0
        total_positive = sum(positive_correlations.values())
        if total_positive > 0:
            for metric, corr in positive_correlations.items():
                weight_key = metric_to_weight.get(metric)
                if weight_key:
                    optimal_weights[weight_key] = corr / total_positive
        else:
            # Fallback to equal weights if no positive correlations
            for weight_key in metric_to_weight.values():
                optimal_weights[weight_key] = 1.0 / len(metric_to_weight)

        return optimal_weights

    def _apply_learning_rate(
        self,
        current_weights: dict[str, float],
        optimal_weights: dict[str, float],
    ) -> dict[str, float]:
        """
        Apply learning rate to gradually adjust weights.

        Formula: new = current * (1 - lr) + optimal * lr
        """
        adjusted = {}
        for key in current_weights:
            current = current_weights.get(key, 0.0)
            optimal = optimal_weights.get(key, current)
            adjusted[key] = current * (1 - self.learning_rate) + optimal * self.learning_rate
        return adjusted

    def _normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        """Normalize weights to sum to 1.0."""
        total = sum(weights.values())
        if total == 0:
            return self._get_default_weights()
        return {k: v / total for k, v in weights.items()}

    def _get_default_weights(self) -> dict[str, float]:
        """Get default scoring weights."""
        return {
            "complexity": 0.18,
            "security": 0.27,
            "maintainability": 0.24,
            "test_coverage": 0.13,
            "performance": 0.08,
            "structure": 0.05,
            "devex": 0.05,
        }

    def get_weight_adjustment_recommendation(
        self, outcomes: list[CodeOutcome] | None = None
    ) -> dict[str, Any]:
        """
        Get recommendation for weight adjustments without applying.

        Args:
            outcomes: List of outcomes (if None, loads from tracker)

        Returns:
            Dictionary with recommendations and analysis
        """
        if outcomes is None:
            outcomes = self.outcome_tracker.load_outcomes(limit=1000)

        if len(outcomes) < self.MIN_OUTCOMES_FOR_ADJUSTMENT:
            return {
                "recommended": False,
                "reason": f"Insufficient outcomes ({len(outcomes)})",
                "required": self.MIN_OUTCOMES_FOR_ADJUSTMENT,
            }

        correlations = self._calculate_correlations(outcomes)
        current_weights = self._get_default_weights()
        optimal_weights = self._calculate_optimal_weights(correlations, current_weights)

        # Calculate recommended adjustments
        adjustments = {
            metric: optimal_weights.get(metric, current_weights.get(metric, 0.0))
            - current_weights.get(metric, 0.0)
            for metric in current_weights
        }

        return {
            "recommended": True,
            "correlations": correlations,
            "current_weights": current_weights,
            "optimal_weights": optimal_weights,
            "adjustments": adjustments,
            "outcomes_analyzed": len(outcomes),
        }
