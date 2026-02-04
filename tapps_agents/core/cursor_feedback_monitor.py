"""
Cursor IDE feedback monitor.

Monitors workspace files for feedback signals and tracks satisfaction.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .feedback_collector import FeedbackCollector

logger = logging.getLogger(__name__)


class CursorFeedbackMonitor:
    """
    Monitors Cursor IDE workspace for feedback signals.
    
    Detects manual edits, completion signals, and satisfaction indicators.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        callback: Callable[[Any], None] | None = None,
    ):
        """
        Initialize feedback monitor.
        
        Args:
            project_root: Project root directory
            callback: Optional callback function for feedback events
        """
        self.project_root = project_root or Path.cwd()
        self.feedback_collector = FeedbackCollector(self.project_root)
        self.callback = callback
        self.monitoring = False
        self.watched_files: dict[Path, float] = {}  # Path -> last modified time

    def start_monitoring(self, interval_seconds: float = 5.0) -> None:
        """
        Start monitoring workspace files.
        
        Args:
            interval_seconds: Check interval in seconds
        """
        if self.monitoring:
            logger.warning("Monitor already running")
            return
        
        self.monitoring = True
        logger.info("Starting Cursor feedback monitor")
        
        # In a real implementation, this would run in a background thread
        # For now, just mark as monitoring
        # Background agents would handle this in production

    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.monitoring = False
        logger.info("Stopped Cursor feedback monitor")

    def check_command_files(self) -> list[Any]:
        """
        Check for command files and collect feedback.
        
        Returns:
            List of FeedbackRecord objects
        """
        feedback_records = []
        
        # Look for command files in .cursor directory
        cursor_dir = self.project_root / ".cursor"
        if not cursor_dir.exists():
            return feedback_records
        
        # Check for skill command files
        command_files = list(cursor_dir.glob("**/.cursor-skill-command.txt"))
        
        for command_file in command_files:
            try:
                # Check if file was modified since last check
                mtime = command_file.stat().st_mtime
                if command_file not in self.watched_files or mtime > self.watched_files[command_file]:
                    feedback = self.feedback_collector.collect_from_command_file(command_file)
                    if feedback:
                        feedback_records.append(feedback)
                        if self.callback:
                            self.callback(feedback)
                    
                    self.watched_files[command_file] = mtime
            
            except Exception as e:
                logger.warning(f"Error checking command file {command_file}: {e}")
        
        return feedback_records

    def detect_manual_edits(
        self, target_files: list[Path]
    ) -> list[Any]:
        """
        Detect manual edits to agent-generated files.
        
        Args:
            target_files: List of files to monitor
            
        Returns:
            List of FeedbackRecord objects
        """
        feedback_records = []
        
        # This would typically compare against a snapshot
        # For now, simplified implementation
        for file_path in target_files:
            if not file_path.exists():
                continue
            
            try:
                # Check modification time
                mtime = file_path.stat().st_mtime
                if file_path not in self.watched_files:
                    self.watched_files[file_path] = mtime
                    continue
                
                # File was modified
                if mtime > self.watched_files[file_path]:
                    # Read current content
                    current_content = file_path.read_text(encoding="utf-8")
                    
                    # In production, would compare against stored snapshot
                    # For now, just record that file was modified
                    feedback = self.feedback_collector.collect_from_workspace_changes(
                        file_path, "", current_content  # Simplified
                    )
                    if feedback:
                        feedback_records.append(feedback)
                    
                    self.watched_files[file_path] = mtime
            
            except Exception as e:
                logger.warning(f"Error detecting edits in {file_path}: {e}")
        
        return feedback_records

