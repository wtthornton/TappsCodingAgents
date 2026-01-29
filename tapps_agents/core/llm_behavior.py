"""
LLM Behavior Configuration

Manages configuration for LLM behavior patterns including workflow enforcement.
Part of ENH-001: Workflow Enforcement System.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = Path(".tapps-agents/config.yaml")


@dataclass
class EnforcementConfig:
    """
    Configuration for workflow enforcement system.

    Controls how the system enforces workflow usage when LLMs attempt
    direct code edits. Part of the ENH-001 Workflow Enforcement System.

    Attributes:
        mode: Enforcement mode:
            - "blocking": Block direct edits, require workflows
            - "warning": Show warning but allow edits
            - "silent": Log only, no user-facing messages
        confidence_threshold: Minimum confidence score (0-100) to trigger
            enforcement. Lower values = more aggressive enforcement.
        suggest_workflows: Whether to suggest specific workflows in messages
        block_direct_edits: Whether to actually block operations in
            blocking mode (vs just showing message)

    Example:
        >>> # Load from default config file
        >>> config = EnforcementConfig.from_config_file()
        >>> if config.mode == "blocking":
        ...     # Block the operation
        ...     pass

        >>> # Load from custom config file
        >>> config = EnforcementConfig.from_config_file(Path("custom.yaml"))

        >>> # Use defaults
        >>> config = EnforcementConfig()
        >>> assert config.mode == "blocking"
        >>> assert config.confidence_threshold == 60.0
    """

    mode: Literal["blocking", "warning", "silent"] = "blocking"
    confidence_threshold: float = 60.0
    suggest_workflows: bool = True
    block_direct_edits: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_mode(self.mode)
        self._validate_threshold(self.confidence_threshold)

    def _validate_mode(self, mode: str) -> None:
        """
        Validate enforcement mode.

        Args:
            mode: Mode string to validate

        Raises:
            ValueError: If mode is not one of the allowed values
        """
        valid_modes = ["blocking", "warning", "silent"]
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid enforcement mode: {mode}. "
                f"Must be one of {valid_modes}"
            )

    def _validate_threshold(self, threshold: float) -> None:
        """
        Validate confidence threshold.

        Args:
            threshold: Threshold value to validate

        Raises:
            TypeError: If threshold is not a number
            ValueError: If threshold is out of range [0, 100]
        """
        if not isinstance(threshold, (int, float)):
            raise TypeError(
                f"confidence_threshold must be a number, got {type(threshold).__name__}"
            )
        if not 0 <= threshold <= 100:
            raise ValueError(
                f"confidence_threshold must be in range [0, 100], got {threshold}"
            )

    @classmethod
    def from_config_file(
        cls,
        config_path: Path | None = None
    ) -> EnforcementConfig:
        """
        Load configuration from YAML file.

        Loads workflow enforcement configuration from the project's config file
        at `.tapps-agents/config.yaml` (or a custom path). The configuration
        should be under the `llm_behavior.workflow_enforcement` section.

        If the config file or sections are missing, returns an instance with
        default values. This allows the system to work out-of-the-box without
        requiring explicit configuration.

        Args:
            config_path: Path to config file. If None, uses default path
                (.tapps-agents/config.yaml in current directory)

        Returns:
            EnforcementConfig instance loaded from file or with defaults

        Raises:
            ValueError: If YAML is invalid or config values fail validation

        Example:
            >>> # Load from default location
            >>> config = EnforcementConfig.from_config_file()

            >>> # Load from custom location
            >>> config = EnforcementConfig.from_config_file(Path("custom.yaml"))

            >>> # Missing file returns defaults
            >>> config = EnforcementConfig.from_config_file(Path("nonexistent.yaml"))
            >>> assert config.mode == "blocking"  # Default value

        YAML Configuration Format:
            llm_behavior:
              mode: "senior-developer"

              workflow_enforcement:
                mode: "blocking"           # "blocking" | "warning" | "silent"
                confidence_threshold: 60   # 0-100
                suggest_workflows: true
                block_direct_edits: true
        """
        config_path = config_path or DEFAULT_CONFIG_PATH

        # Return defaults if file doesn't exist
        if not config_path.exists():
            logger.debug(
                "Config file not found at %s. Using default enforcement config.",
                config_path
            )
            return cls()

        # Load and parse YAML
        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML in config file: {e}"
            ) from e
        except OSError as e:
            logger.warning(
                "Failed to read config file, using defaults: %s",
                e
            )
            return cls()

        # Handle empty file
        if not config_data:
            logger.debug("Config file is empty. Using default enforcement config.")
            return cls()

        # Navigate to workflow_enforcement section
        if "llm_behavior" not in config_data:
            logger.debug(
                "No 'llm_behavior' section in config. Using default enforcement config."
            )
            return cls()

        llm_behavior = config_data["llm_behavior"]
        if not isinstance(llm_behavior, dict):
            logger.debug(
                "'llm_behavior' is not a dict. Using default enforcement config."
            )
            return cls()

        if "workflow_enforcement" not in llm_behavior:
            logger.debug(
                "No 'workflow_enforcement' section in config. Using default enforcement config."
            )
            return cls()

        enforcement_config = llm_behavior["workflow_enforcement"]
        if not isinstance(enforcement_config, dict):
            logger.debug(
                "'workflow_enforcement' is not a dict. Using default enforcement config."
            )
            return cls()

        # Extract and validate fields
        mode = enforcement_config.get("mode", "blocking")
        threshold = enforcement_config.get("confidence_threshold", 60.0)
        suggest = enforcement_config.get("suggest_workflows", True)
        block = enforcement_config.get("block_direct_edits", True)

        # Type conversions with error handling
        try:
            mode_str = str(mode)
            threshold_float = float(threshold)
            suggest_bool = bool(suggest)
            block_bool = bool(block)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid config value type: {e}"
            ) from e

        # Create instance (validation happens in __post_init__)
        return cls(
            mode=mode_str,
            confidence_threshold=threshold_float,
            suggest_workflows=suggest_bool,
            block_direct_edits=block_bool
        )
