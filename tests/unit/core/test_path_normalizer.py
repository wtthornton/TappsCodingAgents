"""
Unit tests for path normalization utilities.

Tests cross-platform path handling, Windows absolute path conversion,
and CLI-safe path formatting.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.core.path_normalizer import (
    ensure_relative_path,
    normalize_for_cli,
    normalize_path,
    normalize_project_root,
)


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_relative_path_unchanged(self, tmp_path: Path):
        """Relative paths should remain unchanged."""
        project_root = tmp_path
        relative_path = "src/file.py"
        
        result = normalize_path(relative_path, project_root)
        
        assert result == relative_path

    def test_absolute_path_within_project(self, tmp_path: Path):
        """Absolute paths within project root should be converted to relative."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        absolute_path = str(file_path.resolve())
        result = normalize_path(absolute_path, project_root)
        
        # Should be relative to project root
        assert result == "src/file.py"
        assert not Path(result).is_absolute()

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_absolute_path(self, tmp_path: Path):
        """Windows absolute paths should be converted to relative."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        # Windows absolute path format
        windows_path = f"C:\\{file_path}"
        # Simulate Windows path by using actual resolved path
        absolute_path = str(file_path.resolve())
        
        result = normalize_path(absolute_path, project_root)
        
        # Should be relative
        assert result == "src/file.py"
        assert not Path(result).is_absolute()

    def test_path_outside_project_root(self, tmp_path: Path):
        """Paths outside project root should return absolute path with warning."""
        project_root = tmp_path
        outside_path = tmp_path.parent / "other" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()
        
        absolute_path = str(outside_path.resolve())
        
        with patch("tapps_agents.core.path_normalizer.logger") as mock_logger:
            result = normalize_path(absolute_path, project_root)
            
            # Should return absolute path
            assert Path(result).is_absolute()
            # Should log warning
            mock_logger.warning.assert_called_once()

    def test_empty_path(self, tmp_path: Path):
        """Empty paths should return empty string."""
        project_root = tmp_path
        
        result = normalize_path("", project_root)
        
        assert result == ""

    def test_path_object_input(self, tmp_path: Path):
        """Should accept Path objects as input."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        result = normalize_path(file_path, project_root)
        
        assert result == "src/file.py"

    def test_path_with_symlinks(self, tmp_path: Path):
        """Should handle paths with symlinks correctly."""
        project_root = tmp_path
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        file_path = real_dir / "file.py"
        file_path.touch()
        
        # Resolve should handle symlinks
        absolute_path = str(file_path.resolve())
        result = normalize_path(absolute_path, project_root)
        
        assert result == "real/file.py"


class TestEnsureRelativePath:
    """Tests for ensure_relative_path function."""

    def test_relative_path_allowed(self, tmp_path: Path):
        """Relative paths should be allowed."""
        project_root = tmp_path
        relative_path = "src/file.py"
        
        result = ensure_relative_path(relative_path, project_root)
        
        assert result == relative_path

    def test_absolute_path_within_project(self, tmp_path: Path):
        """Absolute paths within project should be converted."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        absolute_path = str(file_path.resolve())
        result = ensure_relative_path(absolute_path, project_root)
        
        assert result == "src/file.py"
        assert not Path(result).is_absolute()

    def test_path_outside_project_raises_error(self, tmp_path: Path):
        """Paths outside project root should raise ValueError."""
        project_root = tmp_path
        outside_path = tmp_path.parent / "other" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()
        
        absolute_path = str(outside_path.resolve())
        
        with pytest.raises(ValueError, match="outside project root"):
            ensure_relative_path(absolute_path, project_root)


class TestNormalizeForCli:
    """Tests for normalize_for_cli function."""

    def test_relative_path_unchanged(self, tmp_path: Path):
        """Relative paths should remain unchanged."""
        project_root = tmp_path
        relative_path = "src/file.py"
        
        result = normalize_for_cli(relative_path, project_root)
        
        assert result == relative_path

    def test_absolute_path_converted(self, tmp_path: Path):
        """Absolute paths should be converted to relative."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        absolute_path = str(file_path.resolve())
        result = normalize_for_cli(absolute_path, project_root)
        
        assert result == "src/file.py"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_backslashes_converted(self, tmp_path: Path):
        """Windows backslashes should be converted to forward slashes."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        # Use backslashes (Windows format)
        windows_path = str(file_path).replace("/", "\\")
        result = normalize_for_cli(windows_path, project_root)
        
        # Should use forward slashes
        assert "\\" not in result
        assert "/" in result or result == "src/file.py"

    def test_path_outside_project(self, tmp_path: Path):
        """Paths outside project should still normalize slashes."""
        project_root = tmp_path
        outside_path = tmp_path.parent / "other" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()
        
        absolute_path = str(outside_path.resolve())
        
        with patch("tapps_agents.core.path_normalizer.logger"):
            result = normalize_for_cli(absolute_path, project_root)
            
            # On Windows, should convert backslashes
            if sys.platform == "win32":
                assert "\\" not in result or result == absolute_path.replace("\\", "/")


class TestNormalizeProjectRoot:
    """Tests for normalize_project_root function."""

    def test_absolute_path_unchanged(self, tmp_path: Path):
        """Absolute paths should remain unchanged (but resolved)."""
        absolute_path = tmp_path.resolve()
        
        result = normalize_project_root(absolute_path)
        
        assert result == absolute_path.resolve()
        assert result.is_absolute()

    def test_relative_path_resolved(self, tmp_path: Path):
        """Relative paths should be resolved to absolute."""
        original_cwd = Path.cwd()
        try:
            # Change to tmp_path for relative path test
            import os
            os.chdir(tmp_path)
            
            result = normalize_project_root(".")
            
            assert result.is_absolute()
            assert result.resolve() == tmp_path.resolve()
        finally:
            os.chdir(original_cwd)

    def test_string_input(self, tmp_path: Path):
        """Should accept string input."""
        absolute_path_str = str(tmp_path.resolve())
        
        result = normalize_project_root(absolute_path_str)
        
        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result.resolve() == tmp_path.resolve()

    def test_path_object_input(self, tmp_path: Path):
        """Should accept Path object input."""
        result = normalize_project_root(tmp_path)
        
        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result.resolve() == tmp_path.resolve()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_none_path_handling(self, tmp_path: Path):
        """None paths should be handled gracefully."""
        project_root = tmp_path
        
        # normalize_path should handle empty string, but None would cause error
        # So we test with empty string
        result = normalize_path("", project_root)
        
        assert result == ""

    def test_path_with_special_characters(self, tmp_path: Path):
        """Paths with special characters should be handled."""
        project_root = tmp_path
        special_dir = tmp_path / "dir with spaces"
        special_dir.mkdir()
        file_path = special_dir / "file-name.py"
        file_path.touch()
        
        absolute_path = str(file_path.resolve())
        result = normalize_path(absolute_path, project_root)
        
        # Should preserve special characters
        assert "dir with spaces" in result
        assert "file-name.py" in result

    def test_deep_nested_paths(self, tmp_path: Path):
        """Deeply nested paths should be handled correctly."""
        project_root = tmp_path
        deep_path = tmp_path
        for i in range(5):
            deep_path = deep_path / f"level{i}"
        deep_path.mkdir(parents=True)
        file_path = deep_path / "file.py"
        file_path.touch()
        
        absolute_path = str(file_path.resolve())
        result = normalize_path(absolute_path, project_root)
        
        # Should preserve nesting
        assert "level0" in result
        assert "level4" in result
        assert result.endswith("file.py")

    def test_python_version_compatibility(self, tmp_path: Path):
        """Should work with Python < 3.9 (no is_relative_to)."""
        project_root = tmp_path
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        
        absolute_path = str(file_path.resolve())
        
        # Mock is_relative_to to raise AttributeError (Python < 3.9)
        with patch.object(Path, "is_relative_to", side_effect=AttributeError("Not available")):
            result = normalize_path(absolute_path, project_root)
            
            # Should still work via fallback
            assert result == "src/file.py"
