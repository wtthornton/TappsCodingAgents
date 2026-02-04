"""
Policy loader for .tapps-agents/policies.yaml (plan 3.3).

Machine-readable policies: branch protection, quality thresholds, licensing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class BranchProtectionPolicy:
    require_review_before_merge: bool = False
    no_direct_push_main: bool = True


@dataclass
class QualityPolicy:
    """Lower bounds for quality gates (same scale as QualityThresholds: 0-10)."""

    min_overall: float = 7.0  # 0-10, applied as max(threshold.overall_min, this)
    min_security: float = 6.5


@dataclass
class LicensingPolicy:
    allowed_licenses: list[str] = field(default_factory=list)
    reject_licenses: list[str] = field(default_factory=list)


@dataclass
class Policies:
    """Loaded policies from .tapps-agents/policies.yaml."""

    branch_protection: BranchProtectionPolicy = field(default_factory=BranchProtectionPolicy)
    quality: QualityPolicy = field(default_factory=QualityPolicy)
    licensing: LicensingPolicy = field(default_factory=LicensingPolicy)


def load_policies(project_root: Path | None = None) -> Policies:
    """
    Load .tapps-agents/policies.yaml. Returns defaults if file is missing.

    Schema:
      branch_protection: { require_review_before_merge: bool, no_direct_push_main: bool }
      quality: { min_overall: float, min_security: float }
      licensing: { allowed_licenses: list[str], reject_licenses: list[str] }

    Args:
        project_root: Project root (default: cwd)

    Returns:
        Policies instance
    """
    root = Path(project_root or Path.cwd())
    path = root / ".tapps-agents" / "policies.yaml"
    if not path.exists():
        return Policies()

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Could not load policies.yaml: %s. Using defaults.", e)
        return Policies()

    def _get(d: dict, key: str, default: dict | None = None) -> dict:
        v = (d or {}).get(key)
        return v if isinstance(v, dict) else (default or {})

    bp = _get(data, "branch_protection", {})
    branch_protection = BranchProtectionPolicy(
        require_review_before_merge=bool(bp.get("require_review_before_merge", False)),
        no_direct_push_main=bool(bp.get("no_direct_push_main", True)),
    )

    q = _get(data, "quality", {})
    quality = QualityPolicy(
        min_overall=float(q.get("min_overall", 7.0)),
        min_security=float(q.get("min_security", 6.5)),
    )

    lic = _get(data, "licensing", {})
    allowed = lic.get("allowed_licenses")
    reject = lic.get("reject_licenses")
    licensing = LicensingPolicy(
        allowed_licenses=list(allowed) if isinstance(allowed, list) else [],
        reject_licenses=list(reject) if isinstance(reject, list) else [],
    )

    return Policies(
        branch_protection=branch_protection,
        quality=quality,
        licensing=licensing,
    )


def apply_quality_policy(
    thresholds: QualityThresholds,
    project_root: Path | None = None,
) -> QualityThresholds:
    """
    Apply policies.quality as lower bounds: thresholds never go below policy minimums.

    Use in gate evaluation so that .tapps-agents/policies.yaml can enforce
    minimum quality and security across workflows.

    Args:
        thresholds: Current QualityThresholds from step/config
        project_root: Project root to load policies

    Returns:
        New QualityThresholds with policy lower bounds applied
    """
    from ..quality.quality_gates import QualityThresholds

    p = load_policies(project_root)
    if not p or not p.quality:
        return thresholds
    return QualityThresholds(
        overall_min=max(thresholds.overall_min, p.quality.min_overall),
        security_min=max(thresholds.security_min, p.quality.min_security),
        maintainability_min=thresholds.maintainability_min,
        complexity_max=thresholds.complexity_max,
        test_coverage_min=thresholds.test_coverage_min,
        performance_min=thresholds.performance_min,
    )
