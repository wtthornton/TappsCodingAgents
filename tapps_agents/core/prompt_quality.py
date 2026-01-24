"""
Prompt Quality Analyzer

Analyzes prompt quality and suggests improvements before code generation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PromptQualityScore:
    """Prompt quality analysis result."""

    completeness: float  # 0-1
    specificity: float  # 0-1
    domain_coverage: float  # 0-1
    expert_suggestions: list[str] = None  # type: ignore
    improvement_recommendations: list[str] = None  # type: ignore
    first_pass_probability: float = 0.0  # 0-1

    def __post_init__(self):
        """Initialize default values."""
        if self.expert_suggestions is None:
            self.expert_suggestions = []
        if self.improvement_recommendations is None:
            self.improvement_recommendations = []


class PromptQualityAnalyzer:
    """
    Analyzes prompt quality and suggests improvements.
    
    Scores prompt completeness, specificity, and domain coverage,
    then provides actionable recommendations.
    """

    # Keywords that indicate requirements
    REQUIREMENT_KEYWORDS = [
        "should",
        "must",
        "need",
        "require",
        "implement",
        "create",
        "build",
        "add",
    ]

    # Keywords that indicate constraints
    CONSTRAINT_KEYWORDS = [
        "constraint",
        "limit",
        "must not",
        "avoid",
        "don't",
        "never",
        "only",
    ]

    # Keywords that indicate examples
    EXAMPLE_KEYWORDS = ["example", "like", "similar", "pattern", "follow"]

    def analyze(self, prompt: str, context: dict[str, Any] | None = None) -> PromptQualityScore:
        """
        Analyze prompt quality.

        Args:
            prompt: User prompt text
            context: Optional context (domains, existing code, etc.)

        Returns:
            PromptQualityScore with analysis and recommendations
        """
        prompt_lower = prompt.lower()

        # Calculate completeness
        completeness = self._calculate_completeness(prompt, prompt_lower)

        # Calculate specificity
        specificity = self._calculate_specificity(prompt, prompt_lower)

        # Calculate domain coverage
        domain_coverage = self._calculate_domain_coverage(prompt, prompt_lower, context)

        # Suggest experts
        expert_suggestions = self._suggest_experts(prompt_lower, context)

        # Generate improvement recommendations
        recommendations = self._generate_recommendations(
            completeness, specificity, domain_coverage, prompt
        )

        # Estimate first-pass probability
        first_pass_probability = (
            completeness * 0.4 + specificity * 0.4 + domain_coverage * 0.2
        )

        return PromptQualityScore(
            completeness=completeness,
            specificity=specificity,
            domain_coverage=domain_coverage,
            expert_suggestions=expert_suggestions,
            improvement_recommendations=recommendations,
            first_pass_probability=first_pass_probability,
        )

    def _calculate_completeness(self, prompt: str, prompt_lower: str) -> float:
        """Calculate prompt completeness score."""
        score = 0.0

        # Check for requirements
        has_requirements = any(
            keyword in prompt_lower for keyword in self.REQUIREMENT_KEYWORDS
        )
        if has_requirements:
            score += 0.3

        # Check for constraints
        has_constraints = any(
            keyword in prompt_lower for keyword in self.CONSTRAINT_KEYWORDS
        )
        if has_constraints:
            score += 0.2

        # Check for examples
        has_examples = any(keyword in prompt_lower for keyword in self.EXAMPLE_KEYWORDS)
        if has_examples:
            score += 0.2

        # Check for testing mentions
        has_testing = any(
            word in prompt_lower for word in ["test", "testing", "tests", "coverage"]
        )
        if has_testing:
            score += 0.15

        # Check for error handling
        has_error_handling = any(
            word in prompt_lower
            for word in ["error", "exception", "handle", "catch", "fail"]
        )
        if has_error_handling:
            score += 0.15

        return min(1.0, score)

    def _calculate_specificity(self, prompt: str, prompt_lower: str) -> float:
        """Calculate prompt specificity score."""
        # Length-based specificity (longer = more specific, up to a point)
        word_count = len(prompt.split())
        length_score = min(1.0, word_count / 100.0)  # 100+ words = good

        # Check for specific technical terms
        technical_terms = [
            "api",
            "endpoint",
            "database",
            "schema",
            "authentication",
            "authorization",
            "oauth",
            "jwt",
            "rest",
            "graphql",
            "websocket",
            "async",
            "await",
        ]
        term_count = sum(1 for term in technical_terms if term in prompt_lower)
        term_score = min(1.0, term_count / 5.0)  # 5+ terms = good

        # Check for code patterns or structure mentions
        has_structure = any(
            word in prompt_lower
            for word in ["class", "function", "method", "module", "package"]
        )
        structure_score = 1.0 if has_structure else 0.5

        return (length_score * 0.4 + term_score * 0.4 + structure_score * 0.2)

    def _calculate_domain_coverage(
        self, prompt: str, prompt_lower: str, context: dict[str, Any] | None
    ) -> float:
        """Calculate domain coverage score."""
        # Check for domain-specific keywords
        domain_keywords = {
            "api": ["api", "endpoint", "rest", "graphql"],
            "database": ["database", "sql", "query", "schema"],
            "security": ["security", "auth", "oauth", "jwt", "encrypt"],
            "testing": ["test", "testing", "coverage", "unit", "integration"],
            "performance": ["performance", "optimize", "cache", "async"],
        }

        domains_mentioned = sum(
            1
            for domain, keywords in domain_keywords.items()
            if any(kw in prompt_lower for kw in keywords)
        )

        # Normalize to 0-1 (5 domains max)
        coverage = min(1.0, domains_mentioned / 3.0)  # 3+ domains = good

        return coverage

    def _suggest_experts(
        self, prompt_lower: str, context: dict[str, Any] | None
    ) -> list[str]:
        """Suggest experts based on prompt content."""
        suggestions = []

        # Domain-based suggestions
        if any(word in prompt_lower for word in ["oauth", "auth", "jwt", "token"]):
            suggestions.append("expert-security")

        if any(word in prompt_lower for word in ["api", "endpoint", "rest"]):
            suggestions.append("expert-api-design-integration")

        if any(word in prompt_lower for word in ["database", "sql", "query"]):
            suggestions.append("expert-database-data-management")

        if any(word in prompt_lower for word in ["test", "testing", "coverage"]):
            suggestions.append("expert-testing")

        # Remove duplicates
        return list(set(suggestions))

    def _generate_recommendations(
        self,
        completeness: float,
        specificity: float,
        domain_coverage: float,
        prompt: str,
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if completeness < 0.6:
            recommendations.append(
                "Add more specific requirements, constraints, and examples"
            )

        if specificity < 0.6:
            recommendations.append(
                "Include technical details, code patterns, or structure specifications"
            )

        if domain_coverage < 0.5:
            recommendations.append("Mention relevant domains (API, database, security, etc.)")

        if len(prompt.split()) < 30:
            recommendations.append("Expand prompt with more detail (aim for 50+ words)")

        if not any(word in prompt.lower() for word in ["test", "testing"]):
            recommendations.append("Include testing requirements or expectations")

        return recommendations
