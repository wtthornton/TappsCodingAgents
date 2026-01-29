"""
Environment Variable Validator

Validates required environment variables against .env.example before running scripts.
Secure handling - NEVER echoes secret values.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnvVar:
    """Environment variable definition."""

    name: str
    required: bool = True
    default: str | None = None
    description: str | None = None
    is_secret: bool = False  # Marks as sensitive (never log value)

    def is_set(self) -> bool:
        """Check if environment variable is set."""
        return self.name in os.environ

    def get_value(self) -> str | None:
        """
        Get environment variable value.

        Returns None if not set or if secret (for security).
        """
        if not self.is_set():
            return None

        # Never return secret values
        if self.is_secret:
            return "[REDACTED]"

        return os.environ.get(self.name)


@dataclass
class ValidationResult:
    """Result of environment validation."""

    missing: list[EnvVar] = field(default_factory=list)
    present: list[EnvVar] = field(default_factory=list)
    using_defaults: list[EnvVar] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if validation passed (no missing required vars)."""
        return len(self.missing) == 0

    def has_warnings(self) -> bool:
        """Check if there are warnings (using defaults)."""
        return len(self.using_defaults) > 0


class EnvValidator:
    """
    Validate environment variables against .env.example.

    Security: NEVER echoes secret values, only reports variable names.
    """

    # Patterns that indicate secret/sensitive variables
    SECRET_PATTERNS = [
        r".*_SECRET$",
        r".*_KEY$",
        r".*_TOKEN$",
        r".*PASSWORD.*",
        r".*_CREDENTIALS$",
        r".*API_KEY.*",
    ]

    def __init__(self, env_example_path: Path | None = None):
        """
        Initialize environment validator.

        Args:
            env_example_path: Path to .env.example file.
                            If None, looks in current directory.
        """
        if env_example_path is None:
            env_example_path = Path.cwd() / ".env.example"

        self.env_example_path = env_example_path

    def parse_env_example(self) -> list[EnvVar]:
        """
        Parse .env.example to find required variables.

        Supports formats:
        - REQUIRED_VAR=
        - REQUIRED_VAR=default_value
        - # Required: VAR_NAME
        - VAR_NAME=value  # Required
        - # Secret: VAR_NAME  (marks as secret)

        Returns:
            List of EnvVar definitions
        """
        if not self.env_example_path.exists():
            return []

        vars: dict[str, EnvVar] = {}

        with open(self.env_example_path) as f:
            for line in f:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Check for comment-based markers
                if line.startswith("#"):
                    self._parse_comment(line, vars)
                    continue

                # Parse VAR=value lines
                if "=" in line:
                    self._parse_assignment(line, vars)

        return list(vars.values())

    def _parse_comment(self, line: str, vars: dict[str, EnvVar]):
        """Parse comment line for variable markers."""
        # # Required: VAR_NAME
        required_match = re.match(r"#\s*Required:\s*(\w+)", line, re.IGNORECASE)
        if required_match:
            var_name = required_match.group(1)
            if var_name not in vars:
                vars[var_name] = EnvVar(
                    name=var_name, required=True, is_secret=self._is_secret(var_name)
                )
            else:
                vars[var_name].required = True

        # # Secret: VAR_NAME
        secret_match = re.match(r"#\s*Secret:\s*(\w+)", line, re.IGNORECASE)
        if secret_match:
            var_name = secret_match.group(1)
            if var_name not in vars:
                vars[var_name] = EnvVar(
                    name=var_name, required=False, is_secret=True
                )
            else:
                vars[var_name].is_secret = True

    def _parse_assignment(self, line: str, vars: dict[str, EnvVar]):
        """Parse VAR=value assignment line."""
        # Remove inline comments
        if "#" in line:
            line_part = line.split("#")[0].strip()
            comment = line.split("#")[1].strip()
        else:
            line_part = line
            comment = ""

        # Parse VAR=value
        parts = line_part.split("=", 1)
        if len(parts) != 2:
            return

        var_name = parts[0].strip()
        value = parts[1].strip()

        # Check if marked as required in comment
        required = "required" in comment.lower()

        # Create or update var
        if var_name not in vars:
            vars[var_name] = EnvVar(
                name=var_name,
                required=required,
                default=value if value else None,
                is_secret=self._is_secret(var_name),
            )
        else:
            # Update existing
            if value:
                vars[var_name].default = value
            if required:
                vars[var_name].required = True

    def _is_secret(self, var_name: str) -> bool:
        """Check if variable name indicates a secret."""
        for pattern in self.SECRET_PATTERNS:
            if re.match(pattern, var_name, re.IGNORECASE):
                return True
        return False

    def validate_env(self) -> ValidationResult:
        """
        Validate environment variables against .env.example.

        Returns:
            ValidationResult with missing, present, and default-using variables
        """
        required_vars = self.parse_env_example()

        result = ValidationResult()

        for var in required_vars:
            if var.is_set():
                result.present.append(var)
            elif var.required:
                result.missing.append(var)
            elif var.default is not None:
                result.using_defaults.append(var)

        return result

    def format_result(self, result: ValidationResult) -> str:
        """
        Format validation result for display.

        SECURITY: Never displays secret values.

        Args:
            result: Validation result

        Returns:
            Formatted string
        """
        lines = ["=" * 70]
        lines.append("ENVIRONMENT VARIABLE VALIDATION")
        lines.append("=" * 70)

        if result.is_valid():
            lines.append("\n✅ All required environment variables are set.")
        else:
            lines.append(f"\n❌ {len(result.missing)} required variables are missing:")
            for var in result.missing:
                secret_marker = " [SECRET]" if var.is_secret else ""
                lines.append(f"  - {var.name}{secret_marker}")

        if result.has_warnings():
            lines.append(f"\n⚠️  {len(result.using_defaults)} variables using defaults:")
            for var in result.using_defaults:
                lines.append(f"  - {var.name}")

        if result.present:
            lines.append(f"\n✓ {len(result.present)} variables are set")

        # Add instructions for missing variables
        if not result.is_valid():
            lines.append("\nTo fix:")
            lines.append("1. Copy .env.example to .env")
            lines.append("2. Set values for required variables")
            lines.append("3. NEVER commit .env to version control")

        lines.append("=" * 70)

        return "\n".join(lines)


class EnvValidatorCLI:
    """CLI interface for environment validation."""

    @staticmethod
    def check_env(env_file: Path | None = None, warn_only: bool = False) -> int:
        """
        Check environment variables.

        Args:
            env_file: Path to .env.example (default: .env.example in cwd)
            warn_only: If True, warn instead of failing on missing vars

        Returns:
            Exit code: 0 if valid, 1 if invalid
        """
        validator = EnvValidator(env_file)
        result = validator.validate_env()

        print(validator.format_result(result))

        if not result.is_valid():
            if warn_only:
                print("\n⚠️  Warning: Missing required variables (warn-only mode)\n")
                return 0
            else:
                print("\n❌ Error: Missing required variables\n")
                return 1

        return 0
