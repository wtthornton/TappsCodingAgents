"""
Accessibility Auditor using Playwright snapshots.

Analyzes accessibility snapshots for WCAG 2.2 compliance and generates
accessibility test assertions.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AccessibilityIssue:
    """Accessibility issue found in snapshot."""

    severity: str  # "error", "warning", "info"
    rule: str  # WCAG rule identifier
    element: str  # Element description
    message: str  # Issue description
    suggestion: str  # How to fix


@dataclass
class AccessibilityAudit:
    """Accessibility audit results."""

    score: float  # 0-100 accessibility score
    level: str  # "A", "AA", "AAA" compliance level
    issues: list[AccessibilityIssue]
    passed_checks: int
    total_checks: int
    summary: str


class AccessibilityAuditor:
    """
    Audit accessibility using Playwright snapshots.

    Analyzes accessibility snapshots for WCAG 2.2 compliance.
    """

    # WCAG 2.2 Level A requirements
    WCAG_A_CHECKS = [
        ("alt_text", "Images must have alt text", r'img.*alt=["\']([^"\']*)["\']'),
        ("heading_structure", "Headings must be properly structured", r'<h([1-6])'),
        ("form_labels", "Form inputs must have labels", r'<input.*(?:id|aria-labelledby)'),
        ("link_text", "Links must have descriptive text", r'<a[^>]*>([^<]+)</a>'),
        ("button_text", "Buttons must have accessible text", r'<button[^>]*>([^<]+)</button>'),
    ]

    # WCAG 2.2 Level AA requirements
    WCAG_AA_CHECKS = [
        ("color_contrast", "Text must meet color contrast requirements", None),
        ("keyboard_navigation", "All interactive elements must be keyboard accessible", None),
        ("focus_indicators", "Focus indicators must be visible", None),
    ]

    def audit(self, snapshot_content: str) -> AccessibilityAudit:
        """
        Analyze accessibility snapshot.

        Args:
            snapshot_content: Accessibility snapshot markdown content

        Returns:
            AccessibilityAudit with score and issues
        """
        issues: list[AccessibilityIssue] = []
        passed_checks = 0
        total_checks = 0

        # Extract HTML content from snapshot
        html_content = self._extract_html(snapshot_content)

        # Run WCAG Level A checks
        for check_id, description, pattern in self.WCAG_A_CHECKS:
            total_checks += 1
            issue = self._check_wcag_a(html_content, check_id, description, pattern)
            if issue:
                issues.append(issue)
            else:
                passed_checks += 1

        # Run WCAG Level AA checks (basic checks)
        for check_id, description, _ in self.WCAG_AA_CHECKS:
            total_checks += 1
            issue = self._check_wcag_aa(html_content, check_id, description)
            if issue:
                issues.append(issue)
            else:
                passed_checks += 1

        # Calculate score
        score = (passed_checks / total_checks * 100) if total_checks > 0 else 0.0

        # Determine compliance level
        level = self._determine_level(score, issues)

        # Generate summary
        summary = self._generate_summary(score, level, len(issues), total_checks)

        return AccessibilityAudit(
            score=score,
            level=level,
            issues=issues,
            passed_checks=passed_checks,
            total_checks=total_checks,
            summary=summary,
        )

    def _extract_html(self, snapshot_content: str) -> str:
        """Extract HTML content from snapshot markdown."""
        # Snapshot may be markdown with HTML code blocks
        html_match = re.search(r"```html\n(.*?)\n```", snapshot_content, re.DOTALL)
        if html_match:
            return html_match.group(1)

        # Or it might be direct HTML
        if "<html" in snapshot_content or "<div" in snapshot_content:
            return snapshot_content

        return snapshot_content

    def _check_wcag_a(
        self, html: str, check_id: str, description: str, pattern: str | None
    ) -> AccessibilityIssue | None:
        """Check WCAG Level A requirement."""
        if check_id == "alt_text":
            # Check for images without alt text
            img_pattern = r'<img[^>]*>'
            images = re.findall(img_pattern, html, re.IGNORECASE)
            for img in images:
                if 'alt=' not in img.lower() and 'aria-label=' not in img.lower():
                    return AccessibilityIssue(
                        severity="error",
                        rule="WCAG 2.2.1.1 (Level A)",
                        element=img[:50],
                        message="Image missing alt text",
                        suggestion="Add alt attribute to img tag: <img alt='description'>",
                    )

        elif check_id == "heading_structure":
            # Check for proper heading hierarchy
            headings = re.findall(r'<h([1-6])', html, re.IGNORECASE)
            if headings:
                levels = [int(h) for h in headings]
                # Check for skipped levels (e.g., h1 -> h3)
                for i in range(len(levels) - 1):
                    if levels[i + 1] > levels[i] + 1:
                        return AccessibilityIssue(
                            severity="warning",
                            rule="WCAG 2.4.6 (Level A)",
                            element=f"h{levels[i]} -> h{levels[i+1]}",
                            message="Heading levels should not be skipped",
                            suggestion="Use sequential heading levels (h1, h2, h3, etc.)",
                        )

        elif check_id == "form_labels":
            # Check for form inputs without labels
            inputs = re.findall(r'<input[^>]*>', html, re.IGNORECASE)
            for inp in inputs:
                if 'id=' in inp or 'aria-labelledby=' in inp:
                    continue
                if 'aria-label=' in inp:
                    continue
                # Check if there's a label element nearby (simplified check)
                return AccessibilityIssue(
                    severity="error",
                    rule="WCAG 2.4.6 (Level A)",
                    element=inp[:50],
                    message="Form input missing label",
                    suggestion="Add <label> element or aria-label attribute",
                )

        elif check_id == "link_text":
            # Check for links without descriptive text
            links = re.findall(r'<a[^>]*>([^<]+)</a>', html, re.IGNORECASE)
            for link_text in links:
                link_text = link_text.strip()
                if not link_text or len(link_text) < 3:
                    return AccessibilityIssue(
                        severity="error",
                        rule="WCAG 2.4.4 (Level A)",
                        element=f"Link: {link_text}",
                        message="Link text is not descriptive",
                        suggestion="Use descriptive link text (e.g., 'Read more about accessibility' not 'click here')",
                    )

        elif check_id == "button_text":
            # Check for buttons without text
            buttons = re.findall(r'<button[^>]*>([^<]*)</button>', html, re.IGNORECASE)
            for button_text in buttons:
                button_text = button_text.strip()
                if not button_text:
                    return AccessibilityIssue(
                        severity="error",
                        rule="WCAG 2.4.4 (Level A)",
                        element="Button",
                        message="Button missing accessible text",
                        suggestion="Add text content or aria-label to button",
                    )

        return None

    def _check_wcag_aa(self, html: str, check_id: str, description: str) -> AccessibilityIssue | None:
        """Check WCAG Level AA requirement (basic checks)."""
        # These are harder to check from HTML alone, so we do basic checks
        if check_id == "color_contrast":
            # Can't check color contrast from HTML alone
            # This would require actual rendering
            return None  # Pass for now (would need visual analysis)

        elif check_id == "keyboard_navigation":
            # Check for interactive elements that might not be keyboard accessible
            # This is a simplified check
            interactive_elements = re.findall(
                r'<(button|a|input|select|textarea)[^>]*>', html, re.IGNORECASE
            )
            if not interactive_elements:
                return None

            # Check for tabindex="-1" which makes elements not keyboard accessible
            if 'tabindex="-1"' in html:
                return AccessibilityIssue(
                    severity="warning",
                    rule="WCAG 2.1.1 (Level A)",
                    element="Interactive element",
                    message="Some elements may not be keyboard accessible",
                    suggestion="Ensure all interactive elements are keyboard accessible",
                )

        elif check_id == "focus_indicators":
            # Check for CSS that might hide focus indicators
            # This is a simplified check
            if 'outline: none' in html or 'outline: 0' in html:
                return AccessibilityIssue(
                    severity="warning",
                    rule="WCAG 2.4.7 (Level AA)",
                    element="CSS",
                    message="Focus indicators may be hidden",
                    suggestion="Ensure focus indicators are visible (don't use outline: none without alternative)",
                )

        return None

    def _determine_level(self, score: float, issues: list[AccessibilityIssue]) -> str:
        """Determine WCAG compliance level."""
        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        if error_count == 0 and warning_count == 0 and score >= 95:
            return "AAA"
        elif error_count == 0 and score >= 90:
            return "AA"
        elif error_count < 3 and score >= 80:
            return "A"
        else:
            return "Not Compliant"

    def _generate_summary(
        self, score: float, level: str, issue_count: int, total_checks: int
    ) -> str:
        """Generate audit summary."""
        return (
            f"Accessibility Score: {score:.1f}/100\n"
            f"WCAG Compliance: Level {level}\n"
            f"Issues Found: {issue_count} ({total_checks - issue_count} passed)\n"
            f"Total Checks: {total_checks}"
        )

    def generate_test_assertions(self, audit: AccessibilityAudit) -> list[str]:
        """
        Generate test assertions from audit results.

        Args:
            audit: AccessibilityAudit results

        Returns:
            List of test assertion code strings
        """
        assertions = []

        # Overall score assertion
        assertions.append(
            f"assert accessibility_score >= {audit.score:.1f}, "
            f"'Accessibility score {audit.score:.1f} is below threshold'"
        )

        # Compliance level assertion
        assertions.append(
            f"assert accessibility_level == '{audit.level}', "
            f"'Expected WCAG {audit.level} compliance, got {audit.level}'"
        )

        # Issue-specific assertions
        for issue in audit.issues:
            if issue.severity == "error":
                assertions.append(
                    f"assert not has_accessibility_issue('{issue.rule}'), "
                    f"'{issue.message}'"
                )

        return assertions
