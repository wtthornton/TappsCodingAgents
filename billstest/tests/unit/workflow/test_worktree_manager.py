"""
Unit tests for Worktree Manager.
"""

from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.workflow.worktree_manager import WorktreeManager

pytestmark = pytest.mark.unit


class TestWorktreeManager:
    """Test cases for WorktreeManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a WorktreeManager instance."""
        return WorktreeManager(project_root=tmp_path)

    def test_manager_initialization(self, manager, tmp_path):
        """Test manager initialization."""
        assert manager.project_root == tmp_path
        assert manager.worktrees_dir == tmp_path / ".tapps-agents" / "worktrees"

    def test_sanitize_component(self):
        """Test component sanitization."""
        # Test basic sanitization
        result = WorktreeManager._sanitize_component("test-worktree")
        assert result == "test-worktree"
        
        # Test with invalid characters
        result = WorktreeManager._sanitize_component("test/worktree")
        assert "/" not in result
        
        # Test with long name
        long_name = "a" * 200
        result = WorktreeManager._sanitize_component(long_name)
        assert len(result) <= 80

    def test_safe_worktree_name(self, manager):
        """Test safe worktree name generation."""
        result = manager._safe_worktree_name("test-worktree")
        assert result == "test-worktree"
        
        # Test with path traversal attempt
        with pytest.raises(ValueError):
            manager._safe_worktree_name("../test")

    def test_worktree_path_for(self, manager):
        """Test worktree path generation."""
        path = manager._worktree_path_for("test-worktree")
        assert path == manager.worktrees_dir / "test-worktree"

    def test_branch_for(self, manager):
        """Test branch name generation."""
        branch = manager._branch_for("test-worktree")
        assert branch.startswith("workflow/")
        assert "test" in branch.lower()

    @pytest.mark.asyncio
    async def test_create_worktree_fallback(self, manager, tmp_path):
        """Test worktree creation with git fallback."""
        # Mock git to fail (simulate no git repo)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Git not available")
            
            worktree_path = await manager.create_worktree("test-worktree")
            
            assert worktree_path.exists()
            # Should create directory even if git fails

    @pytest.mark.asyncio
    async def test_remove_worktree(self, manager, tmp_path):
        """Test removing a worktree."""
        worktree_path = manager.worktrees_dir / "test-worktree"
        worktree_path.mkdir(parents=True)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            await manager.remove_worktree("test-worktree")
            
            # Should attempt to remove worktree
            mock_run.assert_called()

    def test_copy_project_files(self, manager, tmp_path):
        """Test copying project files."""
        # Create some test files
        (tmp_path / "test.py").write_text("def test(): pass")
        (tmp_path / "README.md").write_text("# Test")
        
        dest = tmp_path / "worktree"
        dest.mkdir()
        
        manager._copy_project_files(dest)
        
        # Should create .tapps-agents directory
        assert (dest / ".tapps-agents").exists()

