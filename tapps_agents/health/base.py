"""
Base Health Check Interface.

Defines the abstract base class for all health checks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    score: float  # 0-100
    message: str
    details: dict[str, Any] | None = None
    remediation: str | list[str] | None = None

    def is_healthy(self) -> bool:
        """Check if status is healthy."""
        return self.status == "healthy"

    def is_degraded(self) -> bool:
        """Check if status is degraded."""
        return self.status == "degraded"

    def is_unhealthy(self) -> bool:
        """Check if status is unhealthy."""
        return self.status == "unhealthy"


class HealthCheck(ABC):
    """
    Abstract base class for health checks.

    All health checks must implement the run() method which returns
    a HealthCheckResult.
    """

    def __init__(self, name: str, dependencies: list[str] | None = None):
        """
        Initialize health check.

        Args:
            name: Unique name for this health check
            dependencies: List of health check names that must run before this one
        """
        self.name = name
        self.dependencies = dependencies or []

    @abstractmethod
    def run(self) -> HealthCheckResult:
        """
        Run the health check.

        Returns:
            HealthCheckResult with status, score, and details
        """
        pass

    def get_dependencies(self) -> list[str]:
        """
        Get list of health check names that must run before this one.

        Returns:
            List of dependency names
        """
        return self.dependencies

