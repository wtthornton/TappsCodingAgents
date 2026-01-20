"""
Custom Skill Validation System.

Validates custom Skills for format and capability correctness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ValidationSeverity(Enum):
    """Validation error severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error or warning."""

    severity: ValidationSeverity
    field: str | None
    message: str
    suggestion: str | None = None
    line_number: int | None = None

    def __str__(self) -> str:
        """Format error message."""
        parts = [f"[{self.severity.value.upper()}]"]
        if self.field:
            parts.append(f"Field '{self.field}':")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"({self.suggestion})")
        if self.line_number:
            parts.append(f"[Line {self.line_number}]")
        return " ".join(parts)


@dataclass
class ValidationResult:
    """Result of Skill validation."""

    is_valid: bool
    errors: list[ValidationError]
    skill_path: Path
    skill_name: str | None = None

    def has_errors(self) -> bool:
        """Check if result has any errors."""
        return any(e.severity == ValidationSeverity.ERROR for e in self.errors)

    def has_warnings(self) -> bool:
        """Check if result has any warnings."""
        return any(e.severity == ValidationSeverity.WARNING for e in self.errors)

    def get_error_summary(self) -> str:
        """Get summary of validation errors."""
        if self.is_valid and not self.has_warnings():
            return f"✅ Skill '{self.skill_name or self.skill_path.name}' is valid."

        summary_parts = [f"Skill '{self.skill_name or self.skill_path.name}':"]
        error_count = sum(1 for e in self.errors if e.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for e in self.errors if e.severity == ValidationSeverity.WARNING)

        if error_count > 0:
            summary_parts.append(f"{error_count} error(s)")
        if warning_count > 0:
            summary_parts.append(f"{warning_count} warning(s)")

        return " ".join(summary_parts)


class SkillValidator:
    """Validates custom Skills for format and capability correctness."""

    # Required YAML frontmatter fields
    REQUIRED_FIELDS = ["name", "description", "allowed-tools", "model_profile"]

    # Optional YAML frontmatter fields
    OPTIONAL_FIELDS = ["version", "capabilities"]

    # Optional capability tags for guardrails and docs (plan 1.3)
    VALID_CAPABILITIES = frozenset({
        "read-only", "writes-files", "calls-llm", "uses-bash", "orchestrator",
    })

    # Valid tool names (from Claude Code Skills format)
    VALID_TOOLS = {
        "Read",
        "Write",
        "Edit",
        "Grep",
        "Glob",
        "Bash",
        "ListDirectory",
        "SearchCodebase",
        "ReadTextFile",
        "WriteTextFile",
        "EditTextFile",
        "DeleteFile",
        "MoveFile",
        "CopyFile",
        "CreateDirectory",
        "DeleteDirectory",
        "RunCommand",
        "SearchFiles",
        "FindInFiles",
        "GetFileInfo",
    }

    # Required markdown sections
    REQUIRED_SECTIONS = ["Identity", "Instructions"]

    # Optional markdown sections
    OPTIONAL_SECTIONS = [
        "Commands",
        "Capabilities",
        "Constraints",
        "Configuration",
        "Integration",
        "Example Workflow",
        "Best Practices",
        "Usage Examples",
    ]

    def __init__(self, project_root: Path | None = None):
        """
        Initialize validator.

        Args:
            project_root: Project root directory (for resolving paths)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root

    def validate_skill(self, skill_path: Path) -> ValidationResult:
        """
        Validate a Skill file.

        Args:
            skill_path: Path to Skill directory or SKILL.md file

        Returns:
            Validation result
        """
        errors: list[ValidationError] = []

        # Resolve Skill file path
        if skill_path.is_dir():
            skill_file = skill_path / "SKILL.md"
        else:
            skill_file = skill_path

        if not skill_file.exists():
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field=None,
                    message=f"Skill file not found: {skill_file}",
                    suggestion="Ensure SKILL.md exists in the Skill directory",
                )
            )
            return ValidationResult(
                is_valid=False,
                errors=errors,
                skill_path=skill_path,
            )

        # Read and parse Skill file
        try:
            content = skill_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field=None,
                    message="Skill file is not valid UTF-8",
                    suggestion="Ensure file is saved with UTF-8 encoding",
                )
            )
            return ValidationResult(
                is_valid=False,
                errors=errors,
                skill_path=skill_path,
            )
        except Exception as e:
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field=None,
                    message=f"Failed to read Skill file: {e}",
                )
            )
            return ValidationResult(
                is_valid=False,
                errors=errors,
                skill_path=skill_path,
            )

        # Validate format
        format_errors = self._validate_format(content, skill_file)
        errors.extend(format_errors)

        # Extract metadata for capability validation
        metadata = self._extract_metadata(content)
        skill_name = metadata.get("name") if metadata else None

        # Validate capabilities (only if format is valid)
        if not any(e.severity == ValidationSeverity.ERROR for e in format_errors):
            capability_errors = self._validate_capabilities(metadata, content)
            errors.extend(capability_errors)

        # Determine if valid (no errors, warnings are OK)
        is_valid = not any(e.severity == ValidationSeverity.ERROR for e in errors)

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            skill_path=skill_path,
            skill_name=skill_name,
        )

    def _validate_format(self, content: str, skill_file: Path) -> list[ValidationError]:
        """Validate Skill file format."""
        errors: list[ValidationError] = []

        # Check for YAML frontmatter
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not frontmatter_match:
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field=None,
                    message="Missing YAML frontmatter",
                    suggestion="Add YAML frontmatter between --- markers at the start of the file",
                    line_number=1,
                )
            )
            return errors  # Can't continue without frontmatter

        frontmatter_text = frontmatter_match.group(1)
        try:
            metadata = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field=None,
                    message=f"Invalid YAML frontmatter: {e}",
                    suggestion="Check YAML syntax in frontmatter",
                    line_number=2,
                )
            )
            return errors  # Can't continue with invalid YAML

        if not isinstance(metadata, dict):
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field=None,
                    message="YAML frontmatter must be a dictionary/object",
                    suggestion="Ensure frontmatter is a valid YAML object",
                    line_number=2,
                )
            )
            return errors

        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR,
                        field=field,
                        message=f"Missing required field: '{field}'",
                        suggestion=f"Add '{field}' to YAML frontmatter",
                    )
                )

        # Validate field types
        if "name" in metadata and not isinstance(metadata["name"], str):
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field="name",
                    message="Field 'name' must be a string",
                    suggestion="Set 'name' to a string value",
                )
            )

        if "description" in metadata and not isinstance(metadata["description"], str):
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field="description",
                    message="Field 'description' must be a string",
                    suggestion="Set 'description' to a string value",
                )
            )

        if "allowed-tools" in metadata:
            allowed_tools = metadata["allowed-tools"]
            if not isinstance(allowed_tools, (str, list)):
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR,
                        field="allowed-tools",
                        message="Field 'allowed-tools' must be a string or list",
                        suggestion="Set 'allowed-tools' to a comma-separated string or list",
                    )
                )

        if "model_profile" in metadata and not isinstance(metadata["model_profile"], str):
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field="model_profile",
                    message="Field 'model_profile' must be a string",
                    suggestion="Set 'model_profile' to a string value",
                )
            )

        # Validate markdown structure
        markdown_content = content[frontmatter_match.end() :]
        section_errors = self._validate_markdown_sections(markdown_content)
        errors.extend(section_errors)

        return errors

    def _validate_markdown_sections(self, content: str) -> list[ValidationError]:
        """Validate required markdown sections."""
        errors: list[ValidationError] = []

        # Check for required sections
        for section in self.REQUIRED_SECTIONS:
            # Look for section header (## Section Name or # Section Name)
            pattern = rf"^#+\s+{re.escape(section)}\s*$"
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.ERROR,
                        field=None,
                        message=f"Missing required section: '{section}'",
                        suggestion=f"Add a '## {section}' section to the Skill file",
                    )
                )

        return errors

    def _extract_metadata(self, content: str) -> dict[str, Any] | None:
        """Extract metadata from Skill file."""
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter_text = frontmatter_match.group(1)
        try:
            return yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            return None

    def _validate_capabilities(self, metadata: dict[str, Any] | None, content: str) -> list[ValidationError]:
        """Validate Skill capabilities."""
        errors: list[ValidationError] = []

        if not metadata:
            return errors

        # Validate tool names
        allowed_tools = metadata.get("allowed-tools")
        if allowed_tools:
            # Parse tools (can be string or list)
            if isinstance(allowed_tools, str):
                tools = [tool.strip() for tool in allowed_tools.split(",")]
            elif isinstance(allowed_tools, list):
                tools = [str(tool).strip() for tool in allowed_tools]
            else:
                return errors  # Already validated in format check

            # Check each tool
            for tool in tools:
                if tool and tool not in self.VALID_TOOLS:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.WARNING,
                            field="allowed-tools",
                            message=f"Unknown tool name: '{tool}'",
                            suggestion=f"Use one of: {', '.join(sorted(self.VALID_TOOLS))}",
                        )
                    )

        # Validate model_profile (basic check - just ensure it's not empty)
        model_profile = metadata.get("model_profile")
        if model_profile and not isinstance(model_profile, str):
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field="model_profile",
                    message="Field 'model_profile' must be a non-empty string",
                    suggestion="Set 'model_profile' to a valid profile name",
                )
            )
        elif model_profile and len(model_profile.strip()) == 0:
            errors.append(
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    field="model_profile",
                    message="Field 'model_profile' cannot be empty",
                    suggestion="Set 'model_profile' to a valid profile name",
                )
            )

        # Validate capabilities (optional; subset of known set)
        caps = metadata.get("capabilities")
        if isinstance(caps, list):
            for c in caps:
                if isinstance(c, str) and c.strip() and c not in self.VALID_CAPABILITIES:
                    errors.append(
                        ValidationError(
                            severity=ValidationSeverity.WARNING,
                            field="capabilities",
                            message=f"Unknown capability: '{c}'",
                            suggestion=f"Use one of: {', '.join(sorted(self.VALID_CAPABILITIES))}",
                        )
                    )

        # Validate name format (should be lowercase with hyphens)
        name = metadata.get("name")
        if name and isinstance(name, str):
            if not re.match(r"^[a-z0-9-]+$", name):
                errors.append(
                    ValidationError(
                        severity=ValidationSeverity.WARNING,
                        field="name",
                        message=f"Skill name '{name}' should use lowercase letters, numbers, and hyphens",
                        suggestion="Use format like 'my-custom-skill' (lowercase, hyphens)",
                    )
                )

        return errors

    def validate_all_skills(self, skills_dir: Path | None = None) -> list[ValidationResult]:
        """
        Validate all custom Skills in a directory.

        Args:
            skills_dir: Directory containing Skills (defaults to .claude/skills)

        Returns:
            List of validation results
        """
        if skills_dir is None:
            skills_dir = self.project_root / ".claude" / "skills"

        if not skills_dir.exists():
            return []

        results = []
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    result = self.validate_skill(skill_dir)
                    results.append(result)

        return results

