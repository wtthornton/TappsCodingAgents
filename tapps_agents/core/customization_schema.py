"""
Customization file schema validation and structure definitions.

Validates YAML customization files for agent customizations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Schema structure for customization files
CUSTOMIZATION_SCHEMA = {
    "agent_id": str,
    "persona_overrides": {
        "additional_principles": list[str],
        "communication_style": {
            "tone": str,  # "professional" | "casual" | "friendly" | "technical"
            "formality": str,  # "formal" | "informal"
            "verbosity": str,  # "concise" | "detailed" | "balanced"
        },
        "expertise_areas": {
            "add": list[str],
            "emphasize": list[str],
        },
        "custom_instructions": str,
    },
    "command_overrides": {
        "add": list[dict[str, str]],  # [{"name": str, "description": str, "handler": str}]
        "modify": list[dict[str, str]],  # [{"name": str, "description": str}]
    },
    "dependency_overrides": {
        "tasks": {"add": list[str]},
        "templates": {"add": list[str]},
        "data": {"add": list[str]},
    },
    "project_context": {
        "always_load": list[str],
        "preferences": dict[str, Any],
    },
}


class CustomizationValidationError(Exception):
    """Raised when customization file validation fails."""

    pass


def validate_customization_file(
    file_path: Path, agent_id: str | None = None
) -> tuple[bool, list[str]]:
    """
    Validate a customization YAML file.

    Args:
        file_path: Path to the customization file
        agent_id: Expected agent_id (if None, extracted from filename)

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: list[str] = []

    # Check file exists
    if not file_path.exists():
        errors.append(f"Customization file not found: {file_path}")
        return False, errors

    # Extract agent_id from filename if not provided
    if agent_id is None:
        filename = file_path.stem  # e.g., "dev-custom" from "dev-custom.yaml"
        if "-custom" in filename:
            agent_id = filename.replace("-custom", "")
        else:
            errors.append(
                f"Filename '{file_path.name}' does not match pattern '{{agent-id}}-custom.yaml'"
            )
            return False, errors

    # Load and parse YAML
    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
        return False, errors
    except OSError as e:
        errors.append(f"Error reading file: {e}")
        return False, errors

    if not isinstance(data, dict):
        errors.append("Customization file must contain a YAML dictionary")
        return False, errors

    # Validate agent_id matches filename
    if "agent_id" not in data:
        errors.append("Missing required field: agent_id")
    elif data["agent_id"] != agent_id:
        errors.append(
            f"agent_id '{data['agent_id']}' does not match filename (expected '{agent_id}')"
        )

    # Validate structure (basic checks)
    _validate_structure(data, errors, agent_id)

    # Check for unknown keys
    known_keys = {
        "agent_id",
        "persona_overrides",
        "command_overrides",
        "dependency_overrides",
        "project_context",
    }
    unknown_keys = set(data.keys()) - known_keys
    if unknown_keys:
        errors.append(
            f"Unknown customization keys (will be ignored): {', '.join(sorted(unknown_keys))}"
        )

    return len(errors) == 0, errors


def _validate_structure(data: dict[str, Any], errors: list[str], agent_id: str) -> None:
    """Validate the structure of customization data."""
    # Validate persona_overrides
    if "persona_overrides" in data:
        persona = data["persona_overrides"]
        if not isinstance(persona, dict):
            errors.append("persona_overrides must be a dictionary")
        else:
            if "additional_principles" in persona:
                if not isinstance(persona["additional_principles"], list):
                    errors.append("persona_overrides.additional_principles must be a list")
            if "communication_style" in persona:
                if not isinstance(persona["communication_style"], dict):
                    errors.append("persona_overrides.communication_style must be a dictionary")
            if "expertise_areas" in persona:
                if not isinstance(persona["expertise_areas"], dict):
                    errors.append("persona_overrides.expertise_areas must be a dictionary")
                else:
                    if "add" in persona["expertise_areas"]:
                        if not isinstance(persona["expertise_areas"]["add"], list):
                            errors.append(
                                "persona_overrides.expertise_areas.add must be a list"
                            )
                    if "emphasize" in persona["expertise_areas"]:
                        if not isinstance(persona["expertise_areas"]["emphasize"], list):
                            errors.append(
                                "persona_overrides.expertise_areas.emphasize must be a list"
                            )

    # Validate command_overrides
    if "command_overrides" in data:
        commands = data["command_overrides"]
        if not isinstance(commands, dict):
            errors.append("command_overrides must be a dictionary")
        else:
            if "add" in commands:
                if not isinstance(commands["add"], list):
                    errors.append("command_overrides.add must be a list")
                else:
                    for i, cmd in enumerate(commands["add"]):
                        if not isinstance(cmd, dict):
                            errors.append(
                                f"command_overrides.add[{i}] must be a dictionary"
                            )
                        elif "name" not in cmd:
                            errors.append(
                                f"command_overrides.add[{i}] missing required field 'name'"
                            )
            if "modify" in commands:
                if not isinstance(commands["modify"], list):
                    errors.append("command_overrides.modify must be a list")
                else:
                    for i, cmd in enumerate(commands["modify"]):
                        if not isinstance(cmd, dict):
                            errors.append(
                                f"command_overrides.modify[{i}] must be a dictionary"
                            )
                        elif "name" not in cmd:
                            errors.append(
                                f"command_overrides.modify[{i}] missing required field 'name'"
                            )

    # Validate dependency_overrides
    if "dependency_overrides" in data:
        deps = data["dependency_overrides"]
        if not isinstance(deps, dict):
            errors.append("dependency_overrides must be a dictionary")
        else:
            for dep_type in ["tasks", "templates", "data"]:
                if dep_type in deps:
                    if not isinstance(deps[dep_type], dict):
                        errors.append(f"dependency_overrides.{dep_type} must be a dictionary")
                    elif "add" in deps[dep_type]:
                        if not isinstance(deps[dep_type]["add"], list):
                            errors.append(
                                f"dependency_overrides.{dep_type}.add must be a list"
                            )

    # Validate project_context
    if "project_context" in data:
        context = data["project_context"]
        if not isinstance(context, dict):
            errors.append("project_context must be a dictionary")
        else:
            if "always_load" in context:
                if not isinstance(context["always_load"], list):
                    errors.append("project_context.always_load must be a list")


def validate_referenced_files(
    data: dict[str, Any], project_root: Path, base_path: Path | None = None
) -> list[str]:
    """
    Validate that referenced files in customization exist.

    Args:
        data: Parsed customization data
        project_root: Project root directory
        base_path: Base path for relative file references (defaults to project_root)

    Returns:
        List of warnings (files that don't exist)
    """
    warnings: list[str] = []
    if base_path is None:
        base_path = project_root

    # Check dependency_overrides files
    if "dependency_overrides" in data:
        deps = data["dependency_overrides"]
        for dep_type in ["tasks", "templates", "data"]:
            if dep_type in deps and "add" in deps[dep_type]:
                for file_ref in deps[dep_type]["add"]:
                    if not isinstance(file_ref, str):
                        continue
                    # Try to resolve file path
                    file_path = base_path / file_ref
                    if not file_path.exists():
                        warnings.append(
                            f"Referenced {dep_type} file not found: {file_ref}"
                        )

    # Check project_context.always_load files
    if "project_context" in data:
        context = data["project_context"]
        if "always_load" in context:
            for file_ref in context["always_load"]:
                if not isinstance(file_ref, str):
                    continue
                file_path = base_path / file_ref
                if not file_path.exists():
                    warnings.append(f"Referenced always_load file not found: {file_ref}")

    return warnings

