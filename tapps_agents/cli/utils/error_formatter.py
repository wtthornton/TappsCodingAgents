"""
Error formatter for CLI commands.

Formats errors with structured, actionable messages including context, suggestions, and examples.
"""

from typing import Any


class ErrorFormatter:
    """Formats errors with structured, actionable messages."""
    
    def format_validation_error(self, result: "ValidationResult") -> str:
        """
        Format validation errors with structure: Error | Suggestions | Examples.
        
        Args:
            result: ValidationResult from command validation
            
        Returns:
            Formatted error message string
        """
        if not result.has_errors():
            return ""
        
        error_lines = []
        error_lines.append("Validation Error")
        error_lines.append("=" * 60)
        
        error_lines.append("\nErrors:")
        for error in result.errors:
            error_lines.append(f"  • {error}")
        
        if result.suggestions:
            error_lines.append("\nSuggestions:")
            for suggestion in result.suggestions:
                error_lines.append(f"  • {suggestion}")
        
        if result.examples:
            error_lines.append("\nExamples:")
            for example in result.examples:
                error_lines.append(f"  $ {example}")
        
        return "\n".join(error_lines)
    
    def format_error(
        self,
        error_message: str,
        error_type: str = "Error",
        context: dict[str, Any] | None = None,
        suggestion: str | None = None,
        example: str | None = None,
    ) -> str:
        """
        Format general error with structure: Error | Context | Suggestion | Example.
        
        Args:
            error_message: Main error message
            error_type: Error type/category
            context: Optional context dictionary
            suggestion: Optional suggestion for fixing the error
            example: Optional example command or code
            
        Returns:
            Formatted error message string
        """
        error_lines = []
        error_lines.append(f"{error_type}: {error_message}")
        error_lines.append("=" * 60)
        
        if context:
            error_lines.append("\nContext:")
            for key, value in context.items():
                error_lines.append(f"  {key}: {value}")
        
        if suggestion:
            error_lines.append(f"\nSuggestion: {suggestion}")
        
        if example:
            error_lines.append(f"\nExample: {example}")
        
        return "\n".join(error_lines)
