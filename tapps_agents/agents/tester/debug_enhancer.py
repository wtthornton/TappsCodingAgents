"""
Enhanced Debugging Tools for Playwright Tests.

Provides screenshot comparison, failure analysis, and debugging utilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Import visual regression tester
try:
    from .visual_regression import VisualRegressionTester, VisualDiff
except ImportError:
    VisualRegressionTester = None
    VisualDiff = None


@dataclass
class FailureAnalysis:
    """Analysis of test failure."""

    test_name: str
    error_message: str
    screenshot_path: Path | None = None
    trace_path: Path | None = None
    network_requests: list[dict[str, Any]] | None = None
    console_errors: list[str] | None = None
    visual_diff: VisualDiff | None = None
    recommendations: list[str] | None = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class DebugEnhancer:
    """
    Enhanced debugging tools for test failures.

    Provides screenshot comparison, failure analysis, and debugging recommendations.
    """

    def __init__(
        self,
        screenshot_dir: Path | None = None,
        enable_visual_regression: bool = True,
    ):
        """
        Initialize debug enhancer.

        Args:
            screenshot_dir: Directory for failure screenshots (default: .tapps-agents/failures/)
            enable_visual_regression: Enable visual regression testing
        """
        if screenshot_dir is None:
            screenshot_dir = Path(".tapps-agents") / "failures"
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.visual_tester: VisualRegressionTester | None = None
        if enable_visual_regression and VisualRegressionTester:
            self.visual_tester = VisualRegressionTester()

    def analyze_failure(
        self,
        test_name: str,
        error_message: str,
        screenshot_path: Path | None = None,
        trace_path: Path | None = None,
        network_requests: list[dict[str, Any]] | None = None,
        console_errors: list[str] | None = None,
        baseline_name: str | None = None,
    ) -> FailureAnalysis:
        """
        Analyze test failure and provide recommendations.

        Args:
            test_name: Name of the failed test
            error_message: Error message from test failure
            screenshot_path: Optional screenshot path
            trace_path: Optional trace file path
            network_requests: Optional network requests
            console_errors: Optional console errors
            baseline_name: Optional baseline name for visual comparison

        Returns:
            FailureAnalysis with recommendations
        """
        analysis = FailureAnalysis(
            test_name=test_name,
            error_message=error_message,
            screenshot_path=screenshot_path,
            trace_path=trace_path,
            network_requests=network_requests,
            console_errors=console_errors,
        )

        # Visual regression check
        if (
            self.visual_tester
            and screenshot_path
            and screenshot_path.exists()
            and baseline_name
        ):
            try:
                visual_diff = self.visual_tester.compare(
                    screenshot_path, baseline_name
                )
                analysis.visual_diff = visual_diff
                if visual_diff.has_regression:
                    analysis.recommendations.append(
                        f"Visual regression detected: {visual_diff.difference_percentage:.2f}% difference. "
                        f"Review diff: {visual_diff.diff_path}"
                    )
            except Exception as e:
                logger.warning(f"Visual comparison failed: {e}")

        # Network analysis
        if network_requests:
            failed_requests = [
                r for r in network_requests if r.get("status", 200) >= 400
            ]
            if failed_requests:
                analysis.recommendations.append(
                    f"Found {len(failed_requests)} failed network requests. "
                    "Check API endpoints and network connectivity."
                )

        # Console error analysis
        if console_errors:
            analysis.recommendations.append(
                f"Found {len(console_errors)} JavaScript errors. "
                "Check browser console for details."
            )

        # Trace file recommendation
        if trace_path and trace_path.exists():
            analysis.recommendations.append(
                f"View trace file for detailed debugging: npx playwright show-trace {trace_path}"
            )

        # General recommendations based on error message
        error_lower = error_message.lower()
        if "timeout" in error_lower:
            analysis.recommendations.append(
                "Timeout error: Consider increasing wait timeouts or checking for slow network requests."
            )
        if "element not found" in error_lower or "selector" in error_lower:
            analysis.recommendations.append(
                "Element not found: Verify selector is correct and element is visible/loaded."
            )
        if "network" in error_lower or "fetch" in error_lower:
            analysis.recommendations.append(
                "Network error: Check API endpoints, CORS settings, and network connectivity."
            )

        return analysis

    def save_failure_screenshot(
        self, screenshot_path: Path, test_name: str
    ) -> Path:
        """
        Save failure screenshot with standardized naming.

        Args:
            screenshot_path: Path to screenshot
            test_name: Test name

        Returns:
            Path to saved screenshot
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = "".join(c for c in test_name if c.isalnum() or c in ("-", "_"))
        failure_filename = f"{safe_test_name}_{timestamp}.png"
        failure_path = self.screenshot_dir / failure_filename

        import shutil

        shutil.copy2(screenshot_path, failure_path)
        logger.info(f"Saved failure screenshot: {failure_path}")

        return failure_path

    def generate_failure_report(self, analysis: FailureAnalysis) -> str:
        """
        Generate human-readable failure report.

        Args:
            analysis: FailureAnalysis object

        Returns:
            Formatted failure report string
        """
        report_lines = [
            f"Test Failure: {analysis.test_name}",
            "=" * 60,
            f"Error: {analysis.error_message}",
            "",
        ]

        if analysis.screenshot_path:
            report_lines.append(f"Screenshot: {analysis.screenshot_path}")

        if analysis.trace_path:
            report_lines.append(
                f"Trace: {analysis.trace_path}\n"
                f"View: npx playwright show-trace {analysis.trace_path}"
            )

        if analysis.visual_diff:
            report_lines.append(
                f"\nVisual Regression:\n"
                f"  Similarity: {analysis.visual_diff.similarity_score:.2f}%\n"
                f"  Difference: {analysis.visual_diff.difference_percentage:.2f}%\n"
                f"  Diff Image: {analysis.visual_diff.diff_path}"
            )

        if analysis.network_requests:
            failed = [r for r in analysis.network_requests if r.get("status", 200) >= 400]
            report_lines.append(f"\nNetwork Requests: {len(analysis.network_requests)} total, {len(failed)} failed")

        if analysis.console_errors:
            report_lines.append(f"\nConsole Errors: {len(analysis.console_errors)}")

        if analysis.recommendations:
            report_lines.append("\nRecommendations:")
            for i, rec in enumerate(analysis.recommendations, 1):
                report_lines.append(f"  {i}. {rec}")

        return "\n".join(report_lines)
