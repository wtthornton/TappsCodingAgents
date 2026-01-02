"""
Tests for CLI error formatter.
"""

import pytest

from tapps_agents.cli.utils.error_formatter import ErrorFormatter
from tapps_agents.cli.validators.command_validator import ValidationResult

pytestmark = pytest.mark.unit


class TestErrorFormatter:
    """Tests for ErrorFormatter class."""
    
    def test_format_validation_error_empty(self):
        """Test formatting validation error with empty result."""
        formatter = ErrorFormatter()
        result = ValidationResult(
            valid=True,
            errors=[],
            suggestions=[],
            examples=[],
        )
        formatted = formatter.format_validation_error(result)
        
        assert formatted == ""
    
    def test_format_validation_error_single_error(self):
        """Test formatting validation error with single error."""
        formatter = ErrorFormatter()
        result = ValidationResult(
            valid=False,
            errors=["--prompt argument is required"],
            suggestions=["Provide --prompt with feature description"],
            examples=['tapps-agents simple-mode build --prompt "Add feature"'],
        )
        formatted = formatter.format_validation_error(result)
        
        assert "Validation Error" in formatted
        assert "=" in formatted  # Separator line
        assert "Errors:" in formatted
        assert "--prompt argument is required" in formatted
        assert "Suggestions:" in formatted
        assert "Provide --prompt with feature description" in formatted
        assert "Examples:" in formatted
        assert 'tapps-agents simple-mode build --prompt "Add feature"' in formatted
    
    def test_format_validation_error_multiple_errors(self):
        """Test formatting validation error with multiple errors."""
        formatter = ErrorFormatter()
        result = ValidationResult(
            valid=False,
            errors=["Error 1", "Error 2"],
            suggestions=["Suggestion 1", "Suggestion 2"],
            examples=["Example 1", "Example 2"],
        )
        formatted = formatter.format_validation_error(result)
        
        assert "Errors:" in formatted
        assert "Error 1" in formatted
        assert "Error 2" in formatted
        assert "•" in formatted  # Bullet points
        assert "$" in formatted  # Example prefix
    
    def test_format_validation_error_no_suggestions(self):
        """Test formatting validation error without suggestions."""
        formatter = ErrorFormatter()
        result = ValidationResult(
            valid=False,
            errors=["Error 1"],
            suggestions=[],
            examples=[],
        )
        formatted = formatter.format_validation_error(result)
        
        assert "Error 1" in formatted
        assert "Suggestions:" not in formatted
        assert "Examples:" not in formatted
    
    def test_format_error_basic(self):
        """Test formatting general error."""
        formatter = ErrorFormatter()
        formatted = formatter.format_error(
            error_message="Something went wrong",
            error_type="Execution Error",
        )
        
        assert "Execution Error: Something went wrong" in formatted
        assert "=" in formatted  # Separator line
    
    def test_format_error_with_context(self):
        """Test formatting error with context."""
        formatter = ErrorFormatter()
        formatted = formatter.format_error(
            error_message="Network timeout",
            error_type="Network Error",
            context={"timeout": 30, "retries": 3},
        )
        
        assert "Network Error: Network timeout" in formatted
        assert "Context:" in formatted
        assert "timeout: 30" in formatted
        assert "retries: 3" in formatted
    
    def test_format_error_with_suggestion(self):
        """Test formatting error with suggestion."""
        formatter = ErrorFormatter()
        formatted = formatter.format_error(
            error_message="Config file not found",
            error_type="Configuration Error",
            suggestion="Run 'tapps-agents init' to create config file",
        )
        
        assert "Configuration Error: Config file not found" in formatted
        assert "Suggestion:" in formatted
        assert "Run 'tapps-agents init'" in formatted
    
    def test_format_error_with_example(self):
        """Test formatting error with example."""
        formatter = ErrorFormatter()
        formatted = formatter.format_error(
            error_message="Invalid command",
            error_type="Validation Error",
            example="tapps-agents simple-mode build --prompt 'feature'",
        )
        
        assert "Validation Error: Invalid command" in formatted
        assert "Example:" in formatted
        assert "tapps-agents simple-mode build" in formatted
    
    def test_format_error_complete(self):
        """Test formatting error with all fields."""
        formatter = ErrorFormatter()
        formatted = formatter.format_error(
            error_message="Workflow execution failed",
            error_type="Execution Error",
            context={"workflow_id": "wf-123", "step": 3},
            suggestion="Check workflow logs for details",
            example="tapps-agents simple-mode build --prompt 'feature'",
        )
        
        assert "Execution Error: Workflow execution failed" in formatted
        assert "Context:" in formatted
        assert "workflow_id: wf-123" in formatted
        assert "Suggestion:" in formatted
        assert "Example:" in formatted
