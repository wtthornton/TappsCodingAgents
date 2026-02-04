"""
Zero-Config Mode for Simple Mode.

Provides smart defaults with auto-detection and a configuration wizard
for customization. This allows Simple Mode to work out-of-the-box with
minimal or no configuration.
"""

import sys
from pathlib import Path
from typing import Any

from ..cli.feedback import get_feedback
from ..core.config import ProjectConfig, load_config, save_config
from ..core.project_type_detector import detect_project_type


class ZeroConfigMode:
    """Manages zero-config mode with smart defaults and auto-detection."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.feedback = get_feedback()
        self.config_path = self._find_config_file()

    def _find_config_file(self) -> Path:
        """Find or create config file path."""
        current = self.project_root
        for parent in [current] + list(current.parents):
            candidate = parent / ".tapps-agents" / "config.yaml"
            if candidate.exists():
                return candidate
        # Return default path
        return self.project_root / ".tapps-agents" / "config.yaml"

    def auto_configure(self) -> ProjectConfig:
        """
        Automatically configure Simple Mode with smart defaults based on project detection.

        Returns:
            Configured ProjectConfig instance
        """
        self.feedback.info("Auto-configuring Simple Mode with smart defaults...")

        # Load existing config or create new one
        if self.config_path.exists():
            config = load_config(self.config_path)
        else:
            config = ProjectConfig()

        # Detect project type
        project_type, confidence, reason = detect_project_type(self.project_root)
        
        # Apply smart defaults based on project type
        self._apply_smart_defaults(config, project_type, confidence)

        # Save configuration
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        save_config(self.config_path, config)

        self.feedback.success(f"Simple Mode auto-configured (saved to {self.config_path})")
        return config

    def _apply_smart_defaults(
        self, config: ProjectConfig, project_type: str | None, confidence: float
    ) -> None:
        """Apply smart defaults based on project type."""
        # Enable Simple Mode with sensible defaults
        config.simple_mode.enabled = True
        config.simple_mode.auto_detect = True
        config.simple_mode.natural_language = True
        config.simple_mode.show_advanced = False

        # Project-type specific defaults
        if project_type == "api-service":
            # API services: focus on security and documentation (all 7 weights must sum to 1.0)
            config.agents.reviewer.include_scoring = True
            config.agents.reviewer.quality_threshold = 75.0
            config.scoring.quality_threshold = 75.0
            config.scoring.weights.security = 0.32
            config.scoring.weights.maintainability = 0.22
            config.scoring.weights.test_coverage = 0.18
            config.scoring.weights.complexity = 0.14
            config.scoring.weights.performance = 0.04
            config.scoring.weights.structure = 0.05
            config.scoring.weights.devex = 0.05

        elif project_type == "web-app":
            # Web apps: balance performance and maintainability (all 7 weights must sum to 1.0)
            config.agents.reviewer.include_scoring = True
            config.agents.reviewer.quality_threshold = 70.0
            config.scoring.quality_threshold = 70.0
            config.scoring.weights.maintainability = 0.27
            config.scoring.weights.performance = 0.23
            config.scoring.weights.security = 0.18
            config.scoring.weights.test_coverage = 0.14
            config.scoring.weights.complexity = 0.08
            config.scoring.weights.structure = 0.05
            config.scoring.weights.devex = 0.05

        elif project_type == "cli-tool":
            # CLI tools: focus on usability and error handling (all 7 weights must sum to 1.0)
            config.agents.reviewer.include_scoring = True
            config.agents.reviewer.quality_threshold = 70.0
            config.scoring.quality_threshold = 70.0
            config.scoring.weights.maintainability = 0.27
            config.scoring.weights.complexity = 0.23
            config.scoring.weights.test_coverage = 0.22
            config.scoring.weights.security = 0.13
            config.scoring.weights.performance = 0.05
            config.scoring.weights.structure = 0.05
            config.scoring.weights.devex = 0.05

        elif project_type == "library":
            # Libraries: focus on API design and test coverage (all 7 weights must sum to 1.0)
            config.agents.reviewer.include_scoring = True
            config.agents.reviewer.quality_threshold = 75.0
            config.scoring.quality_threshold = 75.0
            config.scoring.weights.test_coverage = 0.27
            config.scoring.weights.maintainability = 0.23
            config.scoring.weights.complexity = 0.18
            config.scoring.weights.security = 0.14
            config.scoring.weights.performance = 0.08
            config.scoring.weights.structure = 0.05
            config.scoring.weights.devex = 0.05

        else:
            # Generic defaults for unknown project types
            config.agents.reviewer.include_scoring = True
            config.agents.reviewer.quality_threshold = 70.0
            config.scoring.quality_threshold = 70.0

        # Store detected project type for reference
        if project_type:
            if not hasattr(config, "project_metadata"):
                # Store in a way that doesn't break existing config structure
                pass  # Could add metadata field if needed

    def run_configuration_wizard(self) -> ProjectConfig:
        """
        Run an interactive configuration wizard for customizing Simple Mode.

        Returns:
            Configured ProjectConfig instance
        """
        self.feedback.start_operation("Simple Mode Configuration Wizard")

        # Load existing config or create new one
        if self.config_path.exists():
            config = load_config(self.config_path)
        else:
            config = ProjectConfig()

        try:
            print("\n" + "=" * 70)
            print(" " * 15 + "Simple Mode Configuration Wizard")
            print("=" * 70)
            print("\nThis wizard will help you customize Simple Mode settings.")
            print("Press Enter to accept defaults or type your choice.\n")

            # Basic settings
            print("1. Basic Settings")
            print("-" * 70)
            
            enabled = self._ask_yes_no("Enable Simple Mode?", config.simple_mode.enabled)
            config.simple_mode.enabled = enabled

            if enabled:
                natural_language = self._ask_yes_no(
                    "Enable natural language commands?", config.simple_mode.natural_language
                )
                config.simple_mode.natural_language = natural_language

                auto_detect = self._ask_yes_no(
                    "Auto-detect project type?", config.simple_mode.auto_detect
                )
                config.simple_mode.auto_detect = auto_detect

                show_advanced = self._ask_yes_no(
                    "Show advanced options?", config.simple_mode.show_advanced
                )
                config.simple_mode.show_advanced = show_advanced

            # Quality thresholds
            print("\n2. Quality Settings")
            print("-" * 70)
            
            quality_threshold = self._ask_float(
                "Minimum quality score (0-100):",
                config.scoring.quality_threshold,
                min_value=0.0,
                max_value=100.0,
            )
            config.scoring.quality_threshold = quality_threshold
            config.agents.reviewer.quality_threshold = quality_threshold

            # Save configuration
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            save_config(self.config_path, config)

            self.feedback.success("Configuration saved successfully!")
            print(f"\n✓ Configuration saved to: {self.config_path}")
            print("\nYou can run this wizard again anytime with:")
            print("  tapps-agents simple-mode configure")

            return config

        except KeyboardInterrupt:
            self.feedback.warning("\n\nConfiguration cancelled by user.")
            sys.exit(0)
        except Exception as e:
            self.feedback.error(
                f"Configuration failed: {e}",
                error_code="config_wizard_error",
                exit_code=1,
            )
            raise

    def _ask_yes_no(self, question: str, default: bool) -> bool:
        """Ask a yes/no question with a default value."""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{question} [{default_str}]: ").strip().lower()

        if not response:
            return default
        return response in ("y", "yes", "true", "1")

    def _ask_float(
        self, question: str, default: float, min_value: float, max_value: float
    ) -> float:
        """Ask for a float value with validation."""
        while True:
            response = input(f"{question} [{default}]: ").strip()
            if not response:
                return default

            try:
                value = float(response)
                if min_value <= value <= max_value:
                    return value
                else:
                    print(f"Value must be between {min_value} and {max_value}")
            except ValueError:
                print("Please enter a valid number")

    def get_smart_defaults(self, project_type: str | None = None) -> dict[str, Any]:
        """
        Get smart defaults for a given project type.

        Args:
            project_type: Optional project type (will be detected if not provided)

        Returns:
            Dictionary of default configuration values
        """
        if not project_type:
            project_type, _, _ = detect_project_type(self.project_root)

        defaults = {
            "enabled": True,
            "auto_detect": True,
            "natural_language": True,
            "show_advanced": False,
        }

        # Add project-type specific defaults
        if project_type:
            defaults["project_type"] = project_type
            defaults["detected"] = True
        else:
            defaults["detected"] = False

        return defaults

