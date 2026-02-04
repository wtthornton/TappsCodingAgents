"""
Tests for exception naming and validation maintainability.

Epic 26: Core Maintainability — Unify Errors and Validation
- Story 26.1: Prevent stdlib-shadowing exception names
- Story 26.2: Ensure centralized validation usage
"""

import builtins
import inspect

import pytest

from tapps_agents.core import exceptions
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.path_validator import PathValidator

pytestmark = pytest.mark.unit

# Python built-in exceptions that should not be shadowed
STDLIB_EXCEPTIONS = {
    name
    for name, obj in inspect.getmembers(builtins)
    if inspect.isclass(obj) and issubclass(obj, BaseException) and obj is not BaseException
}


class TestExceptionNaming:
    """Test that custom exceptions don't shadow stdlib exceptions."""

    def test_no_stdlib_shadowing(self):
        """Test that no custom exception class shadows a Python built-in exception."""
        custom_exceptions = {
            name: obj
            for name, obj in inspect.getmembers(exceptions)
            if inspect.isclass(obj)
            and issubclass(obj, BaseException)
            and obj is not BaseException
        }

        shadowing = []
        for name, _exc_class in custom_exceptions.items():
            if name in STDLIB_EXCEPTIONS:
                shadowing.append(name)

        assert not shadowing, (
            f"Custom exceptions shadow Python built-ins: {shadowing}. "
            f"Rename these to avoid ambiguity (e.g., FileNotFoundError -> AgentFileNotFoundError)."
        )

    def test_agent_file_not_found_error_exists(self):
        """Test that AgentFileNotFoundError exists and doesn't shadow built-in."""
        assert hasattr(exceptions, "AgentFileNotFoundError")
        assert issubclass(exceptions.AgentFileNotFoundError, exceptions.FileOperationError)
        assert exceptions.AgentFileNotFoundError is not FileNotFoundError

    def test_file_not_found_error_alias_deprecated(self):
        """Test that FileNotFoundError alias exists for backwards compatibility."""
        # The alias should exist but be the same as AgentFileNotFoundError
        assert hasattr(exceptions, "FileNotFoundError")
        assert exceptions.FileNotFoundError is exceptions.AgentFileNotFoundError


class TestCentralizedValidation:
    """Test that centralized validation is used correctly."""

    def test_base_agent_has_validate_path(self):
        """Test that BaseAgent has _validate_path method."""
        assert hasattr(BaseAgent, "_validate_path")
        assert callable(BaseAgent._validate_path)

    def test_path_validator_exists(self):
        """Test that PathValidator class exists."""
        assert PathValidator is not None
        assert hasattr(PathValidator, "validate_path")
        assert hasattr(PathValidator, "validate_read_path")
        assert hasattr(PathValidator, "validate_write_path")

    def test_base_agent_uses_path_validator(self):
        """Test that BaseAgent._validate_path uses PathValidator."""
        # Check that _validate_path imports and uses PathValidator
        source = inspect.getsource(BaseAgent._validate_path)
        assert "PathValidator" in source or "path_validator" in source

    def test_path_validator_raises_appropriate_exceptions(self, tmp_path):
        """Test that PathValidator raises appropriate exceptions."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".tapps-agents").mkdir()
        validator = PathValidator(project_root)
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            validator.validate_read_path(project_root / "nonexistent.py")
        
        # Test with path outside allowed roots
        outside_path = tmp_path / "outside" / "file.py"
        outside_path.parent.mkdir()
        outside_path.write_text("test")
        with pytest.raises(Exception):  # Should raise PathValidationError or ValueError
            validator.validate_read_path(outside_path)

