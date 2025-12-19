"""
Learning Progression System for Simple Mode.

Tracks usage, manages feature unlock system (Beginner → Intermediate → Advanced),
and provides progression indicators to guide users as they gain experience.
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..cli.feedback import get_feedback


class UserLevel(Enum):
    """User proficiency levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class UsageStats:
    """Usage statistics for Simple Mode."""

    total_commands: int = 0
    build_commands: int = 0
    review_commands: int = 0
    fix_commands: int = 0
    test_commands: int = 0
    first_use_date: str | None = None
    last_use_date: str | None = None
    days_active: int = 0
    consecutive_days: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageStats":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ProgressionState:
    """Current progression state for a user."""

    level: UserLevel = UserLevel.BEGINNER
    commands_to_next_level: int = 10
    features_unlocked: list[str] = None
    tips_shown: list[str] = None

    def __post_init__(self):
        """Initialize default lists."""
        if self.features_unlocked is None:
            self.features_unlocked = ["simple_mode", "natural_language"]
        if self.tips_shown is None:
            self.tips_shown = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "commands_to_next_level": self.commands_to_next_level,
            "features_unlocked": self.features_unlocked,
            "tips_shown": self.tips_shown,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgressionState":
        """Create from dictionary."""
        level_str = data.get("level", "beginner")
        level = UserLevel(level_str) if isinstance(level_str, str) else UserLevel.BEGINNER
        return cls(
            level=level,
            commands_to_next_level=data.get("commands_to_next_level", 10),
            features_unlocked=data.get("features_unlocked", ["simple_mode", "natural_language"]),
            tips_shown=data.get("tips_shown", []),
        )


class LearningProgressionTracker:
    """Tracks user progression and manages feature unlocks."""

    # Level thresholds
    BEGINNER_TO_INTERMEDIATE = 10  # commands
    INTERMEDIATE_TO_ADVANCED = 50  # commands

    # Feature unlock requirements
    FEATURE_UNLOCKS = {
        "agent_specific_commands": {"level": UserLevel.INTERMEDIATE, "commands": 10},
        "advanced_workflows": {"level": UserLevel.INTERMEDIATE, "commands": 15},
        "custom_orchestrators": {"level": UserLevel.ADVANCED, "commands": 50},
        "expert_consultation": {"level": UserLevel.ADVANCED, "commands": 30},
        "multi_agent_parallel": {"level": UserLevel.ADVANCED, "commands": 40},
    }

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.feedback = get_feedback()
        self.stats_file = (
            self.project_root / ".tapps-agents" / "simple-mode-stats.json"
        )
        self.progression_file = (
            self.project_root / ".tapps-agents" / "simple-mode-progression.json"
        )

        self.stats = self._load_stats()
        self.progression = self._load_progression()

    def _load_stats(self) -> UsageStats:
        """Load usage statistics from file."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, encoding="utf-8") as f:
                    data = json.load(f)
                    return UsageStats.from_dict(data)
            except Exception:
                pass
        return UsageStats()

    def _load_progression(self) -> ProgressionState:
        """Load progression state from file."""
        if self.progression_file.exists():
            try:
                with open(self.progression_file, encoding="utf-8") as f:
                    data = json.load(f)
                    return ProgressionState.from_dict(data)
            except Exception:
                pass
        return ProgressionState()

    def _save_stats(self) -> None:
        """Save usage statistics to file."""
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats.to_dict(), f, indent=2)

    def _save_progression(self) -> None:
        """Save progression state to file."""
        self.progression_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progression_file, "w", encoding="utf-8") as f:
            json.dump(self.progression.to_dict(), f, indent=2)

    def record_command(self, action: str) -> None:
        """
        Record a command execution.

        Args:
            action: The action performed (build, review, fix, test)
        """
        now = datetime.now(UTC).isoformat()

        # Update stats
        self.stats.total_commands += 1
        if action == "build":
            self.stats.build_commands += 1
        elif action == "review":
            self.stats.review_commands += 1
        elif action == "fix":
            self.stats.fix_commands += 1
        elif action == "test":
            self.stats.test_commands += 1

        if not self.stats.first_use_date:
            self.stats.first_use_date = now
        self.stats.last_use_date = now

        # Update days active
        if self.stats.first_use_date:
            first_date = datetime.fromisoformat(self.stats.first_use_date.replace("Z", "+00:00"))
            last_date = datetime.fromisoformat(now.replace("Z", "+00:00"))
            days_diff = (last_date - first_date).days
            self.stats.days_active = max(self.stats.days_active, days_diff + 1)

        # Check for level progression
        old_level = self.progression.level
        self._update_level()
        new_level = self.progression.level

        # Check for feature unlocks
        unlocked_features = self._check_feature_unlocks()

        # Save state
        self._save_stats()
        self._save_progression()

        # Show progression messages
        if new_level != old_level:
            self._show_level_up_message(old_level, new_level)

        if unlocked_features:
            self._show_feature_unlock_message(unlocked_features)

    def _update_level(self) -> None:
        """Update user level based on total commands."""
        total = self.stats.total_commands

        if total >= self.INTERMEDIATE_TO_ADVANCED:
            new_level = UserLevel.ADVANCED
            commands_to_next = 0
        elif total >= self.BEGINNER_TO_INTERMEDIATE:
            new_level = UserLevel.INTERMEDIATE
            commands_to_next = self.INTERMEDIATE_TO_ADVANCED - total
        else:
            new_level = UserLevel.BEGINNER
            commands_to_next = self.BEGINNER_TO_INTERMEDIATE - total

        self.progression.level = new_level
        self.progression.commands_to_next_level = commands_to_next

    def _check_feature_unlocks(self) -> list[str]:
        """Check if any new features should be unlocked."""
        unlocked = []

        for feature, requirements in self.FEATURE_UNLOCKS.items():
            if feature in self.progression.features_unlocked:
                continue  # Already unlocked

            level_met = self.progression.level.value >= requirements["level"].value
            commands_met = self.stats.total_commands >= requirements["commands"]

            if level_met and commands_met:
                self.progression.features_unlocked.append(feature)
                unlocked.append(feature)

        return unlocked

    def _show_level_up_message(self, old_level: UserLevel, new_level: UserLevel) -> None:
        """Show a message when user levels up."""
        print("\n" + "=" * 70)
        print(f"🎉 Level Up! {old_level.value.title()} → {new_level.value.title()}")
        print("=" * 70)
        print(f"\nCongratulations! You've reached {new_level.value} level!")
        print(f"You've used Simple Mode {self.stats.total_commands} times.")
        print("\nNew features available:")
        self._list_unlocked_features(new_level)
        print()

    def _show_feature_unlock_message(self, features: list[str]) -> None:
        """Show a message when new features are unlocked."""
        print("\n" + "-" * 70)
        print("🔓 New Features Unlocked!")
        print("-" * 70)
        for feature in features:
            feature_name = feature.replace("_", " ").title()
            print(f"  ✓ {feature_name}")
        print("\n💡 Try these new features to explore more capabilities!")
        print("-" * 70)
        print()

    def _list_unlocked_features(self, level: UserLevel) -> None:
        """List features available at a given level."""
        if level == UserLevel.INTERMEDIATE:
            print("  • Agent-specific commands (e.g., @reviewer *review)")
            print("  • Advanced workflow presets")
            print("  • Custom quality thresholds")
        elif level == UserLevel.ADVANCED:
            print("  • All intermediate features")
            print("  • Custom orchestrators")
            print("  • Expert consultation system")
            print("  • Multi-agent parallel execution")

    def get_progression_summary(self) -> dict[str, Any]:
        """Get a summary of current progression."""
        return {
            "level": self.progression.level.value,
            "total_commands": self.stats.total_commands,
            "commands_to_next_level": self.progression.commands_to_next_level,
            "features_unlocked": len(self.progression.features_unlocked),
            "days_active": self.stats.days_active,
            "command_breakdown": {
                "build": self.stats.build_commands,
                "review": self.stats.review_commands,
                "fix": self.stats.fix_commands,
                "test": self.stats.test_commands,
            },
        }

    def show_progression_indicator(self) -> None:
        """Display a visual progression indicator."""
        level = self.progression.level
        total = self.stats.total_commands
        to_next = self.progression.commands_to_next_level

        print("\n" + "-" * 70)
        print("📊 Your Progress")
        print("-" * 70)
        print(f"Level: {level.value.title()}")
        print(f"Total commands: {total}")

        if to_next > 0:
            next_level = (
                UserLevel.INTERMEDIATE
                if level == UserLevel.BEGINNER
                else UserLevel.ADVANCED
            )
            print(f"Commands to {next_level.value.title()}: {to_next}")
        else:
            print("🎉 You've reached the highest level!")

        print(f"Days active: {self.stats.days_active}")
        print(f"Features unlocked: {len(self.progression.features_unlocked)}")
        print("-" * 70)
        print()

    def is_feature_unlocked(self, feature: str) -> bool:
        """Check if a feature is unlocked."""
        return feature in self.progression.features_unlocked

    def get_next_tip(self) -> str | None:
        """Get the next tip to show based on progression."""
        # Tips based on level and usage
        tips = {
            UserLevel.BEGINNER: [
                "💡 Try different commands: build, review, fix, test",
                "💡 Use natural language - Simple Mode understands many ways to express the same intent",
                "💡 Check your progress with: tapps-agents simple-mode progress",
            ],
            UserLevel.INTERMEDIATE: [
                "💡 Try agent-specific commands for more control: @reviewer *review",
                "💡 Explore advanced workflow presets for complex tasks",
                "💡 Customize quality thresholds in your config file",
            ],
            UserLevel.ADVANCED: [
                "💡 Create custom orchestrators for your specific workflows",
                "💡 Use expert consultation for domain-specific guidance",
                "💡 Leverage multi-agent parallel execution for faster results",
            ],
        }

        level_tips = tips.get(self.progression.level, [])
        if not level_tips:
            return None

        # Return a tip that hasn't been shown yet
        for tip in level_tips:
            if tip not in self.progression.tips_shown:
                self.progression.tips_shown.append(tip)
                self._save_progression()
                return tip

        # All tips shown, reset and start over
        self.progression.tips_shown = []
        if level_tips:
            tip = level_tips[0]
            self.progression.tips_shown.append(tip)
            self._save_progression()
            return tip

        return None

