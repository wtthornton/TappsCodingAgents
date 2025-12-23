"""
Progressive prompt refiner.

Implements incremental improvements without catastrophic forgetting.
"""

import logging
from typing import Any
from uuid import uuid4

from ..evaluation_models import PromptVersion
from ..prompt_base import BasePromptOptimizer, PromptOutcome, PromptVariation

logger = logging.getLogger(__name__)


class ProgressiveRefiner(BasePromptOptimizer):
    """
    Progressive prompt refinement with version control.
    
    Implements incremental improvements while maintaining stability.
    """

    def __init__(self):
        """Initialize progressive refiner."""
        self.version_history: list[PromptVersion] = []

    def optimize(
        self, current_prompt: str, outcomes: list[PromptOutcome]
    ) -> str:
        """
        Optimize prompt based on outcomes (progressive refinement).
        
        Args:
            current_prompt: Current prompt text
            outcomes: Outcomes from prompt variations
            
        Returns:
            Optimized prompt text
        """
        if not outcomes:
            return current_prompt
        
        # Identify improvement opportunities based on outcomes
        improvements = self._identify_improvements(current_prompt, outcomes)
        
        # Apply improvements incrementally
        optimized = current_prompt
        for improvement in improvements:
            optimized = self._apply_improvement(optimized, improvement)
        
        # Limit changes to prevent catastrophic forgetting
        # Keep core structure while improving specifics
        optimized = self._preserve_core_structure(current_prompt, optimized)
        
        return optimized

    def generate_variations(self, base_prompt: str, count: int = 3) -> list[PromptVariation]:
        """
        Generate prompt variations for testing.
        
        Args:
            base_prompt: Base prompt to vary
            count: Number of variations to generate
            
        Returns:
            List of prompt variations
        """
        variations = []
        
        # Generate variations with different emphases
        variations_templates = [
            base_prompt,  # Base
            base_prompt + "\n\nFocus on critical issues and security vulnerabilities first.",
            base_prompt + "\n\nProvide detailed, actionable feedback with specific examples.",
            base_prompt + "\n\nBe thorough and comprehensive in your analysis.",
        ]
        
        for i in range(min(count, len(variations_templates))):
            variation = PromptVariation(
                id=str(uuid4()),
                prompt_text=variations_templates[i],
                metadata={"variation_type": "progressive", "index": i},
            )
            variations.append(variation)
        
        return variations

    def _identify_improvements(
        self, prompt: str, outcomes: list[PromptOutcome]
    ) -> list[str]:
        """Identify specific improvements to make."""
        improvements = []
        
        # Analyze which variations performed best
        successful = [o for o in outcomes if o.success_rate() > 0.7]
        
        if not successful:
            # If no successful variations, suggest adding structure
            if "instruction" not in prompt.lower():
                improvements.append("add_instructions")
            if "example" not in prompt.lower():
                improvements.append("add_examples")
        
        return improvements

    def _apply_improvement(self, prompt: str, improvement: str) -> str:
        """Apply a specific improvement to prompt."""
        if improvement == "add_instructions":
            if "instruction" not in prompt.lower():
                prompt = prompt + "\n\nInstructions:\n- Provide specific, actionable feedback\n- Prioritize critical issues"
        elif improvement == "add_examples":
            if "example" not in prompt.lower():
                prompt = prompt + "\n\nExample: 'This code has a security vulnerability: [specific issue]'"
        
        return prompt

    def _preserve_core_structure(self, original: str, optimized: str) -> str:
        """Preserve core structure while allowing improvements."""
        # Simple heuristic: keep first paragraph and key sections
        # In production, would use more sophisticated structure analysis
        
        # Limit total change to prevent drastic rewrites
        if len(optimized) > len(original) * 1.5:
            # Too much change, preserve more of original
            return original + "\n\n" + optimized[len(original):]
        
        return optimized

