"""
Quality Assurance Module.

Epic 6: Comprehensive Quality Assurance & Testing
"""

from .coverage_analyzer import (
    CoverageAnalyzer,
    CoverageMetrics,
    CoverageReport,
)

# Pluggable gates system
from .gates import (
    ApprovalGate,
    BaseGate,
    GateRegistry,
    GateResult,
    GateSeverity,
    PolicyGate,
    SecurityGate,
    get_gate_registry,
)
from .quality_gates import (
    QualityGate,
    QualityGateResult,
    QualityThresholds,
)
from .secret_scanner import (
    SecretFinding,
    SecretScanner,
    SecretScanResult,
)

__all__ = [
    "CoverageAnalyzer",
    "CoverageMetrics",
    "CoverageReport",
    "QualityGate",
    "QualityGateResult",
    "QualityThresholds",
    "SecretFinding",
    "SecretScanResult",
    "SecretScanner",
    # Pluggable gates
    "BaseGate",
    "GateResult",
    "GateSeverity",
    "SecurityGate",
    "PolicyGate",
    "ApprovalGate",
    "GateRegistry",
    "get_gate_registry",
]
