"""
Feedback collector for Cursor IDE interactions.

Monitors Cursor IDE interactions via file-based coordination.
"""

import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .evaluation_models import FeedbackRecord
from .storage_manager import StorageManager

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    Collects feedback from Cursor IDE interactions.
    
    Monitors file-based coordination files for feedback signals.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize feedback collector.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.storage_manager = StorageManager(self.project_root)
        self.feedback_storage = self.storage_manager.feedback

    def collect_from_command_file(
        self, command_file: Path
    ) -> FeedbackRecord | None:
        """
        Collect feedback from Cursor skill command file.
        
        Args:
            command_file: Path to .cursor-skill-command.txt
            
        Returns:
            FeedbackRecord if feedback detected, None otherwise
        """
        if not command_file.exists():
            return None
        
        try:
            command_text = command_file.read_text(encoding="utf-8")
            
            # Parse command (format: @agent *command args...)
            parts = command_text.strip().split()
            if not parts or not parts[0].startswith("@"):
                return None
            
            agent_name = parts[0][1:]  # Remove @
            command = parts[1] if len(parts) > 1 else ""
            
            # Check for completion signal
            completion_file = command_file.parent / ".cursor-skill-completed.txt"
            accepted = False
            if completion_file.exists():
                completion_data = completion_file.read_text(encoding="utf-8")
                accepted = "accepted" in completion_data.lower()
            
            # Create feedback record
            feedback = FeedbackRecord(
                id=str(uuid4()),
                agent_name=agent_name,
                command=command,
                prompt_version_id=None,  # Will be linked later
                accepted=accepted,
                timestamp=datetime.now(),
                metadata={
                    "command_file": str(command_file),
                    "command_text": command_text[:500],  # Truncate
                },
            )
            
            # Store feedback
            self.feedback_storage.save_feedback(feedback.to_dict())
            
            return feedback
        
        except Exception as e:
            logger.warning(f"Error collecting feedback from {command_file}: {e}")
            return None

    def collect_from_workspace_changes(
        self, target_file: Path, original_content: str, current_content: str
    ) -> FeedbackRecord | None:
        """
        Detect feedback from workspace file changes.
        
        Args:
            target_file: File that was changed
            original_content: Original file content (before agent)
            current_content: Current file content (after user edits)
            
        Returns:
            FeedbackRecord if changes detected
        """
        # Detect if user made manual edits (rejection signal)
        if original_content != current_content:
            # Simple heuristic: if significant changes, likely feedback
            # More sophisticated analysis could use diff algorithms
            
            # Check if it's a complete rewrite (rejection)
            similarity = self._calculate_similarity(original_content, current_content)
            accepted = similarity > 0.7  # If >70% similar, likely accepted with minor edits
            
            feedback = FeedbackRecord(
                id=str(uuid4()),
                agent_name="unknown",  # Will be inferred from context
                command="edit",
                prompt_version_id=None,
                accepted=accepted,
                feedback_text=f"File modified: {similarity:.2%} similarity",
                timestamp=datetime.now(),
                metadata={
                    "target_file": str(target_file),
                    "similarity": similarity,
                },
            )
            
            self.feedback_storage.save_feedback(feedback.to_dict())
            return feedback
        
        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def list_recent_feedback(
        self, agent_name: str | None = None, limit: int = 100
    ) -> list[FeedbackRecord]:
        """
        List recent feedback records.
        
        Args:
            agent_name: Optional filter by agent
            limit: Maximum number of records
            
        Returns:
            List of FeedbackRecord objects
        """
        files = self.feedback_storage.list_feedback(agent_name=agent_name)
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        feedback_records = []
        for file_path in files[:limit]:
            try:
                data = self.feedback_storage.load_feedback(file_path.name)
                feedback_records.append(FeedbackRecord.from_dict(data))
            except Exception:
                continue
        
        return feedback_records

