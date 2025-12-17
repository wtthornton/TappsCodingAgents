"""
Customization loader for agent customizations.

Loads and merges customization files with base agent configurations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .customization_schema import (
    validate_customization_file,
    validate_referenced_files,
)

logger = logging.getLogger(__name__)


def load_customization(
    agent_id: str, project_root: Path | None = None
) -> dict[str, Any] | None:
    """
    Load customization file for an agent.

    Args:
        agent_id: Agent identifier (e.g., "dev", "implementer")
        project_root: Project root directory (defaults to cwd)

    Returns:
        Parsed customization data or None if not found/invalid
    """
    if project_root is None:
        project_root = Path.cwd()

    # Check for customization file
    custom_path = (
        project_root
        / ".tapps-agents"
        / "customizations"
        / f"{agent_id}-custom.yaml"
    )

    if not custom_path.exists():
        return None

    # Validate and load
    is_valid, errors = validate_customization_file(custom_path, agent_id)
    if not is_valid:
        logger.warning(
            f"Customization file validation failed for {agent_id}: {', '.join(errors)}"
        )
        return None

    try:
        with open(custom_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Error loading customization file {custom_path}: {e}")
        return None

    # Check for referenced files (warnings only)
    warnings = validate_referenced_files(data, project_root)
    for warning in warnings:
        logger.warning(f"Customization file {custom_path}: {warning}")

    return data


def merge_persona_overrides(
    base_persona: dict[str, Any], customizations: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Merge persona overrides with base persona.

    Args:
        base_persona: Base agent persona configuration
        customizations: Customization data (may be None)

    Returns:
        Merged persona configuration
    """
    if customizations is None or "persona_overrides" not in customizations:
        return base_persona.copy()

    overrides = customizations["persona_overrides"]
    merged = base_persona.copy()

    # Merge additional_principles (append)
    if "additional_principles" in overrides:
        if "additional_principles" not in merged:
            merged["additional_principles"] = []
        merged["additional_principles"].extend(overrides["additional_principles"])

    # Merge communication_style (override)
    if "communication_style" in overrides:
        if "communication_style" not in merged:
            merged["communication_style"] = {}
        merged["communication_style"].update(overrides["communication_style"])

    # Merge expertise_areas
    if "expertise_areas" in overrides:
        if "expertise_areas" not in merged:
            merged["expertise_areas"] = {"add": [], "emphasize": []}
        if "add" in overrides["expertise_areas"]:
            merged["expertise_areas"].setdefault("add", []).extend(
                overrides["expertise_areas"]["add"]
            )
        if "emphasize" in overrides["expertise_areas"]:
            merged["expertise_areas"].setdefault("emphasize", []).extend(
                overrides["expertise_areas"]["emphasize"]
            )

    # Merge custom_instructions (append)
    if "custom_instructions" in overrides:
        base_instructions = merged.get("custom_instructions", "")
        custom_instructions = overrides["custom_instructions"]
        if base_instructions:
            merged["custom_instructions"] = f"{base_instructions}\n\n{custom_instructions}"
        else:
            merged["custom_instructions"] = custom_instructions

    return merged


def merge_command_overrides(
    base_commands: list[dict[str, str]], customizations: dict[str, Any] | None
) -> list[dict[str, str]]:
    """
    Merge command overrides with base commands.

    Args:
        base_commands: Base agent commands
        customizations: Customization data (may be None)

    Returns:
        Merged commands list
    """
    if customizations is None or "command_overrides" not in customizations:
        return base_commands.copy()

    overrides = customizations["command_overrides"]
    merged = base_commands.copy()

    # Add new commands
    if "add" in overrides:
        merged.extend(overrides["add"])

    # Modify existing commands
    if "modify" in overrides:
        command_map = {cmd.get("name", ""): i for i, cmd in enumerate(merged)}
        for mod in overrides["modify"]:
            cmd_name = mod.get("name", "")
            if cmd_name in command_map:
                # Update existing command
                idx = command_map[cmd_name]
                merged[idx].update(mod)
            else:
                # Command not found, log warning
                logger.warning(f"Command '{cmd_name}' not found for modification")

    return merged


def merge_dependency_overrides(
    base_dependencies: dict[str, list[str]], customizations: dict[str, Any] | None
) -> dict[str, list[str]]:
    """
    Merge dependency overrides with base dependencies.

    Args:
        base_dependencies: Base agent dependencies (e.g., {"tasks": [...], "templates": [...]})
        customizations: Customization data (may be None)

    Returns:
        Merged dependencies dictionary
    """
    if customizations is None or "dependency_overrides" not in customizations:
        return base_dependencies.copy()

    overrides = customizations["dependency_overrides"]
    merged = base_dependencies.copy()

    # Merge each dependency type
    for dep_type in ["tasks", "templates", "data"]:
        if dep_type in overrides and "add" in overrides[dep_type]:
            if dep_type not in merged:
                merged[dep_type] = []
            merged[dep_type].extend(overrides[dep_type]["add"])

    return merged


def merge_project_context(
    base_context: dict[str, Any] | None, customizations: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Merge project context overrides.

    Args:
        base_context: Base project context (may be None)
        customizations: Customization data (may be None)

    Returns:
        Merged project context
    """
    merged = (base_context or {}).copy()

    if customizations is None or "project_context" not in customizations:
        return merged

    overrides = customizations["project_context"]

    # Merge always_load (append)
    if "always_load" in overrides:
        if "always_load" not in merged:
            merged["always_load"] = []
        merged["always_load"].extend(overrides["always_load"])

    # Merge preferences (override)
    if "preferences" in overrides:
        if "preferences" not in merged:
            merged["preferences"] = {}
        merged["preferences"].update(overrides["preferences"])

    return merged


def apply_customizations(
    base_config: dict[str, Any],
    customizations: dict[str, Any] | None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """
    Apply customizations to base agent configuration.

    This is the main entry point for merging customizations with base config.

    Args:
        base_config: Base agent configuration
        customizations: Customization data (may be None)
        project_root: Project root directory (for file validation)

    Returns:
        Merged configuration
    """
    if customizations is None:
        return base_config.copy()

    merged = base_config.copy()

    # Merge persona
    if "persona" in base_config:
        merged["persona"] = merge_persona_overrides(
            base_config["persona"], customizations
        )

    # Merge commands
    if "commands" in base_config:
        merged["commands"] = merge_command_overrides(
            base_config["commands"], customizations
        )

    # Merge dependencies
    if "dependencies" in base_config:
        merged["dependencies"] = merge_dependency_overrides(
            base_config["dependencies"], customizations
        )

    # Merge project context
    if "project_context" in base_config or "project_context" in customizations:
        merged["project_context"] = merge_project_context(
            base_config.get("project_context"), customizations
        )

    return merged

