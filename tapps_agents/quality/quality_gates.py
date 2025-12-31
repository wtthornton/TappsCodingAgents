"""
Quality Gates Module.

Story 6.4: Quality Gates & Review Integration
Phase 2.2: Enhanced with coverage analysis integration

- Implement quality thresholds (8.0+ overall, 8.5+ security)
- Add quality gates to workflows
- Integrate scores into Review Agent decisions
- Create quality reports
- Async coverage measurement using CoverageAnalyzer
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class QualityThresholds:
    """Quality score thresholds for gates."""

    overall_min: float = 8.0
    security_min: float = 8.5
    maintainability_min: float = 7.0
    complexity_max: float = 5.0  # Lower is better, so this is a max
    test_coverage_min: float = 80.0
    performance_min: float = 7.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityThresholds":
        """Create from dictionary."""
        return cls(
            overall_min=data.get("overall_min", 8.0),
            security_min=data.get("security_min", 8.5),
            maintainability_min=data.get("maintainability_min", 7.0),
            complexity_max=data.get("complexity_max", 5.0),
            test_coverage_min=data.get("test_coverage_min", 80.0),
            performance_min=data.get("performance_min", 7.0),
        )


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""

    passed: bool
    overall_passed: bool
    security_passed: bool
    maintainability_passed: bool
    complexity_passed: bool
    test_coverage_passed: bool
    performance_passed: bool
    failures: list[str]
    warnings: list[str]
    scores: dict[str, float]
    thresholds: QualityThresholds

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "overall_passed": self.overall_passed,
            "security_passed": self.security_passed,
            "maintainability_passed": self.maintainability_passed,
            "complexity_passed": self.complexity_passed,
            "test_coverage_passed": self.test_coverage_passed,
            "performance_passed": self.performance_passed,
            "failures": self.failures,
            "warnings": self.warnings,
            "scores": self.scores,
            "thresholds": {
                "overall_min": self.thresholds.overall_min,
                "security_min": self.thresholds.security_min,
                "maintainability_min": self.thresholds.maintainability_min,
                "complexity_max": self.thresholds.complexity_max,
                "test_coverage_min": self.thresholds.test_coverage_min,
                "performance_min": self.thresholds.performance_min,
            },
        }


class QualityGate:
    """
    Evaluate quality gates against scoring thresholds.

    Story 6.4: Quality Gates & Review Integration
    """

    def __init__(self, thresholds: QualityThresholds | None = None):
        """
        Initialize quality gate.

        Args:
            thresholds: Quality thresholds (default: standard thresholds)
        """
        self.thresholds = thresholds or QualityThresholds()

    def evaluate(
        self,
        scores: dict[str, float],
        thresholds: QualityThresholds | None = None,
    ) -> QualityGateResult:
        """
        Evaluate quality scores against thresholds.

        Args:
            scores: Dictionary with quality scores
            thresholds: Optional thresholds to use (overrides instance thresholds)

        Returns:
            QualityGateResult with evaluation results
        """
        if thresholds is None:
            thresholds = self.thresholds

        # Lazy import to avoid circular dependency
        from ..agents.reviewer.score_constants import ScoreNormalizer, extract_scores_normalized
        
        # Normalize all scores to consistent scales using score constants
        normalized_scores = extract_scores_normalized(scores)
        
        normalizer = ScoreNormalizer()
        
        # Extract normalized scores (individual metrics are 0-10, overall is 0-100)
        # Convert overall score to 0-10 scale for threshold comparison (thresholds are 0-10)
        overall_score = normalizer.normalize_overall_score(
            normalized_scores["overall_score"], from_scale_100=True
        )
        security_score = normalized_scores["security_score"]
        maintainability_score = normalized_scores["maintainability_score"]
        complexity_score = normalized_scores["complexity_score"]  # Lower is better
        test_coverage_score = normalized_scores["test_coverage_score"]
        performance_score = normalized_scores["performance_score"]

        # Evaluate each threshold
        overall_passed = overall_score >= thresholds.overall_min
        security_passed = security_score >= thresholds.security_min
        maintainability_passed = maintainability_score >= thresholds.maintainability_min
        complexity_passed = complexity_score <= thresholds.complexity_max
        # Test coverage: convert from 0-10 scale to percentage (0-100) for threshold comparison
        test_coverage_pct = normalizer.test_coverage_to_percentage(test_coverage_score)
        test_coverage_passed = test_coverage_pct >= thresholds.test_coverage_min
        performance_passed = performance_score >= thresholds.performance_min

        # Collect failures and warnings
        failures: list[str] = []
        warnings: list[str] = []

        if not overall_passed:
            failures.append(
                f"Overall score {overall_score:.2f} below threshold {thresholds.overall_min}"
            )
        if not security_passed:
            failures.append(
                f"Security score {security_score:.2f} below threshold {thresholds.security_min}"
            )
        if not maintainability_passed:
            warnings.append(
                f"Maintainability score {maintainability_score:.2f} below threshold {thresholds.maintainability_min}"
            )
        if not complexity_passed:
            warnings.append(
                f"Complexity score {complexity_score:.2f} above threshold {thresholds.complexity_max}"
            )
        if not test_coverage_passed:
            warnings.append(
                f"Test coverage {test_coverage_pct:.2f}% below threshold {thresholds.test_coverage_min}%"
            )
        if not performance_passed:
            warnings.append(
                f"Performance score {performance_score:.2f} below threshold {thresholds.performance_min}"
            )

        # Gate passes if all critical metrics pass (overall and security)
        passed = overall_passed and security_passed

        return QualityGateResult(
            passed=passed,
            overall_passed=overall_passed,
            security_passed=security_passed,
            maintainability_passed=maintainability_passed,
            complexity_passed=complexity_passed,
            test_coverage_passed=test_coverage_passed,
            performance_passed=performance_passed,
            failures=failures,
            warnings=warnings,
            scores={
                "overall_score": overall_score,
                "security_score": security_score,
                "maintainability_score": maintainability_score,
                "complexity_score": complexity_score,
                "test_coverage_score": test_coverage_score,
                "performance_score": performance_score,
            },
            thresholds=thresholds,
        )

    def evaluate_from_review_result(
        self, review_result: dict[str, Any], thresholds: QualityThresholds | None = None
    ) -> QualityGateResult:
        """
        Evaluate quality gate from Reviewer Agent result.

        Args:
            review_result: Result dictionary from Reviewer Agent
            thresholds: Optional thresholds to use

        Returns:
            QualityGateResult with evaluation results
        """
        # Extract scores from review result
        scores = review_result.get("scores", {})
        if not scores:
            # Try to extract from nested structure
            scoring = review_result.get("scoring", {})
            if scoring:
                scores = scoring.get("scores", {})

        return self.evaluate(scores, thresholds)

    async def check_coverage(
        self,
        file_path: Path,
        language: Any,
        threshold: float = 0.8,
        test_file_path: Path | None = None,
        project_root: Path | None = None,
    ) -> QualityGateResult:
        """
        Check test coverage for a file and evaluate against threshold.
        
        Phase 2.2: Coverage Analysis Integration
        
        Note: This method uses CoverageAnalyzer which runs tool operations (subprocess commands).
        Tool operations work in both Cursor and headless modes. This is Cursor-first compatible.
        
        Args:
            file_path: Path to the source file
            language: Detected language (from LanguageDetector)
            threshold: Minimum coverage threshold (0.0-1.0)
            test_file_path: Optional path to test file
            project_root: Optional project root directory
            
        Returns:
            QualityGateResult with coverage evaluation results
        """
        from ...agents.tester.coverage_analyzer import CoverageAnalyzer
        from ...core.language_detector import Language

        # Ensure language is Language enum
        if not isinstance(language, Language):
            # Try to convert if it's a string
            try:
                language = Language(language)
            except (ValueError, TypeError):
                language = Language.UNKNOWN

        # Measure coverage using CoverageAnalyzer
        # CoverageAnalyzer runs tool operations (pytest, jest, etc.) which work in both modes
        # This is Cursor-first compatible as it doesn't require LLM operations
        analyzer = CoverageAnalyzer()
        coverage_result = await analyzer.measure_coverage(
            file_path=file_path,
            language=language,
            test_file_path=test_file_path,
            project_root=project_root,
        )

        # Convert coverage percentage (0-100) to 0-1 scale
        coverage_pct = coverage_result.coverage_percentage / 100.0
        coverage_passed = coverage_pct >= threshold

        # Lazy import to avoid circular dependency
        from ..agents.reviewer.score_constants import ScoreNormalizer
        
        # Create scores dict for evaluation using normalized scales
        # Test coverage: percentage (0-100) to 0-10 scale
        normalizer = ScoreNormalizer()
        test_coverage_0_10 = normalizer.normalize_test_coverage(
            coverage_result.coverage_percentage, from_percentage=True
        )
        
        scores: dict[str, float] = {
            "test_coverage_score": test_coverage_0_10,  # 0-10 scale
            "overall_score": 100.0 if coverage_passed else 50.0,  # 0-100 scale
        }

        # Evaluate using existing evaluate method
        thresholds = QualityThresholds(test_coverage_min=threshold * 100.0)
        result = self.evaluate(scores, thresholds)

        # Enhance result with coverage-specific information
        if coverage_result.error:
            result.failures.append(f"Coverage measurement error: {coverage_result.error}")
            result.passed = False

        # Add coverage details to scores
        result.scores.update(
            {
                "coverage_percentage": coverage_result.coverage_percentage,
                "coverage_lines_covered": coverage_result.lines_covered,
                "coverage_lines_total": coverage_result.lines_total,
                "coverage_framework": coverage_result.framework,
            }
        )

        return result
