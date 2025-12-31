"""
Temp Directory Manager - Phase 3 Simplification

Provides temporary directory isolation for tasks that don't require git operations.
This reduces the git dependency and simplifies setup for non-git use cases.
"""

import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class TempDirectoryManager:
    """
    Manages temporary directories for task isolation.
    
    Phase 3 Simplification: Alternative to git worktrees for non-git use cases.
    Provides isolation without requiring git repository.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        prefix: str = "tapps-agent-",
        cleanup_on_exit: bool = True,
    ):
        """
        Initialize TempDirectoryManager.

        Args:
            base_dir: Base directory for temp directories (default: system temp)
            prefix: Prefix for temp directory names
            cleanup_on_exit: If True, cleanup on Python exit
        """
        self.base_dir = base_dir
        self.prefix = prefix
        self.cleanup_on_exit = cleanup_on_exit
        self.temp_dirs: dict[str, Path] = {}

        if cleanup_on_exit:
            import atexit

            atexit.register(self.cleanup_all)

    def create_temp_dir(self, task_id: str, copy_from: Path | None = None) -> Path:
        """
        Create a temporary directory for a task.

        Args:
            task_id: Unique identifier for the task
            copy_from: Optional source directory to copy files from

        Returns:
            Path to temporary directory
        """
        # Create temp directory
        if self.base_dir:
            temp_dir = Path(tempfile.mkdtemp(
                prefix=self.prefix, dir=self.base_dir
            ))
        else:
            temp_dir = Path(tempfile.mkdtemp(prefix=self.prefix))

        self.temp_dirs[task_id] = temp_dir
        logger.info(f"Created temp directory for {task_id}: {temp_dir}")

        # Copy files from source if provided
        if copy_from and copy_from.exists():
            try:
                self._copy_directory(copy_from, temp_dir)
                logger.debug(f"Copied files from {copy_from} to {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to copy files from {copy_from}: {e}")

        return temp_dir

    def get_temp_dir(self, task_id: str) -> Path | None:
        """
        Get temporary directory for a task.

        Args:
            task_id: Task identifier

        Returns:
            Path to temporary directory or None if not found
        """
        return self.temp_dirs.get(task_id)

    def remove_temp_dir(self, task_id: str) -> bool:
        """
        Remove temporary directory for a task.

        Args:
            task_id: Task identifier

        Returns:
            True if removed successfully, False otherwise
        """
        temp_dir = self.temp_dirs.pop(task_id, None)
        if temp_dir is None:
            return False

        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info(f"Removed temp directory for {task_id}: {temp_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove temp directory {temp_dir}: {e}")
            return False

    def cleanup_all(self) -> int:
        """
        Clean up all temporary directories.

        Returns:
            Number of directories cleaned up
        """
        cleaned = 0
        task_ids = list(self.temp_dirs.keys())

        for task_id in task_ids:
            if self.remove_temp_dir(task_id):
                cleaned += 1

        return cleaned

    def _copy_directory(self, src: Path, dst: Path) -> None:
        """
        Copy directory contents from source to destination.

        Args:
            src: Source directory
            dst: Destination directory
        """
        # Create destination if it doesn't exist
        dst.mkdir(parents=True, exist_ok=True)

        # Copy files and directories
        for item in src.iterdir():
            src_item = src / item.name
            dst_item = dst / item.name

            if src_item.is_dir():
                # Recursively copy directories
                shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            else:
                # Copy files
                shutil.copy2(src_item, dst_item)


def needs_git_operations(task_type: str, commands: list[str]) -> bool:
    """
    Determine if a task needs git operations.

    Args:
        task_type: Type of task (e.g., "reviewer", "tester", "implementer")
        commands: List of commands to execute

    Returns:
        True if git operations are needed, False otherwise
    """
    # Tasks that typically need git operations
    git_required_tasks = {
        "implementer",  # Code changes need git
        "refactor",  # Refactoring needs git
        "workflow",  # Workflows may need git
    }

    # Commands that indicate git operations
    git_indicators = [
        "git ",
        "commit",
        "branch",
        "merge",
        "rebase",
        "worktree",
    ]

    # Check task type
    if task_type.lower() in git_required_tasks:
        return True

    # Check commands for git indicators
    commands_str = " ".join(commands).lower()
    if any(indicator in commands_str for indicator in git_indicators):
        return True

    # Default: don't need git for most tasks
    return False

