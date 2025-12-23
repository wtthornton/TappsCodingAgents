"""Relevance scorer for context ranking."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Scores relevance of context pieces."""

    def score(self, context_piece: dict[str, Any], query: str | None = None) -> float:
        """Score relevance of a context piece."""
        # Simple scoring: higher for more recent, related files
        score = 0.5  # Base score
        
        # Boost for query matches
        if query:
            content = str(context_piece.get("content", ""))
            if query.lower() in content.lower():
                score += 0.3
        
        return min(1.0, score)

