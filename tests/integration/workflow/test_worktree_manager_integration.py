"""
Integration tests for WorktreeManager.

These tests use real git commands (subprocess) and a real filesystem to validate
WorktreeManager behavior. They belong in integration/ rather than unit/ because:
- They invoke real `git` via subprocess
- They test the full interaction: WorktreeManager + git + filesystem
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tapps_agents.workflow.worktree_manager import WorktreeManager

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603 - fixed args, no shell
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _init_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")
    return repo


async def test_create_worktree_branch_already_exists(tmp_path: Path) -> None:
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    wt1 = await manager.create_worktree("example")
    assert wt1.exists()

    # Remove the worktree directory (branch should remain).
    await manager.remove_worktree("example")

    # Re-create with same name should succeed even though branch exists.
    wt2 = await manager.create_worktree("example")
    assert wt2.exists()


async def test_create_worktree_fallback_copies_repo_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Create a project-like structure (not necessarily a git repo).
    project_root = tmp_path / "project"
    (project_root / "tapps_agents").mkdir(parents=True)
    (project_root / "tests").mkdir(parents=True)
    (project_root / "docs").mkdir(parents=True)
    (project_root / "workflows").mkdir(parents=True)
    (project_root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (project_root / "README.md").write_text("readme\n", encoding="utf-8")

    manager = WorktreeManager(project_root=project_root)

    def _always_fail(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise subprocess.CalledProcessError(returncode=1, cmd=kwargs.get("args") or args[0])

    monkeypatch.setattr(subprocess, "run", _always_fail)

    wt = await manager.create_worktree("fallback")
    assert (wt / "tapps_agents").exists()
    assert (wt / "tests").exists()
    assert (wt / "docs").exists()
    assert (wt / "workflows").exists()
    assert (wt / "pyproject.toml").exists()


async def test_cleanup_all_removes_only_worktrees_dir(tmp_path: Path) -> None:
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    wt = await manager.create_worktree("one")
    assert wt.exists()

    # Create a sentinel outside the worktrees dir to ensure we don't delete it.
    sentinel = repo / "SENTINEL.txt"
    sentinel.write_text("do-not-delete", encoding="utf-8")

    await manager.cleanup_all()
    assert sentinel.exists()


async def test_merge_worktree_clean_merge(tmp_path: Path) -> None:
    """Test clean merge case - no conflicts."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    # Create initial file
    (repo / "main.txt").write_text("main content\n", encoding="utf-8")
    _git(repo, "add", "main.txt")
    _git(repo, "commit", "-m", "Add main.txt")

    # Create worktree and make changes
    worktree_path = await manager.create_worktree("test-merge")
    (worktree_path / "worktree.txt").write_text("worktree content\n", encoding="utf-8")
    _git(worktree_path, "add", "worktree.txt")
    _git(worktree_path, "commit", "-m", "Add worktree.txt")

    # Ensure main repo working tree is clean (worktree creation might leave traces)
    try:
        _git(repo, "reset", "--hard", "HEAD")
        _git(repo, "clean", "-fd")
    except subprocess.CalledProcessError:
        pass

    # Merge worktree branch into main
    result = await manager.merge_worktree("test-merge")

    assert result["success"] is True
    assert result["has_conflicts"] is False
    assert len(result["conflicted_files"]) == 0
    assert result["error"] is None

    # Verify merge was successful
    assert (repo / "worktree.txt").exists()
    assert (repo / "worktree.txt").read_text(encoding="utf-8") == "worktree content\n"


async def test_merge_worktree_with_conflicts(tmp_path: Path) -> None:
    """Test merge with conflicts - verify conflict detection and report generation."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    # Create initial file in main branch
    (repo / "conflict.txt").write_text("main version\n", encoding="utf-8")
    _git(repo, "add", "conflict.txt")
    _git(repo, "commit", "-m", "Add conflict.txt")

    # Create worktree and modify same file differently
    worktree_path = await manager.create_worktree("test-conflict")
    (worktree_path / "conflict.txt").write_text("worktree version\n", encoding="utf-8")
    _git(worktree_path, "add", "conflict.txt")
    _git(worktree_path, "commit", "-m", "Modify conflict.txt in worktree")

    # Ensure main repo working tree is clean
    try:
        _git(repo, "reset", "--hard", "HEAD")
    except subprocess.CalledProcessError:
        pass

    # Modify file in main branch to create conflict
    (repo / "conflict.txt").write_text("main modified\n", encoding="utf-8")
    _git(repo, "add", "conflict.txt")
    _git(repo, "commit", "-m", "Modify conflict.txt in main")

    # Attempt merge - should detect conflicts
    result = await manager.merge_worktree("test-conflict")

    assert result["success"] is False
    assert result["has_conflicts"] is True
    assert len(result["conflicted_files"]) > 0
    assert "conflict.txt" in result["conflicted_files"]
    assert result["conflict_report_path"] is not None
    assert result["conflict_report_path"].exists()

    # Verify conflict report content
    report_data = json.loads(result["conflict_report_path"].read_text(encoding="utf-8"))
    assert report_data["worktree_name"] == "test-conflict"
    assert report_data["conflict_count"] > 0
    assert "conflict.txt" in report_data["conflicted_files"]
    assert "guidance" in report_data
    assert "resolution_steps" in report_data["guidance"]

    # Verify working tree is in conflicted state
    status_result = _git(repo, "status", "--porcelain")
    assert "UU" in status_result.stdout or "conflict.txt" in status_result.stdout

    # Test abort merge
    abort_success = await manager.abort_merge()
    assert abort_success is True

    # Verify working tree is clean after abort
    status_result = _git(repo, "status", "--porcelain")
    assert not status_result.stdout.strip() or "conflict.txt" not in status_result.stdout

    # Verify original content is restored
    assert (repo / "conflict.txt").read_text(encoding="utf-8") == "main modified\n"


async def test_merge_worktree_requires_clean_working_tree(tmp_path: Path) -> None:
    """Test that merge fails if working tree is not clean."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    # Create initial file and commit
    (repo / "main.txt").write_text("main content\n", encoding="utf-8")
    _git(repo, "add", "main.txt")
    _git(repo, "commit", "-m", "Add main.txt")

    # Create worktree
    worktree_path = await manager.create_worktree("test-dirty")
    (worktree_path / "worktree.txt").write_text("worktree content\n", encoding="utf-8")
    _git(worktree_path, "add", "worktree.txt")
    _git(worktree_path, "commit", "-m", "Add worktree.txt")

    # Create uncommitted changes in main repo (tracked file modification)
    (repo / "main.txt").write_text("modified but not committed\n", encoding="utf-8")
    _git(repo, "add", "main.txt")  # Stage it to make it a tracked change

    # Attempt merge should fail due to dirty working tree
    with pytest.raises(ValueError, match="Working tree is not clean"):
        await manager.merge_worktree("test-dirty")


async def test_merge_worktree_nonexistent_worktree(tmp_path: Path) -> None:
    """Test that merge fails for nonexistent worktree."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    with pytest.raises(ValueError, match="does not exist"):
        await manager.merge_worktree("nonexistent")


async def test_abort_merge_no_merge_in_progress(tmp_path: Path) -> None:
    """Test that abort returns False when no merge is in progress."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    result = await manager.abort_merge()
    assert result is False


async def test_merge_worktree_specific_target_branch(tmp_path: Path) -> None:
    """Test merging into a specific target branch."""
    repo = _init_git_repo(tmp_path)
    manager = WorktreeManager(project_root=repo)

    # Create initial file
    (repo / "main.txt").write_text("main content\n", encoding="utf-8")
    _git(repo, "add", "main.txt")
    _git(repo, "commit", "-m", "Add main.txt")

    # Create a target branch
    _git(repo, "checkout", "-b", "target-branch")

    # Ensure working tree is clean
    try:
        _git(repo, "reset", "--hard", "HEAD")
    except subprocess.CalledProcessError:
        pass

    # Create worktree and make changes
    worktree_path = await manager.create_worktree("test-target")
    (worktree_path / "worktree.txt").write_text("worktree content\n", encoding="utf-8")
    _git(worktree_path, "add", "worktree.txt")
    _git(worktree_path, "commit", "-m", "Add worktree.txt")

    # Ensure working tree is still clean before merge
    try:
        _git(repo, "reset", "--hard", "HEAD")
    except subprocess.CalledProcessError:
        pass

    # Merge into specific target branch
    result = await manager.merge_worktree("test-target", target_branch="target-branch")

    assert result["success"] is True
    assert result["has_conflicts"] is False

    # Verify merge was successful on target branch
    assert (repo / "worktree.txt").exists()
    assert (repo / "worktree.txt").read_text(encoding="utf-8") == "worktree content\n"
