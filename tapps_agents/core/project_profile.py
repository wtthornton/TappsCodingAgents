"""
Project Profile System

Automatically detects and stores project characteristics (deployment type, tenancy,
user scale, compliance, security level) to provide context-aware expert guidance.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import yaml

from .config import load_config
from ..workflow.detector import ProjectDetector


@dataclass
class ComplianceRequirement:
    """A compliance requirement with confidence and indicators."""
    name: str
    confidence: float
    indicators: List[str] = field(default_factory=list)


@dataclass
class ProjectProfile:
    """
    Project profile with detected characteristics.
    
    All fields are optional to support progressive disclosure.
    """
    deployment_type: Optional[str] = None  # local, cloud, enterprise
    deployment_type_confidence: float = 0.0
    deployment_type_indicators: List[str] = field(default_factory=list)
    
    tenancy: Optional[str] = None  # single-tenant, multi-tenant
    tenancy_confidence: float = 0.0
    tenancy_indicators: List[str] = field(default_factory=list)
    
    user_scale: Optional[str] = None  # single-user, small-team, department, enterprise
    user_scale_confidence: float = 0.0
    user_scale_indicators: List[str] = field(default_factory=list)
    
    compliance_requirements: List[ComplianceRequirement] = field(default_factory=list)
    
    security_level: Optional[str] = None  # basic, standard, high, critical
    security_level_confidence: float = 0.0
    security_level_indicators: List[str] = field(default_factory=list)
    
    detected_at: Optional[str] = None  # ISO timestamp
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary for YAML serialization."""
        data = asdict(self)
        # Convert ComplianceRequirement objects to dicts
        data['compliance_requirements'] = [
            asdict(req) for req in self.compliance_requirements
        ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectProfile':
        """Create profile from dictionary (YAML deserialization)."""
        # Convert compliance requirements back to objects
        compliance_data = data.pop('compliance_requirements', [])
        compliance_reqs = [
            ComplianceRequirement(**req) if isinstance(req, dict) else req
            for req in compliance_data
        ]
        
        profile = cls(**{k: v for k, v in data.items() if k != 'compliance_requirements'})
        profile.compliance_requirements = compliance_reqs
        return profile


class ProjectProfileDetector:
    """
    Detects project profile characteristics using ProjectDetector.
    
    Orchestrates detection methods and aggregates results into ProjectProfile.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize profile detector.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        self.detector = ProjectDetector(project_root=self.project_root)
    
    def detect(self) -> ProjectProfile:
        """
        Detect all project profile characteristics.
        
        Returns:
            ProjectProfile with detected characteristics
        """
        profile = ProjectProfile()
        profile.detected_at = datetime.utcnow().isoformat() + "Z"
        
        # Detect deployment type
        deployment_type, deployment_confidence, deployment_indicators = self.detector.detect_deployment_type()
        if deployment_type:
            profile.deployment_type = deployment_type
            profile.deployment_type_confidence = deployment_confidence
            profile.deployment_type_indicators = deployment_indicators
        
        # Detect compliance requirements
        compliance_data = self.detector.detect_compliance_requirements()
        profile.compliance_requirements = [
            ComplianceRequirement(name=name, confidence=conf, indicators=indicators)
            for name, conf, indicators in compliance_data
        ]
        
        # Detect security level
        security_level, security_confidence, security_indicators = self.detector.detect_security_level()
        if security_level:
            profile.security_level = security_level
            profile.security_level_confidence = security_confidence
            profile.security_level_indicators = security_indicators
        
        return profile


def save_project_profile(profile: ProjectProfile, project_root: Optional[Path] = None) -> Path:
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
    profile_dir.mkdir(exist_ok=True)
    
    profile_file = profile_dir / "project-profile.yaml"
    
    # Convert to dict and save as YAML
    data = profile.to_dict()
    
    with open(profile_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    return profile_file


def load_project_profile(project_root: Optional[Path] = None) -> Optional[ProjectProfile]:
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
        with open(profile_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return None
        
        return ProjectProfile.from_dict(data)
    except Exception:
        # Fail gracefully - profile is optional
        return None


def detect_and_save_profile(project_root: Optional[Path] = None) -> ProjectProfile:
    """
    Detect project profile and save it.
    
    Convenience function that combines detection and saving.
    
    Args:
        project_root: Root directory (defaults to current directory)
        
    Returns:
        Detected ProjectProfile
    """
    detector = ProjectProfileDetector(project_root=project_root)
    profile = detector.detect()
    save_project_profile(profile, project_root=project_root)
    return profile

