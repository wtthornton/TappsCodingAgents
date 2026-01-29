"""
Passive Expert Notification System

Proactively suggests relevant experts during manual coding to prevent users
from forgetting to consult domain experts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .domain_detector import DomainDetector
from .expert_engine import ExpertEngine


@dataclass
class Notification:
    """Expert consultation notification."""

    expert_id: str
    expert_name: str
    domain: str
    priority: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def format(self) -> str:
        """Format notification for display."""
        return f"""ℹ️  Detected {self.domain} domain - Consider consulting {self.expert_name} (priority: {self.priority:.2f})
   Use: tapps-agents expert consult {self.expert_id} "your query"
"""


class PassiveNotifier:
    """
    Proactively suggest experts during manual coding.

    Detects domains from context and notifies users about relevant high-priority
    experts (priority > threshold, default 0.9).
    """

    def __init__(
        self,
        expert_engine: ExpertEngine,
        enabled: bool = True,
        high_priority_threshold: float = 0.9,
        throttle_seconds: int = 60,
    ):
        """
        Initialize passive notifier.

        Args:
            expert_engine: Expert engine for expert lookup
            enabled: Enable/disable notifications
            high_priority_threshold: Minimum priority for notifications (default: 0.9)
            throttle_seconds: Minimum seconds between repeated notifications (default: 60)
        """
        self.expert_engine = expert_engine
        self.enabled = enabled
        self.high_priority_threshold = high_priority_threshold
        self.throttle_seconds = throttle_seconds

        self.domain_detector = DomainDetector()
        self._notification_history: dict[str, datetime] = {}  # expert_id -> last_notified

    def notify_if_relevant(self, context: str) -> list[Notification]:
        """
        Check context for domains and return notifications for relevant experts.

        Args:
            context: Context string (prompt, code, file content)

        Returns:
            List of notifications for high-priority relevant experts
        """
        if not self.enabled:
            return []

        # Detect domains from context
        detected_domains = self.domain_detector.detect_domains(context)

        notifications: list[Notification] = []

        # Find relevant experts for detected domains
        for domain in detected_domains:
            experts = self.expert_engine.find_experts_by_domain(domain)

            for expert in experts:
                # Check priority threshold
                if expert.priority < self.high_priority_threshold:
                    continue

                # Check throttling
                if self._is_throttled(expert.id):
                    continue

                # Create notification
                notification = Notification(
                    expert_id=expert.id,
                    expert_name=expert.name,
                    domain=domain,
                    priority=expert.priority,
                    message=f"Detected {domain} domain",
                )

                notifications.append(notification)

                # Update notification history
                self._notification_history[expert.id] = datetime.now()

        return notifications

    def _is_throttled(self, expert_id: str) -> bool:
        """
        Check if expert notification is throttled.

        Args:
            expert_id: Expert ID

        Returns:
            True if throttled, False otherwise
        """
        if expert_id not in self._notification_history:
            return False

        last_notified = self._notification_history[expert_id]
        elapsed = (datetime.now() - last_notified).total_seconds()

        return elapsed < self.throttle_seconds

    def format_notifications(self, notifications: list[Notification]) -> str:
        """
        Format multiple notifications for display.

        Args:
            notifications: List of notifications

        Returns:
            Formatted string for all notifications
        """
        if not notifications:
            return ""

        lines = []
        for notif in notifications:
            lines.append(notif.format())

        return "\n".join(lines)

    def clear_history(self):
        """Clear notification history (for testing)."""
        self._notification_history.clear()

    @classmethod
    def from_config(cls, expert_engine: ExpertEngine, config: Any) -> PassiveNotifier:
        """
        Create PassiveNotifier from configuration.

        Args:
            expert_engine: Expert engine
            config: Project configuration object

        Returns:
            Configured PassiveNotifier instance
        """
        # Extract config values
        enabled = True
        threshold = 0.9
        throttle = 60

        if hasattr(config, "expert"):
            expert_config = config.expert
            enabled = getattr(expert_config, "passive_notifications_enabled", True)
            threshold = getattr(expert_config, "high_priority_threshold", 0.9)
            throttle = getattr(expert_config, "notification_throttle", 60)

        return cls(
            expert_engine=expert_engine,
            enabled=enabled,
            high_priority_threshold=threshold,
            throttle_seconds=throttle,
        )


class NotificationFormatter:
    """Format notifications for different output contexts."""

    @staticmethod
    def format_cli(notifications: list[Notification]) -> str:
        """Format notifications for CLI output."""
        if not notifications:
            return ""

        lines = ["\n" + "=" * 70]
        lines.append("💡 EXPERT SUGGESTIONS")
        lines.append("=" * 70)

        for notif in notifications:
            lines.append(f"\n{notif.format()}")

        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    @staticmethod
    def format_ide(notifications: list[Notification]) -> str:
        """Format notifications for IDE integration."""
        if not notifications:
            return ""

        lines = []
        for notif in notifications:
            lines.append(
                f"💡 {notif.expert_name}: Consider consulting for {notif.domain} domain"
            )

        return "\n".join(lines)

    @staticmethod
    def format_json(notifications: list[Notification]) -> str:
        """Format notifications as JSON."""
        import json

        data = [
            {
                "expert_id": n.expert_id,
                "expert_name": n.expert_name,
                "domain": n.domain,
                "priority": n.priority,
                "message": n.message,
                "timestamp": n.timestamp.isoformat(),
            }
            for n in notifications
        ]

        return json.dumps(data, indent=2)
