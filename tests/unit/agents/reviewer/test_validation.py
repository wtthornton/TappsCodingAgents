"""
Unit tests for Input Validation Utilities.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.validation import (
    validate_boolean,
    validate_code_input,
    validate_code_string,
    validate_file_path,
    validate_file_path_input,
    validate_inputs,
    validate_non_negative_float,
    validate_positive_int,
)

pytestmark = pytest.mark.unit


class TestValidationFunctions:
    """Tests for validation utility functions."""

    def test_validate_file_path_valid(self, tmp_path):
        """Test validating valid file path."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test")
        assert validate_file_path(test_file) is True

    def test_validate_file_path_none(self):
        """Test validating None file path."""
        assert validate_file_path(None) is False

    def test_validate_file_path_not_path(self):
        """Test validating non-Path file path."""
        assert validate_file_path("not_a_path") is False

    def test_validate_file_path_not_exists(self, tmp_path):
        """Test validating non-existent file path."""
        nonexistent = tmp_path / "nonexistent.py"
        assert validate_file_path(nonexistent) is False

    def test_validate_code_string_valid(self):
        """Test validating valid code string."""
        assert validate_code_string("def hello(): pass") is True

    def test_validate_code_string_empty(self):
        """Test validating empty code string."""
        assert validate_code_string("") is False

    def test_validate_code_string_whitespace_only(self):
        """Test validating whitespace-only code string."""
        assert validate_code_string("   \n\t  ") is False

    def test_validate_code_string_none(self):
        """Test validating None code string."""
        assert validate_code_string(None) is False

    def test_validate_boolean_true(self):
        """Test validating True boolean."""
        assert validate_boolean(True) is True

    def test_validate_boolean_false(self):
        """Test validating False boolean."""
        assert validate_boolean(False) is True

    def test_validate_boolean_invalid(self):
        """Test validating non-boolean."""
        assert validate_boolean("true") is False
        assert validate_boolean(1) is False

    def test_validate_positive_int_valid(self):
        """Test validating valid positive integer."""
        assert validate_positive_int(5) is True

    def test_validate_positive_int_zero(self):
        """Test validating zero (not positive)."""
        assert validate_positive_int(0) is False

    def test_validate_positive_int_negative(self):
        """Test validating negative integer."""
        assert validate_positive_int(-5) is False

    def test_validate_non_negative_float_valid(self):
        """Test validating valid non-negative float."""
        assert validate_non_negative_float(5.5) is True
        assert validate_non_negative_float(0.0) is True

    def test_validate_non_negative_float_negative(self):
        """Test validating negative float."""
        assert validate_non_negative_float(-5.5) is False

    def test_validate_non_negative_float_int(self):
        """Test validating integer (should work)."""
        assert validate_non_negative_float(5) is True


class TestValidateCodeInput:
    """Tests for validate_code_input function."""

    def test_validate_code_input_valid(self):
        """Test validating valid code input."""
        validate_code_input("def hello(): pass", "test_method")

    def test_validate_code_input_empty(self):
        """Test validating empty code input raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            validate_code_input("", "test_method")

    def test_validate_code_input_none(self):
        """Test validating None code input raises ValueError."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            validate_code_input(None, "test_method")


class TestValidateFilePathInput:
    """Tests for validate_file_path_input function."""

    def test_validate_file_path_input_valid(self, tmp_path):
        """Test validating valid file path input."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test")
        result = validate_file_path_input(test_file, must_exist=True, method_name="test")
        assert isinstance(result, Path)
        assert result == test_file

    def test_validate_file_path_input_string(self, tmp_path):
        """Test validating string file path input."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test")
        result = validate_file_path_input(str(test_file), must_exist=True, method_name="test")
        assert isinstance(result, Path)

    def test_validate_file_path_input_none(self):
        """Test validating None file path input raises ValueError."""
        with pytest.raises(ValueError, match="cannot be None"):
            validate_file_path_input(None, must_exist=True, method_name="test")

    def test_validate_file_path_input_not_exists(self, tmp_path):
        """Test validating non-existent file path raises FileNotFoundError."""
        nonexistent = tmp_path / "nonexistent.py"
        with pytest.raises(FileNotFoundError):
            validate_file_path_input(nonexistent, must_exist=True, method_name="test")

    def test_validate_file_path_input_directory(self, tmp_path):
        """Test validating directory as file path raises ValueError."""
        with pytest.raises(ValueError, match="must be a file"):
            validate_file_path_input(tmp_path, must_exist=True, method_name="test")


class TestValidateInputsDecorator:
    """Tests for @validate_inputs decorator."""

    @validate_inputs(
        value=validate_boolean,
        count=validate_positive_int,
    )
    async def async_validated_method(self, value: bool, count: int):
        """Async method with validation."""
        return value, count

    @validate_inputs(
        value=validate_boolean,
        count=validate_positive_int,
    )
    def sync_validated_method(self, value: bool, count: int):
        """Sync method with validation."""
        return value, count

    @pytest.mark.asyncio
    async def test_validate_inputs_async_valid(self):
        """Test async method with valid inputs."""
        result = await self.async_validated_method(True, 5)
        assert result == (True, 5)

    @pytest.mark.asyncio
    async def test_validate_inputs_async_invalid(self):
        """Test async method with invalid inputs raises ValueError."""
        with pytest.raises(ValueError, match="Invalid.*value"):
            await self.async_validated_method("not_bool", 5)

    def test_validate_inputs_sync_valid(self):
        """Test sync method with valid inputs."""
        result = self.sync_validated_method(True, 5)
        assert result == (True, 5)

    def test_validate_inputs_sync_invalid(self):
        """Test sync method with invalid inputs raises ValueError."""
        with pytest.raises(ValueError, match="Invalid.*count"):
            self.sync_validated_method(True, -5)

    @validate_inputs(value=validate_boolean)
    def method_with_default(self, value: bool = True):
        """Method with default parameter."""
        return value

    def test_validate_inputs_with_default(self):
        """Test validation with default parameter."""
        result = self.method_with_default()
        assert result is True
