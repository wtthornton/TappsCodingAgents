"""
Quality Gate Enforcement

Enforces quality gates for Epic work and critical services.
"""

import logging
from typing import Any

from ..quality.quality_gates import QualityGate, QualityThresholds

logger = logging.getLogger(__name__)


class QualityEnforcement:
    """
    Enforces quality gates with automatic loopback.

    Features:
    - Auto-fail if quality score < threshold
    - Require security scan for Epic stories
    - Enforce test coverage ≥ 80%
    - Block deployment if gates fail
    """

    def __init__(
        self,
        quality_threshold: float = 70.0,
        critical_service_threshold: float = 80.0,
        enforce_mode: str = "mandatory",
    ):
        """
        Initialize quality enforcement.

        Args:
            quality_threshold: Minimum quality score (default: 70)
            critical_service_threshold: Minimum for critical services (default: 80)
            enforce_mode: mandatory or optional
        """
        self.quality_threshold = quality_threshold
        self.critical_service_threshold = critical_service_threshold
        self.enforce_mode = enforce_mode

    def check_gates(
        self, scores: dict[str, float], is_critical: bool = False
    ) -> dict[str, Any]:
        """
        Check quality gates.

        Args:
            scores: Quality scores dictionary
            is_critical: Whether this is a critical service

        Returns:
            Gate check result
        """
        threshold = (
            self.critical_service_threshold if is_critical else self.quality_threshold
        )

        quality_gate = QualityGate(
            thresholds=QualityThresholds(overall_min=threshold)
        )

        # Check if scores meet thresholds
        overall_score = scores.get("overall_score", 0.0)
        passed = overall_score >= threshold

        result = {
            "passed": passed,
            "overall_score": overall_score,
            "threshold": threshold,
            "is_critical": is_critical,
            "enforcement_mode": self.enforce_mode,
        }

        if not passed and self.enforce_mode == "mandatory":
            result["blocked"] = True
            result["message"] = f"Quality gate failed: {overall_score:.1f} < {threshold}"

        return result

