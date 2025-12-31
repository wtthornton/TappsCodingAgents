"""
Git Worktree Utilities for Background Agents

Provides utilities for creating and managing git worktrees for parallel agent execution.
This prevents file conflicts when multiple agents run simultaneously.

Phase 3 Simplification: Supports temp directories for non-git use cases.
"""

import logging
import shutil
import subprocess  # nosec B404
from datetime import datetime, timedelta
from pathlib import Path

from .temp_directory import TempDirectoryManager, needs_git_operations

logger = logging.getLogger(__name__)


class WorktreeManager:
    """
    Manages git worktrees for parallel agent execution.
    
    Phase 3 Simplification: Automatically uses temp directories when git operations
    are not needed, reducing git dependency.
    """

    def __init__(
        self,
        base_path: Path,
        worktree_base: Path | None = None,
        use_temp_for_non_git: bool = True,
    ):
        """
        Initialize WorktreeManager.

        Args:
            base_path: Base repository path
            worktree_base: Base directory for worktrees (default: .tapps-agents/worktrees)
            use_temp_for_non_git: If True, use temp directories when git not needed (Phase 3)
        """
        self.base_path = Path(base_path).resolve()
        self.worktree_base = (
            worktree_base or self.base_path / ".tapps-agents" / "worktrees"
        )
        self.worktree_base.mkdir(parents=True, exist_ok=True)
        self.use_temp_for_non_git = use_temp_for_non_git
        self.temp_manager = TempDirectoryManager(
            base_dir=self.worktree_base / "temp" if use_temp_for_non_git else None
        )

    def create_worktree(
        self,
        agent_id: str,
        branch_name: str | None = None,
        task_type: str | None = None,
        commands: list[str] | None = None,
    ) -> Path:
        """
        Create a git worktree or temp directory for an agent.

        Phase 3 Simplification: Automatically uses temp directory when git operations
        are not needed.

        Args:
            agent_id: Unique identifier for the agent
            branch_name: Optional branch name (default: agent/{agent_id})
            task_type: Optional task type to determine if git is needed
            commands: Optional list of commands to determine if git is needed

        Returns:
            Path to the worktree or temp directory
        """
        # Phase 3: Check if git operations are needed
        if self.use_temp_for_non_git and task_type:
            if not needs_git_operations(task_type, commands or []):
                # Use temp directory instead of worktree
                temp_dir = self.temp_manager.create_temp_dir(
                    agent_id, copy_from=self.base_path
                )
                logger.info(
                    f"Using temp directory for {agent_id} (git not needed): {temp_dir}"
                )
                return temp_dir

        # Use git worktree (existing behavior)
        branch_name = branch_name or f"agent/{agent_id}"
        worktree_path = self.worktree_base / agent_id

        # Check if worktree already exists
        if worktree_path.exists():
            logger.warning(f"Worktree {agent_id} already exists, reusing")
            return worktree_path

        try:
            # Create worktree
            git_path = shutil.which("git") or "git"
            cmd = [git_path, "worktree", "add", str(worktree_path), "-b", branch_name]

            subprocess.run(  # nosec B603
                cmd, cwd=self.base_path, capture_output=True, text=True, check=True
            )

            logger.info(f"Created worktree {agent_id} at {worktree_path}")
            return worktree_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree {agent_id}: {e.stderr}")
            raise

    def remove_worktree(self, agent_id: str) -> bool:
        """
        Remove a git worktree or temp directory.

        Phase 3 Simplification: Handles both worktrees and temp directories.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            True if successful, False otherwise
        """
        # Phase 3: Check if it's a temp directory first
        if self.temp_manager.get_temp_dir(agent_id):
            return self.temp_manager.remove_temp_dir(agent_id)

        # Remove git worktree (existing behavior)
        worktree_path = self.worktree_base / agent_id

        if not worktree_path.exists():
            logger.warning(f"Worktree {agent_id} does not exist")
            return False

        try:
            # Remove worktree using git command
            git_path = shutil.which("git") or "git"
            cmd = [git_path, "worktree", "remove", str(worktree_path), "--force"]

            subprocess.run(  # nosec B603
                cmd, cwd=self.base_path, capture_output=True, text=True, check=True
            )

            logger.info(f"Removed worktree {agent_id}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove worktree {agent_id}: {e.stderr}")
            # Fallback: try to remove directory manually
            try:
                shutil.rmtree(worktree_path)
                logger.info(f"Manually removed worktree directory {agent_id}")
                return True
            except Exception as e2:
                logger.error(f"Failed to manually remove worktree {agent_id}: {e2}")
                return False

    def list_worktrees(self) -> dict[str, Path]:
        """
        List all active worktrees.

        Returns:
            Dictionary mapping agent_id to worktree path
        """
        worktrees = {}

        try:
            git_path = shutil.which("git") or "git"
            cmd = [git_path, "worktree", "list"]
            result = subprocess.run(  # nosec B603
                cmd, cwd=self.base_path, capture_output=True, text=True, check=True
            )

            # Parse output
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        worktree_path = Path(parts[0])
                        if worktree_path.parent == self.worktree_base:
                            agent_id = worktree_path.name
                            worktrees[agent_id] = worktree_path

            return worktrees

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list worktrees: {e.stderr}")
            return {}

    def cleanup_worktrees(
        self,
        keep_active: bool = True,
        retention_days: int | None = None,
        older_than: timedelta | None = None,
    ) -> int:
        """
        Clean up worktrees (remove branches and directories).

        Args:
            keep_active: If True, keep worktrees that have uncommitted changes
            retention_days: Keep worktrees newer than N days (None = no age limit)
            older_than: Keep worktrees newer than this timedelta (overrides retention_days)

        Returns:
            Number of worktrees cleaned up
        """
        worktrees = self.list_worktrees()
        cleaned = 0

        # Calculate cutoff time
        cutoff_time = None
        if older_than:
            cutoff_time = datetime.now() - older_than
        elif retention_days:
            cutoff_time = datetime.now() - timedelta(days=retention_days)

        for agent_id, worktree_path in worktrees.items():
            try:
                # Check age if retention period specified
                if cutoff_time:
                    worktree_mtime = datetime.fromtimestamp(worktree_path.stat().st_mtime)
                    if worktree_mtime > cutoff_time:
                        logger.debug(
                            f"Skipping worktree {agent_id} (newer than retention period)"
                        )
                        continue

                # Check for completion marker
                completion_file = worktree_path / ".tapps-agents" / "completed.txt"
                if not completion_file.exists() and keep_active:
                    logger.debug(f"Skipping worktree {agent_id} (not marked as completed)")
                    continue

                # Check for uncommitted changes
                if keep_active:
                    git_path = shutil.which("git") or "git"
                    cmd = [git_path, "status", "--porcelain"]
                    result = subprocess.run(  # nosec B603
                        cmd, cwd=worktree_path, capture_output=True, text=True
                    )
                    if result.stdout.strip():
                        logger.info(
                            f"Skipping worktree {agent_id} (has uncommitted changes)"
                        )
                        continue

                # Remove worktree
                if self.remove_worktree(agent_id):
                    cleaned += 1
                    logger.info(f"Cleaned up worktree {agent_id}")

            except Exception as e:
                logger.error(f"Error cleaning up worktree {agent_id}: {e}")

        return cleaned

    def auto_cleanup(
        self,
        retention_days: int = 7,
        keep_active: bool = True,
    ) -> int:
        """
        Automatically clean up old worktrees based on retention policy.

        Args:
            retention_days: Keep worktrees newer than N days (default: 7)
            keep_active: If True, keep worktrees that have uncommitted changes

        Returns:
            Number of worktrees cleaned up
        """
        return self.cleanup_worktrees(
            keep_active=keep_active,
            retention_days=retention_days,
        )

    def get_worktree_path(self, agent_id: str) -> Path | None:
        """
        Get the path to an existing worktree.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Path to worktree if it exists, None otherwise
        """
        worktree_path = self.worktree_base / agent_id
        if worktree_path.exists():
            return worktree_path
        return None


def create_worktree_for_agent(
    base_path: Path, agent_id: str, worktree_base: Path | None = None
) -> Path:
    """
    Convenience function to create a worktree for an agent.

    Args:
        base_path: Base repository path
        agent_id: Unique identifier for the agent
        worktree_base: Base directory for worktrees

    Returns:
        Path to the worktree directory
    """
    manager = WorktreeManager(base_path, worktree_base)
    return manager.create_worktree(agent_id)
