"""
Tests for temp_directory.py
"""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.core.temp_directory import (
    TempDirectoryManager,
    needs_git_operations,
)


class TestTempDirectoryManager:
    """Test TempDirectoryManager class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        manager = TempDirectoryManager()
        
        assert manager.base_dir is None
        assert manager.prefix == "tapps-agent-"
        assert manager.cleanup_on_exit is True
        assert len(manager.temp_dirs) == 0

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            manager = TempDirectoryManager(
                base_dir=base_dir,
                prefix="custom-",
                cleanup_on_exit=False,
            )
            
            assert manager.base_dir == base_dir
            assert manager.prefix == "custom-"
            assert manager.cleanup_on_exit is False

    def test_create_temp_dir(self):
        """Test creating a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            manager = TempDirectoryManager(base_dir=base_dir)
            
            temp_path = manager.create_temp_dir("task-1")
            
            assert temp_path.exists()
            assert temp_path.is_dir()
            assert temp_path.name.startswith("tapps-agent-")
            assert manager.get_temp_dir("task-1") == temp_path

    def test_create_temp_dir_with_copy(self):
        """Test creating temp directory with file copy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            source_dir = base_dir / "source"
            source_dir.mkdir()
            
            # Create a test file
            test_file = source_dir / "test.txt"
            test_file.write_text("test content")
            
            manager = TempDirectoryManager(base_dir=base_dir)
            temp_path = manager.create_temp_dir("task-1", copy_from=source_dir)
            
            # Check that file was copied
            copied_file = temp_path / "test.txt"
            assert copied_file.exists()
            assert copied_file.read_text() == "test content"

    def test_get_temp_dir(self):
        """Test getting temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            manager = TempDirectoryManager(base_dir=base_dir)
            
            # Create temp dir
            temp_path = manager.create_temp_dir("task-1")
            
            # Get temp dir
            retrieved_path = manager.get_temp_dir("task-1")
            
            assert retrieved_path == temp_path

    def test_get_temp_dir_not_found(self):
        """Test getting non-existent temp directory."""
        manager = TempDirectoryManager()
        
        result = manager.get_temp_dir("non-existent")
        
        assert result is None

    def test_remove_temp_dir(self):
        """Test removing temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            manager = TempDirectoryManager(base_dir=base_dir)
            
            # Create temp dir
            temp_path = manager.create_temp_dir("task-1")
            assert temp_path.exists()
            
            # Remove temp dir
            result = manager.remove_temp_dir("task-1")
            
            assert result is True
            assert not temp_path.exists()
            assert manager.get_temp_dir("task-1") is None

    def test_remove_temp_dir_not_found(self):
        """Test removing non-existent temp directory."""
        manager = TempDirectoryManager()
        
        result = manager.remove_temp_dir("non-existent")
        
        assert result is False

    def test_cleanup_all(self):
        """Test cleaning up all temporary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            manager = TempDirectoryManager(base_dir=base_dir)
            
            # Create multiple temp dirs
            temp1 = manager.create_temp_dir("task-1")
            temp2 = manager.create_temp_dir("task-2")
            temp3 = manager.create_temp_dir("task-3")
            
            assert len(manager.temp_dirs) == 3
            
            # Cleanup all
            cleaned = manager.cleanup_all()
            
            assert cleaned == 3
            assert len(manager.temp_dirs) == 0
            assert not temp1.exists()
            assert not temp2.exists()
            assert not temp3.exists()

    def test_copy_directory(self):
        """Test copying directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create files and subdirectories
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "file2.txt").write_text("content2")
            subdir = source_dir / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")
            
            manager = TempDirectoryManager()
            manager._copy_directory(source_dir, dest_dir)
            
            # Check files were copied
            assert (dest_dir / "file1.txt").exists()
            assert (dest_dir / "file2.txt").exists()
            assert (dest_dir / "subdir" / "file3.txt").exists()
            
            # Check content
            assert (dest_dir / "file1.txt").read_text() == "content1"
            assert (dest_dir / "subdir" / "file3.txt").read_text() == "content3"


def test_needs_git_operations():
    """Test needs_git_operations function."""
    # Tasks that need git
    assert needs_git_operations("implementer", ["implement"]) is True
    assert needs_git_operations("refactor", ["refactor"]) is True
    assert needs_git_operations("workflow", ["run"]) is True
    
    # Commands with git indicators
    assert needs_git_operations("reviewer", ["git status"]) is True
    assert needs_git_operations("tester", ["commit changes"]) is True
    assert needs_git_operations("reviewer", ["create branch"]) is True
    
    # Tasks that don't need git
    assert needs_git_operations("reviewer", ["review"]) is False
    assert needs_git_operations("tester", ["test"]) is False
    assert needs_git_operations("documenter", ["document"]) is False
