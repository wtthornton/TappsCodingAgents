"""
Storage module for external feedback data.

Handles persistent storage and retrieval of external evaluation feedback.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .external_feedback_models import ExternalFeedbackData
from .storage_models import StoragePath

logger = logging.getLogger(__name__)


class ExternalFeedbackStorage:
    """Manages storage of external feedback data."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize external feedback storage.

        Args:
            project_root: Project root directory. If None, uses current directory.
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.storage_path = StoragePath.from_project_root(project_root)
        self.feedback_dir = self.storage_path.feedback_dir
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def save_feedback(self, feedback_data: ExternalFeedbackData) -> Path:
        """
        Save feedback data to file.

        Args:
            feedback_data: ExternalFeedbackData instance

        Returns:
            Path to saved file

        Raises:
            IOError: If file system operation fails
        """
        # Generate filename from feedback ID
        filename = f"feedback-{feedback_data.feedback_id}.json"
        file_path = self.feedback_dir / filename

        # Convert to dict for JSON serialization
        data = feedback_data.to_dict()

        # Atomic write (write to temp file, then rename)
        temp_path = file_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(file_path)
            logger.debug(f"Saved external feedback to {file_path}")
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to save feedback: {e}") from e

        return file_path

    def load_feedback(self, feedback_id: str) -> ExternalFeedbackData | None:
        """
        Load feedback by ID.

        Args:
            feedback_id: Feedback UUID

        Returns:
            ExternalFeedbackData instance or None if not found
        """
        filename = f"feedback-{feedback_id}.json"
        file_path = self.feedback_dir / filename

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ExternalFeedbackData.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load feedback {feedback_id}: {e}")
            return None

    def list_feedback(
        self,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
    ) -> list[ExternalFeedbackData]:
        """
        List feedback entries with optional filtering.

        Args:
            workflow_id: Filter by workflow ID
            agent_id: Filter by agent ID
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            limit: Maximum number of entries to return

        Returns:
            List of ExternalFeedbackData instances
        """
        feedback_entries: list[ExternalFeedbackData] = []

        # Find all feedback files
        if not self.feedback_dir.exists():
            return feedback_entries

        feedback_files = list(self.feedback_dir.glob("feedback-*.json"))
        for file_path in feedback_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                feedback = ExternalFeedbackData.from_dict(data)

                # Apply filters
                if workflow_id and (
                    not feedback.context or feedback.context.workflow_id != workflow_id
                ):
                    continue
                if agent_id and (
                    not feedback.context or feedback.context.agent_id != agent_id
                ):
                    continue
                if start_date and feedback.timestamp < start_date:
                    continue
                if end_date and feedback.timestamp > end_date:
                    continue

                feedback_entries.append(feedback)
            except Exception as e:
                logger.warning(f"Failed to load feedback file {file_path}: {e}")
                continue

        # Sort by timestamp (newest first)
        feedback_entries.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        if limit is not None and limit > 0:
            feedback_entries = feedback_entries[:limit]

        return feedback_entries

    def aggregate_feedback(
        self,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate feedback statistics.

        Args:
            workflow_id: Filter by workflow ID
            agent_id: Filter by agent ID
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)

        Returns:
            Dictionary with aggregation statistics
        """
        feedback_entries = self.list_feedback(
            workflow_id=workflow_id,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
        )

        if not feedback_entries:
            return {
                "count": 0,
                "average_ratings": {},
                "suggestion_count": 0,
            }

        # Aggregate ratings
        rating_sums: dict[str, float] = {}
        rating_counts: dict[str, int] = {}
        total_suggestions = 0

        for feedback in feedback_entries:
            total_suggestions += len(feedback.suggestions)
            for metric, rating in feedback.performance_ratings.items():
                rating_sums[metric] = rating_sums.get(metric, 0.0) + rating
                rating_counts[metric] = rating_counts.get(metric, 0) + 1

        # Calculate averages
        average_ratings: dict[str, float] = {}
        for metric in rating_sums:
            if rating_counts[metric] > 0:
                average_ratings[metric] = rating_sums[metric] / rating_counts[metric]

        return {
            "count": len(feedback_entries),
            "average_ratings": average_ratings,
            "suggestion_count": total_suggestions,
            "average_suggestions_per_feedback": total_suggestions / len(feedback_entries)
            if feedback_entries
            else 0.0,
        }
