"""
Commit Manager - Manages git commits for bug fixes.
"""

import logging
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig, load_config
from ..core.git_operations import commit_changes, get_current_branch, is_git_repository

from .bug_finder import BugInfo

logger = logging.getLogger(__name__)


class CommitManager:
    """Manages git commits for bug fixes."""

    def __init__(
        self,
        project_root: Path | None = None,
        strategy: str = "one-per-bug",
    ) -> None:
        """
        Initialize CommitManager.

        Args:
            project_root: Project root directory
            strategy: Commit strategy - "one-per-bug" or "batch"
        """
        self.project_root = project_root or Path.cwd()
        self.strategy = strategy

        # Validate git repository
        if not is_git_repository(self.project_root):
            logger.warning(f"Not a git repository: {self.project_root}")

    async def commit_fix(
        self,
        bug: BugInfo,
        commit_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Commit a single fix.

        Args:
            bug: BugInfo object with bug details
            commit_message: Custom commit message (auto-generated if None)

        Returns:
            Dictionary with:
                - success: bool
                - commit_hash: str | None
                - branch: str | None
                - message: str
                - error: str | None (if failed)
        """
        if not is_git_repository(self.project_root):
            return {
                "success": False,
                "commit_hash": None,
                "branch": None,
                "message": commit_message or self._generate_commit_message(bug),
                "error": "Not a git repository",
            }

        try:
            message = commit_message or self._generate_commit_message(bug)
            branch = get_current_branch(self.project_root)

            # Commit changes
            commit_hash = commit_changes(
                message=message,
                project_root=self.project_root,
            )

            logger.info(f"Committed fix: {commit_hash[:8]} - {message}")

            return {
                "success": True,
                "commit_hash": commit_hash,
                "branch": branch,
                "message": message,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error committing fix: {e}", exc_info=True)
            return {
                "success": False,
                "commit_hash": None,
                "branch": None,
                "message": commit_message or self._generate_commit_message(bug),
                "error": str(e),
            }

    async def commit_batch(
        self,
        bugs: list[BugInfo],
        commit_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Commit multiple fixes in one commit.

        Args:
            bugs: List of BugInfo objects
            commit_message: Custom commit message (auto-generated if None)

        Returns:
            Dictionary with commit information
        """
        if not is_git_repository(self.project_root):
            return {
                "success": False,
                "commit_hash": None,
                "branch": None,
                "message": commit_message or self._generate_batch_commit_message(bugs),
                "error": "Not a git repository",
            }

        try:
            message = commit_message or self._generate_batch_commit_message(bugs)
            branch = get_current_branch(self.project_root)

            # Commit changes
            commit_hash = commit_changes(
                message=message,
                project_root=self.project_root,
            )

            logger.info(f"Committed batch fix: {commit_hash[:8]} - {message}")

            return {
                "success": True,
                "commit_hash": commit_hash,
                "branch": branch,
                "message": message,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error committing batch fix: {e}", exc_info=True)
            return {
                "success": False,
                "commit_hash": None,
                "branch": None,
                "message": commit_message or self._generate_batch_commit_message(bugs),
                "error": str(e),
            }

    def _generate_commit_message(self, bug: BugInfo) -> str:
        """
        Generate commit message for a bug fix.

        Args:
            bug: BugInfo object

        Returns:
            Commit message string
        """
        # Extract first line of error message (main error)
        error_first_line = bug.error_message.split("\n")[0].strip()
        if len(error_first_line) > 100:
            error_first_line = error_first_line[:97] + "..."

        return f"Fix: {error_first_line} (from {bug.test_name})"

    def _generate_batch_commit_message(self, bugs: list[BugInfo]) -> str:
        """
        Generate commit message for batch fixes.

        Args:
            bugs: List of BugInfo objects

        Returns:
            Commit message string
        """
        file_count = len(set(bug.file_path for bug in bugs))
        return f"Fix: {len(bugs)} bugs in {file_count} file(s)"
