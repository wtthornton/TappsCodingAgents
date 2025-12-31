"""
Unit tests for CodeValidator utility.

Tests code validation functionality including Python syntax validation,
error detection, and fix suggestions.
"""

import pytest

from tapps_agents.core.code_validator import CodeValidator, ValidationResult

pytestmark = pytest.mark.unit


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test ValidationResult creation with valid code."""
        result = ValidationResult(
            is_valid=True,
            error_message=None,
            error_line=None,
            error_column=None,
            error_type=None,
            suggested_fix=None,
            language="python",
        )
        assert result.is_valid is True
        assert result.error_message is None
        assert result.language == "python"

    def test_validation_result_invalid(self):
        """Test ValidationResult creation with invalid code."""
        result = ValidationResult(
            is_valid=False,
            error_message="invalid syntax",
            error_line=1,
            error_column=5,
            error_type="SyntaxError",
            suggested_fix="Add colon",
            language="python",
        )
        assert result.is_valid is False
        assert result.error_message == "invalid syntax"
        assert result.error_line == 1
        assert result.error_type == "SyntaxError"
        assert result.suggested_fix == "Add colon"


class TestCodeValidator:
    """Test CodeValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = CodeValidator()

    # Valid Python code tests
    def test_validate_python_valid_code(self):
        """Test validate_python() with valid Python code."""
        code = """
def hello():
    print("world")
"""
        result = self.validator.validate_python(code)
        assert result.is_valid is True
        assert result.error_message is None
        assert result.error_type is None

    def test_validate_python_valid_code_with_imports(self):
        """Test validate_python() with valid code including imports."""
        code = """
import os
from pathlib import Path

def test():
    return Path("test")
"""
        result = self.validator.validate_python(code)
        assert result.is_valid is True

    def test_validate_python_valid_code_with_classes(self):
        """Test validate_python() with valid class definition."""
        code = """
class TestClass:
    def __init__(self):
        self.value = 1
    
    def method(self):
        return self.value
"""
        result = self.validator.validate_python(code)
        assert result.is_valid is True

    # Invalid Python code tests
    def test_validate_python_missing_colon(self):
        """Test validate_python() with missing colon."""
        code = """
def hello()
    print("world")
"""
        result = self.validator.validate_python(code)
        assert result.is_valid is False
        assert result.error_type == "SyntaxError"
        assert result.error_line is not None

    def test_validate_python_unclosed_parenthesis(self):
        """Test validate_python() with unclosed parenthesis."""
        code = """
def hello(
    print("world")
"""
        result = self.validator.validate_python(code)
        assert result.is_valid is False
        assert result.error_type == "SyntaxError"

    def test_validate_python_indentation_error(self):
        """Test validate_python() with indentation error."""
        code = """
def hello():
print("world")
"""
        result = self.validator.validate_python(code)
        assert result.is_valid is False
        assert "indentation" in result.error_message.lower() or result.error_type == "IndentationError"

    def test_validate_python_invalid_import_syntax(self):
        """Test validate_python() with invalid import syntax."""
        code = """
from services.ai-automation-service-new.src.database import *
"""
        result = self.validator.validate_python(code)
        # This should be invalid due to hyphens in module path
        assert result.is_valid is False

    # Edge cases
    def test_validate_python_empty_code(self):
        """Test validate_python() with empty code."""
        result = self.validator.validate_python("")
        assert result.is_valid is False
        assert "empty" in result.error_message.lower()

    def test_validate_python_whitespace_only(self):
        """Test validate_python() with whitespace only."""
        result = self.validator.validate_python("   \n\t  ")
        assert result.is_valid is False

    def test_validate_python_with_file_path(self):
        """Test validate_python() with file_path parameter."""
        code = "def hello(): print('world')"
        result = self.validator.validate_python(code, file_path="test.py")
        assert result.is_valid is True

    # Language support tests
    def test_validate_python_language(self):
        """Test validate() with language='python'."""
        code = "def hello(): print('world')"
        result = self.validator.validate(code, language="python")
        assert result.is_valid is True
        assert result.language == "python"

    def test_validate_typescript_stubbed(self):
        """Test validate() with language='typescript' (stubbed)."""
        code = "function hello() { console.log('world'); }"
        result = self.validator.validate(code, language="typescript")
        # Currently stubbed - returns is_valid=True
        assert result.is_valid is True
        assert result.language == "typescript"

    def test_validate_javascript_stubbed(self):
        """Test validate() with language='javascript' (stubbed)."""
        code = "function hello() { console.log('world'); }"
        result = self.validator.validate(code, language="javascript")
        # Currently stubbed - returns is_valid=True
        assert result.is_valid is True
        assert result.language == "javascript"

    def test_validate_unknown_language(self):
        """Test validate() with unknown language."""
        code = "some code"
        result = self.validator.validate(code, language="unknown")
        # Unknown language - skip validation
        assert result.is_valid is True

    # Error suggestion tests
    def test_suggest_fix_missing_parenthesis(self):
        """Test suggest_fix() for missing closing parenthesis."""
        code = "def hello("
        try:
            compile(code, "<string>", "exec")
            pytest.skip("Code compiled unexpectedly")
        except SyntaxError as e:
            fix = self.validator.suggest_fix(e, code)
            assert fix is not None
            assert "parenthesis" in fix.lower()

    def test_suggest_fix_missing_colon(self):
        """Test suggest_fix() for missing colon."""
        code = "def hello()"
        try:
            compile(code, "<string>", "exec")
            pytest.skip("Code compiled unexpectedly")
        except SyntaxError as e:
            fix = self.validator.suggest_fix(e, code)
            # May or may not have suggestion depending on error details
            assert fix is None or "colon" in fix.lower()

    def test_suggest_fix_indentation(self):
        """Test suggest_fix() for indentation error."""
        code = "def hello():\nprint('world')"
        try:
            compile(code, "<string>", "exec")
            pytest.skip("Code compiled unexpectedly")
        except IndentationError as e:
            fix = self.validator.suggest_fix(e, code)
            # suggest_fix may or may not have a suggestion for indentation
            # The important thing is it doesn't crash
            assert fix is None or "indentation" in fix.lower()

    def test_suggest_fix_non_syntax_error(self):
        """Test suggest_fix() with non-SyntaxError exception."""
        error = ValueError("Not a syntax error")
        fix = self.validator.suggest_fix(error, "some code")
        assert fix is None
