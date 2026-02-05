"""Configuration validator for TappsCodingAgents.

This module validates all TappsCodingAgents configuration files including
experts.yaml, domains.md, tech-stack.yaml, and config.yaml.

Module: Phase 1.1 - Configuration Validator
From: docs/INIT_AUTOFILL_DETAILED_REQUIREMENTS.md
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yaml
from yaml import YAMLError


@dataclass
class ValidationError:
    """Validation error with file, line, and message."""
    file: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None

    def __str__(self) -> str:
        """Format error message."""
        location = f"{self.file}"
        if self.line is not None:
            location += f":{self.line}"
            if self.column is not None:
                location += f":{self.column}"
        return f"ERROR [{location}] {self.message}"


@dataclass
class ValidationWarning:
    """Validation warning with file and message."""
    file: str
    message: str
    line: Optional[int] = None

    def __str__(self) -> str:
        """Format warning message."""
        location = f"{self.file}"
        if self.line is not None:
            location += f":{self.line}"
        return f"WARNING [{location}] {self.message}"


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def add_error(self, file: str, message: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
        """Add validation error."""
        self.errors.append(ValidationError(file=file, message=message, line=line, column=column))
        self.valid = False

    def add_warning(self, file: str, message: str, line: Optional[int] = None) -> None:
        """Add validation warning."""
        self.warnings.append(ValidationWarning(file=file, message=message, line=line))

    def add_suggestion(self, suggestion: str) -> None:
        """Add improvement suggestion."""
        self.suggestions.append(suggestion)

    def __str__(self) -> str:
        """Format validation result."""
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  {error}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  {warning}")
        if self.suggestions:
            lines.append(f"Suggestions ({len(self.suggestions)}):")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")
        if not self.errors and not self.warnings:
            lines.append("✅ Validation passed")
        return "\n".join(lines)


class ConfigValidator:
    """Validates all TappsCodingAgents configuration files.

    This validator checks:
    - YAML syntax with line-number error reporting
    - Required fields exist
    - File path references are valid
    - Configuration consistency

    Supports auto-fix for common issues when --fix flag is provided.
    """

    def __init__(self, project_root: Optional[Path] = None, auto_fix: bool = False):
        """Initialize validator.

        Args:
            project_root: Root directory of project (defaults to current directory)
            auto_fix: Enable automatic fixing of issues
        """
        self.project_root = project_root or Path.cwd()
        self.tapps_agents_dir = self.project_root / ".tapps-agents"
        self.auto_fix = auto_fix

    def validate_all(self) -> ValidationResult:
        """Validate all configuration files.

        Returns:
            ValidationResult: Combined validation result
        """
        result = ValidationResult(valid=True)

        # Validate each configuration file
        experts_result = self.validate_experts_yaml()
        domains_result = self.validate_domains_md()
        tech_stack_result = self.validate_tech_stack_yaml()
        config_result = self.validate_config_yaml()
        knowledge_result = self.validate_knowledge_files()

        # Combine results
        for r in [experts_result, domains_result, tech_stack_result, config_result, knowledge_result]:
            result.errors.extend(r.errors)
            result.warnings.extend(r.warnings)
            result.suggestions.extend(r.suggestions)
            if not r.valid:
                result.valid = False

        return result

    def validate_experts_yaml(self) -> ValidationResult:
        """Validate experts.yaml structure and references.

        Checks:
        - Valid YAML syntax
        - Required fields: name, description, priority, domain, consultation_triggers, knowledge_files
        - File paths exist
        - Priority values are valid (0.0 - 1.0)

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult(valid=True)
        file_path = self.tapps_agents_dir / "experts.yaml"

        # Check file exists
        if not file_path.exists():
            result.add_warning(
                file="experts.yaml",
                message="File does not exist (optional if using built-in experts only)"
            )
            return result

        # Parse YAML
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except YAMLError as e:
            result.add_error(
                file="experts.yaml",
                message=f"YAML parsing error: {e}",
                line=getattr(e, "problem_mark", None) and e.problem_mark.line + 1  # type: ignore
            )
            return result
        except Exception as e:
            result.add_error(file="experts.yaml", message=f"Failed to read file: {e}")
            return result

        # Validate structure
        if not isinstance(data, dict):
            result.add_error(file="experts.yaml", message="Root element must be a dictionary")
            return result

        if "experts" not in data:
            result.add_error(file="experts.yaml", message="Missing 'experts' key")
            return result

        if not isinstance(data["experts"], list):
            result.add_error(file="experts.yaml", message="'experts' must be a list")
            return result

        # Validate each expert
        for idx, expert in enumerate(data["experts"]):
            expert_name = expert.get("name", f"expert_{idx}")

            # Check required fields
            required_fields = ["name", "description", "priority", "domain", "consultation_triggers", "knowledge_files"]
            for field in required_fields:
                if field not in expert:
                    result.add_error(
                        file="experts.yaml",
                        message=f"Expert '{expert_name}': missing required field '{field}'"
                    )

            # Validate priority
            if "priority" in expert:
                priority = expert["priority"]
                if not isinstance(priority, (int, float)):
                    result.add_error(
                        file="experts.yaml",
                        message=f"Expert '{expert_name}': priority must be a number"
                    )
                elif not (0.0 <= priority <= 1.0):
                    result.add_error(
                        file="experts.yaml",
                        message=f"Expert '{expert_name}': priority must be between 0.0 and 1.0 (got {priority})"
                    )

            # Validate knowledge_files paths
            if "knowledge_files" in expert:
                if not isinstance(expert["knowledge_files"], list):
                    result.add_error(
                        file="experts.yaml",
                        message=f"Expert '{expert_name}': knowledge_files must be a list"
                    )
                else:
                    for kf_path in expert["knowledge_files"]:
                        full_path = self.tapps_agents_dir / kf_path
                        if not full_path.exists():
                            result.add_error(
                                file="experts.yaml",
                                message=f"Expert '{expert_name}': knowledge file not found: {kf_path}"
                            )

        return result

    def validate_domains_md(self) -> ValidationResult:
        """Validate domains.md expert and knowledge file references.

        Checks:
        - File exists
        - Expert references are valid
        - Knowledge file paths exist

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult(valid=True)
        file_path = self.tapps_agents_dir / "domains.md"

        # Check file exists
        if not file_path.exists():
            result.add_warning(
                file="domains.md",
                message="File does not exist (optional)"
            )
            return result

        # Read file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            result.add_error(file="domains.md", message=f"Failed to read file: {e}")
            return result

        # Basic validation - check for markdown structure
        if not content.strip():
            result.add_warning(file="domains.md", message="File is empty")

        # TODO: More sophisticated validation of domain structure
        # For now, just check that it's readable

        return result

    def validate_tech_stack_yaml(self) -> ValidationResult:
        """Validate tech-stack.yaml structure.

        Checks:
        - Valid YAML syntax
        - Expected structure (languages, libraries, frameworks)

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult(valid=True)
        file_path = self.tapps_agents_dir / "tech-stack.yaml"

        # Check file exists
        if not file_path.exists():
            result.add_warning(
                file="tech-stack.yaml",
                message="File does not exist (will be auto-generated by TechStackDetector)"
            )
            result.add_suggestion("Run 'tapps-agents init' to auto-detect tech stack")
            return result

        # Parse YAML
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except YAMLError as e:
            result.add_error(
                file="tech-stack.yaml",
                message=f"YAML parsing error: {e}",
                line=getattr(e, "problem_mark", None) and e.problem_mark.line + 1  # type: ignore
            )
            return result
        except Exception as e:
            result.add_error(file="tech-stack.yaml", message=f"Failed to read file: {e}")
            return result

        # Validate structure
        if not isinstance(data, dict):
            result.add_error(file="tech-stack.yaml", message="Root element must be a dictionary")
            return result

        # Check for expected keys (optional but recommended)
        recommended_keys = ["languages", "libraries", "frameworks", "context7_priority"]
        for key in recommended_keys:
            if key not in data:
                result.add_warning(
                    file="tech-stack.yaml",
                    message=f"Missing recommended key: '{key}'"
                )

        return result

    def validate_config_yaml(self) -> ValidationResult:
        """Validate config.yaml keys and values.

        Checks:
        - Valid YAML syntax
        - Known configuration keys
        - Value types are correct

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult(valid=True)
        file_path = self.tapps_agents_dir / "config.yaml"

        # Check file exists
        if not file_path.exists():
            result.add_error(
                file="config.yaml",
                message="File does not exist (required)"
            )
            result.add_suggestion("Run 'tapps-agents init' to create config.yaml")
            return result

        # Parse YAML
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except YAMLError as e:
            result.add_error(
                file="config.yaml",
                message=f"YAML parsing error: {e}",
                line=getattr(e, "problem_mark", None) and e.problem_mark.line + 1  # type: ignore
            )
            return result
        except Exception as e:
            result.add_error(file="config.yaml", message=f"Failed to read file: {e}")
            return result

        # Validate structure
        if not isinstance(data, dict):
            result.add_error(file="config.yaml", message="Root element must be a dictionary")
            return result

        # TODO: Validate known configuration keys and value types
        # For now, just check that it's valid YAML

        return result

    def validate_knowledge_files(self) -> ValidationResult:
        """Check all knowledge_files paths exist.

        Scans experts.yaml for knowledge_files references and verifies they exist.

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult(valid=True)
        experts_file = self.tapps_agents_dir / "experts.yaml"

        # If experts.yaml doesn't exist, skip
        if not experts_file.exists():
            return result

        # Parse experts.yaml
        try:
            with open(experts_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            # If parsing fails, it will be caught by validate_experts_yaml
            return result

        if not isinstance(data, dict) or "experts" not in data:
            return result

        # Check all knowledge_files
        for expert in data.get("experts", []):
            expert_name = expert.get("name", "unknown")
            for kf_path in expert.get("knowledge_files", []):
                full_path = self.tapps_agents_dir / kf_path
                if not full_path.exists():
                    result.add_error(
                        file="experts.yaml",
                        message=f"Knowledge file not found for expert '{expert_name}': {kf_path}"
                    )

        return result

    def fix_common_issues(self) -> int:
        """Auto-fix common configuration issues.

        Fixes:
        - Create missing directories
        - Fix indentation issues
        - Add missing required fields with defaults

        Returns:
            int: Number of issues fixed
        """
        if not self.auto_fix:
            return 0

        fixes_count = 0

        # Ensure .tapps-agents directory exists
        if not self.tapps_agents_dir.exists():
            self.tapps_agents_dir.mkdir(parents=True, exist_ok=True)
            fixes_count += 1

        # TODO: Implement more auto-fix logic
        # - Fix YAML indentation
        # - Add missing required fields with defaults
        # - Create missing knowledge file directories

        return fixes_count


def main() -> int:
    """CLI entry point for config validation.

    Returns:
        int: Exit code (0 = success, 1 = validation failed)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate TappsCodingAgents configuration")
    parser.add_argument("--fix", action="store_true", help="Auto-fix common issues")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    args = parser.parse_args()

    validator = ConfigValidator(project_root=args.project_root, auto_fix=args.fix)

    if args.fix:
        fixes = validator.fix_common_issues()
        print(f"Fixed {fixes} issues")

    result = validator.validate_all()
    print(result)

    return 0 if result.valid else 1


if __name__ == "__main__":
    exit(main())
