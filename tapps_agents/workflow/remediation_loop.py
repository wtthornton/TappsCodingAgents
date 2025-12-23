"""
Remediation loop for automatic issue fixing.

Implements bounded loopback protocol with structured fix plans.
"""

import logging
from typing import Any

from ..core.evaluation_models import Issue, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class RemediationLoop:
    """
    Bounded loopback protocol for automatic issue remediation.
    
    Creates structured fix plans from issues, re-validates after fixes,
    and handles bounded retries with escalation.
    """

    def __init__(
        self,
        max_retries: int = 3,
        enable_regression_protection: bool = True,
    ):
        """
        Initialize remediation loop.
        
        Args:
            max_retries: Maximum remediation retry attempts
            enable_regression_protection: Enable regression protection
        """
        self.max_retries = max_retries
        self.enable_regression_protection = enable_regression_protection
        self.retry_count = 0
        self.baseline: dict[str, Any] | None = None

    def create_fix_plan(self, issues: IssueManifest) -> "FixPlan":
        """
        Create structured fix plan from issues.
        
        Args:
            issues: Issues to fix
            
        Returns:
            FixPlan with prioritized fixes
        """
        # Prioritize by severity
        prioritized = issues.prioritize()
        
        # Group fixes by owner step
        fixes_by_step: dict[str, list[Issue]] = {}
        for issue in prioritized.issues:
            step = issue.owner_step
            if step not in fixes_by_step:
                fixes_by_step[step] = []
            fixes_by_step[step].append(issue)
        
        return FixPlan(
            issues=prioritized,
            fixes_by_step=fixes_by_step,
            total_fixes=len(prioritized.issues),
            critical_fixes=len(prioritized.get_critical_issues()),
            high_fixes=len(prioritized.get_high_issues()),
        )

    def should_retry(
        self,
        current_issues: IssueManifest,
        previous_issues: IssueManifest | None = None,
    ) -> tuple[bool, str]:
        """
        Determine if remediation should retry.
        
        Args:
            current_issues: Current issues after fix attempt
            previous_issues: Issues before fix attempt (for regression check)
            
        Returns:
            Tuple of (should_retry, reason)
        """
        if self.retry_count >= self.max_retries:
            return False, f"Maximum retries ({self.max_retries}) reached"
        
        # Check for regression
        if self.enable_regression_protection and previous_issues:
            if self._has_regressed(current_issues, previous_issues):
                return False, "Regression detected - stopping to prevent further degradation"
        
        # Retry if critical or high issues remain
        critical_count = len(current_issues.get_critical_issues())
        high_count = len(current_issues.get_high_issues())
        
        if critical_count > 0:
            return True, f"Critical issues remain: {critical_count}"
        
        if high_count > 5:
            return True, f"High issues above threshold: {high_count}"
        
        return False, "No critical issues and high issues below threshold"

    def _has_regressed(
        self, current: IssueManifest, previous: IssueManifest
    ) -> bool:
        """Check if issues have regressed (more critical/high issues)."""
        current_critical = len(current.get_critical_issues())
        previous_critical = len(previous.get_critical_issues())
        
        current_high = len(current.get_high_issues())
        previous_high = len(previous.get_high_issues())
        
        # Regression if critical or high issues increased
        return (
            current_critical > previous_critical
            or current_high > previous_high + 2  # Allow small fluctuations
        )

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1

    def reset(self) -> None:
        """Reset retry counter."""
        self.retry_count = 0

    def set_baseline(self, baseline: dict[str, Any]) -> None:
        """Set baseline for regression protection."""
        self.baseline = baseline


class FixPlan:
    """Structured fix plan from issues."""

    def __init__(
        self,
        issues: IssueManifest,
        fixes_by_step: dict[str, list[Issue]],
        total_fixes: int,
        critical_fixes: int,
        high_fixes: int,
    ):
        """Initialize fix plan."""
        self.issues = issues
        self.fixes_by_step = fixes_by_step
        self.total_fixes = total_fixes
        self.critical_fixes = critical_fixes
        self.high_fixes = high_fixes

    def get_fixes_for_step(self, step: str) -> list[Issue]:
        """Get fixes for a specific workflow step."""
        return self.fixes_by_step.get(step, [])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_fixes": self.total_fixes,
            "critical_fixes": self.critical_fixes,
            "high_fixes": self.high_fixes,
            "fixes_by_step": {
                step: [issue.id for issue in issues]
                for step, issues in self.fixes_by_step.items()
            },
        }

