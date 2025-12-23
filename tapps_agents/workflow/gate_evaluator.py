"""
Composite gate evaluator for Tier 1 Enhancement.

Replaces score-only gates with issue + verification outcome gates.
"""

import logging
from typing import Any

from ..core.evaluation_models import IssueManifest, IssueSeverity
from ..quality.quality_gates import QualityGate, QualityGateResult, QualityThresholds

logger = logging.getLogger(__name__)


class CompositeGateEvaluator:
    """
    Composite gate evaluator using issues + verification outcomes.
    
    Implements hard fail/soft fail/loopback logic based on:
    - Critical issues (hard fail)
    - Verification failures (hard fail)
    - High issues above threshold (soft fail/loopback)
    - Regression vs baseline (soft fail/loopback)
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize composite gate evaluator.
        
        Args:
            config: Configuration with issue thresholds
        """
        self.config = config or {}
        self.issue_thresholds = self.config.get("issue_severity_thresholds", {
            "critical": 0,  # Hard fail
            "high": 5,  # Soft fail/loopback
            "medium": 10,
            "low": 20,
        })
        self.quality_gate = QualityGate()

    def evaluate(
        self,
        scores: dict[str, float] | None = None,
        issues: IssueManifest | None = None,
        verification_results: list[Any] | None = None,
        baseline: dict[str, Any] | None = None,
        thresholds: QualityThresholds | None = None,
    ) -> "CompositeGateResult":
        """
        Evaluate composite gate.
        
        Args:
            scores: Quality scores
            issues: Issues manifest
            verification_results: Verification/test results
            baseline: Baseline for regression detection
            thresholds: Quality thresholds
            
        Returns:
            CompositeGateResult
        """
        # Evaluate quality scores (existing gate logic)
        quality_result: QualityGateResult | None = None
        if scores:
            quality_result = self.quality_gate.evaluate(scores, thresholds)
        
        # Check for hard fail conditions
        hard_fail = False
        hard_fail_reasons: list[str] = []
        
        if issues:
            critical_count = len(issues.get_critical_issues())
            if critical_count > self.issue_thresholds.get("critical", 0):
                hard_fail = True
                hard_fail_reasons.append(f"Critical issues: {critical_count}")
        
        # Check verification failures
        if verification_results:
            failures = [r for r in verification_results if not getattr(r, "passed", True)]
            if failures:
                hard_fail = True
                hard_fail_reasons.append(f"Verification failures: {len(failures)}")
        
        # Check for soft fail/loopback conditions
        soft_fail = False
        loopback = False
        soft_fail_reasons: list[str] = []
        
        if issues and not hard_fail:
            high_count = len(issues.get_high_issues())
            high_threshold = self.issue_thresholds.get("high", 5)
            if high_count > high_threshold:
                soft_fail = True
                loopback = True
                soft_fail_reasons.append(f"High issues above threshold: {high_count} > {high_threshold}")
        
        # Check for regression
        if baseline and scores:
            regression = self._detect_regression(scores, baseline)
            if regression:
                soft_fail = True
                loopback = True
                soft_fail_reasons.append("Regression detected vs baseline")
        
        # Overall gate decision
        passed = not hard_fail and not soft_fail and (
            quality_result.passed if quality_result else True
        )
        
        return CompositeGateResult(
            passed=passed,
            hard_fail=hard_fail,
            soft_fail=soft_fail,
            loopback=loopback,
            hard_fail_reasons=hard_fail_reasons,
            soft_fail_reasons=soft_fail_reasons,
            quality_result=quality_result,
            issues=issues,
        )

    def _detect_regression(
        self, current_scores: dict[str, float], baseline: dict[str, Any]
    ) -> bool:
        """Detect if current scores regress from baseline."""
        baseline_scores = baseline.get("scores", {})
        
        for key in ["overall_score", "security_score", "maintainability_score"]:
            current = current_scores.get(key, 0.0)
            baseline_score = baseline_scores.get(key, 0.0)
            
            # Regression if score dropped by more than 5%
            if baseline_score > 0 and current < baseline_score * 0.95:
                return True
        
        return False


class CompositeGateResult:
    """Result of composite gate evaluation."""

    def __init__(
        self,
        passed: bool,
        hard_fail: bool,
        soft_fail: bool,
        loopback: bool,
        hard_fail_reasons: list[str],
        soft_fail_reasons: list[str],
        quality_result: QualityGateResult | None = None,
        issues: IssueManifest | None = None,
    ):
        """Initialize composite gate result."""
        self.passed = passed
        self.hard_fail = hard_fail
        self.soft_fail = soft_fail
        self.loopback = loopback
        self.hard_fail_reasons = hard_fail_reasons
        self.soft_fail_reasons = soft_fail_reasons
        self.quality_result = quality_result
        self.issues = issues

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "passed": self.passed,
            "hard_fail": self.hard_fail,
            "soft_fail": self.soft_fail,
            "loopback": self.loopback,
            "hard_fail_reasons": self.hard_fail_reasons,
            "soft_fail_reasons": self.soft_fail_reasons,
        }
        
        if self.quality_result:
            result["quality_result"] = self.quality_result.to_dict()
        
        if self.issues:
            result["issues"] = self.issues.to_dict()
        
        return result

