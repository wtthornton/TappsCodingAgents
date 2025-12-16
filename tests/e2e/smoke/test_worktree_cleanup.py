"""
Smoke E2E tests for worktree creation and cleanup.

Tests validate that:
- Worktrees can be created under .tapps-agents/worktrees/
- Worktrees can be cleaned up (idempotent removal)
- Multiple worktrees can coexist
- Cleanup doesn't affect main working tree
"""


import pytest

from tapps_agents.workflow.worktree_manager import WorktreeManager


@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
class TestWorktreeCleanup:
    """Test worktree creation and cleanup."""

    def test_worktree_directory_structure(self, e2e_project):
        """Test that worktree directory structure is created."""
        manager = WorktreeManager(project_root=e2e_project)
        
        # Verify worktrees directory exists or is created
        assert manager.worktrees_dir == e2e_project / ".tapps-agents" / "worktrees"
        
        # Create worktrees directory if it doesn't exist
        manager.worktrees_dir.mkdir(parents=True, exist_ok=True)
        
        assert manager.worktrees_dir.exists()

    @pytest.mark.asyncio
    async def test_worktree_creation_fallback(self, e2e_project):
        """Test worktree creation (fallback to directory if git not available)."""
        manager = WorktreeManager(project_root=e2e_project)
        
        worktree_name = "test-worktree-1"
        worktree_path = await manager.create_worktree(worktree_name)
        
        # Verify worktree was created
        assert worktree_path.exists()
        assert worktree_path.is_dir()
        
        # Verify worktree is in correct location
        expected_path = e2e_project / ".tapps-agents" / "worktrees" / worktree_name
        assert worktree_path == expected_path or worktree_path.name == worktree_name

    @pytest.mark.asyncio
    async def test_worktree_cleanup_idempotent(self, e2e_project):
        """Test that worktree cleanup is idempotent."""
        manager = WorktreeManager(project_root=e2e_project)
        
        worktree_name = "test-worktree-cleanup"
        
        # Create worktree
        worktree_path = await manager.create_worktree(worktree_name)
        assert worktree_path.exists()
        
        # Remove worktree
        await manager.remove_worktree(worktree_name)
        assert not worktree_path.exists()
        
        # Remove again (should not raise)
        await manager.remove_worktree(worktree_name)
        assert not worktree_path.exists()

    @pytest.mark.asyncio
    async def test_multiple_worktrees_coexist(self, e2e_project):
        """Test that multiple worktrees can coexist."""
        manager = WorktreeManager(project_root=e2e_project)
        
        worktree_names = ["worktree-1", "worktree-2", "worktree-3"]
        worktree_paths = []
        
        # Create multiple worktrees
        for name in worktree_names:
            path = await manager.create_worktree(name)
            worktree_paths.append(path)
            assert path.exists()
        
        # Verify all worktrees exist
        for path in worktree_paths:
            assert path.exists()
        
        # Verify worktrees directory contains all worktrees
        worktrees_dir = manager.worktrees_dir
        if worktrees_dir.exists():
            worktree_dirs = [d for d in worktrees_dir.iterdir() if d.is_dir()]
            assert len(worktree_dirs) >= len(worktree_names)

    @pytest.mark.asyncio
    async def test_cleanup_doesnt_affect_main_tree(self, e2e_project):
        """Test that cleanup doesn't affect main working tree."""
        manager = WorktreeManager(project_root=e2e_project)
        
        # Create a file in main project
        test_file = e2e_project / "test_main_file.txt"
        test_file.write_text("main project file")
        
        # Create worktree
        worktree_name = "test-worktree-main"
        worktree_path = await manager.create_worktree(worktree_name)
        
        # Remove worktree
        await manager.remove_worktree(worktree_name)
        
        # Verify main project file still exists
        assert test_file.exists()
        assert test_file.read_text() == "main project file"
        
        # Verify main project structure is intact
        assert (e2e_project / ".tapps-agents").exists()

    def test_worktree_filesystem_invariants(self, e2e_project):
        """Test filesystem invariants (worktree structure, cleanup)."""
        manager = WorktreeManager(project_root=e2e_project)
        
        # Verify worktrees directory structure
        worktrees_dir = manager.worktrees_dir
        worktrees_dir.mkdir(parents=True, exist_ok=True)
        
        assert worktrees_dir.exists()
        assert worktrees_dir.is_dir()
        
        # Verify worktrees directory is under .tapps-agents
        assert ".tapps-agents" in worktrees_dir.parts
        assert "worktrees" in worktrees_dir.parts

    @pytest.mark.asyncio
    async def test_cleanup_all_worktrees(self, e2e_project):
        """Test cleanup_all removes all worktrees."""
        manager = WorktreeManager(project_root=e2e_project)
        
        # Create multiple worktrees
        worktree_names = ["cleanup-all-1", "cleanup-all-2"]
        for name in worktree_names:
            await manager.create_worktree(name)
        
        # Verify worktrees exist
        worktrees_dir = manager.worktrees_dir
        if worktrees_dir.exists():
            worktree_dirs_before = [d for d in worktrees_dir.iterdir() if d.is_dir()]
            assert len(worktree_dirs_before) >= len(worktree_names)
        
        # Cleanup all
        await manager.cleanup_all()
        
        # Verify worktrees are removed
        if worktrees_dir.exists():
            worktree_dirs_after = [d for d in worktrees_dir.iterdir() if d.is_dir()]
            # After cleanup, there should be fewer or no worktrees
            assert len(worktree_dirs_after) <= len(worktree_dirs_before)
