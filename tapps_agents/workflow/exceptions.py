"""
Custom exceptions for workflow observability features.

Extends the base TappsAgentsError hierarchy for observability-specific errors.
"""

from ..core.exceptions import TappsAgentsError, WorkflowError, WorkflowNotFoundError


class ObservabilityError(TappsAgentsError):
    """Base exception for observability-related errors."""

    pass


class GraphGenerationError(ObservabilityError):
    """Raised when execution graph generation fails."""

    pass


class EmptyWorkflowError(ObservabilityError):
    """Raised when workflow has no steps to generate graph from."""

    pass


class InvalidTraceError(ObservabilityError):
    """Raised when execution trace has invalid structure."""

    pass


class DashboardGenerationError(ObservabilityError):
    """Raised when observability dashboard generation fails."""

    pass


class OpenTelemetryExportError(ObservabilityError):
    """Raised when OpenTelemetry trace export fails."""

    pass
