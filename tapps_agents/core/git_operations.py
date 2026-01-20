"""
Git operations utility module.

Provides functions for git commit, push, and branch operations.
Used by bug fix agent for automatic commit functionality.
"""

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _ensure_utf8_encoding() -> None:
    """Ensure UTF-8 encoding for Windows console output."""
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            # Python < 3.7 - use environment variable only
            pass


def _get_git_path() -> str:
    """Get git executable path."""
    return shutil.which("git") or "git"


def _run_git_command(
    args: list[str],
    cwd: Path | None = None,
    capture_output: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Run a git command with proper encoding.

    Args:
        args: Git command arguments (e.g., ['status', '--porcelain'])
        cwd: Working directory (default: current directory)
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise on non-zero exit code

    Returns:
        CompletedProcess with stdout/stderr
    """
    _ensure_utf8_encoding()
    git_path = _get_git_path()
    cwd = cwd or Path.cwd()

    try:
        result = subprocess.run(
            [git_path] + args,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e) if e.stderr else str(e)
        logger.error(f"Git command failed: {' '.join([git_path] + args)}\nError: {error_msg}")
        raise
    except FileNotFoundError:
        raise RuntimeError("Git is not installed or not found in PATH")


def check_git_available() -> bool:
    """Check if Git is available."""
    return shutil.which("git") is not None


def is_git_repository(path: Path | None = None) -> bool:
    """Check if path is a git repository."""
    path = path or Path.cwd()
    return (path / ".git").exists() or (path / ".git").is_dir()


def get_current_branch(path: Path | None = None) -> str:
    """Get the current git branch name."""
    path = path or Path.cwd()
    result = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path, check=True)
    return result.stdout.strip()


def check_uncommitted_changes(path: Path | None = None) -> list[str]:
    """Check for uncommitted changes."""
    path = path or Path.cwd()
    result = _run_git_command(["status", "--porcelain"], cwd=path, check=True)
    lines = result.stdout.strip().split("\n")
    return [line for line in lines if line.strip()]


def create_and_checkout_branch(branch_name: str, path: Path | None = None) -> dict[str, Any]:
    """
    Create a new branch and check it out.

    Args:
        branch_name: Name of the new branch
        path: Path to git repository (default: current directory)

    Returns:
        Dictionary with success status and branch name
    """
    path = path or Path.cwd()

    if not check_git_available():
        raise RuntimeError("Git is not installed or not in PATH")

    if not is_git_repository(path):
        raise RuntimeError(f"Not a git repository: {path}")

    try:
        # Create and checkout branch
        _run_git_command(["checkout", "-b", branch_name], cwd=path, check=True)
        logger.info(f"Created and checked out branch: {branch_name}")
        return {"success": True, "branch": branch_name, "error": None}
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e) if e.stderr else str(e)
        logger.error(f"Failed to create branch: {error_msg}")
        # If branch already exists, try to checkout (plan 2.3 branch-for-agent-changes)
        if "already exists" in error_msg.lower():
            try:
                _run_git_command(["checkout", branch_name], cwd=path, check=True)
                logger.info(f"Checked out existing branch: {branch_name}")
                return {"success": True, "branch": branch_name, "error": None}
            except subprocess.CalledProcessError:
                pass
        return {"success": False, "branch": branch_name, "error": error_msg}


def checkout_branch(branch_name: str, path: Path | None = None) -> dict[str, Any]:
    """
    Check out an existing branch.

    Args:
        branch_name: Name of the branch
        path: Path to git repository (default: current directory)

    Returns:
        Dictionary with success status and branch name
    """
    path = path or Path.cwd()
    if not check_git_available() or not is_git_repository(path):
        return {"success": False, "branch": branch_name, "error": "Git not available or not a repository"}
    try:
        _run_git_command(["checkout", branch_name], cwd=path, check=True)
        return {"success": True, "branch": branch_name, "error": None}
    except subprocess.CalledProcessError as e:
        return {"success": False, "branch": branch_name, "error": e.stderr or str(e)}


def commit_changes(
    message: str,
    files: list[str] | None = None,
    branch: str = "main",
    path: Path | None = None,
) -> dict[str, Any]:
    """
    Commit changes to git repository.

    Args:
        message: Commit message
        files: List of specific files to commit (None = all changes)
        branch: Target branch (default: "main")
        path: Path to git repository (default: current directory)

    Returns:
        Dictionary with:
        - success: bool
        - commit_hash: str | None
        - branch: str
        - error: str | None

    Raises:
        RuntimeError: If git is not available or not in a repository
        ValueError: If not on the specified branch and branch is not "main"
    """
    path = path or Path.cwd()

    # Validate git availability
    if not check_git_available():
        raise RuntimeError("Git is not installed or not in PATH")

    # Validate git repository
    if not is_git_repository(path):
        raise RuntimeError(f"Not a git repository: {path}")

    # Check current branch
    current_branch = get_current_branch(path)
    if branch != "main" and current_branch != branch:
        logger.warning(
            f"Current branch is '{current_branch}', but target branch is '{branch}'"
        )
    elif current_branch != branch:
        logger.warning(
            f"Current branch is '{current_branch}', committing to '{branch}'"
        )

    # Check for changes
    uncommitted = check_uncommitted_changes(path)
    if not uncommitted:
        return {
            "success": False,
            "commit_hash": None,
            "branch": current_branch,
            "error": "No uncommitted changes to commit",
        }

    try:
        # Stage files
        if files:
            # Stage specific files
            for file_path in files:
                file_full_path = path / file_path
                if file_full_path.exists():
                    _run_git_command(["add", file_path], cwd=path, check=True)
                else:
                    logger.warning(f"File not found, skipping: {file_path}")
        else:
            # Stage all changes
            _run_git_command(["add", "-A"], cwd=path, check=True)

        # Commit
        commit_result = _run_git_command(
            ["commit", "-m", message], cwd=path, check=True
        )

        # Get commit hash
        hash_result = _run_git_command(
            ["rev-parse", "HEAD"], cwd=path, check=True
        )
        commit_hash = hash_result.stdout.strip()

        logger.info(
            f"Committed changes to branch '{current_branch}': {commit_hash[:8]}"
        )

        return {
            "success": True,
            "commit_hash": commit_hash,
            "branch": current_branch,
            "error": None,
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e) if e.stderr else str(e)
        logger.error(f"Failed to commit changes: {error_msg}")
        return {
            "success": False,
            "commit_hash": None,
            "branch": current_branch,
            "error": error_msg,
        }


def push_changes(
    branch: str = "main",
    path: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Push changes to remote repository.

    Args:
        branch: Branch to push (default: "main")
        path: Path to git repository (default: current directory)
        force: Whether to force push (default: False, NEVER use True for main)

    Returns:
        Dictionary with:
        - success: bool
        - branch: str
        - error: str | None

    Raises:
        RuntimeError: If git is not available or not in a repository
        ValueError: If force=True and branch is "main"
    """
    path = path or Path.cwd()

    # Safety check: never force push to main
    if force and branch == "main":
        raise ValueError("Cannot force push to main branch")

    # Plan 3.3: no_direct_push_main from policies.yaml
    if branch == "main":
        try:
            from .policy_loader import load_policies
            p = load_policies(path)
            if p and p.branch_protection and getattr(p.branch_protection, "no_direct_push_main", True):
                raise ValueError(
                    "Direct push to main is disallowed by .tapps-agents/policies.yaml (branch_protection.no_direct_push_main). "
                    "Create a branch and merge via PR, or adjust policies."
                )
        except ValueError:
            raise
        except Exception:  # pylint: disable=broad-except
            pass  # if policy load fails, allow push

    # Validate git availability
    if not check_git_available():
        raise RuntimeError("Git is not installed or not in PATH")

    # Validate git repository
    if not is_git_repository(path):
        raise RuntimeError(f"Not a git repository: {path}")

    try:
        # Build push command
        push_args = ["push"]
        if force:
            push_args.append("--force")
        push_args.extend(["origin", branch])

        push_result = _run_git_command(push_args, cwd=path, check=True)

        logger.info(f"Pushed changes to remote branch '{branch}'")

        return {
            "success": True,
            "branch": branch,
            "error": None,
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e) if e.stderr else str(e)
        logger.error(f"Failed to push changes: {error_msg}")
        return {
            "success": False,
            "branch": branch,
            "error": error_msg,
        }


def create_pull_request(
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
    path: Path | None = None,
) -> dict[str, Any]:
    """
    Create a pull request using GitHub CLI (gh) if available.

    Args:
        title: PR title
        body: PR body/description
        head_branch: Source branch (branch with changes)
        base_branch: Target branch (default: "main")
        path: Path to git repository (default: current directory)

    Returns:
        Dictionary with:
        - success: bool
        - pr_url: str | None
        - pr_number: int | None
        - error: str | None
    """
    path = path or Path.cwd()

    # Check if GitHub CLI is available
    gh_path = shutil.which("gh")
    if not gh_path:
        logger.warning(
            "GitHub CLI (gh) not found. PR creation requires 'gh' to be installed and authenticated."
        )
        return {
            "success": False,
            "pr_url": None,
            "pr_number": None,
            "error": "GitHub CLI (gh) not found. Install from https://cli.github.com/",
        }

    try:
        # Create PR using GitHub CLI
        pr_args = [
            "pr",
            "create",
            "--title", title,
            "--body", body,
            "--head", head_branch,
            "--base", base_branch,
        ]

        result = subprocess.run(
            [gh_path] + pr_args,
            cwd=path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

        # Parse PR URL from output (gh outputs the PR URL)
        output = result.stdout.strip()
        pr_url = output if output.startswith("http") else None

        # Try to extract PR number from URL
        pr_number = None
        if pr_url:
            # URL format: https://github.com/owner/repo/pull/123
            parts = pr_url.split("/")
            if "pull" in parts:
                try:
                    pr_number = int(parts[parts.index("pull") + 1])
                except (ValueError, IndexError):
                    pass

        logger.info(f"Created pull request: {pr_url or output}")

        return {
            "success": True,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "error": None,
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e) if e.stderr else str(e)
        logger.error(f"Failed to create pull request: {error_msg}")
        return {
            "success": False,
            "pr_url": None,
            "pr_number": None,
            "error": error_msg,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "pr_url": None,
            "pr_number": None,
            "error": "GitHub CLI (gh) not found",
        }
