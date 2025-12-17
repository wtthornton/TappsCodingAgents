"""
Role template loader for user role templates.

Loads and applies user role templates to customize agent behavior based on user role.
Role templates provide sensible defaults that can be overridden by customizations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_role_template(
    role_id: str | None, project_root: Path | None = None
) -> dict[str, Any] | None:
    """
    Load user role template by role ID.

    Args:
        role_id: Role identifier (e.g., "senior-developer")
        project_root: Project root directory (defaults to cwd)

    Returns:
        Parsed role template data or None if not found/invalid
    """
    if role_id is None:
        return None

    if project_root is None:
        project_root = Path.cwd()

    # Try project-specific template first
    project_template_path = (
        project_root / "templates" / "user_roles" / f"{role_id}.yaml"
    )

    # Try framework template
    framework_template_path = (
        Path(__file__).parent.parent.parent / "templates" / "user_roles" / f"{role_id}.yaml"
    )

    # Try project template first, then framework template
    template_path = None
    if project_template_path.exists():
        template_path = project_template_path
    elif framework_template_path.exists():
        template_path = framework_template_path
    else:
        logger.debug(f"Role template not found: {role_id}")
        return None

    try:
        with open(template_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                logger.warning(f"Role template {template_path} is empty")
                return None
            return data
    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Error loading role template {template_path}: {e}")
        return None


def get_role_from_config(
    project_root: Path | None = None,
) -> str | None:
    """
    Get user role ID from project configuration.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Role ID if found in config, None otherwise
    """
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / ".tapps-agents" / "config.yaml"
    if not config_path.exists():
        return None

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config and isinstance(config, dict):
                # Check for user_role in config
                user_role = config.get("user_role")
                if user_role and isinstance(user_role, str):
                    return user_role
    except (OSError, yaml.YAMLError) as e:
        logger.debug(f"Error reading role from config: {e}")

    return None


def apply_role_template_to_agent_config(
    base_config: dict[str, Any],
    role_template: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Apply role template configuration to agent base config.

    This merges role template settings into the agent configuration.
    Role templates are applied before customizations (customizations can override).

    Args:
        base_config: Base agent configuration
        role_template: Role template data (may be None)

    Returns:
        Merged configuration with role template applied
    """
    if role_template is None:
        return base_config.copy()

    merged = base_config.copy()

    # Apply verbosity settings (if agent supports it)
    if "verbosity" in role_template:
        verbosity = role_template["verbosity"]
        if "persona" not in merged:
            merged["persona"] = {}
        if "communication_style" not in merged["persona"]:
            merged["persona"]["communication_style"] = {}
        
        # Map verbosity level to communication style
        level = verbosity.get("level", "balanced")
        merged["persona"]["communication_style"]["verbosity"] = level
        merged["persona"]["communication_style"]["explanations"] = verbosity.get("explanations", True)
        merged["persona"]["communication_style"]["examples"] = verbosity.get("examples", True)
        merged["persona"]["communication_style"]["learning_focus"] = verbosity.get("learning_focus", False)

    # Apply workflow defaults (if agent supports it)
    if "workflow_defaults" in role_template:
        workflow_defaults = role_template["workflow_defaults"]
        if "workflow" not in merged:
            merged["workflow"] = {}
        merged["workflow"].update(workflow_defaults)

    # Apply expert priorities (merge into project context or expert config)
    if "expert_priorities" in role_template:
        expert_priorities = role_template["expert_priorities"]
        if "project_context" not in merged:
            merged["project_context"] = {}
        if "expert_priorities" not in merged["project_context"]:
            merged["project_context"]["expert_priorities"] = {}
        # Merge expert priorities (role template values take precedence)
        merged["project_context"]["expert_priorities"].update(expert_priorities)

    # Apply documentation preferences
    if "documentation_preferences" in role_template:
        doc_prefs = role_template["documentation_preferences"]
        if "documentation" not in merged:
            merged["documentation"] = {}
        merged["documentation"].update(doc_prefs)

    # Apply review depth settings
    if "review_depth" in role_template:
        review_depth = role_template["review_depth"]
        if "review" not in merged:
            merged["review"] = {}
        merged["review"].update(review_depth)

    return merged


def load_and_apply_role_template(
    agent_config: dict[str, Any],
    role_id: str | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """
    Load and apply role template to agent configuration.

    This is the main entry point for applying role templates.

    Args:
        agent_config: Base agent configuration
        role_id: Role identifier (if None, will try to read from config)
        project_root: Project root directory (defaults to cwd)

    Returns:
        Agent configuration with role template applied
    """
    # Get role ID if not provided
    if role_id is None:
        role_id = get_role_from_config(project_root)

    # Load role template
    role_template = load_role_template(role_id, project_root)

    # Apply role template
    return apply_role_template_to_agent_config(agent_config, role_template)

