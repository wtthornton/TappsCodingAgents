"""
Adaptive Voting Engine

Adjusts expert voting weights based on performance data.
"""

import logging
from typing import Any

from .performance_tracker import ExpertPerformance, ExpertPerformanceTracker
from .weight_distributor import ExpertWeightMatrix, WeightDistributor

logger = logging.getLogger(__name__)


class AdaptiveVotingEngine:
    """
    Adjusts expert voting weights based on performance.
    
    Analyzes expert performance data and adjusts weight matrix
    to favor high-performing experts while maintaining 51% primary rule.
    """

    # Performance thresholds
    HIGH_PERFORMANCE_THRESHOLD = 0.75  # First-pass success rate
    LOW_PERFORMANCE_THRESHOLD = 0.50  # First-pass success rate
    HIGH_CONFIDENCE_THRESHOLD = 0.80  # Average confidence

    def __init__(
        self,
        performance_tracker: ExpertPerformanceTracker | None = None,
    ):
        """
        Initialize adaptive voting engine.

        Args:
            performance_tracker: ExpertPerformanceTracker instance
        """
        self.performance_tracker = performance_tracker or ExpertPerformanceTracker()

    async def adjust_voting_weights(
        self,
        performance_data: dict[str, ExpertPerformance] | None = None,
        current_matrix: ExpertWeightMatrix | None = None,
    ) -> ExpertWeightMatrix:
        """
        Adjust voting weights based on performance.

        Args:
            performance_data: Dictionary of expert performance (if None, loads from tracker)
            current_matrix: Current weight matrix (if None, loads from domain config)

        Returns:
            Updated ExpertWeightMatrix
        """
        # Load performance data if not provided
        if performance_data is None:
            performance_data = self.performance_tracker.get_all_performance(days=30)

        if not performance_data:
            logger.warning("No performance data available for weight adjustment")
            return current_matrix or self._get_default_matrix()

        # Load current matrix if not provided
        if current_matrix is None:
            current_matrix = self._load_current_matrix()

        if not current_matrix:
            logger.warning("No current weight matrix available")
            return self._get_default_matrix()

        # Calculate weight adjustments
        adjustments = self._calculate_weight_adjustments(
            performance_data, current_matrix
        )

        # Apply adjustments (maintaining 51% primary rule)
        adjusted_matrix = self._apply_adjustments(current_matrix, adjustments)

        logger.info("Adjusted expert voting weights based on performance")
        return adjusted_matrix

    def _calculate_weight_adjustments(
        self,
        performance_data: dict[str, ExpertPerformance],
        current_matrix: ExpertWeightMatrix,
    ) -> dict[str, dict[str, float]]:
        """
        Calculate weight adjustments for each expert-domain pair.

        Returns:
            Dictionary mapping expert_id -> domain -> adjustment (-1.0 to 1.0)
        """
        adjustments: dict[str, dict[str, float]] = {}

        for expert_id in current_matrix.experts:
            adjustments[expert_id] = {}
            performance = performance_data.get(expert_id)

            if not performance:
                # No performance data - no adjustment
                for domain in current_matrix.domains:
                    adjustments[expert_id][domain] = 0.0
                continue

            # Calculate adjustment factor based on performance
            adjustment_factor = self._calculate_adjustment_factor(performance)

            for domain in current_matrix.domains:
                # Primary domain gets stronger adjustment
                is_primary = (
                    current_matrix.get_primary_expert(domain) == expert_id
                )

                if is_primary:
                    # Primary: adjust by factor (but maintain >= 51%)
                    adjustments[expert_id][domain] = adjustment_factor * 0.1
                else:
                    # Secondary: adjust by factor
                    adjustments[expert_id][domain] = adjustment_factor * 0.05

        return adjustments

    def _calculate_adjustment_factor(
        self, performance: ExpertPerformance
    ) -> float:
        """
        Calculate adjustment factor based on performance metrics.

        Returns:
            Adjustment factor (-1.0 to 1.0)
            Positive = increase weight, Negative = decrease weight
        """
        # Base factor from first-pass success rate
        success_factor = (performance.first_pass_success_rate - 0.5) * 2.0  # -1 to 1

        # Confidence factor
        confidence_factor = (performance.avg_confidence - 0.7) * 2.0  # -1 to 1

        # Quality improvement factor
        improvement_factor = min(1.0, max(-1.0, performance.code_quality_improvement / 10.0))

        # Weighted combination
        factor = (
            success_factor * 0.5
            + confidence_factor * 0.3
            + improvement_factor * 0.2
        )

        return max(-1.0, min(1.0, factor))

    def _apply_adjustments(
        self,
        current_matrix: ExpertWeightMatrix,
        adjustments: dict[str, dict[str, float]],
    ) -> ExpertWeightMatrix:
        """
        Apply adjustments to weight matrix.

        Maintains 51% primary rule by redistributing secondary weights.
        """
        # Create new weights dictionary
        new_weights: dict[str, dict[str, float]] = {}

        for expert_id in current_matrix.experts:
            new_weights[expert_id] = {}
            for domain in current_matrix.domains:
                current_weight = current_matrix.get_expert_weight(expert_id, domain)
                adjustment = adjustments.get(expert_id, {}).get(domain, 0.0)

                # Apply adjustment
                new_weight = current_weight + adjustment

                # Clamp to valid range
                new_weight = max(0.0, min(1.0, new_weight))

                new_weights[expert_id][domain] = new_weight

        # Normalize to maintain 51% primary and sum to 1.0 per domain
        normalized_weights = self._normalize_matrix(new_weights, current_matrix)

        return ExpertWeightMatrix(
            weights=normalized_weights,
            domains=current_matrix.domains,
            experts=current_matrix.experts,
        )

    def _normalize_matrix(
        self,
        weights: dict[str, dict[str, float]],
        original_matrix: ExpertWeightMatrix,
    ) -> dict[str, dict[str, float]]:
        """
        Normalize weights to maintain 51% primary rule and sum to 1.0 per domain.
        """
        normalized: dict[str, dict[str, float]] = {}

        for domain in original_matrix.domains:
            # Get primary expert
            primary_expert = original_matrix.get_primary_expert(domain)
            if not primary_expert:
                continue

            # Get current weights for this domain
            domain_weights = {
                expert_id: weights.get(expert_id, {}).get(domain, 0.0)
                for expert_id in original_matrix.experts
            }

            # Ensure primary has at least 51%
            primary_weight = domain_weights[primary_expert]
            if primary_weight < 0.51:
                domain_weights[primary_expert] = 0.51

            # Calculate remaining weight for others
            remaining = 1.0 - domain_weights[primary_expert]
            other_experts = [
                eid for eid in original_matrix.experts if eid != primary_expert
            ]

            if other_experts:
                # Redistribute remaining weight proportionally
                total_other = sum(domain_weights.get(eid, 0.0) for eid in other_experts)
                if total_other > 0:
                    for expert_id in other_experts:
                        proportion = domain_weights.get(expert_id, 0.0) / total_other
                        domain_weights[expert_id] = remaining * proportion
                else:
                    # Equal distribution if no existing weights
                    per_expert = remaining / len(other_experts)
                    for expert_id in other_experts:
                        domain_weights[expert_id] = per_expert

            # Store normalized weights
            for expert_id in original_matrix.experts:
                if expert_id not in normalized:
                    normalized[expert_id] = {}
                normalized[expert_id][domain] = domain_weights[expert_id]

        return normalized

    def _load_current_matrix(self) -> ExpertWeightMatrix | None:
        """Load current weight matrix from domain config."""
        from pathlib import Path

        project_root = Path.cwd()
        domains_file = project_root / ".tapps-agents" / "domains.md"

        if not domains_file.exists():
            return None

        try:
            from .domain_config import DomainConfigParser

            domain_config = DomainConfigParser.parse(domains_file)
            return domain_config.weight_matrix
        except Exception as e:
            logger.warning(f"Error loading weight matrix: {e}")
            return None

    def _get_default_matrix(self) -> ExpertWeightMatrix:
        """Get default weight matrix (single expert, 100% weight)."""
        return ExpertWeightMatrix(
            weights={"expert-default": {"default": 1.0}},
            domains=["default"],
            experts=["expert-default"],
        )
