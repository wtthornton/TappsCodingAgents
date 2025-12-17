"""
Tech Stack Template Merging Module

Merges stack-specific templates with default configuration, handling
deep merging, variable expansion, conditional blocks, and user overrides.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Variable pattern: {{variable.name}} or {{variable.nested.name}}
VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")

# Conditional block patterns: {{#if var}}...{{/if}} and {{#if var}}...{{#else}}...{{/if}}
CONDITIONAL_IF_PATTERN = re.compile(r"\{\{#if\s+([a-zA-Z0-9_.]+)\}\}")
CONDITIONAL_ELSE_PATTERN = re.compile(r"\{\{#else\}\}")
CONDITIONAL_ENDIF_PATTERN = re.compile(r"\{\{/if\}\}")


@dataclass
class ConditionalTrace:
    """Trace information for conditional block evaluation."""
    
    condition: str
    variable_path: str
    variable_value: Any
    evaluated: bool
    reason: str


@dataclass
class TemplateTrace:
    """Trace information for template rendering."""
    
    template_path: str | None = None
    variables_used: dict[str, Any] = field(default_factory=dict)
    conditionals_evaluated: list[ConditionalTrace] = field(default_factory=list)
    variable_expansions: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary for JSON serialization."""
        return {
            "template_path": self.template_path,
            "variables_used": self.variables_used,
            "conditionals_evaluated": [
                {
                    "condition": c.condition,
                    "variable_path": c.variable_path,
                    "variable_value": str(c.variable_value),
                    "evaluated": c.evaluated,
                    "reason": c.reason,
                }
                for c in self.conditionals_evaluated
            ],
            "variable_expansions": self.variable_expansions,
        }
    
    def to_json(self) -> str:
        """Convert trace to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


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
    trace: TemplateTrace | None = None,
) -> Any:
    """
    Expand template variables in a value.
    
    Supports variable expansion in strings and nested structures.
    Variables use {{variable.name}} syntax.
    
    Args:
        value: Value that may contain variables
        variables: Dictionary of variable values
        context: Additional context for variable resolution (optional)
        trace: Optional trace object to record expansions (optional)
    
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
            resolved = _resolve_variable(var_path, all_vars)
            if trace and var_path not in trace.variable_expansions:
                trace.variable_expansions[var_path] = resolved
            return resolved
        
        return VARIABLE_PATTERN.sub(replace_var, value)
    
    elif isinstance(value, dict):
        # Recursively expand variables in dictionary
        return {k: expand_variables(v, variables, context, trace) for k, v in value.items()}
    
    elif isinstance(value, list):
        # Recursively expand variables in list
        return [expand_variables(item, variables, context, trace) for item in value]
    
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


def _resolve_variable_value(var_path: str, variables: dict[str, Any]) -> Any:
    """
    Resolve a variable path and return the actual value (not string).
    
    Args:
        var_path: Dot-separated variable path
        variables: Dictionary of variables
    
    Returns:
        Resolved value (any type) or None if not found
    """
    parts = var_path.split(".")
    current = variables
    
    try:
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None
        
        return current
    
    except (AttributeError, TypeError):
        return None


def _evaluate_condition(var_path: str, variables: dict[str, Any]) -> tuple[bool, Any, str]:
    """
    Safely evaluate a conditional variable.
    
    Safe evaluation rules:
    - Variable must exist in allowlisted variables
    - Only checks presence/truthiness (no arbitrary expressions)
    - Missing variables evaluate to False
    
    Args:
        var_path: Variable path to evaluate
        variables: Dictionary of variables
    
    Returns:
        Tuple of (evaluated, value, reason) where:
        - evaluated: Boolean result
        - value: Variable value (for trace)
        - reason: Human-readable reason
    """
    value = _resolve_variable_value(var_path, variables)
    
    if value is None:
        return (False, None, f"Variable '{var_path}' not found - evaluating to False")
    
    # Safe truthiness check (no arbitrary code execution)
    if isinstance(value, bool):
        evaluated = value
        reason = f"Variable '{var_path}' is boolean: {value}"
    elif isinstance(value, (str, list, dict)):
        evaluated = bool(value)  # Non-empty string/list/dict is truthy
        reason = f"Variable '{var_path}' is {'non-empty' if value else 'empty'}"
    elif isinstance(value, (int, float)):
        evaluated = value != 0
        reason = f"Variable '{var_path}' is numeric: {value} (non-zero is truthy)"
    else:
        evaluated = bool(value)
        reason = f"Variable '{var_path}' evaluated to {evaluated}"
    
    return (evaluated, value, reason)


def _process_conditional_blocks(
    content: str,
    variables: dict[str, Any],
    trace: TemplateTrace | None = None,
) -> str:
    """
    Process conditional blocks in YAML content string.
    
    Supports syntax:
    - {{#if variable.path}}...{{/if}}
    - {{#if variable.path}}...{{#else}}...{{/if}}
    
    Args:
        content: YAML content string with conditional blocks
        variables: Variables for conditional evaluation
        trace: Optional trace object to record evaluations
    
    Returns:
        Content with conditionals processed
    """
    result = []
    i = 0
    
    while i < len(content):
        # Look for {{#if ...}}
        if_match = CONDITIONAL_IF_PATTERN.search(content, i)
        if not if_match:
            # No more conditionals, append rest of content
            result.append(content[i:])
            break
        
        # Append content before conditional
        result.append(content[i : if_match.start()])
        
        # Extract variable path from {{#if var.path}}
        var_path = if_match.group(1)
        
        # Find matching {{/if}}
        endif_pos = if_match.end()
        depth = 1
        else_pos = None
        endif_match = None
        
        while endif_pos < len(content) and depth > 0:
            # Check for {{#else}}
            else_match = CONDITIONAL_ELSE_PATTERN.search(content, endif_pos)
            if else_match and depth == 1 and else_pos is None:
                else_pos = else_match.start()
                endif_pos = else_match.end()
                continue
            
            # Check for {{/if}}
            endif_match = CONDITIONAL_ENDIF_PATTERN.search(content, endif_pos)
            if endif_match:
                if depth == 1:
                    # Found matching endif - break and process
                    break
                else:
                    # Nested conditional (not supported, but handle gracefully)
                    depth -= 1
                    endif_pos = endif_match.end()
                    continue
            
            # Check for nested {{#if}}
            nested_if = CONDITIONAL_IF_PATTERN.search(content, endif_pos)
            if nested_if:
                depth += 1
                endif_pos = nested_if.end()
                continue
            
            # No match found, break
            break
        
        # Check if we successfully found matching endif
        if endif_match is None or depth != 1:
            # No matching {{/if}} found, treat as literal text
            result.append(content[if_match.start() : if_match.end()])
            i = if_match.end()
            continue
        
        # Extract true and false branches
        if else_pos is not None:
            true_branch = content[if_match.end() : else_pos]
            false_branch = content[CONDITIONAL_ELSE_PATTERN.search(content, else_pos).end() : endif_match.start()]
        else:
            true_branch = content[if_match.end() : endif_match.start()]
            false_branch = ""
        
        # Evaluate condition
        evaluated, value, reason = _evaluate_condition(var_path, variables)
        
        # Record in trace if provided
        if trace:
            trace.conditionals_evaluated.append(
                ConditionalTrace(
                    condition=f"{{{{#if {var_path}}}}}",
                    variable_path=var_path,
                    variable_value=value,
                    evaluated=evaluated,
                    reason=reason,
                )
            )
        
        # Append appropriate branch
        if evaluated:
            result.append(true_branch)
        else:
            result.append(false_branch)
        
        i = endif_match.end()
    
    return "".join(result)


def load_template(
    template_path: Path,
    variables: dict[str, Any] | None = None,
    trace: TemplateTrace | None = None,
) -> dict[str, Any]:
    """
    Load a template YAML file and process conditional blocks.
    
    Args:
        template_path: Path to template YAML file
        variables: Variables for conditional evaluation (optional)
        trace: Optional trace object to record processing (optional)
    
    Returns:
        Template dictionary with conditionals processed
    
    Raises:
        FileNotFoundError: If template file doesn't exist
        yaml.YAMLError: If template is invalid YAML
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    try:
        content = template_path.read_text(encoding="utf-8")
        
        # Process conditional blocks if variables provided
        if variables:
            content = _process_conditional_blocks(content, variables, trace)
            if trace:
                trace.template_path = str(template_path)
                trace.variables_used = variables.copy()
        
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
    trace: TemplateTrace | None = None,
) -> dict[str, Any]:
    """
    Merge template with default config and user overrides.
    
    Merge order (precedence from lowest to highest):
    1. Default config (base)
    2. Template values (override defaults)
    3. User config (override template and defaults)
    
    Variables are expanded in template before merging.
    Conditional blocks are processed during template loading.
    
    Args:
        template: Template dictionary (conditionals already processed)
        default_config: Default configuration dictionary
        user_config: User override configuration (optional)
        variables: Variables for template expansion (optional)
        trace: Optional trace object to record processing (optional)
    
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
        template = expand_variables(template, variables, trace=trace)
        if trace:
            # Record variable expansions
            for key, value in template.items():
                if isinstance(value, str) and "{{" in value:
                    trace.variable_expansions[key] = value
    
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
    enable_trace: bool = False,
    trace_output_path: Path | None = None,
) -> tuple[dict[str, Any], TemplateTrace | None]:
    """
    Apply a template to configuration (main entry point).
    
    This function:
    1. Loads the template (if provided)
    2. Builds template variables
    3. Processes conditional blocks in template
    4. Expands variables in template
    5. Merges template with defaults and user config
    6. Optionally generates trace output
    
    Args:
        template_path: Path to template file (None = no template)
        default_config: Default configuration
        user_config: User override configuration (optional)
        project_root: Project root directory (optional)
        tech_stack: Detected tech stack (optional)
        project_name: Project name (optional)
        enable_trace: Whether to generate trace output (default: False)
        trace_output_path: Path to save trace JSON file (optional)
    
    Returns:
        Tuple of (merged_config, trace) where:
        - merged_config: Merged configuration dictionary
        - trace: TemplateTrace object (None if tracing disabled)
    
    Examples:
        >>> default = {"agent_config": {"reviewer": {"quality_threshold": 70.0}}}
        >>> template_path = Path("templates/tech_stacks/fastapi.yaml")
        >>> config, trace = apply_template_to_config(template_path, default)
        # Returns config with FastAPI-specific overrides and trace info
    """
    trace = TemplateTrace() if enable_trace else None
    
    # If no template, just merge defaults with user config
    if template_path is None or not template_path.exists():
        if user_config:
            return (deep_merge_dict(default_config, user_config), trace)
        return (default_config.copy(), trace)
    
    # Build variables for expansion (needed for conditionals)
    if project_root is None:
        project_root = Path.cwd()
    
    variables = build_template_variables(project_root, tech_stack, project_name)
    
    # Load template with conditional processing
    try:
        template = load_template(template_path, variables, trace)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.warning(f"Failed to load template {template_path}: {e}")
        # Fallback to defaults + user config
        if user_config:
            return (deep_merge_dict(default_config, user_config), trace)
        return (default_config.copy(), trace)
    
    # Merge template with configs
    merged = merge_template_with_config(
        template,
        default_config,
        user_config,
        variables,
        trace,
    )
    
    # Save trace if requested
    if trace and trace_output_path:
        try:
            trace_output_path.parent.mkdir(parents=True, exist_ok=True)
            trace_output_path.write_text(trace.to_json(), encoding="utf-8")
            logger.info(f"Template trace saved to {trace_output_path}")
        except Exception as e:
            logger.warning(f"Failed to save trace to {trace_output_path}: {e}")
    
    return (merged, trace)

