"""
SDLC Phase Validation Helpers

Provides validators for SDLC phase validation in e2e tests.
"""

import logging
from pathlib import Path
from typing import Any

from tapps_agents.workflow.models import Artifact, WorkflowState, WorkflowStep
from tapps_agents.workflow.validation import ValidationResult, WorkflowValidator

logger = logging.getLogger(__name__)


class SDLCPhaseValidator(WorkflowValidator):
    """Validator for SDLC phase artifacts."""

    def __init__(self, project_path: Path):
        """
        Initialize SDLC phase validator.

        Args:
            project_path: Path to the project being validated
        """
        self.project_path = Path(project_path)

    def validate_requirements(
        self, artifacts: dict[str, Artifact], state: WorkflowState
    ) -> ValidationResult:
        """Validate requirements phase artifacts."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check for requirements.md artifact
        requirements_artifact = artifacts.get("requirements.md")
        if not requirements_artifact:
            errors.append("requirements.md artifact not found")
            return ValidationResult(passed=False, errors=errors, warnings=warnings)

        # Check if file exists
        requirements_path = self.project_path / requirements_artifact.path
        if not requirements_path.exists():
            errors.append(f"requirements.md file not found at {requirements_path}")
            return ValidationResult(passed=False, errors=errors, warnings=warnings)

        # Check if file is not empty
        if requirements_path.stat().st_size == 0:
            errors.append("requirements.md is empty")
            return ValidationResult(passed=False, errors=errors, warnings=warnings)

        # Check for expected content (basic validation)
        content = requirements_path.read_text(encoding="utf-8", errors="ignore").lower()
        if not content:
            warnings.append("requirements.md has no readable content")

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_architecture(
        self, artifacts: dict[str, Artifact], state: WorkflowState
    ) -> ValidationResult:
        """Validate architecture phase artifacts."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check for architecture.md artifact
        architecture_artifact = artifacts.get("architecture.md")
        if not architecture_artifact:
            warnings.append("architecture.md artifact not found (may be optional)")
            return ValidationResult(passed=True, errors=errors, warnings=warnings)

        # Check if file exists
        architecture_path = self.project_path / architecture_artifact.path
        if not architecture_path.exists():
            warnings.append(f"architecture.md file not found at {architecture_path}")
            return ValidationResult(passed=True, errors=errors, warnings=warnings)

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_implementation(
        self, artifacts: dict[str, Artifact], state: WorkflowState
    ) -> ValidationResult:
        """Validate implementation phase artifacts."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check for implementation artifacts (HTML, CSS, JS files)
        html_files = [k for k in artifacts.keys() if k.endswith(".html")]
        css_files = [k for k in artifacts.keys() if k.endswith(".css")]
        js_files = [k for k in artifacts.keys() if k.endswith(".js")]

        if not html_files and not css_files and not js_files:
            warnings.append("No implementation artifacts found (HTML, CSS, or JS files)")

        # Validate HTML files if present
        for html_file in html_files:
            html_artifact = artifacts[html_file]
            html_path = self.project_path / html_artifact.path
            if html_path.exists():
                content = html_path.read_text(encoding="utf-8", errors="ignore")
                # Basic HTML validation
                if "<html" not in content.lower() and "<!doctype" not in content.lower():
                    warnings.append(f"{html_file} may not be valid HTML")

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_quality_gate(
        self, step: WorkflowStep, scoring_result: dict[str, Any], state: WorkflowState
    ) -> ValidationResult:
        """Validate quality gate thresholds."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check if scoring result has required fields
        if not scoring_result:
            errors.append("No scoring result provided")
            return ValidationResult(passed=False, errors=errors, warnings=warnings)

        # Check thresholds (default: overall_min: 70, security_min: 7.0)
        overall_score = scoring_result.get("overall_score", 0)
        security_score = scoring_result.get("security_score", 0.0)

        overall_min = step.gate.get("overall_min", 70) if step.gate else 70
        security_min = step.gate.get("security_min", 7.0) if step.gate else 7.0

        if overall_score < overall_min:
            errors.append(
                f"Overall score {overall_score} below threshold {overall_min}"
            )

        if security_score < security_min:
            errors.append(
                f"Security score {security_score} below threshold {security_min}"
            )

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)


# Helper functions for common assertions
def assert_requirements_contain(requirements_path: Path, keywords: list[str]) -> None:
    """
    Assert that requirements.md contains expected keywords.

    Args:
        requirements_path: Path to requirements.md file
        keywords: List of keywords that should be present

    Raises:
        AssertionError: If requirements don't contain expected keywords
    """
    if not requirements_path.exists():
        raise AssertionError(f"requirements.md not found at {requirements_path}")

    content = requirements_path.read_text(encoding="utf-8", errors="ignore").lower()
    missing = [kw for kw in keywords if kw.lower() not in content]

    if missing:
        raise AssertionError(
            f"requirements.md missing expected keywords: {missing}"
        )


def assert_architecture_includes(architecture_path: Path, topics: list[str]) -> None:
    """
    Assert that architecture.md includes expected topics.

    Args:
        architecture_path: Path to architecture.md file
        topics: List of topics that should be present

    Raises:
        AssertionError: If architecture doesn't include expected topics
    """
    if not architecture_path.exists():
        raise AssertionError(f"architecture.md not found at {architecture_path}")

    content = architecture_path.read_text(encoding="utf-8", errors="ignore").lower()
    missing = [topic for topic in topics if topic.lower() not in content]

    if missing:
        raise AssertionError(
            f"architecture.md missing expected topics: {missing}"
        )


def assert_html_has_dark_theme(html_path: Path) -> None:
    """
    Assert that HTML file has dark theme CSS.

    Args:
        html_path: Path to HTML file

    Raises:
        AssertionError: If HTML doesn't have dark theme
    """
    if not html_path.exists():
        raise AssertionError(f"HTML file not found at {html_path}")

    content = html_path.read_text(encoding="utf-8", errors="ignore").lower()

    # Check for dark theme indicators
    dark_indicators = [
        "background-color: #",
        "background: #",
        "dark",
        "background-color: rgb(0",
        "background-color: rgb(1",
    ]

    has_dark = any(indicator in content for indicator in dark_indicators)

    if not has_dark:
        raise AssertionError(f"HTML file {html_path} does not appear to have dark theme")


def assert_html_has_animations(html_path: Path) -> None:
    """
    Assert that HTML file has animations.

    Args:
        html_path: Path to HTML file

    Raises:
        AssertionError: If HTML doesn't have animations
    """
    if not html_path.exists():
        raise AssertionError(f"HTML file not found at {html_path}")

    content = html_path.read_text(encoding="utf-8", errors="ignore").lower()

    # Check for animation indicators
    animation_indicators = [
        "@keyframes",
        "animation:",
        "transition:",
        "animate",
    ]

    has_animation = any(indicator in content for indicator in animation_indicators)

    if not has_animation:
        raise AssertionError(f"HTML file {html_path} does not appear to have animations")


def assert_quality_gate_passed(scoring_result: dict[str, Any], thresholds: dict[str, Any]) -> None:
    """
    Assert that quality gate passed with given thresholds.

    Args:
        scoring_result: Scoring result dictionary
        thresholds: Threshold dictionary (e.g., {"overall_min": 70, "security_min": 7.0})

    Raises:
        AssertionError: If quality gate didn't pass
    """
    overall_score = scoring_result.get("overall_score", 0)
    security_score = scoring_result.get("security_score", 0.0)

    overall_min = thresholds.get("overall_min", 70)
    security_min = thresholds.get("security_min", 7.0)

    errors = []
    if overall_score < overall_min:
        errors.append(
            f"Overall score {overall_score} below threshold {overall_min}"
        )
    if security_score < security_min:
        errors.append(
            f"Security score {security_score} below threshold {security_min}"
        )

    if errors:
        raise AssertionError(f"Quality gate failed: {', '.join(errors)}")

