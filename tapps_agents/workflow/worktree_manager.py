"""
Worktree Manager - Manages Git worktrees for workflow steps.

This module handles worktree creation, artifact copying, and cleanup.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 - fixed args, no shell
from pathlib import Path
from typing import Any

from .models import Artifact, WorkflowStep


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

    async def create_worktree(self, worktree_name: str) -> Path:
        """
        Create a new Git worktree for a workflow step.

        Args:
            worktree_name: Name for the worktree

        Returns:
            Path to the worktree
        """
        worktree_path = self.worktrees_dir / worktree_name
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if worktree already exists
        if worktree_path.exists():
            # Clean up existing worktree
            await self.remove_worktree(worktree_name)

        # Create worktree using git command
        try:
            result = subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    str(worktree_path),
                    "-b",
                    f"workflow/{worktree_name}",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # If branch already exists, try without -b
            try:
                result = subprocess.run(
                    ["git", "worktree", "add", str(worktree_path)],
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
        # Copy essential files and directories
        essential_items = [
            ".tapps-agents",
            "requirements.md",
            "stories",
            "architecture.md",
            "api-specs",
            "src",
            "tests",
            "docs",
        ]

        for item in essential_items:
            src = self.project_root / item
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, dest / item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dest / item)

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
                            step_id=step.id,
                            type="file" if artifact_path.is_file() else "directory",
                            path=str(main_path),
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

        from datetime import datetime

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
                            step_id=step.id,
                            type="file",
                            path=str(main_path),
                            created_at=datetime.now(),
                        )
                    )

        return artifacts

    async def remove_worktree(self, worktree_name: str) -> None:
        """
        Remove a worktree.

        Args:
            worktree_name: Name of the worktree to remove
        """
        worktree_path = self.worktrees_dir / worktree_name

        if not worktree_path.exists():
            return

        # Try to remove via git worktree
        try:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
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

