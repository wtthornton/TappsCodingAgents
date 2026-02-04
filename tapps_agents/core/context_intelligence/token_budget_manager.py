"""Token budget manager for context injection."""

import logging

logger = logging.getLogger(__name__)


class TokenBudgetManager:
    """Manages token budgets for context."""

    def __init__(self, budget: int = 4000):
        self.budget = budget
        self.used = 0

    def can_add(self, estimated_tokens: int) -> bool:
        """Check if estimated tokens can be added."""
        return self.used + estimated_tokens <= self.budget

    def add(self, tokens: int) -> None:
        """Add tokens to used budget."""
        self.used += tokens

    def reset(self) -> None:
        """Reset budget."""
        self.used = 0

