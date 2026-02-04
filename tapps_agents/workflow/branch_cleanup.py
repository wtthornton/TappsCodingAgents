"""
Branch Cleanup Service - Detects and cleans up orphaned Git branches.

This service identifies branches that were created for workflow worktrees but
no longer have associated worktrees, and optionally deletes them.
"""

from __future__ import annotations

import fnmatch
import logging
import shutil
import subprocess  # nosec B404 - fixed args, no shell
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..core.config import BranchCleanupConfig, load_config

logger = logging.getLogger(__name__)


@dataclass
class BranchMetadata:
    """Metadata about a Git branch"""

    name: str
    created_at: datetime | None = None
    last_commit: datetime | None = None
    age_days: float | None = None
    is_orphaned: bool = False


@dataclass
class OrphanedBranch:
    """Represents an orphaned branch that can be cleaned up"""

    branch_name: str
    metadata: BranchMetadata
    reason: str  # Why it's considered orphaned


@dataclass
class CleanupReport:
    """Report of branch cleanup operation"""

    total_branches_scanned: int
    orphaned_branches_found: int
    branches_deleted: int
    branches_failed: int
    dry_run: bool
    branches: list[OrphanedBranch]
    errors: list[str]


class BranchCleanupService:
    """
    Service for detecting and cleaning up orphaned workflow branches.

    Orphaned branches are branches that match workflow/agent patterns but
    no longer have associated worktrees.
    """

    def __init__(
        self,
        project_root: Path,
        config: BranchCleanupConfig | None = None,
    ):
        """
        Initialize Branch Cleanup Service.

        Args:
            project_root: Root directory of the project
            config: Branch cleanup configuration (uses default if not provided)
        """
        self.project_root = project_root
        if config is None:
            project_config = load_config()
            self.config = project_config.workflow.branch_cleanup
        else:
            self.config = config
        self.worktree_manager = None  # Lazy import to avoid circular dependency

    def _get_worktree_manager(self):
        """Lazy import WorktreeManager to avoid circular dependency."""
        if self.worktree_manager is None:
            from .worktree_manager import WorktreeManager

            self.worktree_manager = WorktreeManager(project_root=self.project_root)
        return self.worktree_manager

    def _get_git_branches(self) -> list[str]:
        """
        Get list of all local Git branches.

        Returns:
            List of branch names (without refs/heads/ prefix)
        """
        git_path = shutil.which("git") or "git"
        try:
            result = subprocess.run(
                [git_path, "branch", "--format=%(refname:short)"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            branches = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip() and not line.strip().startswith("*")
            ]
            # Remove current branch marker if present
            return [b.lstrip("*").strip() for b in branches]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get Git branches: {e.stderr}")
            return []

    def _get_branch_metadata(self, branch_name: str) -> BranchMetadata | None:
        """
        Get metadata for a branch (creation date, last commit, age).

        Args:
            branch_name: Name of the branch

        Returns:
            BranchMetadata or None if branch doesn't exist
        """
        git_path = shutil.which("git") or "git"
        try:
            # Get last commit date
            result = subprocess.run(
                [
                    git_path,
                    "log",
                    "-1",
                    "--format=%ct",
                    branch_name,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            if not result.stdout.strip():
                return None

            timestamp = int(result.stdout.strip())
            last_commit = datetime.fromtimestamp(timestamp)

            # Calculate age
            age_days = (datetime.now() - last_commit).total_seconds() / 86400.0

            return BranchMetadata(
                name=branch_name,
                last_commit=last_commit,
                age_days=age_days,
            )
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.debug(f"Failed to get metadata for branch {branch_name}: {e}")
            return None

    def _matches_pattern(self, branch_name: str) -> bool:
        """
        Check if a branch matches any of the configured patterns.

        Args:
            branch_name: Name of the branch to check

        Returns:
            True if branch matches any pattern
        """
        for _pattern_type, pattern in self.config.patterns.items():
            if fnmatch.fnmatch(branch_name, pattern):
                return True
        return False

    def _branch_has_worktree(self, branch_name: str) -> bool:
        """
        Check if a branch has an associated worktree.

        Args:
            branch_name: Name of the branch to check

        Returns:
            True if branch has an associated worktree
        """
        git_path = shutil.which("git") or "git"
        try:
            result = subprocess.run(
                [git_path, "worktree", "list", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            # Parse worktree list output
            for line in result.stdout.split("\n"):
                if line.startswith("branch ") and branch_name in line:
                    return True
                # Also check for worktree path that might contain branch name
                if branch_name in line and "worktree" in line.lower():
                    return True
            return False
        except subprocess.CalledProcessError:
            return False

    async def detect_orphaned_branches(
        self, patterns: dict[str, str] | None = None
    ) -> list[OrphanedBranch]:
        """
        Detect orphaned branches that match workflow/agent patterns.

        Args:
            patterns: Optional override patterns (uses config patterns if not provided)

        Returns:
            List of orphaned branches
        """
        if patterns is None:
            patterns = self.config.patterns

        orphaned: list[OrphanedBranch] = []
        branches = self._get_git_branches()
        total_scanned = len(branches)

        logger.info(f"Scanning {total_scanned} branches for orphaned workflow branches")

        for branch_name in branches:
            # Check if branch matches patterns
            matches = False
            for _pattern_type, pattern in patterns.items():
                if fnmatch.fnmatch(branch_name, pattern):
                    matches = True
                    break

            if not matches:
                continue

            # Get branch metadata
            metadata = self._get_branch_metadata(branch_name)
            if metadata is None:
                continue

            # Check if branch has associated worktree
            has_worktree = self._branch_has_worktree(branch_name)

            # Check age if retention_days is configured
            is_old_enough = True
            if self.config.retention_days > 0 and metadata.age_days is not None:
                is_old_enough = metadata.age_days >= self.config.retention_days

            # Branch is orphaned if:
            # 1. Matches pattern
            # 2. No associated worktree
            # 3. Meets retention age (if configured)
            if not has_worktree and is_old_enough:
                reason = "No associated worktree"
                if metadata.age_days is not None:
                    reason += f", age: {metadata.age_days:.1f} days"
                if self.config.retention_days > 0:
                    reason += f" (>= {self.config.retention_days} days retention)"

                metadata.is_orphaned = True
                orphaned.append(
                    OrphanedBranch(
                        branch_name=branch_name, metadata=metadata, reason=reason
                    )
                )

        logger.info(f"Found {len(orphaned)} orphaned branches")
        return orphaned

    async def cleanup_orphaned_branches(
        self,
        dry_run: bool = False,
        patterns: dict[str, str] | None = None,
        max_age_days: int | None = None,
    ) -> CleanupReport:
        """
        Clean up orphaned branches.

        Args:
            dry_run: If True, don't actually delete branches (just report)
            patterns: Optional override patterns
            max_age_days: Optional override for max age (uses config if not provided)

        Returns:
            CleanupReport with results
        """
        # Temporarily override retention_days if max_age_days provided
        original_retention = self.config.retention_days
        if max_age_days is not None:
            self.config.retention_days = max_age_days

        try:
            orphaned = await self.detect_orphaned_branches(patterns=patterns)
        finally:
            # Restore original retention
            self.config.retention_days = original_retention

        deleted_count = 0
        failed_count = 0
        errors: list[str] = []

        worktree_manager = self._get_worktree_manager()

        for branch in orphaned:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete branch: {branch.branch_name}")
                deleted_count += 1
                continue

            try:
                success = worktree_manager._delete_branch(branch.branch_name)
                if success:
                    deleted_count += 1
                    logger.info(f"Deleted orphaned branch: {branch.branch_name}")
                else:
                    failed_count += 1
                    error_msg = f"Failed to delete branch: {branch.branch_name}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            except Exception as e:
                failed_count += 1
                error_msg = f"Error deleting branch {branch.branch_name}: {e}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        branches = self._get_git_branches()
        total_scanned = len(branches) + deleted_count  # Approximate original count

        return CleanupReport(
            total_branches_scanned=total_scanned,
            orphaned_branches_found=len(orphaned),
            branches_deleted=deleted_count,
            branches_failed=failed_count,
            dry_run=dry_run,
            branches=orphaned,
            errors=errors,
        )
