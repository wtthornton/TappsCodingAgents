"""
Progress.txt Logger - Human-Readable Append-Only Logging

Ralph-style progress logging for autonomous workflow execution.
Provides simple, human-readable progress tracking alongside comprehensive structured logs.
"""

from pathlib import Path


class ProgressLogger:
    """Simple append-only progress logger (Ralph-style)."""

    def __init__(self, progress_file: Path):
        """
        Initialize ProgressLogger.

        Args:
            progress_file: Path to progress.txt file (typically .tapps-agents/progress.txt)
        """
        self.progress_file = Path(progress_file)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

    def log_iteration(
        self,
        iteration: int,
        story_title: str | None = None,
        files_changed: list[str] | None = None,
        learnings: list[str] | None = None,
        thread_id: str | None = None,
        status: str = "completed",
    ) -> None:
        """
        Append iteration log to progress.txt.

        Args:
            iteration: Iteration number (1-based)
            story_title: Title of the story/workflow step being executed
            files_changed: List of file paths that were changed
            learnings: List of learnings/discoveries from this iteration
            thread_id: Workflow ID or thread ID for reference
            status: Status of the iteration (completed, failed, running)
        """
        # Build log entry
        lines = [f"Iteration {iteration}: "]

        # Add story title or generic description
        if story_title:
            lines[0] += f'Implemented story "{story_title}"'
        else:
            lines[0] += "Workflow execution"

        # Add files changed
        if files_changed:
            file_list = ", ".join(files_changed)
            lines.append(f"  - Files changed: {file_list}")
        else:
            lines.append("  - Files changed: None")

        # Add learnings
        if learnings:
            for learning in learnings:
                lines.append(f"  - Learnings: {learning}")
        else:
            lines.append("  - Learnings: None")

        # Add thread/workflow ID
        if thread_id:
            lines.append(f"  - Thread: {thread_id}")

        # Add status
        lines.append(f"  - Status: {status}")

        # Add blank line for readability
        lines.append("")

        # Append to file
        log_entry = "\n".join(lines)
        try:
            with open(self.progress_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Don't fail workflow if logging fails
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to write to progress.txt: {e}")

    def log_story_completion(
        self,
        story_id: str,
        story_title: str,
        passes: bool,
        files_changed: list[str] | None = None,
        learnings: list[str] | None = None,
    ) -> None:
        """
        Log story completion (passes: true/false pattern).

        Args:
            story_id: Unique identifier for the story
            story_title: Title of the story
            passes: Whether the story passed (True) or failed (False)
            files_changed: List of file paths that were changed
            learnings: List of learnings/discoveries
        """
        # Build log entry for story completion
        status = "passed" if passes else "failed"
        lines = [f"Story {story_id}: "]

        # Add story title
        lines[0] += f'"{story_title}" - {status.upper()}'

        # Add files changed
        if files_changed:
            file_list = ", ".join(files_changed)
            lines.append(f"  - Files changed: {file_list}")
        else:
            lines.append("  - Files changed: None")

        # Add learnings
        if learnings:
            for learning in learnings:
                lines.append(f"  - Learnings: {learning}")
        else:
            lines.append("  - Learnings: None")

        # Add status
        lines.append(f"  - Status: {status}")

        # Add blank line for readability
        lines.append("")

        # Append to file
        log_entry = "\n".join(lines)
        try:
            with open(self.progress_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Don't fail workflow if logging fails
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to write to progress.txt: {e}")
