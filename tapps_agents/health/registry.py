"""
Health Check Registry.

Manages registration and discovery of health checks.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class HealthCheckRegistry:
    """Registry for health checks."""

    def __init__(self):
        """Initialize health check registry."""
        self._checks: dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck) -> None:
        """
        Register a health check.

        Args:
            check: Health check instance to register

        Raises:
            ValueError: If check with same name already registered
        """
        if check.name in self._checks:
            raise ValueError(f"Health check '{check.name}' is already registered")

        self._checks[check.name] = check
        logger.debug(f"Registered health check: {check.name}")

    def get(self, name: str) -> HealthCheck | None:
        """
        Get a health check by name.

        Args:
            name: Name of the health check

        Returns:
            HealthCheck instance or None if not found
        """
        return self._checks.get(name)

    def get_all(self) -> dict[str, HealthCheck]:
        """
        Get all registered health checks.

        Returns:
            Dictionary mapping check names to HealthCheck instances
        """
        return self._checks.copy()

    def list_names(self) -> list[str]:
        """
        List all registered health check names.

        Returns:
            List of health check names
        """
        return list(self._checks.keys())

    def run(self, name: str) -> HealthCheckResult | None:
        """
        Run a specific health check.

        Args:
            name: Name of the health check to run

        Returns:
            HealthCheckResult or None if check not found
        """
        check = self.get(name)
        if not check:
            logger.warning(f"Health check '{name}' not found")
            return None

        try:
            return check.run()
        except Exception as e:
            logger.error(f"Error running health check '{name}': {e}", exc_info=True)
            return HealthCheckResult(
                name=name,
                status="unhealthy",
                score=0.0,
                message=f"Health check failed with error: {e}",
                details={"error": str(e)},
            )

    def run_all(self, check_names: list[str] | None = None) -> dict[str, HealthCheckResult]:
        """
        Run all registered health checks (or specified subset).

        Args:
            check_names: Optional list of check names to run. If None, runs all.

        Returns:
            Dictionary mapping check names to HealthCheckResult instances
        """
        if check_names is None:
            check_names = self.list_names()

        results: dict[str, HealthCheckResult] = {}

        # Build dependency graph and determine execution order
        execution_order = self._topological_sort(check_names)

        for name in execution_order:
            if name not in check_names:
                continue
            results[name] = self.run(name)

        return results

    def _topological_sort(self, check_names: list[str]) -> list[str]:
        """
        Topologically sort health checks based on dependencies.

        Args:
            check_names: List of check names to sort

        Returns:
            Sorted list of check names respecting dependencies
        """
        # Build dependency graph
        graph: dict[str, set[str]] = {}
        for name in check_names:
            check = self.get(name)
            if check:
                graph[name] = set(check.get_dependencies())

        # Topological sort using Kahn's algorithm
        in_degree: dict[str, int] = {name: 0 for name in check_names}
        for name in check_names:
            for dep in graph.get(name, set()):
                if dep in in_degree:
                    in_degree[name] += 1

        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for dependent nodes
            for name in check_names:
                if node in graph.get(name, set()):
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        # Add any remaining nodes (shouldn't happen if no cycles)
        for name in check_names:
            if name not in result:
                result.append(name)

        return result

