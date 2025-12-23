"""
Inline Command Suggestions

Suggests tapps-agents commands in Cursor chat.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class InlineSuggester:
    """
    Suggests tapps-agents commands based on user actions.

    Features:
    - Detect when user is doing manual work that could use tapps-agents
    - Suggest commands with context
    - Show usage examples
    """

    def suggest(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Suggest commands based on context.

        Args:
            context: User action context

        Returns:
            List of command suggestions
        """
        suggestions = []

        # Detect manual test writing
        if context.get("action") == "writing_tests":
            suggestions.append({
                "command": "@simple-mode *test <file>",
                "description": "Generate tests automatically",
                "confidence": 0.9,
            })

        # Detect manual code review
        if context.get("action") == "reviewing_code":
            suggestions.append({
                "command": "@simple-mode *review <file>",
                "description": "Automated code review with quality scores",
                "confidence": 0.85,
            })

        return suggestions

