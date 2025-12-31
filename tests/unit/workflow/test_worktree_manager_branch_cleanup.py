"""
Unit tests for WorktreeManager branch cleanup functionality.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tapps_agents.workflow.worktree_manager import WorktreeManager

pytestmark = pytest.mark.unit


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git command."""
    return subprocess.run(  # nosec B603 - fixed args, no shell
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _init_git_repo(tmp_path: Path) -> Path:
    """Initialize a git repository for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")
    return repo


@pytest.mark.asyncio
async def test_delete_branch_success(tmp_path: Path) -> None:
    """Test successfully deleting an existing branch."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Create a test branch
    branch_name = "test-branch-123"
    _git(repo, "checkout", "-b", branch_name)
    _git(repo, "checkout", "main")  # Switch back to main
    
    # Verify branch exists
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name in result.stdout
    
    # Delete the branch
    success = manager._delete_branch(branch_name)
    assert success is True
    
    # Verify branch is deleted
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name not in result.stdout


@pytest.mark.asyncio
async def test_delete_branch_nonexistent(tmp_path: Path) -> None:
    """Test deleting a non-existent branch returns True (idempotent)."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Try to delete non-existent branch
    success = manager._delete_branch("nonexistent-branch-xyz")
    assert success is True  # Should return True (idempotent operation)


@pytest.mark.asyncio
async def test_delete_branch_unmerged_force(tmp_path: Path) -> None:
    """Test force deleting an unmerged branch."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Create a branch with a commit
    branch_name = "unmerged-branch"
    _git(repo, "checkout", "-b", branch_name)
    (repo / "unmerged.txt").write_text("unmerged content\n", encoding="utf-8")
    _git(repo, "add", "unmerged.txt")
    _git(repo, "commit", "-m", "unmerged commit")
    _git(repo, "checkout", "main")
    
    # Verify branch exists
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name in result.stdout
    
    # Delete should use force delete since branch is unmerged
    success = manager._delete_branch(branch_name)
    assert success is True
    
    # Verify branch is deleted
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name not in result.stdout


@pytest.mark.asyncio
async def test_remove_worktree_with_branch_deletion(tmp_path: Path) -> None:
    """Test removing worktree with branch deletion enabled."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Create a worktree (which creates a branch)
    wt = await manager.create_worktree("test-worktree")
    worktree_name = "test-worktree"
    branch_name = manager._branch_for(worktree_name)
    
    # Verify branch exists
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name in result.stdout
    
    # Remove worktree with branch deletion
    await manager.remove_worktree(worktree_name, delete_branch=True)
    
    # Verify worktree directory is removed
    assert not wt.exists()
    
    # Verify branch is deleted
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name not in result.stdout


@pytest.mark.asyncio
async def test_remove_worktree_without_branch_deletion(tmp_path: Path) -> None:
    """Test removing worktree without branch deletion."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Create a worktree (which creates a branch)
    wt = await manager.create_worktree("test-worktree-keep")
    worktree_name = "test-worktree-keep"
    branch_name = manager._branch_for(worktree_name)
    
    # Verify branch exists
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name in result.stdout
    
    # Remove worktree without branch deletion
    await manager.remove_worktree(worktree_name, delete_branch=False)
    
    # Verify worktree directory is removed
    assert not wt.exists()
    
    # Verify branch still exists
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name in result.stdout


@pytest.mark.asyncio
async def test_remove_worktree_backward_compatibility(tmp_path: Path) -> None:
    """Test remove_worktree default behavior (backward compatibility)."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Create a worktree
    wt = await manager.create_worktree("test-default")
    worktree_name = "test-default"
    branch_name = manager._branch_for(worktree_name)
    
    # Remove worktree with default parameters (delete_branch=True by default)
    await manager.remove_worktree(worktree_name)
    
    # Verify worktree is removed
    assert not wt.exists()
    
    # Verify branch is deleted (default behavior)
    result = _git(repo, "branch", "--list", branch_name)
    assert branch_name not in result.stdout


@pytest.mark.asyncio
async def test_remove_worktree_nonexistent(tmp_path: Path) -> None:
    """Test removing a non-existent worktree doesn't fail."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Try to remove non-existent worktree (should not raise)
    await manager.remove_worktree("nonexistent-worktree", delete_branch=True)


@pytest.mark.asyncio
async def test_remove_worktree_branch_already_deleted(tmp_path: Path) -> None:
    """Test removing worktree when branch is already deleted."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)
    
    # Create a worktree
    wt = await manager.create_worktree("test-already-deleted")
    worktree_name = "test-already-deleted"
    branch_name = manager._branch_for(worktree_name)
    
    # Manually delete the branch first
    _git(repo, "branch", "-D", branch_name)
    
    # Remove worktree (should handle missing branch gracefully)
    await manager.remove_worktree(worktree_name, delete_branch=True)
    
    # Verify worktree is removed
    assert not wt.exists()
