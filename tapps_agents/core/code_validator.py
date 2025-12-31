"""
Code Validator - Validates generated code for syntax errors before writing to files.

Prevents broken code from being written by validating syntax using language-specific
parsers (Python ast.parse, TypeScript compiler, etc.).
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of code validation."""

    is_valid: bool
    """Whether the code is valid (no syntax errors)."""

    error_message: str | None = None
    """Error message if validation failed."""

    error_line: int | None = None
    """Line number where error occurred (1-indexed)."""

    error_column: int | None = None
    """Column number where error occurred (1-indexed)."""

    error_type: str | None = None
    """Type of error (e.g., 'SyntaxError', 'IndentationError')."""

    suggested_fix: str | None = None
    """Suggested fix for the error (if available)."""

    language: str = "python"
    """Language of the validated code."""


class CodeValidator:
    """
    Validates generated code for syntax errors before writing to files.

    Supports:
    - Python (using ast.parse)
    - TypeScript (using TypeScript compiler - if available)
    - JavaScript (using esprima or similar - if available)
    """

    def __init__(self):
        """Initialize code validator."""
        pass

    def validate(
        self,
        code: str,
        language: str = "python",
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate code for syntax errors.

        Args:
            code: Code string to validate
            language: Language of the code (python, typescript, javascript)
            file_path: Optional file path for better error messages

        Returns:
            ValidationResult with validation status and error details

        Examples:
            >>> validator = CodeValidator()
            >>> result = validator.validate("def hello(): print('world')")
            >>> result.is_valid
            True

            >>> result = validator.validate("def hello( print('world')")
            >>> result.is_valid
            False
            >>> result.error_type
            'SyntaxError'
        """
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Code is empty",
                error_type="EmptyCodeError",
                language=language,
            )

        if language == "python":
            return self.validate_python(code, file_path)
        elif language == "typescript":
            return self.validate_typescript(code, file_path)
        elif language == "javascript":
            return self.validate_javascript(code, file_path)
        else:
            # Unknown language - skip validation
            return ValidationResult(
                is_valid=True,
                error_message=None,
                language=language,
            )

    def validate_python(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate Python code syntax using ast.parse.

        Args:
            code: Python code string to validate
            file_path: Optional file path for better error messages

        Returns:
            ValidationResult with validation status

        Raises:
            ValueError: If code is empty or None
        """
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Python code is empty",
                error_type="EmptyCodeError",
                language="python",
            )

        try:
            ast.parse(code, filename=str(file_path) if file_path else "<string>")
            return ValidationResult(
                is_valid=True,
                error_message=None,
                error_line=None,
                error_column=None,
                error_type=None,
                suggested_fix=None,
                language="python",
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                error_message=str(e.msg) if e.msg else str(e),
                error_line=e.lineno,
                error_column=e.offset,
                error_type=type(e).__name__,
                suggested_fix=self.suggest_fix(e, code),
                language="python",
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unexpected error during validation: {str(e)}",
                error_type=type(e).__name__,
                language="python",
            )

    def validate_typescript(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate TypeScript code syntax.

        Args:
            code: TypeScript code string to validate
            file_path: Optional file path for better error messages

        Returns:
            ValidationResult with validation status

        Note:
            Currently returns is_valid=True (validation not implemented).
            Future: Use TypeScript compiler (tsc) or parser library.
        """
        # TODO: Implement TypeScript validation using tsc or parser
        # For now, skip validation for TypeScript
        return ValidationResult(
            is_valid=True,
            error_message=None,
            language="typescript",
        )

    def validate_javascript(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate JavaScript code syntax.

        Args:
            code: JavaScript code string to validate
            file_path: Optional file path for better error messages

        Returns:
            ValidationResult with validation status

        Note:
            Currently returns is_valid=True (validation not implemented).
            Future: Use esprima or similar parser library.
        """
        # TODO: Implement JavaScript validation using esprima or similar
        # For now, skip validation for JavaScript
        return ValidationResult(
            is_valid=True,
            error_message=None,
            language="javascript",
        )

    def suggest_fix(
        self,
        error: SyntaxError | Exception,
        code: str,
    ) -> str | None:
        """
        Suggest a fix for a syntax error.

        Args:
            error: The syntax error exception
            code: The code that caused the error

        Returns:
            Suggested fix string, or None if no suggestion available

        Examples:
            >>> validator = CodeValidator()
            >>> error = SyntaxError("invalid syntax", ("<string>", 1, 5, "def hello("))
            >>> fix = validator.suggest_fix(error, "def hello(")
            >>> fix is not None
            True
        """
        if not isinstance(error, SyntaxError):
            return None

        error_msg = str(error.msg) if error.msg else ""
        error_line = error.lineno
        error_offset = error.offset

        # Common fixes
        suggestions = []

        # Missing closing parenthesis
        if "(" in error_msg or "unexpected EOF" in error_msg.lower():
            if error_line and error_line <= len(code.split("\n")):
                lines = code.split("\n")
                line = lines[error_line - 1] if error_line > 0 else ""
                if "(" in line and ")" not in line:
                    suggestions.append("Missing closing parenthesis ')'")

        # Missing colon
        if "expected ':'" in error_msg.lower() or "invalid syntax" in error_msg.lower():
            if error_line and error_line <= len(code.split("\n")):
                lines = code.split("\n")
                line = lines[error_line - 1] if error_line > 0 else ""
                if line.strip().endswith(")"):
                    suggestions.append("Missing colon ':' after function/class definition")

        # Indentation error
        if "indentation" in error_msg.lower():
            suggestions.append("Check indentation (use 4 spaces, not tabs)")

        # Invalid import syntax
        if "import" in error_msg.lower() or "cannot import" in error_msg.lower():
            suggestions.append(
                "Check import statement syntax. Module paths with hyphens should use underscores."
            )

        if suggestions:
            return " | ".join(suggestions)

        return None
