"""
Project Profile System - Auto-detect project characteristics for context-aware expert guidance.

This module provides automatic detection of project characteristics such as:
- Deployment type (local, cloud, enterprise)
- Tenancy (single-tenant, multi-tenant)
- User scale (single-user, small-team, department, enterprise)
- Compliance requirements (GDPR, HIPAA, PCI, SOC2)
- Security level (basic, standard, high, critical)

The profile is used to provide context-aware expert guidance.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from ..workflow.detector import ProjectDetector


@dataclass
class ComplianceRequirement:
    """A compliance requirement with confidence."""

    name: str
    confidence: float
    indicators: list[str] = field(default_factory=list)


@dataclass
class ProjectProfile:
    """
    Project profile with detected characteristics.

    All fields are optional to support progressive disclosure.
    Confidence scores indicate detection reliability.
    """

    deployment_type: str | None = None
    deployment_type_confidence: float = 0.0
    deployment_type_indicators: list[str] = field(default_factory=list)

    tenancy: str | None = None
    tenancy_confidence: float = 0.0
    tenancy_indicators: list[str] = field(default_factory=list)

    user_scale: str | None = None
    user_scale_confidence: float = 0.0
    user_scale_indicators: list[str] = field(default_factory=list)

    compliance_requirements: list[ComplianceRequirement] = field(default_factory=list)

    security_level: str | None = None
    security_level_confidence: float = 0.0
    security_level_indicators: list[str] = field(default_factory=list)

    detected_at: str | None = None

    def to_dict(self) -> dict:
        """Convert profile to dictionary for YAML serialization."""
        data = asdict(self)
        # Convert ComplianceRequirement objects to dicts
        data["compliance_requirements"] = [
            asdict(req) for req in self.compliance_requirements
        ]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> ProjectProfile:
        """Create profile from dictionary."""
        # Convert compliance requirement dicts to objects
        compliance_reqs = [
            ComplianceRequirement(**req) if isinstance(req, dict) else req
            for req in data.get("compliance_requirements", [])
        ]
        data["compliance_requirements"] = compliance_reqs
        return cls(**data)

    def format_context(self, min_confidence: float = 0.7) -> str:
        """
        Format profile as context string for expert prompts.

        Only includes high-confidence values (>= min_confidence).

        Args:
            min_confidence: Minimum confidence to include a value

        Returns:
            Formatted context string
        """
        parts = []

        if self.deployment_type and self.deployment_type_confidence >= min_confidence:
            parts.append(
                f"- Deployment: {self.deployment_type} (confidence: {self.deployment_type_confidence:.1f})"
            )

        if self.security_level and self.security_level_confidence >= min_confidence:
            parts.append(
                f"- Security Level: {self.security_level} (confidence: {self.security_level_confidence:.1f})"
            )

        if self.compliance_requirements:
            high_conf_compliance = [
                req.name
                for req in self.compliance_requirements
                if req.confidence >= min_confidence
            ]
            if high_conf_compliance:
                parts.append(f"- Compliance: {', '.join(high_conf_compliance)}")

        if self.tenancy and self.tenancy_confidence >= min_confidence:
            parts.append(
                f"- Tenancy: {self.tenancy} (confidence: {self.tenancy_confidence:.1f})"
            )

        if self.user_scale and self.user_scale_confidence >= min_confidence:
            parts.append(
                f"- User Scale: {self.user_scale} (confidence: {self.user_scale_confidence:.1f})"
            )

        if not parts:
            return ""

        return "Project Context:\n" + "\n".join(parts)


class ProjectProfileDetector:
    """
    Detects project profile characteristics.

    Wraps ProjectDetector and aggregates results into ProjectProfile.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize profile detector.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        self.detector = ProjectDetector(project_root=self.project_root)

    def detect_profile(self) -> ProjectProfile:
        """
        Detect complete project profile.

        Returns:
            ProjectProfile with all detected characteristics
        """
        profile = ProjectProfile()
        profile.detected_at = datetime.utcnow().isoformat() + "Z"

        # Detect deployment type
        deployment_type, deployment_conf, deployment_indicators = (
            self.detector.detect_deployment_type()
        )
        if deployment_type:
            profile.deployment_type = deployment_type
            profile.deployment_type_confidence = deployment_conf
            profile.deployment_type_indicators = deployment_indicators

        # Detect tenancy
        tenancy, tenancy_conf, tenancy_indicators = self.detector.detect_tenancy()
        if tenancy:
            profile.tenancy = tenancy
            profile.tenancy_confidence = tenancy_conf
            profile.tenancy_indicators = tenancy_indicators

        # Detect compliance requirements (use existing method)
        compliance_results = self.detector.detect_compliance_requirements()
        compliance_reqs = [
            ComplianceRequirement(name=name, confidence=conf, indicators=indicators)
            for name, conf, indicators in compliance_results
        ]
        profile.compliance_requirements = compliance_reqs

        # Detect security level (use existing method)
        security_level, security_conf, security_indicators = (
            self.detector.detect_security_level()
        )
        if security_level:
            profile.security_level = security_level
            profile.security_level_confidence = security_conf
            profile.security_level_indicators = security_indicators

        # Detect user scale (use existing method)
        user_scale, user_scale_conf, user_scale_indicators = (
            self.detector.detect_user_scale()
        )
        if user_scale and user_scale_conf >= 0.5:
            profile.user_scale = user_scale
            profile.user_scale_confidence = user_scale_conf
            profile.user_scale_indicators = user_scale_indicators

        return profile


def save_project_profile(
    profile: ProjectProfile, project_root: Path | None = None
) -> Path:
    """
    Save project profile to YAML file.

    Args:
        profile: ProjectProfile to save
        project_root: Root directory (defaults to current directory)

    Returns:
        Path to saved profile file
    """
    project_root = project_root or Path.cwd()
    profile_dir = project_root / ".tapps-agents"
    profile_dir.mkdir(parents=True, exist_ok=True)

    profile_file = profile_dir / "project-profile.yaml"

    with open(profile_file, "w", encoding="utf-8") as f:
        yaml.dump(profile.to_dict(), f, default_flow_style=False, sort_keys=False)

    return profile_file


def load_project_profile(
    project_root: Path | None = None,
) -> ProjectProfile | None:
    """
    Load project profile from YAML file.

    Args:
        project_root: Root directory (defaults to current directory)

    Returns:
        ProjectProfile if found, None otherwise
    """
    project_root = project_root or Path.cwd()
    profile_file = project_root / ".tapps-agents" / "project-profile.yaml"

    if not profile_file.exists():
        return None

    try:
        with open(profile_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        return ProjectProfile.from_dict(data)
    except (OSError, yaml.YAMLError, ValueError, KeyError) as e:
        # File errors, YAML parsing errors, or invalid data
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to load project profile: {e}")
        return None
