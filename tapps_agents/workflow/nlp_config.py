"""
Configuration Management for Natural Language Parser

Manages parser configuration, aliases, and learning system.
Epic 9 / Story 9.7: Configuration Management and Learning
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class NLPConfig:
    """Configuration for natural language parser."""

    def __init__(self, config_path: Path | None = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file (defaults to .cursor/nl-workflow-config.yaml)
        """
        if config_path is None:
            project_root = Path.cwd()
            config_path = project_root / ".cursor" / "nl-workflow-config.yaml"

        self.config_path = Path(config_path)
        self.config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file or create defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                return self._default_config()
        else:
            return self._default_config()

    def _default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "parser": {
                "confidence_threshold": 0.7,
                "ambiguity_threshold": 0.1,
                "auto_select_threshold": 0.2,
            },
            "aliases": {},  # Custom aliases (extends PRESET_ALIASES)
            "learning": {
                "enabled": True,
                "correction_history_file": ".cursor/nl-learning-history.json",
                "min_corrections_for_learning": 5,
            },
        }

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_confidence_threshold(self) -> float:
        """Get confidence threshold."""
        return self.config.get("parser", {}).get("confidence_threshold", 0.7)

    def get_ambiguity_threshold(self) -> float:
        """Get ambiguity threshold."""
        return self.config.get("parser", {}).get("ambiguity_threshold", 0.1)

    def get_custom_aliases(self) -> dict[str, str]:
        """Get custom aliases."""
        return self.config.get("aliases", {})

    def add_alias(self, alias: str, workflow_name: str) -> bool:
        """
        Add custom alias.

        Args:
            alias: Alias name
            workflow_name: Workflow name to map to

        Returns:
            True if added successfully
        """
        if "aliases" not in self.config:
            self.config["aliases"] = {}

        self.config["aliases"][alias] = workflow_name
        self.save()
        return True

    def remove_alias(self, alias: str) -> bool:
        """
        Remove custom alias.

        Args:
            alias: Alias to remove

        Returns:
            True if removed successfully
        """
        if "aliases" in self.config and alias in self.config["aliases"]:
            del self.config["aliases"][alias]
            self.save()
            return True
        return False

    def is_learning_enabled(self) -> bool:
        """Check if learning is enabled."""
        return self.config.get("learning", {}).get("enabled", True)

    def get_learning_history_path(self) -> Path:
        """Get path to learning history file."""
        history_file = self.config.get("learning", {}).get("correction_history_file", ".cursor/nl-learning-history.json")
        return Path(history_file)


class LearningSystem:
    """Learning system for improving parser accuracy."""

    def __init__(self, config: NLPConfig):
        """
        Initialize learning system.

        Args:
            config: NLPConfig instance
        """
        self.config = config
        self.history_path = config.get_learning_history_path()
        self.corrections: list[dict[str, Any]] = self._load_history()

    def _load_history(self) -> list[dict[str, Any]]:
        """Load correction history."""
        if not self.history_path.exists():
            return []

        try:
            with open(self.history_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load learning history: {e}")
            return []

    def _save_history(self) -> None:
        """Save correction history."""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.corrections, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning history: {e}")

    def record_correction(self, user_input: str, suggested_workflow: str, actual_workflow: str) -> None:
        """
        Record user correction.

        Args:
            user_input: Original user input
            suggested_workflow: Workflow that was suggested
            actual_workflow: Workflow that user actually selected
        """
        if not self.config.is_learning_enabled():
            return

        correction = {
            "user_input": user_input,
            "suggested_workflow": suggested_workflow,
            "actual_workflow": actual_workflow,
            "timestamp": str(Path().cwd()),  # Simple timestamp
        }

        self.corrections.append(correction)
        self._save_history()

        # Check if we have enough corrections to learn
        min_corrections = self.config.config.get("learning", {}).get("min_corrections_for_learning", 5)
        if len(self.corrections) >= min_corrections:
            self._learn_from_corrections()

    def _learn_from_corrections(self) -> None:
        """Learn from correction history (simplified implementation)."""
        # In a full implementation, this would:
        # - Analyze correction patterns
        # - Update confidence weights
        # - Learn alias preferences
        # - Improve matching accuracy
        logger.info(f"Learning from {len(self.corrections)} corrections")

