"""
Pluggable Gates System

Provides pluggable gate interface for security, policy, and approval gates.
"""

from .base import BaseGate, GateResult, GateSeverity
from .exceptions import (
    CircularGateDependencyError,
    GateConfigurationError,
    GateEvaluationError,
    GateNotFoundError,
    GateTimeoutError,
    MissingContextError,
)
from .security_gate import SecurityGate
from .policy_gate import PolicyGate
from .approval_gate import ApprovalGate
from .registry import GateRegistry, get_gate_registry

__all__ = [
    "BaseGate",
    "GateResult",
    "GateSeverity",
    "SecurityGate",
    "PolicyGate",
    "ApprovalGate",
    "GateRegistry",
    "get_gate_registry",
    # Exceptions
    "GateEvaluationError",
    "GateConfigurationError",
    "MissingContextError",
    "GateTimeoutError",
    "GateNotFoundError",
    "CircularGateDependencyError",
]
