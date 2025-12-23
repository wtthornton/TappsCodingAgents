"""
Base classes for evaluation and validation in Tier 1 Enhancement.

Provides abstract base classes for evaluators and validators.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evaluation_models import IssueManifest


@dataclass
class ValidationResult:
    """Result from a validation check."""

    passed: bool
    issues: IssueManifest
    metadata: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        """Allow ValidationResult to be used in boolean context."""
        return self.passed

    def has_issues(self) -> bool:
        """Check if validation found any issues."""
        return len(self.issues.issues) > 0


class BaseEvaluator(ABC):
    """
    Abstract base class for evaluators.
    
    Evaluators perform multi-dimensional evaluation beyond simple scoring.
    """

    @abstractmethod
    def evaluate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> IssueManifest:
        """
        Evaluate a target and return issues found.
        
        Args:
            target: File path or identifier to evaluate
            context: Optional context for evaluation
            
        Returns:
            IssueManifest with found issues
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this evaluator."""
        pass

    @abstractmethod
    def is_applicable(self, target: Path | str) -> bool:
        """
        Check if this evaluator is applicable to the target.
        
        Args:
            target: File path or identifier
            
        Returns:
            True if evaluator can evaluate this target
        """
        pass


class BaseValidator(ABC):
    """
    Abstract base class for pluggable validators.
    
    Validators perform project-specific validation checks.
    """

    @abstractmethod
    def validate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate a target and return validation result.
        
        Args:
            target: File path or identifier to validate
            context: Optional context for validation
            
        Returns:
            ValidationResult with pass/fail status and issues
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this validator."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get description of what this validator checks."""
        pass

    @abstractmethod
    def is_applicable(self, project_profile: dict[str, Any]) -> bool:
        """
        Check if this validator is applicable to the project.
        
        Args:
            project_profile: Project profile from project-profile.yaml
            
        Returns:
            True if validator should run for this project
        """
        pass

