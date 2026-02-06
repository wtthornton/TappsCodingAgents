"""
Score Validator - Score validation, calibration, and explanation

Phase 3.3: Score Validation and Explanation

Provides:
- Score range validation (0-10)
- Score explanations (why score is what it is)
- Improvement suggestions
- Calibration utilities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.language_detector import Language


@dataclass
class ValidationResult:
    """Result of score validation."""

    valid: bool
    score: float
    category: str
    error: str | None = None
    explanation: str | None = None
    suggestions: list[str] = field(default_factory=list)
    calibrated_score: float | None = None


@dataclass
class ScoreExplanation:
    """Explanation of why a score is what it is."""

    score: float
    category: str
    breakdown: dict[str, float] = field(default_factory=dict)
    factors: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)


class ScoreValidator:
    """
    Validates scores and provides explanations and improvement suggestions.

    Phase 3.3: Score Validation
    """

    # Valid score ranges by category
    SCORE_RANGES = {
        "complexity": (0.0, 10.0),
        "security": (0.0, 10.0),
        "maintainability": (0.0, 10.0),
        "test_coverage": (0.0, 10.0),
        "performance": (0.0, 10.0),
        "overall": (0.0, 100.0),
    }

    # Score thresholds for categorization
    EXCELLENT_THRESHOLD = 8.5
    GOOD_THRESHOLD = 7.0
    ACCEPTABLE_THRESHOLD = 5.0
    POOR_THRESHOLD = 3.0

    def validate_score(
        self,
        score: float,
        category: str,
        language: Language | None = None,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate a score and provide explanation.

        Args:
            score: The score to validate
            category: Score category (complexity, security, maintainability, etc.)
            language: Optional language for language-specific validation
            context: Optional context (metrics, other scores, etc.)

        Returns:
            ValidationResult with validation status, explanation, and suggestions
        """
        # Type checking: ensure score is numeric
        # Handle case where a dict might be passed instead of a float
        if isinstance(score, dict):
            # Try to extract a numeric score from the dict
            # Common keys that might contain the actual score
            numeric_score = None
            for key in ["score", "value", category, f"{category}_score"]:
                if key in score and isinstance(score[key], (int, float)):
                    numeric_score = float(score[key])
                    break
            
            if numeric_score is None:
                # No numeric value found in dict, return error
                return ValidationResult(
                    valid=False,
                    score=0.0,
                    category=category,
                    error=f"Invalid score type: expected float/int, got dict. Dict contents: {score}",
                    explanation=f"Score validation failed: received dict instead of numeric value for {category}",
                    suggestions=[
                        "Ensure score calculation returns numeric values (float/int), not dictionaries",
                        "Check score calculation logic to return raw numeric scores",
                    ],
                )
            score = numeric_score
        elif not isinstance(score, (int, float)):
            # Handle other non-numeric types
            return ValidationResult(
                valid=False,
                score=0.0,
                category=category,
                error=f"Invalid score type: expected float/int, got {type(score).__name__}",
                explanation=f"Score validation failed: received {type(score).__name__} instead of numeric value for {category}",
                suggestions=[
                    "Ensure score calculation returns numeric values (float/int)",
                    f"Check that score is not a {type(score).__name__}",
                ],
            )
        else:
            # Ensure score is a float for consistent handling
            score = float(score)

        # Get valid range for category
        min_score, max_score = self.SCORE_RANGES.get(
            category, (0.0, 10.0 if category != "overall" else 100.0)
        )

        # Validate range
        if score < min_score or score > max_score:
            return ValidationResult(
                valid=False,
                score=score,
                category=category,
                error=f"Score {score} is outside valid range [{min_score}, {max_score}]",
                explanation=f"Invalid score: {score} (expected range: {min_score}-{max_score})",
                suggestions=[
                    f"Ensure score calculation returns values in range [{min_score}, {max_score}]",
                    "Check for calculation errors or uninitialized values",
                ],
            )

        # Clamp score to valid range (defensive)
        clamped_score = max(min_score, min(max_score, score))

        # Generate explanation and suggestions
        explanation_obj = self.explain_score(
            clamped_score, category, language=language, context=context
        )

        # Build explanation string from explanation object
        explanation_parts = []
        if explanation_obj.strengths:
            explanation_parts.append(f"Strengths: {', '.join(explanation_obj.strengths)}")
        if explanation_obj.weaknesses:
            explanation_parts.append(f"Areas for improvement: {', '.join(explanation_obj.weaknesses)}")
        if not explanation_parts:
            explanation_parts.append(f"Score: {clamped_score:.1f}/10 ({category})")

        explanation_str = ". ".join(explanation_parts) if explanation_parts else None

        return ValidationResult(
            valid=True,
            score=clamped_score,
            category=category,
            explanation=explanation_str,
            suggestions=explanation_obj.improvement_suggestions,
            calibrated_score=clamped_score,
        )

    def explain_score(
        self,
        score: float,
        category: str,
        language: Language | None = None,
        context: dict[str, Any] | None = None,
    ) -> ScoreExplanation:
        """
        Explain why a score is what it is.

        Args:
            score: The score to explain
            category: Score category
            language: Optional language for language-specific explanations
            context: Optional context (metrics, breakdown, etc.)

        Returns:
            ScoreExplanation with breakdown, factors, and suggestions
        """
        # Normalize score to 0-10 range if it's overall (0-100)
        normalized_score = score / 10.0 if category == "overall" else score

        # Determine score category
        if normalized_score >= self.EXCELLENT_THRESHOLD or normalized_score >= self.GOOD_THRESHOLD or normalized_score >= self.ACCEPTABLE_THRESHOLD or normalized_score >= self.POOR_THRESHOLD:
            pass
        else:
            pass

        # Extract breakdown from context if available
        breakdown = context.get("breakdown", {}) if context else {}
        factors = context.get("factors", []) if context else []

        # Generate strengths and weaknesses based on score
        strengths = []
        weaknesses = []
        improvement_suggestions = []

        if normalized_score >= self.EXCELLENT_THRESHOLD:
            strengths.append(f"{category} is excellent ({score:.1f}/10)")
            strengths.append("Code demonstrates best practices")
        elif normalized_score >= self.GOOD_THRESHOLD:
            strengths.append(f"{category} is good ({score:.1f}/10)")
            improvement_suggestions.append(
                f"Consider minor improvements to reach excellent level (>{self.EXCELLENT_THRESHOLD:.1f})"
            )
        elif normalized_score >= self.ACCEPTABLE_THRESHOLD:
            weaknesses.append(f"{category} is acceptable but could be improved ({score:.1f}/10)")
            improvement_suggestions.extend(
                self._generate_category_suggestions(category, normalized_score, language)
            )
        else:
            weaknesses.append(f"{category} needs significant improvement ({score:.1f}/10)")
            improvement_suggestions.extend(
                self._generate_category_suggestions(category, normalized_score, language)
            )

        return ScoreExplanation(
            score=score,
            category=category,
            breakdown=breakdown,
            factors=factors,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=improvement_suggestions,
        )

    def _generate_category_suggestions(
        self, category: str, score: float, language: Language | None = None
    ) -> list[str]:
        """Generate category-specific improvement suggestions."""
        suggestions = []

        if category == "complexity":
            suggestions.extend(
                [
                    "Break down complex functions into smaller, focused functions",
                    "Reduce nesting depth (aim for < 4 levels)",
                    "Extract complex logic into separate functions or modules",
                    "Use early returns to reduce nesting",
                ]
            )
            if language == Language.PYTHON:
                suggestions.append("Consider using list comprehensions or generator expressions")
            elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT]:
                suggestions.append("Use array methods (map, filter, reduce) instead of loops")
        elif category == "security":
            suggestions.extend(
                [
                    "Review and sanitize all user inputs",
                    "Use parameterized queries/prepared statements",
                    "Implement proper authentication and authorization",
                    "Keep dependencies updated and scan for vulnerabilities",
                ]
            )
            if language == Language.PYTHON:
                suggestions.append("Use secrets module for sensitive operations")
            elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT]:
                suggestions.append("Avoid using eval() or innerHTML with user input")
        elif category == "maintainability":
            suggestions.extend(
                [
                    "Add comprehensive docstrings/comments",
                    "Follow consistent naming conventions",
                    "Reduce code duplication (DRY principle)",
                    "Improve code organization and structure",
                ]
            )
            if language == Language.PYTHON:
                suggestions.append("Use type hints for better code clarity")
            elif language in [Language.TYPESCRIPT, Language.REACT]:
                suggestions.append("Use TypeScript for better type safety")
        elif category == "test_coverage":
            suggestions.extend(
                [
                    f"Increase test coverage to at least {self.GOOD_THRESHOLD*10:.0f}%",
                    "Add unit tests for critical functions",
                    "Include edge cases and error handling in tests",
                    "Add integration tests for important workflows",
                ]
            )
        elif category == "performance":
            suggestions.extend(
                [
                    "Profile code to identify bottlenecks",
                    "Optimize hot paths and frequently called functions",
                    "Consider caching results of expensive operations",
                    "Use appropriate data structures for the use case",
                ]
            )
            if language == Language.REACT:
                suggestions.extend(
                    [
                        "Use React.memo, useMemo, or useCallback to prevent unnecessary re-renders",
                        "Implement code splitting for large components",
                    ]
                )
            elif language == Language.PYTHON:
                suggestions.extend(
                    [
                        "Use async/await for I/O-bound operations",
                        "Consider using functools.lru_cache for expensive computations",
                    ]
                )
        elif category == "linting":
            suggestions.extend(
                [
                    "Run linting tool to identify specific code style issues",
                    "Fix code style violations (PEP 8 for Python, ESLint rules for JS/TS)",
                    "Address all errors (E) and fatal issues (F) first, then warnings (W)",
                    "Review and fix warnings for better code quality",
                ]
            )
            if language == Language.PYTHON:
                suggestions.extend(
                    [
                        "Run 'ruff check' to identify specific linting issues",
                        "Run 'ruff check --fix' to auto-fix many issues automatically",
                        "Configure ruff in pyproject.toml for project-specific rules",
                        "Ensure consistent import ordering and formatting",
                        "Fix line length violations (aim for 88-100 characters per line)",
                    ]
                )
            elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
                suggestions.extend(
                    [
                        "Run 'eslint' to identify specific linting issues",
                        "Run 'eslint --fix' to auto-fix many issues automatically",
                        "Configure ESLint rules in .eslintrc or package.json",
                        "Ensure consistent code formatting (integrate Prettier if needed)",
                        "Fix TypeScript-specific linting issues (strict mode violations)",
                    ]
                )
        elif category == "type_checking":
            suggestions.extend(
                [
                    "Add type annotations to function parameters and return types",
                    "Fix type errors reported by type checker",
                    "Use type hints consistently throughout the codebase",
                    "Enable strict type checking mode for better type safety",
                ]
            )
            if language == Language.PYTHON:
                suggestions.extend(
                    [
                        "Run 'mypy <file>' to see specific type errors",
                        "Add type hints using typing module or Python 3.9+ built-in types",
                        "Use Optional[T] for nullable types, Union[T, U] for multiple types",
                        "Consider using mypy --strict for maximum type safety",
                        "Add return type annotations: 'def func() -> int:'",
                        "Use TypeVar for generic types, Protocol for structural typing",
                    ]
                )
            elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
                suggestions.extend(
                    [
                        "Enable strict mode in tsconfig.json (strict: true)",
                        "Add explicit return types to functions",
                        "Use proper interface/type definitions instead of 'any'",
                        "Fix TypeScript compiler errors systematically",
                        "Avoid using 'any' type - use 'unknown' or specific types",
                        "Use type guards for runtime type checking",
                    ]
                )
        elif category == "duplication":
            suggestions.extend(
                [
                    "Identify and extract duplicate code into reusable functions",
                    "Use helper functions or utility modules for common patterns",
                    "Consider refactoring similar code blocks into shared components",
                    "Aim for < 3% code duplication across the project",
                ]
            )
            if language == Language.PYTHON:
                suggestions.extend(
                    [
                        "Run 'jscpd' to identify specific duplicate code blocks",
                        "Extract common logic into utility functions or classes",
                        "Use decorators or context managers for repeated patterns",
                        "Create shared utility modules for common functionality",
                        "Consider using mixins for shared class behavior",
                    ]
                )
            elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
                suggestions.extend(
                    [
                        "Extract duplicate code into shared utility functions",
                        "Create reusable React components for repeated UI patterns",
                        "Use higher-order components (HOCs) or custom hooks for common logic",
                        "Create shared utility modules or helper functions",
                        "Use composition over duplication for React components",
                    ]
                )
        elif category == "overall":
            # For overall score, provide general improvement suggestions
            # Focus on the most impactful areas
            suggestions.extend(
                [
                    "Review individual quality metrics (complexity, security, maintainability, test coverage, performance)",
                    "Address the lowest-scoring areas first for maximum impact",
                    "Set specific improvement goals for each quality dimension",
                    "Run code quality tools regularly to track progress",
                ]
            )
            if language == Language.PYTHON:
                suggestions.extend(
                    [
                        "Run ruff and mypy to identify code style and type issues",
                        "Use pytest with coverage to improve test coverage",
                    ]
                )
            elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT]:
                suggestions.extend(
                    [
                        "Use ESLint and TypeScript compiler to identify issues",
                        "Run tests with coverage to improve test coverage",
                    ]
                )

        return suggestions

    def validate_all_scores(
        self,
        scores: dict[str, float],
        language: Language | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, ValidationResult]:
        """
        Validate all scores in a score dictionary.

        Args:
            scores: Dictionary of category -> score (can have keys like "complexity_score" or "complexity")
            language: Optional language for language-specific validation
            context: Optional context for explanations

        Returns:
            Dictionary of category -> ValidationResult
        """
        results = {}
        for category, score in scores.items():
            # Skip non-numeric values (e.g., "metrics" dict, strings, lists)
            # Only validate actual numeric scores
            if not isinstance(score, (int, float)):
                continue
            
            # Normalize category name: remove "_score" suffix if present
            # e.g., "complexity_score" -> "complexity", "overall_score" -> "overall"
            normalized_category = category
            if category.endswith("_score"):
                normalized_category = category[:-6]  # Remove "_score" suffix
            
            category_context = (context or {}).get(category, {}) if context else None
            results[category] = self.validate_score(
                score, normalized_category, language=language, context=category_context
            )

        return results

    def calibrate_score(
        self, score: float, category: str, baseline: float | None = None
    ) -> float:
        """
        Calibrate a score against a baseline.

        Args:
            score: The score to calibrate
            category: Score category
            baseline: Optional baseline score for calibration

        Returns:
            Calibrated score
        """
        if baseline is None:
            return score

        # Simple calibration: adjust score based on baseline
        # If baseline is high, scores should be stricter
        # If baseline is low, scores can be more lenient
        calibration_factor = baseline / 7.0  # Use 7.0 as neutral baseline
        calibrated = score * calibration_factor

        # Clamp to valid range
        min_score, max_score = self.SCORE_RANGES.get(category, (0.0, 10.0))
        return max(min_score, min(max_score, calibrated))

