"""Tests for WorkflowDocumentationManager."""

import sys
from unittest.mock import patch

import pytest

from tapps_agents.simple_mode.documentation_manager import (
    DocumentationError,
    WorkflowDocumentationManager,
)


@pytest.fixture
def tmp_docs_dir(tmp_path):
    """Create temporary documentation directory."""
    return tmp_path / "docs" / "workflows" / "simple-mode"


@pytest.fixture
def doc_manager(tmp_docs_dir):
    """Create WorkflowDocumentationManager instance."""
    return WorkflowDocumentationManager(
        base_dir=tmp_docs_dir,
        workflow_id="test-workflow-123",
        create_symlink=False,
    )


class TestWorkflowDocumentationManager:
    """Test WorkflowDocumentationManager."""

    def test_generate_workflow_id_default(self):
        """Test workflow ID generation with default base name."""
        workflow_id = WorkflowDocumentationManager.generate_workflow_id()
        assert workflow_id.startswith("build-")
        assert len(workflow_id) > len("build-")

    def test_generate_workflow_id_custom(self):
        """Test workflow ID generation with custom base name."""
        workflow_id = WorkflowDocumentationManager.generate_workflow_id("test")
        assert workflow_id.startswith("test-")
        assert len(workflow_id) > len("test-")

    def test_generate_workflow_id_uniqueness(self):
        """Test that workflow IDs are unique."""
        id1 = WorkflowDocumentationManager.generate_workflow_id()
        id2 = WorkflowDocumentationManager.generate_workflow_id()
        assert id1 != id2

    def test_get_documentation_dir(self, doc_manager, tmp_docs_dir):
        """Test getting documentation directory."""
        expected = tmp_docs_dir / "test-workflow-123"
        assert doc_manager.get_documentation_dir() == expected

    def test_get_documentation_dir_caching(self, doc_manager):
        """Test that directory path is cached."""
        dir1 = doc_manager.get_documentation_dir()
        dir2 = doc_manager.get_documentation_dir()
        assert dir1 is dir2

    def test_get_step_file_path_with_name(self, doc_manager):
        """Test getting step file path with step name."""
        path = doc_manager.get_step_file_path(1, "enhanced-prompt")
        assert path.name == "step1-enhanced-prompt.md"
        assert path.parent == doc_manager.get_documentation_dir()

    def test_get_step_file_path_without_name(self, doc_manager):
        """Test getting step file path without step name."""
        path = doc_manager.get_step_file_path(1)
        assert path.name == "step1.md"
        assert path.parent == doc_manager.get_documentation_dir()

    def test_create_directory(self, doc_manager):
        """Test directory creation."""
        doc_dir = doc_manager.create_directory()
        assert doc_dir.exists()
        assert doc_dir.is_dir()

    def test_create_directory_existing(self, doc_manager):
        """Test directory creation when directory already exists."""
        doc_dir1 = doc_manager.create_directory()
        doc_dir2 = doc_manager.create_directory()  # Should not raise error
        assert doc_dir1 == doc_dir2

    def test_create_directory_permission_error(self, doc_manager):
        """Test directory creation with permission error."""
        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(DocumentationError):
                doc_manager.create_directory()

    def test_save_step_documentation(self, doc_manager):
        """Test saving step documentation."""
        content = "# Step 1: Enhanced Prompt\n\nTest content"
        file_path = doc_manager.save_step_documentation(1, content, "enhanced-prompt")

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content

    def test_save_step_documentation_creates_directory(self, doc_manager):
        """Test that save creates directory if needed."""
        content = "Test content"
        file_path = doc_manager.save_step_documentation(1, content)

        assert doc_manager.get_documentation_dir().exists()
        assert file_path.exists()

    def test_save_step_documentation_utf8(self, doc_manager):
        """Test that documentation saves with UTF-8 encoding."""
        content = "Test with unicode: ✅ ❌ ⚠️"
        file_path = doc_manager.save_step_documentation(1, content)

        assert file_path.read_text(encoding="utf-8") == content

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Symlink tests require Unix platform",
    )
    def test_create_latest_symlink_unix(self, doc_manager):
        """Test symlink creation on Unix."""
        doc_manager.create_symlink = True
        doc_manager.create_directory()
        symlink_path = doc_manager.create_latest_symlink()

        assert symlink_path is not None
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == doc_manager.get_documentation_dir()

    def test_create_latest_symlink_windows(self, doc_manager):
        """Test pointer file creation on Windows."""
        doc_manager.create_symlink = True
        doc_manager.create_directory()

        with patch("sys.platform", "win32"):
            symlink_path = doc_manager.create_latest_symlink()

            assert symlink_path is not None
            assert symlink_path.exists()
            assert "test-workflow-123" in symlink_path.read_text(encoding="utf-8")
