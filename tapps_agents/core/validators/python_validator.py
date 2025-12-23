"""
Python-specific validator.
"""

import logging
from pathlib import Path
from typing import Any

from ..evaluation_base import BaseValidator, ValidationResult
from ..evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class PythonValidator(BaseValidator):
    """Validator for Python-specific checks."""

    def get_name(self) -> str:
        """Get validator name."""
        return "python"

    def get_description(self) -> str:
        """Get validator description."""
        return "Validates Python-specific coding standards and best practices"

    def is_applicable(self, project_profile: dict[str, Any]) -> bool:
        """Check if validator is applicable to project."""
        languages = project_profile.get("languages", [])
        return "python" in languages

    def validate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate Python file.
        
        Args:
            target: File path to validate
            context: Optional context
            
        Returns:
            ValidationResult
        """
        target_path = Path(target) if isinstance(target, str) else target
        issues = IssueManifest()
        
        if not target_path.exists() or target_path.suffix != ".py":
            return ValidationResult(passed=True, issues=issues)
        
        try:
            code = target_path.read_text(encoding="utf-8")
            
            # Check for Python-specific issues
            # Missing docstrings
            if "def " in code and not '"""' in code[:500] and not "'''" in code[:500]:
                issue = Issue(
                    id=f"python_missing_docstring_{target_path.name}",
                    severity=IssueSeverity.LOW,
                    category=IssueCategory.DOCUMENTATION,
                    evidence="File appears to have functions but no module docstring",
                    repro=f"Review {target_path} for docstrings",
                    suggested_fix="Add module and function docstrings",
                    owner_step="implementation",
                    file_path=str(target_path),
                )
                issues.add_issue(issue)
            
            # Check for common Python issues
            if "import *" in code:
                issue = Issue(
                    id=f"python_wildcard_import_{target_path.name}",
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.MAINTAINABILITY,
                    evidence="Wildcard import (import *) found",
                    repro=f"Check imports in {target_path}",
                    suggested_fix="Replace wildcard imports with explicit imports",
                    owner_step="implementation",
                    file_path=str(target_path),
                )
                issues.add_issue(issue)
        
        except Exception as e:
            logger.warning(f"Error in Python validation: {e}")
        
        passed = len(issues.issues) == 0
        return ValidationResult(passed=passed, issues=issues)

