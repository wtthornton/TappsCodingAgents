"""
Performance Monitor using Playwright network requests.

Collects Core Web Vitals and performance metrics from page loads.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ...core.playwright_mcp_controller import PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceThresholds:
    """Performance thresholds for Core Web Vitals."""

    lcp_good: float = 2.5  # Largest Contentful Paint (seconds) - good
    lcp_needs_improvement: float = 4.0  # LCP - needs improvement

    fid_good: float = 100.0  # First Input Delay (milliseconds) - good
    fid_needs_improvement: float = 300.0  # FID - needs improvement

    cls_good: float = 0.1  # Cumulative Layout Shift - good
    cls_needs_improvement: float = 0.25  # CLS - needs improvement

    fcp_good: float = 1.8  # First Contentful Paint (seconds) - good
    fcp_needs_improvement: float = 3.0  # FCP - needs improvement

    load_time_good: float = 2.0  # Total load time (seconds) - good
    load_time_needs_improvement: float = 4.0  # Load time - needs improvement


class PerformanceMonitor:
    """
    Monitor performance metrics using Playwright.

    Collects Core Web Vitals and other performance metrics.
    """

    def __init__(self, thresholds: PerformanceThresholds | None = None):
        """
        Initialize performance monitor.

        Args:
            thresholds: Performance thresholds (uses defaults if None)
        """
        self.thresholds = thresholds or PerformanceThresholds()
        self.start_time: float | None = None
        self.metrics: PerformanceMetrics | None = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.metrics = PerformanceMetrics()

    def collect_metrics(
        self,
        network_requests: list[dict[str, Any]],
        console_messages: list[dict[str, Any]] | None = None,
    ) -> PerformanceMetrics:
        """
        Collect performance metrics from network requests.

        Args:
            network_requests: List of network requests from Playwright
            console_messages: Optional console messages for additional metrics

        Returns:
            PerformanceMetrics with collected data
        """
        if self.metrics is None:
            self.metrics = PerformanceMetrics()

        # Calculate load time
        if self.start_time:
            self.metrics.load_time = time.time() - self.start_time

        # Analyze network requests
        self.metrics.network_requests = len(network_requests)
        self.metrics.failed_requests = sum(
            1 for req in network_requests if req.get("status", 200) >= 400
        )

        # Extract timing information from requests
        if network_requests:
            # Find main document request
            main_doc = next(
                (
                    req
                    for req in network_requests
                    if req.get("type") == "document" or req.get("url", "").endswith(".html")
                ),
                None,
            )

            if main_doc:
                timing = main_doc.get("timing", {})
                if isinstance(timing, dict):
                    # Calculate FCP (simplified - would need actual paint timing)
                    if "responseStart" in timing and "requestStart" in timing:
                        self.metrics.fcp = (
                            timing.get("responseStart", 0) - timing.get("requestStart", 0)
                        ) / 1000.0

                    # Calculate DOMContentLoaded
                    if "domContentLoadedEventEnd" in timing:
                        self.metrics.dom_content_loaded = (
                            timing.get("domContentLoadedEventEnd", 0) / 1000.0
                        )

        # Extract Core Web Vitals from console messages if available
        if console_messages:
            for msg in console_messages:
                text = msg.get("text", "")
                # Look for performance marks (if page uses Performance API)
                if "LCP" in text:
                    # Extract LCP value (simplified)
                    try:
                        lcp_match = text.split("LCP:")[1].split()[0]
                        self.metrics.lcp = float(lcp_match)
                    except (IndexError, ValueError):
                        pass

        # If metrics not available from network/console, use defaults based on load time
        if self.metrics.lcp is None and self.metrics.load_time:
            # Estimate LCP as 60% of load time (simplified)
            self.metrics.lcp = self.metrics.load_time * 0.6

        if self.metrics.fcp is None and self.metrics.load_time:
            # Estimate FCP as 40% of load time (simplified)
            self.metrics.fcp = self.metrics.load_time * 0.4

        return self.metrics

    def evaluate_performance(self, metrics: PerformanceMetrics) -> dict[str, Any]:
        """
        Evaluate performance metrics against thresholds.

        Args:
            metrics: PerformanceMetrics to evaluate

        Returns:
            Dictionary with evaluation results
        """
        results = {
            "overall_score": 0.0,
            "lcp_status": "unknown",
            "fid_status": "unknown",
            "cls_status": "unknown",
            "fcp_status": "unknown",
            "load_time_status": "unknown",
            "issues": [],
            "recommendations": [],
        }

        scores = []

        # Evaluate LCP
        if metrics.lcp is not None:
            if metrics.lcp <= self.thresholds.lcp_good:
                results["lcp_status"] = "good"
                scores.append(100)
            elif metrics.lcp <= self.thresholds.lcp_needs_improvement:
                results["lcp_status"] = "needs_improvement"
                scores.append(70)
                results["issues"].append(
                    f"LCP ({metrics.lcp:.2f}s) needs improvement (target: <{self.thresholds.lcp_good}s)"
                )
                results["recommendations"].append(
                    "Optimize Largest Contentful Paint: reduce server response time, "
                    "optimize images, preload key resources"
                )
            else:
                results["lcp_status"] = "poor"
                scores.append(40)
                results["issues"].append(
                    f"LCP ({metrics.lcp:.2f}s) is poor (target: <{self.thresholds.lcp_good}s)"
                )
                results["recommendations"].append(
                    "Urgently optimize LCP: use CDN, optimize images, reduce render-blocking resources"
                )

        # Evaluate FID (if available)
        if metrics.fid is not None:
            if metrics.fid <= self.thresholds.fid_good:
                results["fid_status"] = "good"
                scores.append(100)
            elif metrics.fid <= self.thresholds.fid_needs_improvement:
                results["fid_status"] = "needs_improvement"
                scores.append(70)
                results["issues"].append(
                    f"FID ({metrics.fid:.1f}ms) needs improvement (target: <{self.thresholds.fid_good}ms)"
                )
                results["recommendations"].append(
                    "Optimize First Input Delay: reduce JavaScript execution time, "
                    "break up long tasks, use web workers"
                )
            else:
                results["fid_status"] = "poor"
                scores.append(40)

        # Evaluate CLS (if available)
        if metrics.cls is not None:
            if metrics.cls <= self.thresholds.cls_good:
                results["cls_status"] = "good"
                scores.append(100)
            elif metrics.cls <= self.thresholds.cls_needs_improvement:
                results["cls_status"] = "needs_improvement"
                scores.append(70)
                results["issues"].append(
                    f"CLS ({metrics.cls:.3f}) needs improvement (target: <{self.thresholds.cls_good})"
                )
                results["recommendations"].append(
                    "Optimize Cumulative Layout Shift: set size attributes on images/videos, "
                    "avoid inserting content above existing content"
                )
            else:
                results["cls_status"] = "poor"
                scores.append(40)

        # Evaluate FCP
        if metrics.fcp is not None:
            if metrics.fcp <= self.thresholds.fcp_good:
                results["fcp_status"] = "good"
                scores.append(100)
            elif metrics.fcp <= self.thresholds.fcp_needs_improvement:
                results["fcp_status"] = "needs_improvement"
                scores.append(70)
            else:
                results["fcp_status"] = "poor"
                scores.append(40)

        # Evaluate Load Time
        if metrics.load_time is not None:
            if metrics.load_time <= self.thresholds.load_time_good:
                results["load_time_status"] = "good"
                scores.append(100)
            elif metrics.load_time <= self.thresholds.load_time_needs_improvement:
                results["load_time_status"] = "needs_improvement"
                scores.append(70)
                results["issues"].append(
                    f"Load time ({metrics.load_time:.2f}s) needs improvement (target: <{self.thresholds.load_time_good}s)"
                )
            else:
                results["load_time_status"] = "poor"
                scores.append(40)

        # Calculate overall score
        if scores:
            results["overall_score"] = sum(scores) / len(scores)
        else:
            results["overall_score"] = 0.0

        return results

    def generate_test_assertions(
        self, metrics: PerformanceMetrics, thresholds: PerformanceThresholds | None = None
    ) -> list[str]:
        """
        Generate test assertions from performance metrics.

        Args:
            metrics: PerformanceMetrics to generate assertions for
            thresholds: Optional custom thresholds

        Returns:
            List of test assertion code strings
        """
        thresholds = thresholds or self.thresholds
        assertions = []

        # LCP assertion
        if metrics.lcp is not None:
            assertions.append(
                f"assert lcp <= {thresholds.lcp_good}, "
                f"'LCP {metrics.lcp:.2f}s exceeds good threshold {thresholds.lcp_good}s'"
            )

        # FID assertion
        if metrics.fid is not None:
            assertions.append(
                f"assert fid <= {thresholds.fid_good}, "
                f"'FID {metrics.fid:.1f}ms exceeds good threshold {thresholds.fid_good}ms'"
            )

        # CLS assertion
        if metrics.cls is not None:
            assertions.append(
                f"assert cls <= {thresholds.cls_good}, "
                f"'CLS {metrics.cls:.3f} exceeds good threshold {thresholds.cls_good}'"
            )

        # FCP assertion
        if metrics.fcp is not None:
            assertions.append(
                f"assert fcp <= {thresholds.fcp_good}, "
                f"'FCP {metrics.fcp:.2f}s exceeds good threshold {thresholds.fcp_good}s'"
            )

        # Load time assertion
        if metrics.load_time is not None:
            assertions.append(
                f"assert load_time <= {thresholds.load_time_good}, "
                f"'Load time {metrics.load_time:.2f}s exceeds good threshold {thresholds.load_time_good}s'"
            )

        # Network requests assertion
        if metrics.network_requests > 0:
            assertions.append(
                f"assert failed_requests == 0, "
                f"'Found {metrics.failed_requests} failed network requests'"
            )

        return assertions
