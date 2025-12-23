"""
A/B testing framework for prompt variations.
"""

import logging
import random
from typing import Any

from ..prompt_base import PromptABTester, PromptOutcome, PromptVariation

logger = logging.getLogger(__name__)


class PromptABTesterImpl(PromptABTester):
    """
    A/B testing implementation for prompt variations.
    
    Tests multiple prompt variations and tracks outcomes.
    """

    def __init__(self, min_samples: int = 10):
        """
        Initialize A/B tester.
        
        Args:
            min_samples: Minimum samples for statistical significance
        """
        super().__init__()
        self.min_samples = min_samples
        self.statistical_tests = {}

    def select_variation(
        self, variations: list[PromptVariation], mode: str = "balanced"
    ) -> PromptVariation:
        """
        Select a variation for testing.
        
        Args:
            variations: List of variations
            mode: Selection mode (balanced, random, best_known)
            
        Returns:
            Selected variation
        """
        if not variations:
            raise ValueError("No variations provided")
        
        if mode == "random":
            return random.choice(variations)
        
        elif mode == "balanced":
            # Select variation with least samples for balanced testing
            sample_counts = [
                self.outcomes.get(v.id, PromptOutcome(v.id, 0, 0, 0)).usage_count
                for v in variations
            ]
            min_samples_idx = min(range(len(sample_counts)), key=lambda i: sample_counts[i])
            return variations[min_samples_idx]
        
        elif mode == "best_known":
            # Select best performing variation
            best = self.get_best_variation()
            if best and best.id in [v.id for v in variations]:
                return best
            return variations[0]  # Fallback to first
        
        return variations[0]

    def is_statistically_significant(self, variation_id: str) -> bool:
        """
        Check if results are statistically significant.
        
        Args:
            variation_id: Variation ID to check
            
        Returns:
            True if results are significant
        """
        outcome = self.outcomes.get(variation_id)
        if not outcome or outcome.usage_count < self.min_samples:
            return False
        
        # Simple significance test: success rate with confidence
        # More sophisticated tests could use chi-square or t-test
        success_rate = outcome.success_rate()
        
        # Require at least 10 samples and clear winner (>60% success rate)
        return outcome.usage_count >= self.min_samples and success_rate > 0.6

    def get_winner(self) -> PromptVariation | None:
        """Get the winning variation based on statistical significance."""
        if not self.outcomes:
            return None
        
        # Find variations with significant results
        significant = [
            vid for vid in self.outcomes.keys()
            if self.is_statistically_significant(vid)
        ]
        
        if not significant:
            return None
        
        # Return best among significant
        best_id = max(
            significant,
            key=lambda vid: (
                self.outcomes[vid].success_rate(),
                self.outcomes[vid].average_score or 0.0,
            ),
        )
        
        return self.variations.get(best_id)

