"""
Background Agent Configuration Management.

Provides configuration validation, generation, and management for Background Agent
auto-execution setup.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class BackgroundAgentConfigError(Exception):
    """Error in Background Agent configuration."""

    pass


class BackgroundAgentConfigValidator:
    """Validates Background Agent configuration files."""

    REQUIRED_AGENT_FIELDS = ["name", "type", "commands"]
    REQUIRED_TYPE_VALUE = "background"
    OPTIONAL_AGENT_FIELDS = [
        "description",
        "context7_cache",
        "environment",
        "triggers",
        "watch_paths",
        "timeout_seconds",
        "retry_count",
        "enabled",
        "working_directory",
        "output",
    ]

    def __init__(self, config_path: Path | None = None):
        """
        Initialize validator.

        Args:
            config_path: Path to configuration file (defaults to .cursor/background-agents.yaml)
        """
        if config_path is None:
            config_path = Path.cwd() / ".cursor" / "background-agents.yaml"
        self.config_path = config_path

    def validate_file_exists(self) -> tuple[bool, str]:
        """
        Check if configuration file exists.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.config_path.exists():
            return False, f"Configuration file not found: {self.config_path}"
        return True, ""

    def validate_file_permissions(self) -> tuple[bool, str]:
        """
        Check if configuration file is readable.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.config_path.exists():
            return False, f"Configuration file not found: {self.config_path}"

        if not self.config_path.is_file():
            return False, f"Configuration path is not a file: {self.config_path}"

        try:
            with open(self.config_path, encoding="utf-8") as f:
                f.read(1)  # Try to read at least one byte
        except PermissionError:
            return False, f"Permission denied reading configuration file: {self.config_path}"
        except Exception as e:
            return False, f"Error reading configuration file: {e}"

        return True, ""

    def validate_yaml_syntax(self) -> tuple[bool, str, dict[str, Any] | None]:
        """
        Validate YAML syntax and parse configuration.

        Returns:
            Tuple of (is_valid, error_message, parsed_config)
        """
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return True, "", config
        except yaml.YAMLError as e:
            return False, f"Invalid YAML syntax: {e}", None
        except Exception as e:
            return False, f"Error parsing YAML: {e}", None

    def validate_schema(
        self, config: dict[str, Any] | None = None, warn_about_watch_paths: bool = True
    ) -> tuple[bool, list[str], list[str]]:
        """
        Validate configuration schema.

        Args:
            config: Parsed configuration (if None, loads from file)
            warn_about_watch_paths: If True, warn that watch_paths are no longer needed (Phase 2)

        Returns:
            Tuple of (is_valid, list_of_errors, list_of_warnings)
        """
        errors: list[str] = []
        warnings: list[str] = []

        if config is None:
            is_valid, error_msg, config = self.validate_yaml_syntax()
            if not is_valid:
                return False, [error_msg]

        if not isinstance(config, dict):
            return False, ["Configuration must be a YAML object/dictionary"]

        # Validate agents list
        if "agents" not in config:
            errors.append("Missing required top-level field: 'agents'")
            return False, errors

        agents = config["agents"]
        if not isinstance(agents, list):
            errors.append("Field 'agents' must be a list")
            return False, errors

        if len(agents) == 0:
            errors.append("Field 'agents' must contain at least one agent")
            return False, errors

        # Validate each agent
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                errors.append(f"Agent {i+1}: Must be a YAML object/dictionary")
                continue

            # Check required fields
            for field in self.REQUIRED_AGENT_FIELDS:
                if field not in agent:
                    errors.append(f"Agent {i+1}: Missing required field: '{field}'")

            # Validate type field
            if "type" in agent and agent["type"] != self.REQUIRED_TYPE_VALUE:
                errors.append(
                    f"Agent {i+1}: Field 'type' must be '{self.REQUIRED_TYPE_VALUE}' (got: {agent['type']})"
                )

            # Phase 2: watch_paths are no longer required (direct execution fallback)
            # Validate that agent has either triggers (natural language) or watch_paths (legacy auto-execution)
            has_triggers = "triggers" in agent and agent.get("triggers")
            has_watch_paths = "watch_paths" in agent and agent.get("watch_paths")
            
            # Phase 2: watch_paths are optional (direct execution is used as fallback)
            # Only require triggers or watch_paths if neither is present (for backward compatibility)
            if not has_triggers and not has_watch_paths:
                # This is now a warning, not an error (Phase 2: direct execution fallback)
                warnings.append(
                    f"Agent {i+1} ({agent.get('name', 'Unknown')}): No 'triggers' or 'watch_paths' specified. "
                    "Direct execution fallback will be used when API is unavailable. "
                    "Consider adding 'triggers' for natural language prompts if needed."
                )
            
            # Phase 2: Warn that watch_paths are no longer needed
            if warn_about_watch_paths and has_watch_paths:
                warnings.append(
                    f"Agent {i+1} ({agent.get('name', 'Unknown')}): 'watch_paths' is configured but no longer required. "
                    "Direct execution fallback is used automatically when Background Agent API is unavailable. "
                    "You can remove 'watch_paths' to simplify configuration."
                )

            # Validate commands field
            if "commands" in agent:
                if not isinstance(agent["commands"], list):
                    errors.append(f"Agent {i+1}: Field 'commands' must be a list")
                elif len(agent["commands"]) == 0:
                    errors.append(f"Agent {i+1}: Field 'commands' must contain at least one command")

            # Validate watch_paths field
            if "watch_paths" in agent:
                if not isinstance(agent["watch_paths"], list):
                    errors.append(f"Agent {i+1}: Field 'watch_paths' must be a list")
                elif len(agent["watch_paths"]) == 0:
                    errors.append(
                        f"Agent {i+1}: Field 'watch_paths' must contain at least one path"
                    )

            # Validate optional fields
            if "timeout_seconds" in agent:
                if not isinstance(agent["timeout_seconds"], int) or agent["timeout_seconds"] <= 0:
                    errors.append(
                        f"Agent {i+1}: Field 'timeout_seconds' must be a positive integer"
                    )

            if "retry_count" in agent:
                if not isinstance(agent["retry_count"], int) or agent["retry_count"] < 0:
                    errors.append(
                        f"Agent {i+1}: Field 'retry_count' must be a non-negative integer"
                    )

            if "enabled" in agent:
                if not isinstance(agent["enabled"], bool):
                    errors.append(f"Agent {i+1}: Field 'enabled' must be a boolean")

        # Validate global config (optional)
        if "global" in config:
            global_config = config["global"]
            if not isinstance(global_config, dict):
                errors.append("Field 'global' must be a YAML object/dictionary")

        return len(errors) == 0, errors, warnings

    def validate(self, warn_about_watch_paths: bool = True) -> tuple[bool, list[str], list[str]]:
        """
        Perform complete validation.

        Args:
            warn_about_watch_paths: If True, warn that watch_paths are no longer needed (Phase 2)

        Returns:
            Tuple of (is_valid, list_of_errors, list_of_warnings)
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check file exists
        is_valid, error_msg = self.validate_file_exists()
        if not is_valid:
            return False, [error_msg], []

        # Check permissions
        is_valid, error_msg = self.validate_file_permissions()
        if not is_valid:
            return False, [error_msg], []

        # Validate YAML syntax
        is_valid, error_msg, config = self.validate_yaml_syntax()
        if not is_valid:
            return False, [error_msg], []

        # Validate schema
        is_valid, schema_errors, schema_warnings = self.validate_schema(
            config, warn_about_watch_paths=warn_about_watch_paths
        )
        if not is_valid:
            errors.extend(schema_errors)
        warnings.extend(schema_warnings)

        return len(errors) == 0, errors, warnings


class BackgroundAgentConfigGenerator:
    """Generates Background Agent configuration files."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize generator.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.config_path = project_root / ".cursor" / "background-agents.yaml"

    def generate_from_template(
        self, template_path: Path | None = None, overwrite: bool = False
    ) -> dict[str, Any]:
        """
        Generate configuration from template.

        Args:
            template_path: Path to template file (defaults to framework template)
            overwrite: Whether to overwrite existing configuration

        Returns:
            Dictionary with success status and file path
        """
        if self.config_path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"Configuration file already exists: {self.config_path}\nUse --overwrite to replace it.",
                "file_path": str(self.config_path),
            }

        # Load template
        if template_path is None:
            # Try to find framework template
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            template_path = framework_root / "templates" / "background_agents" / "auto-execution-template.yaml"

        if not template_path.exists():
            return {
                "success": False,
                "error": f"Template file not found: {template_path}",
                "file_path": str(self.config_path),
            }

        try:
            # Read template
            template_content = template_path.read_text(encoding="utf-8")

            # Create .cursor directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write configuration file
            self.config_path.write_text(template_content, encoding="utf-8")

            return {
                "success": True,
                "file_path": str(self.config_path),
                "template_path": str(template_path),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate configuration: {e}",
                "file_path": str(self.config_path),
            }

    def generate_minimal_config(self, overwrite: bool = False) -> dict[str, Any]:
        """
        Generate minimal configuration with sensible defaults.

        Args:
            overwrite: Whether to overwrite existing configuration

        Returns:
            Dictionary with success status and file path
        """
        if self.config_path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"Configuration file already exists: {self.config_path}\nUse --overwrite to replace it.",
                "file_path": str(self.config_path),
            }

        # Minimal valid configuration
        config = {
            "agents": [
                {
                    "name": "TappsCodingAgents Workflow Executor",
                    "type": "background",
                    "description": "Automatically execute workflow commands from .cursor-skill-command.txt files",
                    "commands": ["python -m tapps_agents.cli cursor-invoke \"{command}\""],
                    "watch_paths": ["**/.cursor-skill-command.txt"],
                    "enabled": True,
                    "timeout_seconds": 3600,
                }
            ],
            "global": {
                "context7_cache": ".tapps-agents/kb/context7-cache",
                "output_directory": ".tapps-agents/reports",
                "timeout_seconds": 3600,
            },
        }

        try:
            # Create .cursor directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write configuration file
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            return {
                "success": True,
                "file_path": str(self.config_path),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate configuration: {e}",
                "file_path": str(self.config_path),
            }

