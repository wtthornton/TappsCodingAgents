"""
Base Gate Interface

Defines the abstract base class for all pluggable gates.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class GateSeverity(Enum):
    """Gate severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class GateResult:
    """Result of gate evaluation."""

    passed: bool
    severity: GateSeverity
    message: str
    details: dict[str, Any] | None = None
    remediation: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "remediation": self.remediation,
            "metadata": self.metadata,
        }


class BaseGate(ABC):
    """
    Abstract base class for all gates.
    
    All gates must implement the evaluate() method which takes
    a context dictionary and returns a GateResult.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize gate.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Evaluate gate against context.

        Args:
            context: Context dictionary with workflow/step information

        Returns:
            GateResult indicating if gate passed
        """
        pass

    def get_name(self) -> str:
        """Get gate name."""
        return self.name

    def get_config(self) -> dict[str, Any]:
        """Get gate configuration."""
        return self.config
