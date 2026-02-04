"""Token budget monitoring and tracking for workflows.

This module provides token budget monitoring with threshold warnings to prevent
token exhaustion during workflow execution.

@ai-prime-directive: Token monitoring must be:
- Real-time and accurate
- Non-intrusive (minimal performance overhead)
- Configurable (thresholds, warnings)
- Integrated with workflow engine and CLI

Usage:
    from tapps_agents.core.token_monitor import TokenMonitor, TokenBudget

    budget = TokenBudget(total=200000)
    monitor = TokenMonitor(budget)

    # Update after each step
    result = monitor.update(tokens_consumed=5000)
    if result["message"]:
        print(result["message"])
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

logger = logging.getLogger(__name__)


ThresholdLevel = Literal["green", "yellow", "orange", "red"]


@dataclass
class TokenBudget:
    """Token budget tracking for workflows.

    Attributes:
        total: Total token budget (default: 200K for Claude Sonnet 4.5)
        consumed: Tokens consumed so far
        remaining: Tokens remaining
    """
    total: int = 200000  # Claude Sonnet 4.5 limit
    consumed: int = 0
    remaining: int = 200000

    @property
    def usage_percentage(self) -> float:
        """Calculate usage as percentage.

        Returns:
            Usage percentage (0-100)
        """
        if self.total == 0:
            return 0.0
        return (self.consumed / self.total) * 100

    def check_threshold(self) -> ThresholdLevel:
        """Check current threshold level.

        Returns:
            Threshold level: green, yellow, orange, or red
        """
        pct = self.usage_percentage
        if pct >= 90:
            return "red"      # Critical (≥90%)
        elif pct >= 75:
            return "orange"   # High (≥75%)
        elif pct >= 50:
            return "yellow"   # Warning (≥50%)
        else:
            return "green"    # OK (<50%)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "total": self.total,
            "consumed": self.consumed,
            "remaining": self.remaining,
            "usage_percentage": self.usage_percentage,
            "threshold": self.check_threshold()
        }


@dataclass
class TokenMonitorResult:
    """Result from token monitor update.

    Attributes:
        consumed: Total tokens consumed
        remaining: Tokens remaining
        percentage: Usage percentage
        threshold: Current threshold level
        threshold_changed: Whether threshold changed since last update
        message: Optional warning message
        should_checkpoint: Whether checkpoint should be created
    """
    consumed: int
    remaining: int
    percentage: float
    threshold: ThresholdLevel
    threshold_changed: bool
    message: str | None
    should_checkpoint: bool
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "consumed": self.consumed,
            "remaining": self.remaining,
            "percentage": self.percentage,
            "threshold": self.threshold,
            "threshold_changed": self.threshold_changed,
            "message": self.message,
            "should_checkpoint": self.should_checkpoint,
            "timestamp": self.timestamp.isoformat()
        }


class TokenMonitor:
    """Monitor token usage and emit warnings.

    Tracks token consumption across workflow execution and emits warnings
    when thresholds are crossed (50%, 75%, 90%).

    Example:
        >>> budget = TokenBudget(total=200000)
        >>> monitor = TokenMonitor(budget)
        >>>
        >>> # After workflow step
        >>> result = monitor.update(5000)
        >>> if result.message:
        ...     print(result.message)
    """

    def __init__(
        self,
        budget: TokenBudget,
        enable_warnings: bool = True,
        checkpoint_threshold: float = 90.0
    ):
        """Initialize token monitor.

        Args:
            budget: Token budget to monitor
            enable_warnings: Whether to generate warning messages
            checkpoint_threshold: Percentage at which to suggest checkpoint
        """
        self.budget = budget
        self.enable_warnings = enable_warnings
        self.checkpoint_threshold = checkpoint_threshold
        self._last_threshold: ThresholdLevel = "green"
        self._update_count = 0
        self._warning_history: list[TokenMonitorResult] = []

    def update(self, tokens_consumed: int) -> TokenMonitorResult:
        """Update token count and check thresholds.

        Args:
            tokens_consumed: Number of tokens consumed in this update

        Returns:
            Monitor result with threshold info and warnings
        """
        # Update budget
        self.budget.consumed += tokens_consumed
        self.budget.remaining = self.budget.total - self.budget.consumed
        self._update_count += 1

        # Check threshold
        current_threshold = self.budget.check_threshold()
        threshold_changed = current_threshold != self._last_threshold

        # Generate message if threshold changed
        message = None
        if self.enable_warnings and threshold_changed:
            message = self._get_threshold_message(current_threshold)
            logger.info(
                f"Token threshold crossed: {self._last_threshold} → {current_threshold} "
                f"({self.budget.usage_percentage:.1f}% consumed)"
            )

        # Check if checkpoint should be created
        should_checkpoint = self.budget.usage_percentage >= self.checkpoint_threshold

        # Create result
        result = TokenMonitorResult(
            consumed=self.budget.consumed,
            remaining=self.budget.remaining,
            percentage=self.budget.usage_percentage,
            threshold=current_threshold,
            threshold_changed=threshold_changed,
            message=message,
            should_checkpoint=should_checkpoint
        )

        # Update state
        self._last_threshold = current_threshold
        if message:
            self._warning_history.append(result)

        return result

    def _get_threshold_message(self, threshold: ThresholdLevel) -> str:
        """Get warning message for threshold.

        Args:
            threshold: Threshold level

        Returns:
            Warning message or empty string
        """
        remaining_k = self.budget.remaining // 1000
        consumed_pct = self.budget.usage_percentage

        messages = {
            "yellow": (
                f"⚠️  Token Budget Warning: {consumed_pct:.0f}% consumed "
                f"({remaining_k}K remaining)\n"
                "   Consider using lighter workflow presets for remaining tasks."
            ),
            "orange": (
                f"🟠 Token Budget Alert: {consumed_pct:.0f}% consumed "
                f"({remaining_k}K remaining)\n"
                "   Approaching token limit. Consider:\n"
                "   - Using --quick-enhance for simpler enhancements\n"
                "   - Creating checkpoint if workflow is long"
            ),
            "red": (
                f"🔴 Token Budget Critical: {consumed_pct:.0f}% consumed "
                f"({remaining_k}K remaining)\n"
                "   CRITICAL: Very low token budget!\n"
                "   Recommended actions:\n"
                "   - Save checkpoint: tapps-agents checkpoint save\n"
                "   - Resume in new session with: tapps-agents resume <checkpoint-id>\n"
                "   - Or switch to minimal workflow preset"
            )
        }

        return messages.get(threshold, "")

    def get_stats(self) -> dict:
        """Get monitoring statistics.

        Returns:
            Dictionary with monitoring stats
        """
        return {
            "total_updates": self._update_count,
            "warnings_issued": len(self._warning_history),
            "current_threshold": self._last_threshold,
            "budget": self.budget.to_dict(),
            "last_warning": (
                self._warning_history[-1].to_dict()
                if self._warning_history else None
            )
        }

    def format_status(self, verbose: bool = False) -> str:
        """Format current status as string.

        Args:
            verbose: Include detailed statistics

        Returns:
            Formatted status string
        """
        consumed_k = self.budget.consumed // 1000
        remaining_k = self.budget.remaining // 1000
        pct = self.budget.usage_percentage

        # Threshold emoji
        emoji = {
            "green": "✅",
            "yellow": "⚠️",
            "orange": "🟠",
            "red": "🔴"
        }[self._last_threshold]

        status = (
            f"{emoji} Token Budget: {consumed_k}K / {self.budget.total // 1000}K "
            f"({pct:.1f}% used, {remaining_k}K remaining)"
        )

        if verbose:
            stats = self.get_stats()
            status += (
                f"\n   Updates: {stats['total_updates']}, "
                f"Warnings: {stats['warnings_issued']}, "
                f"Threshold: {stats['current_threshold']}"
            )

        return status

    def reset(self, new_total: int | None = None) -> None:
        """Reset token monitor.

        Args:
            new_total: Optional new total budget
        """
        if new_total is not None:
            self.budget.total = new_total
        self.budget.consumed = 0
        self.budget.remaining = self.budget.total
        self._last_threshold = "green"
        self._update_count = 0
        self._warning_history.clear()
        logger.info(f"Token monitor reset (budget: {self.budget.total:,})")


def create_monitor(
    total: int = 200000,
    enable_warnings: bool = True,
    checkpoint_threshold: float = 90.0
) -> TokenMonitor:
    """Create token monitor with default settings.

    Args:
        total: Total token budget
        enable_warnings: Enable warning messages
        checkpoint_threshold: Checkpoint threshold percentage

    Returns:
        Configured TokenMonitor instance

    Example:
        >>> monitor = create_monitor(total=150000)
        >>> result = monitor.update(5000)
    """
    budget = TokenBudget(total=total)
    return TokenMonitor(
        budget=budget,
        enable_warnings=enable_warnings,
        checkpoint_threshold=checkpoint_threshold
    )
