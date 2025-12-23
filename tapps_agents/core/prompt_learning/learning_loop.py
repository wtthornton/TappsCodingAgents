"""Continuous learning loop for prompts."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LearningLoop:
    """Manages continuous prompt learning."""

    def __init__(self):
        self.metrics: dict[str, Any] = {}

    def track_metrics(self, prompt_version_id: str, metrics: dict[str, Any]) -> None:
        """Track metrics for a prompt version."""
        self.metrics[prompt_version_id] = metrics

    def should_optimize(self, prompt_version_id: str) -> bool:
        """Determine if prompt should be optimized."""
        # Simple heuristic: optimize if enough samples collected
        metrics = self.metrics.get(prompt_version_id, {})
        return metrics.get("sample_count", 0) >= 10

