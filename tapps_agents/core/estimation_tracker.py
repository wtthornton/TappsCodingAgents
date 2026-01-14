"""
Estimation Tracker - Tracks estimation accuracy and provides calibration.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EstimationRecord:
    """Record of an estimation with actuals."""

    story_id: str
    estimated_points: int
    actual_points: int | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    complexity: str = "medium"  # "low", "medium", "high"
    confidence: float = 0.5  # 0.0-1.0
    timestamp: str = ""


@dataclass
class EstimationAccuracy:
    """Estimation accuracy metrics."""

    total_estimations: int = 0
    average_error: float = 0.0
    average_absolute_error: float = 0.0
    calibration_factor: float = 1.0  # Multiplier to apply to future estimates
    confidence_score: float = 0.0  # 0-100: How reliable are estimates?


class EstimationTracker:
    """Tracks estimation accuracy and provides calibration."""

    def __init__(self, storage_path: Path | None = None):
        """
        Initialize estimation tracker.

        Args:
            storage_path: Path to store estimation history
        """
        self.storage_path = storage_path or Path(".tapps-agents") / "estimation_history.json"
        self.records: list[EstimationRecord] = []

    def add_estimation(self, record: EstimationRecord):
        """Add an estimation record."""
        self.records.append(record)
        self._save()

    def update_actuals(self, story_id: str, actual_points: int | None = None, actual_hours: float | None = None):
        """Update actual values for an estimation."""
        for record in self.records:
            if record.story_id == story_id:
                if actual_points is not None:
                    record.actual_points = actual_points
                if actual_hours is not None:
                    record.actual_hours = actual_hours
                self._save()
                return

        logger.warning(f"Estimation record not found for story: {story_id}")

    def calculate_accuracy(self) -> EstimationAccuracy:
        """Calculate estimation accuracy metrics."""
        accuracy = EstimationAccuracy()

        # Filter records with actuals
        completed = [r for r in self.records if r.actual_points is not None]
        accuracy.total_estimations = len(completed)

        if not completed:
            return accuracy

        # Calculate errors
        errors = []
        for record in completed:
            if record.estimated_points and record.actual_points:
                error = (record.actual_points - record.estimated_points) / record.estimated_points
                errors.append(error)

        if errors:
            accuracy.average_error = sum(errors) / len(errors)
            accuracy.average_absolute_error = sum(abs(e) for e in errors) / len(errors)

            # Calculate calibration factor (inverse of average error)
            if accuracy.average_error != 0:
                accuracy.calibration_factor = 1.0 / (1.0 + accuracy.average_error)
            else:
                accuracy.calibration_factor = 1.0

            # Calculate confidence score (lower error = higher confidence)
            # 0% error = 100% confidence, 50% error = 0% confidence
            if accuracy.average_absolute_error <= 0.5:
                accuracy.confidence_score = 100.0 * (1.0 - accuracy.average_absolute_error)
            else:
                accuracy.confidence_score = max(0.0, 100.0 * (1.0 - accuracy.average_absolute_error))

        return accuracy

    def get_calibrated_estimate(self, estimated_points: int, complexity: str = "medium") -> dict[str, Any]:
        """
        Get calibrated estimate based on historical accuracy.

        Args:
            estimated_points: Raw estimated story points
            complexity: Story complexity (low, medium, high)

        Returns:
            Dict with calibrated estimate and confidence
        """
        accuracy = self.calculate_accuracy()

        # Apply calibration factor
        calibrated_points = int(estimated_points * accuracy.calibration_factor)

        # Adjust confidence based on complexity
        confidence = accuracy.confidence_score
        if complexity == "high":
            confidence *= 0.8  # Lower confidence for high complexity
        elif complexity == "low":
            confidence *= 1.1  # Higher confidence for low complexity
        confidence = min(100.0, max(0.0, confidence))

        return {
            "estimated_points": estimated_points,
            "calibrated_points": calibrated_points,
            "calibration_factor": accuracy.calibration_factor,
            "confidence": confidence,
            "accuracy_metrics": {
                "average_error": accuracy.average_error,
                "average_absolute_error": accuracy.average_absolute_error,
                "total_estimations": accuracy.total_estimations,
            },
        }

    def _save(self):
        """Save estimation records to file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "records": [
                {
                    "story_id": r.story_id,
                    "estimated_points": r.estimated_points,
                    "actual_points": r.actual_points,
                    "estimated_hours": r.estimated_hours,
                    "actual_hours": r.actual_hours,
                    "complexity": r.complexity,
                    "confidence": r.confidence,
                    "timestamp": r.timestamp,
                }
                for r in self.records
            ]
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load estimation records from file."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.records = [
                EstimationRecord(
                    story_id=r["story_id"],
                    estimated_points=r["estimated_points"],
                    actual_points=r.get("actual_points"),
                    estimated_hours=r.get("estimated_hours"),
                    actual_hours=r.get("actual_hours"),
                    complexity=r.get("complexity", "medium"),
                    confidence=r.get("confidence", 0.5),
                    timestamp=r.get("timestamp", ""),
                )
                for r in data.get("records", [])
            ]
        except Exception as e:
            logger.warning(f"Failed to load estimation history: {e}")
