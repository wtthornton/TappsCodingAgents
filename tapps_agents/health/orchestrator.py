"""
Health Check Orchestrator.

Coordinates execution of all health checks and aggregates results.
"""

from __future__ import annotations

import concurrent.futures
import logging
from pathlib import Path
from typing import Any

from .base import HealthCheckResult
from .collector import HealthMetricsCollector
from .registry import HealthCheckRegistry

logger = logging.getLogger(__name__)


class HealthOrchestrator:
    """Orchestrates health check execution and aggregation."""

    def __init__(
        self,
        registry: HealthCheckRegistry | None = None,
        metrics_collector: HealthMetricsCollector | None = None,
        project_root: Path | None = None,
    ):
        """
        Initialize health orchestrator.

        Args:
            registry: Health check registry (creates default if None)
            metrics_collector: Metrics collector (creates default if None)
            project_root: Project root directory
        """
        self.registry = registry or HealthCheckRegistry()
        self.metrics_collector = metrics_collector or HealthMetricsCollector(
            project_root=project_root
        )
        self.project_root = project_root or Path.cwd()

    def run_all_checks(
        self, check_names: list[str] | None = None, save_metrics: bool = True
    ) -> dict[str, HealthCheckResult]:
        """
        Run all health checks (or specified subset).

        Args:
            check_names: Optional list of check names to run. If None, runs all.
            save_metrics: Whether to save results to metrics storage

        Returns:
            Dictionary mapping check names to HealthCheckResult instances
        """
        results = self.registry.run_all(check_names)

        # Save metrics if requested
        if save_metrics:
            for result in results.values():
                if result:
                    self.metrics_collector.record_health_check_result(result)

        return results

    def run_checks_parallel(
        self, check_names: list[str] | None = None, max_workers: int = 4
    ) -> dict[str, HealthCheckResult]:
        """
        Run health checks in parallel where possible.

        Args:
            check_names: Optional list of check names to run
            max_workers: Maximum number of parallel workers

        Returns:
            Dictionary mapping check names to HealthCheckResult instances
        """
        if check_names is None:
            check_names = self.registry.list_names()

        # Build dependency graph
        dependency_graph: dict[str, set[str]] = {}
        independent_checks: list[str] = []
        dependent_checks: list[str] = []

        for name in check_names:
            check = self.registry.get(name)
            if check:
                deps = check.get_dependencies()
                dependency_graph[name] = set(deps)
                if not deps:
                    independent_checks.append(name)
                else:
                    dependent_checks.append(name)

        results: dict[str, HealthCheckResult] = {}

        # Run independent checks in parallel
        if independent_checks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_check = {
                    executor.submit(self.registry.run, name): name for name in independent_checks
                }
                for future in concurrent.futures.as_completed(future_to_check):
                    check_name = future_to_check[future]
                    try:
                        result = future.result()
                        if result:
                            results[check_name] = result
                    except Exception as e:
                        logger.error(f"Error running check {check_name}: {e}", exc_info=True)
                        results[check_name] = HealthCheckResult(
                            name=check_name,
                            status="unhealthy",
                            score=0.0,
                            message=f"Check failed with error: {e}",
                            details={"error": str(e)},
                        )

        # Run dependent checks sequentially (respecting dependencies)
        execution_order = self.registry._topological_sort(dependent_checks)
        for name in execution_order:
            if name not in results:
                result = self.registry.run(name)
                if result:
                    results[name] = result

        # Save metrics
        for result in results.values():
            if result:
                self.metrics_collector.record_health_check_result(result)

        return results

    def get_overall_health(self, results: dict[str, HealthCheckResult] | None = None) -> dict[str, Any]:
        """
        Calculate overall health status from check results.

        Args:
            results: Optional check results (runs all checks if None)

        Returns:
            Dictionary with overall health information
        """
        if results is None:
            results = self.run_all_checks(save_metrics=True)

        if not results:
            return {
                "status": "unknown",
                "score": 0.0,
                "message": "No health checks available",
                "checks_count": 0,
            }

        # Calculate weighted average score
        # Critical checks (environment, execution) have higher weight
        critical_checks = {"environment", "execution"}
        total_weight = 0.0
        weighted_score = 0.0

        status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}

        for name, result in results.items():
            if not result:
                continue

            weight = 2.0 if name in critical_checks else 1.0
            total_weight += weight
            weighted_score += result.score * weight

            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine overall status
        if status_counts["unhealthy"] > 0:
            overall_status = "unhealthy"
        elif status_counts["degraded"] > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Build remediation list (prioritized)
        all_remediations: list[str] = []
        for name, result in results.items():
            if result and result.remediation:
                if isinstance(result.remediation, list):
                    all_remediations.extend(result.remediation)
                elif isinstance(result.remediation, str):
                    all_remediations.append(result.remediation)

        # Deduplicate and prioritize
        unique_remediations = []
        seen = set()
        for rem in all_remediations:
            rem_lower = rem.lower()
            if rem_lower not in seen:
                seen.add(rem_lower)
                unique_remediations.append(rem)

        # Prioritize: unhealthy checks first, then degraded
        prioritized_remediations = []
        for name, result in results.items():
            if result and result.remediation and result.status == "unhealthy":
                if isinstance(result.remediation, list):
                    prioritized_remediations.extend(result.remediation)
                else:
                    prioritized_remediations.append(result.remediation)

        for name, result in results.items():
            if result and result.remediation and result.status == "degraded":
                if isinstance(result.remediation, list):
                    prioritized_remediations.extend(result.remediation)
                else:
                    prioritized_remediations.append(result.remediation)

        # Add remaining unique remediations
        for rem in unique_remediations:
            if rem not in prioritized_remediations:
                prioritized_remediations.append(rem)

        return {
            "status": overall_status,
            "score": overall_score,
            "message": f"Overall health: {overall_status} ({overall_score:.1f}/100)",
            "checks_count": len(results),
            "status_counts": status_counts,
            "checks": {
                name: {
                    "status": result.status,
                    "score": result.score,
                    "message": result.message,
                }
                for name, result in results.items()
                if result
            },
            "remediation": prioritized_remediations[:5],  # Top 5 remediation actions
        }

