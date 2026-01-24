"""
Iteration Reduction System

Reduces iterations needed to achieve code quality by learning from patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .outcome_tracker import CodeOutcome, OutcomeTracker

logger = logging.getLogger(__name__)


@dataclass
class IterationPattern:
    """Pattern identified from iteration history."""

    pattern_type: str  # "common_fix", "proactive_suggestion", "pre_validation"
    description: str
    frequency: int  # How often this pattern appears
    success_rate: float  # Success rate when applied
    suggestion: str  # Suggested action


class IterationReducer:
    """
    Reduces iterations needed to achieve quality.
    
    Learns from iteration patterns and provides proactive suggestions
    to minimize code revision cycles.
    """

    def __init__(self, outcome_tracker: OutcomeTracker | None = None):
        """
        Initialize iteration reducer.

        Args:
            outcome_tracker: OutcomeTracker instance
        """
        self.outcome_tracker = outcome_tracker or OutcomeTracker()

    def analyze_iteration_patterns(
        self, outcomes: list[CodeOutcome] | None = None
    ) -> list[IterationPattern]:
        """
        Analyze iteration patterns from outcomes.

        Args:
            outcomes: List of outcomes (if None, loads from tracker)

        Returns:
            List of identified patterns
        """
        if outcomes is None:
            outcomes = self.outcome_tracker.load_outcomes(limit=1000)

        patterns = []

        # Pattern 1: High iteration count outcomes
        high_iteration = [o for o in outcomes if o.iterations > 2]
        if len(high_iteration) > len(outcomes) * 0.2:  # 20%+ have high iterations
            patterns.append(
                IterationPattern(
                    pattern_type="common_fix",
                    description="Many outcomes require 3+ iterations",
                    frequency=len(high_iteration),
                    success_rate=0.5,  # Assume moderate success
                    suggestion="Provide more comprehensive initial feedback",
                )
            )

        # Pattern 2: Low initial scores
        low_initial = [
            o
            for o in outcomes
            if self._calculate_overall_score(o.initial_scores) < 60
        ]
        if len(low_initial) > len(outcomes) * 0.3:  # 30%+ have low initial scores
            patterns.append(
                IterationPattern(
                    pattern_type="pre_validation",
                    description="Many outcomes start with low scores",
                    frequency=len(low_initial),
                    success_rate=0.6,
                    suggestion="Pre-validate code patterns before generation",
                )
            )

        # Pattern 3: Missing expert consultations
        no_experts = [o for o in outcomes if not o.expert_consultations]
        if len(no_experts) > len(outcomes) * 0.4:  # 40%+ have no expert consultations
            patterns.append(
                IterationPattern(
                    pattern_type="proactive_suggestion",
                    description="Many outcomes lack expert consultations",
                    frequency=len(no_experts),
                    success_rate=0.7,
                    suggestion="Suggest expert consultations proactively",
                )
            )

        return patterns

    def get_proactive_suggestions(
        self, prompt: str, code_context: str | None = None
    ) -> list[str]:
        """
        Get proactive suggestions to reduce iterations.

        Args:
            prompt: User prompt
            code_context: Optional code context

        Returns:
            List of proactive suggestions
        """
        suggestions = []

        # Analyze patterns
        patterns = self.analyze_iteration_patterns()

        # Apply patterns to generate suggestions
        for pattern in patterns:
            if pattern.pattern_type == "proactive_suggestion":
                suggestions.append(pattern.suggestion)

        # Code-specific suggestions
        if code_context:
            # Check for common issues
            if "import" in code_context and "typing" not in code_context:
                suggestions.append("Add type hints to improve code quality")

            if "def " in code_context and "async" not in code_context:
                # Check if async would be beneficial
                if any(word in code_context for word in ["request", "fetch", "get", "post"]):
                    suggestions.append("Consider async/await for I/O operations")

        return suggestions

    def pre_validate_patterns(
        self, code: str, patterns: list[str] | None = None
    ) -> list[str]:
        """
        Pre-validate code against known problematic patterns.

        Args:
            code: Code to validate
            patterns: Optional list of patterns to check

        Returns:
            List of issues found
        """
        issues = []

        # Common patterns that lead to iterations
        if patterns is None:
            patterns = [
                "missing type hints",
                "no error handling",
                "hardcoded values",
                "missing docstrings",
            ]

        code_lower = code.lower()

        if "missing type hints" in patterns:
            if "def " in code and ":" in code:
                # Check for type hints
                if not any(
                    word in code
                    for word in ["->", "Optional", "List", "Dict", "str", "int"]
                ):
                    issues.append("Missing type hints in function definitions")

        if "no error handling" in patterns:
            if any(word in code for word in ["open(", "request", "fetch"]):
                if "try:" not in code and "except" not in code:
                    issues.append("Missing error handling for I/O operations")

        if "hardcoded values" in patterns:
            if any(word in code for word in ['"http://', "'http://", "localhost"]):
                issues.append("Hardcoded URLs or values detected")

        return issues

    def _calculate_overall_score(self, scores: dict[str, float]) -> float:
        """Calculate overall quality score."""
        weights = {
            "complexity_score": 0.18,
            "security_score": 0.27,
            "maintainability_score": 0.24,
            "test_coverage_score": 0.13,
            "performance_score": 0.08,
            "structure_score": 0.05,
            "devex_score": 0.05,
        }

        total = 0.0
        for metric, weight in weights.items():
            if metric in scores:
                score = scores[metric]
                if score <= 10.0:
                    score = score * 10.0
                total += score * weight

        return total
