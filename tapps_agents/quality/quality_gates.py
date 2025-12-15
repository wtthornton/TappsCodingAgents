"""
Quality Gates Module.

Story 6.4: Quality Gates & Review Integration
- Implement quality thresholds (8.0+ overall, 8.5+ security)
- Add quality gates to workflows
- Integrate scores into Review Agent decisions
- Create quality reports
"""

from dataclasses import dataclass
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

        # Extract scores (normalize to 0-10 scale for comparison)
        overall_score = scores.get("overall_score", 0.0) / 10.0  # Convert 0-100 to 0-10
        security_score = scores.get("security_score", 0.0)
        maintainability_score = scores.get("maintainability_score", 0.0)
        complexity_score = scores.get("complexity_score", 10.0)  # Lower is better
        test_coverage_score = scores.get("test_coverage_score", 0.0)
        performance_score = scores.get("performance_score", 0.0)

        # Evaluate each threshold
        overall_passed = overall_score >= thresholds.overall_min
        security_passed = security_score >= thresholds.security_min
        maintainability_passed = maintainability_score >= thresholds.maintainability_min
        complexity_passed = complexity_score <= thresholds.complexity_max
        # Test coverage is typically 0-100%, convert to 0-10 scale for comparison
        test_coverage_pct = test_coverage_score * 10.0  # Convert 0-10 to 0-100
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
