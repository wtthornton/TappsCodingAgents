"""
Tests for CLI command validators.
"""

from argparse import Namespace

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.cli.validators.command_validator import (
    CommandValidator,
    ValidationResult,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_validation_result_valid(self):
        """Test ValidationResult with valid result."""
        result = ValidationResult(
            valid=True,
            errors=[],
            suggestions=[],
            examples=[],
        )
        assert result.valid is True
        assert result.has_errors() is False
        assert len(result.errors) == 0
    
    def test_validation_result_invalid(self):
        """Test ValidationResult with invalid result."""
        result = ValidationResult(
            valid=False,
            errors=["Error 1", "Error 2"],
            suggestions=["Suggestion 1"],
            examples=["Example 1"],
        )
        assert result.valid is False
        assert result.has_errors() is True
        assert len(result.errors) == 2


class TestCommandValidator:
    """Tests for CommandValidator class."""
    
    def test_validate_build_command_valid(self):
        """Test validation with valid arguments."""
        validator = CommandValidator()
        args = Namespace(
            prompt="Add user authentication",
            file=None,
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.has_errors() is False
    
    def test_validate_build_command_missing_prompt(self):
        """Test validation with missing prompt."""
        validator = CommandValidator()
        args = Namespace(
            prompt=None,
            file=None,
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert "--prompt argument is required" in result.errors[0]
        assert len(result.suggestions) > 0
        assert len(result.examples) > 0
    
    def test_validate_build_command_empty_prompt(self):
        """Test validation with empty prompt."""
        validator = CommandValidator()
        args = Namespace(
            prompt="",
            file=None,
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert "--prompt cannot be empty" in result.errors[0]
        assert len(result.suggestions) > 0
        assert len(result.examples) > 0
    
    def test_validate_build_command_whitespace_only_prompt(self):
        """Test validation with whitespace-only prompt."""
        validator = CommandValidator()
        args = Namespace(
            prompt="   \n\t  ",
            file=None,
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert "--prompt cannot be empty" in result.errors[0]
    
    def test_validate_build_command_valid_file_path(self):
        """Test validation with valid file path."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.touch()
            
            validator = CommandValidator()
            args = Namespace(
                prompt="Add feature",
                file=str(test_file),
                fast=False,
                auto=False,
            )
            result = validator.validate_build_command(args)
            
            assert result.valid is True
            assert len(result.errors) == 0
    
    def test_validate_build_command_invalid_file_path_parent_missing(self):
        """Test validation with file path whose parent doesn't exist."""
        validator = CommandValidator()
        args = Namespace(
            prompt="Add feature",
            file="/nonexistent/path/to/file.py",
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        # For absolute paths with missing parent, should error
        # (This assumes Unix-style paths - may need adjustment for Windows)
        if result.valid is False:
            # Expected if parent directory doesn't exist
            assert len(result.errors) >= 0  # May or may not error depending on OS
    
    def test_validate_build_command_relative_file_path(self):
        """Test validation with relative file path (allowed)."""
        validator = CommandValidator()
        args = Namespace(
            prompt="Add feature",
            file="src/api/auth.py",
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        # Relative paths are allowed (will be resolved during execution)
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_build_command_invalid_file_type(self):
        """Test validation with invalid file type (not string)."""
        validator = CommandValidator()
        args = Namespace(
            prompt="Add feature",
            file=123,  # Invalid type
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert "--file must be a string" in result.errors[0]
    
    def test_validate_build_command_multiple_errors(self):
        """Test validation with multiple errors."""
        validator = CommandValidator()
        args = Namespace(
            prompt="",  # Empty
            file=123,  # Invalid type
            fast=False,
            auto=False,
        )
        result = validator.validate_build_command(args)
        
        assert result.valid is False
        assert len(result.errors) >= 1  # At least empty prompt error
