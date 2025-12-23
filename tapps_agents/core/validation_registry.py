"""
Validation registry for pluggable validators.

Auto-detects validators based on project profile and loads them.
"""

import logging
from pathlib import Path
from typing import Any

from .evaluation_base import BaseValidator
from .project_profile import ProjectProfile

logger = logging.getLogger(__name__)


class ValidationRegistry:
    """
    Registry for project-specific validators.
    
    Auto-detects validators based on project profile and loads them.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize validation registry.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.validators: dict[str, BaseValidator] = {}
        self.project_profile: ProjectProfile | None = None

    def load_project_profile(self, profile_path: Path | None = None) -> None:
        """
        Load project profile for validator detection.
        
        Args:
            profile_path: Optional path to project-profile.yaml
        """
        if profile_path is None:
            profile_path = self.project_root / ".tapps-agents" / "project-profile.yaml"
        
        if profile_path.exists():
            try:
                self.project_profile = ProjectProfile.load(profile_path)
            except Exception as e:
                logger.warning(f"Failed to load project profile: {e}")
        else:
            # Create default profile
            self.project_profile = ProjectProfile()

    def detect_validators(self) -> list[str]:
        """
        Detect applicable validators from project profile.
        
        Returns:
            List of validator identifiers
        """
        if self.project_profile is None:
            self.load_project_profile()
        
        detected: list[str] = []
        
        # Detect by language
        languages = self.project_profile.languages if self.project_profile else []
        if "python" in languages:
            detected.append("python")
        if "typescript" in languages or "javascript" in languages:
            detected.append("typescript")
        
        # Detect by frameworks/tools
        frameworks = self.project_profile.frameworks if self.project_profile else []
        if any("docker" in f.lower() for f in frameworks):
            detected.append("docker")
        if any("ci" in f.lower() or "github" in f.lower() for f in frameworks):
            detected.append("ci")
        
        return detected

    def register_validator(self, validator: BaseValidator) -> None:
        """
        Register a validator.
        
        Args:
            validator: Validator instance
        """
        self.validators[validator.get_name()] = validator
        logger.debug(f"Registered validator: {validator.get_name()}")

    def get_validators(self, project_profile: dict[str, Any] | None = None) -> list[BaseValidator]:
        """
        Get validators applicable to project.
        
        Args:
            project_profile: Optional project profile dict
            
        Returns:
            List of applicable validators
        """
        if not project_profile and self.project_profile:
            project_profile = self.project_profile.to_dict()
        
        applicable = []
        for validator in self.validators.values():
            if validator.is_applicable(project_profile or {}):
                applicable.append(validator)
        
        return applicable

    def validate(
        self, target: Path | str, project_profile: dict[str, Any] | None = None
    ) -> list[Any]:
        """
        Run all applicable validators on target.
        
        Args:
            target: File path or identifier to validate
            project_profile: Optional project profile
            
        Returns:
            List of ValidationResult objects
        """
        validators = self.get_validators(project_profile)
        results = []
        
        for validator in validators:
            try:
                result = validator.validate(target, project_profile)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error in validator {validator.get_name()}: {e}")
        
        return results

