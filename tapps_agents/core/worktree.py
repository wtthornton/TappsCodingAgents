"""
Git Worktree Utilities for Background Agents

Provides utilities for creating and managing git worktrees for parallel agent execution.
This prevents file conflicts when multiple agents run simultaneously.
"""

import logging
import shutil
import subprocess  # nosec B404
from pathlib import Path

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Manages git worktrees for parallel agent execution."""

    def __init__(self, base_path: Path, worktree_base: Path | None = None):
        """
        Initialize WorktreeManager.

        Args:
            base_path: Base repository path
            worktree_base: Base directory for worktrees (default: .tapps-agents/worktrees)
        """
        self.base_path = Path(base_path).resolve()
        self.worktree_base = (
            worktree_base or self.base_path / ".tapps-agents" / "worktrees"
        )
        self.worktree_base.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, agent_id: str, branch_name: str | None = None) -> Path:
        """
        Create a git worktree for an agent.

        Args:
            agent_id: Unique identifier for the agent
            branch_name: Optional branch name (default: agent/{agent_id})

        Returns:
            Path to the worktree directory
        """
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
        Remove a git worktree.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            True if successful, False otherwise
        """
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

    def cleanup_worktrees(self, keep_active: bool = True) -> int:
        """
        Clean up worktrees (remove branches and directories).

        Args:
            keep_active: If True, keep worktrees that have uncommitted changes

        Returns:
            Number of worktrees cleaned up
        """
        worktrees = self.list_worktrees()
        cleaned = 0

        for agent_id, worktree_path in worktrees.items():
            try:
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

            except Exception as e:
                logger.error(f"Error cleaning up worktree {agent_id}: {e}")

        return cleaned

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
