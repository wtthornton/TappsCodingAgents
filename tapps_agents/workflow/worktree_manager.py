"""
Worktree Manager - Manages Git worktrees for workflow steps.

This module handles worktree creation, artifact copying, and cleanup.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import subprocess  # nosec B404 - fixed args, no shell
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Artifact, WorkflowStep

logger = logging.getLogger(__name__)


class WorktreeManager:
    """
    Manages Git worktrees for workflow step isolation.
    
    Each workflow step runs in its own worktree to prevent conflicts
    and enable clean rollback.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Worktree Manager.

        Args:
            project_root: Root directory for the project
        """
        self.project_root = project_root
        self.worktrees_dir = project_root / ".tapps-agents" / "worktrees"

    @staticmethod
    def _sanitize_component(value: str, *, max_len: int = 80) -> str:
        """
        Sanitize a user-provided identifier into a safe path/branch component.

        - Avoids path separators and Windows-invalid characters
        - Keeps names reasonably short to mitigate MAX_PATH issues
        """
        value = (value or "").strip()
        if not value:
            return "worktree"

        # Replace separators and invalid chars with '-'
        value = value.replace("\\", "-").replace("/", "-")
        value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
        value = re.sub(r"-{2,}", "-", value).strip("-")

        if not value:
            return "worktree"

        if len(value) > max_len:
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
            value = f"{value[: max_len - 11]}-{digest}"
        return value

    def _safe_worktree_name(self, worktree_name: str) -> str:
        # Ensure no traversal; store only as a single directory name.
        if Path(worktree_name).is_absolute() or any(
            part in {".", ".."} for part in Path(worktree_name).parts
        ):
            raise ValueError(f"Invalid worktree name: {worktree_name!r}")
        return self._sanitize_component(worktree_name, max_len=80)

    def _worktree_path_for(self, worktree_name: str) -> Path:
        safe_name = self._safe_worktree_name(worktree_name)
        return self.worktrees_dir / safe_name

    def _branch_for(self, worktree_name: str) -> str:
        safe_name = self._sanitize_component(worktree_name, max_len=90)
        # Keep branch names well under git limits and Windows path quirks.
        if len(safe_name) > 90:
            safe_name = safe_name[:90]
        return f"workflow/{safe_name}"

    async def create_worktree(self, worktree_name: str) -> Path:
        """
        Create a new Git worktree for a workflow step.

        Args:
            worktree_name: Name for the worktree

        Returns:
            Path to the worktree
        """
        worktree_path = self._worktree_path_for(worktree_name)
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if worktree already exists
        if worktree_path.exists():
            # Clean up existing worktree
            await self.remove_worktree(worktree_path.name)

        # Create worktree using git command
        try:
            git_path = shutil.which("git") or "git"
            branch = self._branch_for(worktree_path.name)
            subprocess.run(
                [
                    git_path,
                    "worktree",
                    "add",
                    str(worktree_path),
                    "-b",
                    branch,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            # If branch already exists, attach the worktree to it.
            try:
                git_path = shutil.which("git") or "git"
                branch = self._branch_for(worktree_path.name)
                subprocess.run(
                    [git_path, "worktree", "add", str(worktree_path), branch],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError:
                # If worktree creation fails, create a regular directory
                worktree_path.mkdir(parents=True, exist_ok=True)
                # Copy project files
                self._copy_project_files(worktree_path)

        return worktree_path

    def _copy_project_files(self, dest: Path) -> None:
        """Copy project files to worktree (fallback if git worktree fails)."""
        # Create a fresh .tapps-agents folder in the worktree (do not recursively copy worktrees).
        (dest / ".tapps-agents").mkdir(parents=True, exist_ok=True)

        essential_items = [
            # Core repo content
            "tapps_agents",
            "tests",
            "docs",
            "workflows",
            # Key project files
            "pyproject.toml",
            "README.md",
            "LICENSE",
        ]

        # If capabilities exist, include them (but never copy worktrees).
        capabilities_dir = self.project_root / ".tapps-agents" / "capabilities"
        if capabilities_dir.exists():
            essential_items.append(str(Path(".tapps-agents") / "capabilities"))

        for item in essential_items:
            src = self.project_root / item
            if not src.exists():
                continue

            dst = dest / item
            if src.is_dir():
                shutil.copytree(
                    src,
                    dst,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(
                        ".git",
                        ".venv",
                        "__pycache__",
                        ".pytest_cache",
                        ".ruff_cache",
                        ".mypy_cache",
                        "htmlcov",
                        "dist",
                        "build",
                        "reports",
                        "worktrees",
                    ),
                )
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    async def copy_artifacts(
        self, worktree_path: Path, artifacts: list[Artifact]
    ) -> None:
        """
        Copy artifacts from previous steps to worktree.

        Args:
            worktree_path: Path to worktree
            artifacts: List of artifacts to copy
        """
        for artifact in artifacts:
            # Ensure artifact is an Artifact object
            if not isinstance(artifact, Artifact):
                # Skip if not an Artifact object
                continue
                
            if not artifact.path:
                continue
                
            src_path = Path(artifact.path)
            if not src_path.exists():
                continue

            # Determine destination path
            if src_path.is_absolute() and self.project_root in src_path.parents:
                # Relative to project root
                rel_path = src_path.relative_to(self.project_root)
                dest_path = worktree_path / rel_path
            else:
                # Use filename only
                dest_path = worktree_path / src_path.name

            # Copy file or directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)

    async def extract_artifacts(
        self, worktree_path: Path, step: WorkflowStep
    ) -> list[Artifact]:
        """
        Extract artifacts created in worktree.

        Args:
            worktree_path: Path to worktree
            step: Workflow step definition

        Returns:
            List of artifacts found
        """
        artifacts: list[Artifact] = []

        # Check for expected artifacts from step definition
        if step.creates:
            for artifact_name in step.creates:
                artifact_path = worktree_path / artifact_name
                if artifact_path.exists():
                    # Copy to main project
                    main_path = self.project_root / artifact_name
                    main_path.parent.mkdir(parents=True, exist_ok=True)

                    if artifact_path.is_dir():
                        shutil.copytree(artifact_path, main_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(artifact_path, main_path)

                    artifacts.append(
                        Artifact(
                            name=artifact_name,
                            path=str(main_path),
                            status="complete",
                            created_by=step.id,
                            created_at=datetime.now(),
                            metadata={"type": "file" if artifact_path.is_file() else "directory"},
                        )
                    )

        # Also scan for common artifact patterns
        common_patterns = [
            "requirements.md",
            "stories/*.md",
            "architecture.md",
            "api-specs/**/*",
            "src/**/*.py",
            "tests/**/*.py",
            "docs/**/*.md",
        ]

        for pattern in common_patterns:
            for artifact_path in worktree_path.glob(pattern):
                if artifact_path.is_file():
                    # Copy to main project
                    rel_path = artifact_path.relative_to(worktree_path)
                    main_path = self.project_root / rel_path
                    main_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(artifact_path, main_path)

                    artifacts.append(
                        Artifact(
                            name=artifact_path.name,
                            path=str(main_path),
                            status="complete",
                            created_by=step.id,
                            created_at=datetime.now(),
                            metadata={"type": "file"},
                        )
                    )

        return artifacts

    def _delete_branch(self, branch_name: str) -> bool:
        """
        Delete a Git branch (safe delete with force fallback).

        Args:
            branch_name: Name of the branch to delete (e.g., "workflow/...")

        Returns:
            True if branch was deleted or didn't exist, False on error
        """
        git_path = shutil.which("git") or "git"

        # Verify branch exists
        try:
            subprocess.run(
                [git_path, "rev-parse", "--verify", branch_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            # Branch doesn't exist - treat as success
            logger.debug(f"Branch {branch_name} doesn't exist, nothing to delete")
            return True

        # Attempt safe delete first
        try:
            subprocess.run(
                [git_path, "branch", "-d", branch_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            logger.info(f"Successfully deleted branch: {branch_name}")
            return True
        except subprocess.CalledProcessError:
            # Safe delete failed (branch not merged), try force delete
            try:
                subprocess.run(
                    [git_path, "branch", "-D", branch_name],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=True,
                )
                logger.info(f"Successfully force-deleted branch: {branch_name}")
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(
                    f"Failed to delete branch {branch_name}: {e.stderr or 'unknown error'}"
                )
                return False

    async def remove_worktree(
        self, worktree_name: str, delete_branch: bool = True
    ) -> None:
        """
        Remove a worktree.

        Args:
            worktree_name: Name of the worktree to remove
        """
        worktree_path = self._worktree_path_for(worktree_name)

        if not worktree_path.exists():
            return

        # Try to remove via git worktree
        try:
            git_path = shutil.which("git") or "git"
            subprocess.run(
                [git_path, "worktree", "remove", str(worktree_path), "--force"],
                cwd=self.project_root,
                capture_output=True,
                check=False,  # Don't fail if git command fails
            )
        except Exception:
            pass

        # Fallback: remove directory
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

    async def cleanup_all(self) -> None:
        """Clean up all worktrees."""
        if not self.worktrees_dir.exists():
            return

        for worktree_dir in self.worktrees_dir.iterdir():
            if worktree_dir.is_dir():
                await self.remove_worktree(worktree_dir.name)

        # Best-effort prune to clean up stale worktree metadata.
        try:
            git_path = shutil.which("git") or "git"
            subprocess.run(
                [git_path, "worktree", "prune"],
                cwd=self.project_root,
                capture_output=True,
                check=False,
            )
        except Exception:
            pass

    def _check_working_tree_clean(self) -> bool:
        """
        Check if the working tree is clean (no uncommitted changes).

        Note: Untracked files are ignored as they don't affect merge operations.

        Returns:
            True if working tree is clean, False otherwise
        """
        try:
            git_path = shutil.which("git") or "git"
            result = subprocess.run(
                [git_path, "status", "--porcelain", "--untracked-files=no"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return not result.stdout.strip()
        except subprocess.CalledProcessError:
            return False

    def _get_current_branch(self) -> str:
        """
        Get the current branch name.

        Returns:
            Current branch name

        Raises:
            RuntimeError: If unable to determine current branch
        """
        try:
            git_path = shutil.which("git") or "git"
            result = subprocess.run(
                [git_path, "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get current branch: {e.stderr}") from e

    def _detect_conflicts(self) -> list[str]:
        """
        Detect conflicted files in the working tree.

        Returns:
            List of file paths with conflicts
        """
        conflicted_files: list[str] = []
        try:
            git_path = shutil.which("git") or "git"
            result = subprocess.run(
                [git_path, "diff", "--name-only", "--diff-filter=U"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    conflicted_files.append(line.strip())
        except subprocess.CalledProcessError:
            # If command fails, try alternative method
            try:
                git_path = shutil.which("git") or "git"
                result = subprocess.run(
                    [git_path, "status", "--porcelain"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                for line in result.stdout.strip().split("\n"):
                    if line.strip() and line.startswith("UU"):
                        # UU indicates unmerged (conflicted) files
                        file_path = line[3:].strip()
                        conflicted_files.append(file_path)
            except subprocess.CalledProcessError:
                pass
        return conflicted_files

    def _write_conflict_report(
        self,
        worktree_name: str,
        branch_name: str,
        target_branch: str,
        conflicted_files: list[str],
        merge_error: str | None = None,
    ) -> Path:
        """
        Write a conflict report to a JSON file.

        Args:
            worktree_name: Name of the worktree being merged
            branch_name: Name of the worktree branch
            target_branch: Target branch for merge
            conflicted_files: List of conflicted file paths
            merge_error: Optional error message from merge attempt

        Returns:
            Path to the conflict report file
        """
        reports_dir = self.project_root / ".tapps-agents" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_filename = f"merge-conflict-{worktree_name}-{timestamp}.json"
        report_path = reports_dir / report_filename

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "worktree_name": worktree_name,
            "worktree_branch": branch_name,
            "target_branch": target_branch,
            "conflicted_files": conflicted_files,
            "conflict_count": len(conflicted_files),
            "merge_error": merge_error,
            "guidance": {
                "resolution_steps": [
                    "1. Review conflicted files listed above",
                    "2. Manually resolve conflicts in each file",
                    "3. Mark conflicts as resolved: git add <file>",
                    "4. Complete merge: git commit",
                    "5. Or abort merge: git merge --abort",
                ],
                "abort_command": "git merge --abort",
            },
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        return report_path

    async def merge_worktree(
        self,
        worktree_name: str,
        target_branch: str | None = None,
    ) -> dict[str, Any]:
        """
        Merge a worktree branch into the target branch.

        Epic 1 / Story 1.5: Worktree Merge & Conflict Resolution

        Args:
            worktree_name: Name of the worktree to merge
            target_branch: Target branch to merge into (defaults to current branch)

        Returns:
            Dictionary with merge result:
            - success: bool
            - has_conflicts: bool
            - conflicted_files: list[str]
            - conflict_report_path: Path | None
            - error: str | None

        Raises:
            ValueError: If working tree is not clean or worktree doesn't exist
            RuntimeError: If unable to determine current branch
        """
        # Validate worktree exists
        worktree_path = self._worktree_path_for(worktree_name)
        if not worktree_path.exists():
            raise ValueError(f"Worktree {worktree_name} does not exist")

        # Check working tree is clean
        if not self._check_working_tree_clean():
            raise ValueError(
                "Working tree is not clean. Please commit or stash changes before merging."
            )

        # Get target branch
        if target_branch is None:
            target_branch = self._get_current_branch()

        # Get worktree branch name
        branch_name = self._branch_for(worktree_name)

        # Verify branch exists
        git_path = shutil.which("git") or "git"
        try:
            subprocess.run(
                [git_path, "rev-parse", "--verify", branch_name],
                cwd=self.project_root,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return {
                "success": False,
                "has_conflicts": False,
                "conflicted_files": [],
                "conflict_report_path": None,
                "error": f"Branch {branch_name} does not exist",
            }

        # Attempt merge
        try:
            subprocess.run(
                [git_path, "merge", "--no-ff", "--no-commit", branch_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # Merge succeeded without conflicts
            # Complete the merge
            subprocess.run(
                [git_path, "commit", "--no-edit"],
                cwd=self.project_root,
                capture_output=True,
                check=True,
            )

            return {
                "success": True,
                "has_conflicts": False,
                "conflicted_files": [],
                "conflict_report_path": None,
                "error": None,
            }

        except subprocess.CalledProcessError as e:
            # Merge failed - check for conflicts
            conflicted_files = self._detect_conflicts()

            if conflicted_files:
                # Conflicts detected - write report
                report_path = self._write_conflict_report(
                    worktree_name=worktree_name,
                    branch_name=branch_name,
                    target_branch=target_branch,
                    conflicted_files=conflicted_files,
                    merge_error=e.stderr,
                )

                return {
                    "success": False,
                    "has_conflicts": True,
                    "conflicted_files": conflicted_files,
                    "conflict_report_path": report_path,
                    "error": f"Merge conflicts detected in {len(conflicted_files)} file(s)",
                }
            else:
                # Merge failed for other reasons
                return {
                    "success": False,
                    "has_conflicts": False,
                    "conflicted_files": [],
                    "conflict_report_path": None,
                    "error": f"Merge failed: {e.stderr}",
                }

    async def abort_merge(self) -> bool:
        """
        Abort an in-progress merge and restore working tree to pre-merge state.

        Epic 1 / Story 1.5: Worktree Merge & Conflict Resolution

        Returns:
            True if merge was aborted successfully, False otherwise
        """
        # Check if merge is in progress
        git_path = shutil.which("git") or "git"
        try:
            result = subprocess.run(
                [git_path, "rev-parse", "--verify", "MERGE_HEAD"],
                cwd=self.project_root,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                # No merge in progress
                return False
        except Exception:
            return False

        # Abort merge
        try:
            subprocess.run(
                [git_path, "merge", "--abort"],
                cwd=self.project_root,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            # If abort fails, try to reset hard to HEAD
            try:
                subprocess.run(
                    [git_path, "reset", "--hard", "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    check=True,
                )
                return True
            except subprocess.CalledProcessError:
                return False

