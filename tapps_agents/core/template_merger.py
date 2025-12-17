"""
Tech Stack Template Merging Module

Merges stack-specific templates with default configuration, handling
deep merging, variable expansion, and user overrides.
"""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Variable pattern: {{variable.name}} or {{variable.nested.name}}
VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")


def deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence for conflicts.
    
    For nested dictionaries, recursively merges. For lists, override replaces base.
    For scalar values, override replaces base.
    
    Args:
        base: Base dictionary (defaults)
        override: Override dictionary (template values)
    
    Returns:
        Merged dictionary
    
    Examples:
        >>> base = {"a": 1, "b": {"c": 2}}
        >>> override = {"b": {"d": 3}, "e": 4}
        >>> deep_merge_dict(base, override)
        {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge_dict(result[key], value)
        else:
            # Override replaces base (for scalars, lists, and non-dict types)
            result[key] = value
    
    return result


def expand_variables(
    value: Any,
    variables: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> Any:
    """
    Expand template variables in a value.
    
    Supports variable expansion in strings and nested structures.
    Variables use {{variable.name}} syntax.
    
    Args:
        value: Value that may contain variables
        variables: Dictionary of variable values
        context: Additional context for variable resolution (optional)
    
    Returns:
        Value with variables expanded
    
    Examples:
        >>> expand_variables("Hello {{name}}", {"name": "World"})
        'Hello World'
        >>> expand_variables({"path": "{{project.root}}/src"}, {"project": {"root": "/app"}})
        {'path': '/app/src'}
    """
    if context is None:
        context = {}
    
    # Combine variables and context
    all_vars = {**variables, **context}
    
    if isinstance(value, str):
        # Expand variables in string
        def replace_var(match):
            var_path = match.group(1)
            return _resolve_variable(var_path, all_vars)
        
        return VARIABLE_PATTERN.sub(replace_var, value)
    
    elif isinstance(value, dict):
        # Recursively expand variables in dictionary
        return {k: expand_variables(v, variables, context) for k, v in value.items()}
    
    elif isinstance(value, list):
        # Recursively expand variables in list
        return [expand_variables(item, variables, context) for item in value]
    
    else:
        # Scalar value, return as-is
        return value


def _resolve_variable(var_path: str, variables: dict[str, Any]) -> str:
    """
    Resolve a variable path (e.g., "project.name") from variables dictionary.
    
    Args:
        var_path: Dot-separated variable path
        variables: Dictionary of variables
    
    Returns:
        Resolved value as string, or original {{var_path}} if not found
    """
    parts = var_path.split(".")
    current = variables
    
    try:
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    # Variable not found, return original
                    return f"{{{{{var_path}}}}}"
            else:
                # Can't traverse further
                return f"{{{{{var_path}}}}}"
        
        # Convert to string
        if current is None:
            return f"{{{{{var_path}}}}}"
        
        return str(current)
    
    except (AttributeError, TypeError):
        # Error during traversal, return original
        return f"{{{{{var_path}}}}}"


def load_template(template_path: Path) -> dict[str, Any]:
    """
    Load a template YAML file.
    
    Args:
        template_path: Path to template YAML file
    
    Returns:
        Template dictionary
    
    Raises:
        FileNotFoundError: If template file doesn't exist
        yaml.YAMLError: If template is invalid YAML
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    try:
        content = template_path.read_text(encoding="utf-8")
        template = yaml.safe_load(content)
        if template is None:
            return {}
        return template
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in template {template_path}: {e}") from e


def merge_template_with_config(
    template: dict[str, Any],
    default_config: dict[str, Any],
    user_config: dict[str, Any] | None = None,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge template with default config and user overrides.
    
    Merge order (precedence from lowest to highest):
    1. Default config (base)
    2. Template values (override defaults)
    3. User config (override template and defaults)
    
    Variables are expanded in template before merging.
    
    Args:
        template: Template dictionary
        default_config: Default configuration dictionary
        user_config: User override configuration (optional)
        variables: Variables for template expansion (optional)
    
    Returns:
        Merged configuration dictionary
    
    Examples:
        >>> template = {"agent_config": {"reviewer": {"quality_threshold": 75.0}}}
        >>> default = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        >>> merge_template_with_config(template, default)
        {'agent_config': {'reviewer': {'quality_threshold': 75.0}}}
    """
    # Expand variables in template if variables provided
    if variables:
        template = expand_variables(template, variables)
    
    # Merge order: default -> template -> user
    merged = deep_merge_dict(default_config, template)
    
    if user_config:
        merged = deep_merge_dict(merged, user_config)
    
    return merged


def build_template_variables(
    project_root: Path,
    tech_stack: dict[str, Any] | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """
    Build variables dictionary for template expansion.
    
    Args:
        project_root: Project root directory
        tech_stack: Detected tech stack (optional)
        project_name: Project name (optional)
    
    Returns:
        Variables dictionary for template expansion
    """
    variables: dict[str, Any] = {
        "project": {
            "root": str(project_root),
            "name": project_name or project_root.name,
        },
    }
    
    if tech_stack:
        variables["tech_stack"] = {
            "frameworks": tech_stack.get("frameworks", []),
            "languages": tech_stack.get("languages", []),
            "libraries": tech_stack.get("libraries", []),
            "package_managers": tech_stack.get("package_managers", []),
        }
    
    return variables


def apply_template_to_config(
    template_path: Path | None,
    default_config: dict[str, Any],
    user_config: dict[str, Any] | None = None,
    project_root: Path | None = None,
    tech_stack: dict[str, Any] | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """
    Apply a template to configuration (main entry point).
    
    This function:
    1. Loads the template (if provided)
    2. Builds template variables
    3. Expands variables in template
    4. Merges template with defaults and user config
    
    Args:
        template_path: Path to template file (None = no template)
        default_config: Default configuration
        user_config: User override configuration (optional)
        project_root: Project root directory (optional)
        tech_stack: Detected tech stack (optional)
        project_name: Project name (optional)
    
    Returns:
        Merged configuration dictionary
    
    Examples:
        >>> default = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        >>> template_path = Path("templates/tech_stacks/fastapi.yaml")
        >>> apply_template_to_config(template_path, default)
        # Returns config with FastAPI-specific overrides
    """
    # If no template, just merge defaults with user config
    if template_path is None or not template_path.exists():
        if user_config:
            return deep_merge_dict(default_config, user_config)
        return default_config.copy()
    
    # Load template
    try:
        template = load_template(template_path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.warning(f"Failed to load template {template_path}: {e}")
        # Fallback to defaults + user config
        if user_config:
            return deep_merge_dict(default_config, user_config)
        return default_config.copy()
    
    # Build variables for expansion
    if project_root is None:
        project_root = Path.cwd()
    
    variables = build_template_variables(project_root, tech_stack, project_name)
    
    # Merge template with configs
    return merge_template_with_config(
        template,
        default_config,
        user_config,
        variables,
    )

