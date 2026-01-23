"""
Custom exceptions for pluggable gates system.

Extends the base TappsAgentsError hierarchy for gate-specific errors.
"""

from ...core.exceptions import TappsAgentsError


class GateEvaluationError(TappsAgentsError):
    """Base exception for gate evaluation errors."""

    pass


class GateConfigurationError(GateEvaluationError):
    """Raised when gate configuration is invalid."""

    pass


class MissingContextError(GateEvaluationError):
    """Raised when required context fields are missing for gate evaluation."""

    pass


class GateTimeoutError(GateEvaluationError):
    """Raised when gate evaluation times out."""

    pass


class GateNotFoundError(GateEvaluationError):
    """Raised when a requested gate is not found in registry."""

    pass


class CircularGateDependencyError(GateEvaluationError):
    """Raised when circular dependencies are detected in gate evaluation."""

    pass
