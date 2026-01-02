"""
Command validator for CLI commands.

Validates command arguments before execution to provide clear, actionable error messages.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of command validation."""
    
    valid: bool
    errors: list[str]
    suggestions: list[str]
    examples: list[str]
    
    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return len(self.errors) > 0


class CommandValidator:
    """Validates CLI command arguments before execution."""
    
    def validate_build_command(self, args: Any) -> ValidationResult:
        """
        Validate simple-mode build command arguments.
        
        Args:
            args: Parsed command arguments object
            
        Returns:
            ValidationResult with validation status and any errors/suggestions
        """
        errors: list[str] = []
        suggestions: list[str] = []
        examples: list[str] = []
        
        # Validate --prompt is provided and not empty
        prompt = getattr(args, "prompt", None)
        if prompt is None:
            errors.append("--prompt argument is required")
            suggestions.append("Provide --prompt with feature description")
            examples.append('tapps-agents simple-mode build --prompt "Add user authentication"')
        elif not isinstance(prompt, str):
            errors.append("--prompt must be a string")
            suggestions.append("Provide a valid string value for --prompt")
            examples.append('tapps-agents simple-mode build --prompt "Add feature"')
        elif not prompt.strip():
            errors.append("--prompt cannot be empty")
            suggestions.append("Provide a non-empty feature description")
            examples.append('tapps-agents simple-mode build --prompt "Add login endpoint"')
        
        # Validate --file path if provided
        file_path = getattr(args, "file", None)
        if file_path:
            if not isinstance(file_path, str):
                errors.append(f"--file must be a string, got {type(file_path).__name__}")
                suggestions.append("Provide a valid file path string")
                examples.append('tapps-agents simple-mode build --prompt "..." --file src/api/auth.py')
            else:
                path = Path(file_path)
                # Only validate if path is absolute or we can resolve it
                # For relative paths, we allow them (will be resolved during execution)
                if path.is_absolute() and not path.exists():
                    parent = path.parent
                    if not parent.exists():
                        errors.append(f"File path directory does not exist: {parent}")
                        suggestions.append("Provide a valid file path or omit --file to create new file")
                        examples.append('tapps-agents simple-mode build --prompt "..." --file src/api/auth.py')
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            suggestions=suggestions,
            examples=examples,
        )
