"""
Predictive Quality Gates

Predicts first-pass success probability before code generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FirstPassPrediction:
    """Prediction of first-pass success probability."""

    probability: float  # 0.0-1.0
    factors: dict[str, float]  # Contributing factors
    recommendations: list[str]  # Suggestions to improve probability
    estimated_iterations: float  # Estimated iterations needed


class PredictiveQualityGates:
    """
    Predicts first-pass success before code generation.
    
    Analyzes prompt quality, expert consultation needs, and
    estimates code quality to suggest improvements.
    """

    def __init__(self):
        """Initialize predictive quality gates."""
        pass

    async def predict_first_pass_success(
        self,
        prompt: str,
        prompt_quality_score: dict[str, float] | None = None,
        expert_suggestions: list[str] | None = None,
        historical_similarity: float | None = None,
    ) -> FirstPassPrediction:
        """
        Predict first-pass success probability.

        Args:
            prompt: User prompt
            prompt_quality_score: Prompt quality metrics (if available)
            expert_suggestions: Suggested expert consultations
            historical_similarity: Similarity to successful historical prompts

        Returns:
            FirstPassPrediction with probability and recommendations
        """
        factors: dict[str, float] = {}

        # Factor 1: Prompt quality (if available)
        if prompt_quality_score:
            completeness = prompt_quality_score.get("completeness", 0.5)
            specificity = prompt_quality_score.get("specificity", 0.5)
            domain_coverage = prompt_quality_score.get("domain_coverage", 0.5)
            factors["prompt_quality"] = (
                completeness * 0.4 + specificity * 0.4 + domain_coverage * 0.2
            )
        else:
            # Estimate from prompt length and keywords
            factors["prompt_quality"] = self._estimate_prompt_quality(prompt)

        # Factor 2: Expert consultation availability
        if expert_suggestions:
            factors["expert_availability"] = min(1.0, len(expert_suggestions) * 0.3)
        else:
            factors["expert_availability"] = 0.5  # Neutral

        # Factor 3: Historical similarity
        if historical_similarity is not None:
            factors["historical_similarity"] = historical_similarity
        else:
            factors["historical_similarity"] = 0.5  # Neutral

        # Calculate overall probability
        probability = (
            factors["prompt_quality"] * 0.5
            + factors["expert_availability"] * 0.3
            + factors["historical_similarity"] * 0.2
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(factors, prompt)

        # Estimate iterations (inverse of probability)
        estimated_iterations = max(1.0, 1.0 / max(probability, 0.1))

        return FirstPassPrediction(
            probability=probability,
            factors=factors,
            recommendations=recommendations,
            estimated_iterations=estimated_iterations,
        )

    def _estimate_prompt_quality(self, prompt: str) -> float:
        """Estimate prompt quality from text analysis."""
        # Simple heuristics
        length_score = min(1.0, len(prompt.split()) / 50.0)  # 50+ words = good

        # Check for key elements
        has_requirements = any(
            word in prompt.lower()
            for word in ["should", "must", "need", "require", "implement"]
        )
        has_examples = any(
            word in prompt.lower() for word in ["example", "like", "similar", "pattern"]
        )
        has_constraints = any(
            word in prompt.lower()
            for word in ["constraint", "limit", "must not", "avoid"]
        )

        element_score = (
            (1.0 if has_requirements else 0.5)
            + (1.0 if has_examples else 0.5)
            + (1.0 if has_constraints else 0.5)
        ) / 3.0

        return (length_score * 0.4 + element_score * 0.6)

    def _generate_recommendations(
        self, factors: dict[str, float], prompt: str
    ) -> list[str]:
        """Generate recommendations to improve first-pass probability."""
        recommendations = []

        if factors.get("prompt_quality", 0.5) < 0.6:
            recommendations.append(
                "Enhance prompt with more specific requirements and examples"
            )

        if factors.get("expert_availability", 0.5) < 0.5:
            recommendations.append(
                "Consider consulting domain experts before code generation"
            )

        if len(prompt.split()) < 20:
            recommendations.append("Add more detail to the prompt")

        if not any(word in prompt.lower() for word in ["test", "tested", "testing"]):
            recommendations.append("Include testing requirements in prompt")

        return recommendations
