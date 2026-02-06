"""
Correlation analyzer for prompt optimization.

Correlates prompt variations with review quality and measures impact.
"""

import logging
from typing import Any

from ..prompt_base import PromptOutcome, PromptVariation

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyzes correlations between prompt variations and outcomes.
    
    Identifies prompt patterns that improve issue detection and quality.
    """

    def __init__(self):
        """Initialize correlation analyzer."""
        pass

    def analyze_correlation(
        self,
        variations: dict[str, PromptVariation],
        outcomes: dict[str, PromptOutcome],
    ) -> dict[str, Any]:
        """
        Analyze correlation between prompt variations and outcomes.
        
        Args:
            variations: Dictionary of variation_id -> PromptVariation
            outcomes: Dictionary of variation_id -> PromptOutcome
            
        Returns:
            Correlation analysis results
        """
        correlations: dict[str, Any] = {
            "variations_analyzed": len(variations),
            "correlations": {},
        }
        
        # Analyze each variation
        for vid, variation in variations.items():
            outcome = outcomes.get(vid)
            if not outcome:
                continue
            
            # Extract prompt features
            features = self._extract_features(variation.prompt_text)
            
            # Correlate with outcome
            correlation = {
                "variation_id": vid,
                "features": features,
                "success_rate": outcome.success_rate(),
                "average_score": outcome.average_score,
                "sample_size": outcome.usage_count,
            }
            
            correlations["correlations"][vid] = correlation
        
        # Identify patterns
        patterns = self._identify_patterns(variations, outcomes)
        correlations["patterns"] = patterns
        
        return correlations

    def _extract_features(self, prompt_text: str) -> dict[str, Any]:
        """Extract features from prompt text."""
        features = {
            "length": len(prompt_text),
            "word_count": len(prompt_text.split()),
            "has_instructions": "instruction" in prompt_text.lower() or "you should" in prompt_text.lower(),
            "has_examples": "example" in prompt_text.lower() or "for instance" in prompt_text.lower(),
            "has_checklist": "checklist" in prompt_text.lower() or "verify" in prompt_text.lower(),
            "tone": "aggressive" if any(word in prompt_text.lower() for word in ["must", "critical", "important"]) else "neutral",
        }
        return features

    def _identify_patterns(
        self,
        variations: dict[str, PromptVariation],
        outcomes: dict[str, PromptOutcome],
    ) -> list[dict[str, Any]]:
        """Identify patterns that correlate with success."""
        patterns = []
        
        # Group by success rate
        successful = [
            (vid, outcomes[vid])
            for vid in variations
            if vid in outcomes and outcomes[vid].success_rate() > 0.7
        ]
        
        [
            (vid, outcomes[vid])
            for vid in variations
            if vid in outcomes and outcomes[vid].success_rate() < 0.4
        ]
        
        # Analyze common features in successful prompts
        if successful:
            successful_features = [
                self._extract_features(variations[vid].prompt_text)
                for vid, _ in successful
            ]
            
            # Find common features
            common_has_instructions = sum(
                f["has_instructions"] for f in successful_features
            ) > len(successful_features) * 0.7
            
            if common_has_instructions:
                patterns.append({
                    "type": "success_pattern",
                    "feature": "has_instructions",
                    "description": "Successful prompts often include clear instructions",
                    "confidence": len(successful) / len(variations) if variations else 0.0,
                })
        
        return patterns

    def measure_impact(
        self, baseline_outcome: PromptOutcome, improved_outcome: PromptOutcome
    ) -> dict[str, Any]:
        """
        Measure impact of prompt improvements.
        
        Args:
            baseline_outcome: Baseline prompt outcome
            improved_outcome: Improved prompt outcome
            
        Returns:
            Impact metrics
        """
        improvement_rate = (
            improved_outcome.success_rate() - baseline_outcome.success_rate()
        )
        
        improvement_score = (
            (improved_outcome.average_score or 0.0) - (baseline_outcome.average_score or 0.0)
        )
        
        return {
            "improvement_rate": improvement_rate,
            "improvement_score": improvement_score,
            "baseline_success_rate": baseline_outcome.success_rate(),
            "improved_success_rate": improved_outcome.success_rate(),
            "relative_improvement": (
                improvement_rate / baseline_outcome.success_rate()
                if baseline_outcome.success_rate() > 0
                else 0.0
            ),
        }

