"""
Cursor Chat Integration for Progress Updates

Sends progress updates to Cursor chat interface during workflow execution.
Epic 8 / Story 8.3: Cursor Chat Integration
"""

import logging

from ..core.unicode_safe import safe_print, _unicode_to_ascii
from .progress_updates import ProgressUpdate

logger = logging.getLogger(__name__)


class ChatUpdateSender:
    """Sends progress updates to Cursor chat interface."""

    def __init__(self, enable_updates: bool = True):
        """
        Initialize chat update sender.

        Args:
            enable_updates: Whether to enable progress updates
        """
        self.enable_updates = enable_updates
        self.last_message_id: str | None = None
        self.message_count = 0

    def send_update(self, formatted_message: str, replace_last: bool = False) -> None:
        """
        Send formatted update to Cursor chat.

        Args:
            formatted_message: Formatted markdown message
            replace_last: Whether to replace last message (not supported, always sends new)
        """
        if not self.enable_updates:
            return

        # Cursor chat doesn't have a direct API, so we use print()
        # which appears in the chat interface
        # Note: Message replacement not supported without API, so we always send new messages
        safe_print(f"\n{formatted_message}\n")
        self.message_count += 1

    def send_progress_update(self, update: ProgressUpdate, formatted: str) -> None:
        """
        Send a progress update.

        Args:
            update: Progress update to send
            formatted: Formatted message string
        """
        # For step progress updates, we could try to replace, but without API
        # we'll just send new messages with clear labeling
        should_replace = (
            update.update_type.value.startswith("step_")
            and update.update_type != update.update_type.STEP_FAILED
        )

        # Since we can't replace, we'll use a compact format for progress updates
        # and full format for important events
        if should_replace and self.message_count > 0:
            # Try to make it clear this is an update (though we can't actually replace)
            formatted = f"**Update:** {formatted}"

        self.send_update(formatted, replace_last=should_replace)

    def send_completion_summary(self, summary: str) -> None:
        """
        Send workflow completion summary.

        Args:
            summary: Formatted summary message
        """
        # Completion summaries are always new messages (not replacements)
        self.send_update(summary, replace_last=False)


def format_progress_bar(percentage: float, width: int = 30) -> str:
    """
    Generate text-based progress bar for chat.

    Args:
        percentage: Completion percentage (0-100)
        width: Width of progress bar in characters

    Returns:
        Formatted progress bar string (ASCII-safe)
    """
    from ..core.unicode_safe import safe_format_progress_bar
    return safe_format_progress_bar(percentage, width)

