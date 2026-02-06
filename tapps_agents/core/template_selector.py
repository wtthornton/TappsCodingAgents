"""
Tech Stack Template Selection Module

Selects appropriate configuration templates based on detected technology stack.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Framework to template file mapping
# Maps detected framework names to template file names (without .yaml extension)
FRAMEWORK_TEMPLATE_MAP: dict[str, str] = {
    "FastAPI": "fastapi",
    "Django": "django",
    "Flask": "flask",
    "React": "react",
    "Next.js": "nextjs",
    "NextJS": "nextjs",  # Alternative spelling
    "Express": "express",
    "NestJS": "nestjs",
    "Vue.js": "vue",
    "Vue": "vue",
    "Angular": "angular",
    "Starlette": "fastapi",  # Starlette projects use FastAPI template
}

# Template priority order for multi-framework projects
# When multiple frameworks are detected, templates are selected in this order
TEMPLATE_PRIORITY_ORDER = [
    "nextjs",  # Fullstack framework takes priority
    "nestjs",  # Enterprise API framework
    "fastapi",  # Modern Python API
    "django",  # Full-featured web framework
    "express",  # Node.js backend
    "flask",  # Lightweight Python web
    "react",  # Frontend framework
    "vue",  # Frontend framework
    "angular",  # Frontend framework
]

# Default template name (used as fallback)
DEFAULT_TEMPLATE = "default"


def normalize_framework_name(framework: str) -> str:
    """
    Normalize framework name for template lookup.
    
    Args:
        framework: Framework name (e.g., "FastAPI", "fastapi", "Fast API")
    
    Returns:
        Normalized framework name matching FRAMEWORK_TEMPLATE_MAP keys
    """
    # Remove extra spaces and normalize case
    normalized = framework.strip()
    
    # Try exact match first
    if normalized in FRAMEWORK_TEMPLATE_MAP:
        return normalized
    
    # Try case-insensitive match
    for key in FRAMEWORK_TEMPLATE_MAP:
        if key.lower() == normalized.lower():
            return key
    
    # Try partial match (e.g., "Fast API" -> "FastAPI")
    normalized_lower = normalized.lower().replace(" ", "").replace("-", "").replace("_", "")
    for key in FRAMEWORK_TEMPLATE_MAP:
        key_normalized = key.lower().replace(" ", "").replace("-", "").replace("_", "")
        if key_normalized == normalized_lower or normalized_lower in key_normalized:
            return key
    
    return normalized


def get_template_for_framework(framework: str) -> str | None:
    """
    Get template file name for a detected framework.
    
    Args:
        framework: Framework name (e.g., "FastAPI", "Next.js")
    
    Returns:
        Template file name (without .yaml extension) or None if not found
    
    Examples:
        >>> get_template_for_framework("FastAPI")
        'fastapi'
        >>> get_template_for_framework("Next.js")
        'nextjs'
        >>> get_template_for_framework("Unknown")
        None
    """
    normalized = normalize_framework_name(framework)
    return FRAMEWORK_TEMPLATE_MAP.get(normalized)


def select_template_for_frameworks(
    frameworks: list[str],
    templates_dir: Path | None = None,
) -> tuple[str | None, str]:
    """
    Select template for multiple detected frameworks.
    
    When multiple frameworks are detected, selects the highest priority template
    that exists. Priority is determined by TEMPLATE_PRIORITY_ORDER.
    
    Args:
        frameworks: List of detected framework names
        templates_dir: Directory containing template files (defaults to framework templates/tech_stacks)
    
    Returns:
        Tuple of (template_name, reason) where:
        - template_name: Template file name (without .yaml) or None if no match
        - reason: Human-readable reason for selection
    
    Examples:
        >>> select_template_for_frameworks(["FastAPI", "React"])
        ('fastapi', 'Selected fastapi (priority 2) from detected frameworks: FastAPI, React')
    """
    if not frameworks:
        return None, "No frameworks detected"
    
    if templates_dir is None:
        # Default to framework's templates directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        templates_dir = framework_root / "templates" / "tech_stacks"
    
    # Get template candidates for each framework
    template_candidates: dict[str, list[str]] = {}
    for framework in frameworks:
        template = get_template_for_framework(framework)
        if template:
            if template not in template_candidates:
                template_candidates[template] = []
            template_candidates[template].append(framework)
    
    if not template_candidates:
        return None, f"No template mapping found for frameworks: {', '.join(frameworks)}"
    
    # Select highest priority template that exists
    for template_name in TEMPLATE_PRIORITY_ORDER:
        if template_name in template_candidates:
            template_file = templates_dir / f"{template_name}.yaml"
            if template_file.exists():
                frameworks_str = ", ".join(template_candidates[template_name])
                priority = TEMPLATE_PRIORITY_ORDER.index(template_name) + 1
                return (
                    template_name,
                    f"Selected {template_name} (priority {priority}) from detected frameworks: {frameworks_str}",
                )
            else:
                logger.warning(
                    f"Template {template_name} mapped but file not found: {template_file}"
                )
    
    # Fallback: return first available template
    first_template = list(template_candidates.keys())[0]
    template_file = templates_dir / f"{first_template}.yaml"
    if template_file.exists():
        frameworks_str = ", ".join(template_candidates[first_template])
        return (
            first_template,
            f"Selected {first_template} (fallback) from detected frameworks: {frameworks_str}",
        )
    
    return None, f"No template files found for candidates: {', '.join(template_candidates.keys())}"


def select_template(
    tech_stack: dict[str, Any],
    templates_dir: Path | None = None,
) -> tuple[str | None, str]:
    """
    Select appropriate template based on detected tech stack.
    
    This is the main entry point for template selection. It handles:
    - Single framework detection
    - Multiple framework detection (priority-based selection)
    - Fallback to default template
    
    Args:
        tech_stack: Tech stack dictionary from detect_tech_stack()
        templates_dir: Directory containing template files (optional)
    
    Returns:
        Tuple of (template_name, reason) where:
        - template_name: Template file name (without .yaml) or None
        - reason: Human-readable reason for selection
    
    Examples:
        >>> tech_stack = {"frameworks": ["FastAPI"]}
        >>> select_template(tech_stack)
        ('fastapi', 'Selected fastapi for detected framework: FastAPI')
    """
    if templates_dir is None:
        # Default to framework's templates directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        templates_dir = framework_root / "templates" / "tech_stacks"
    
    frameworks = tech_stack.get("frameworks", [])
    
    if not frameworks:
        return None, "No frameworks detected in tech stack"
    
    # Single framework - direct mapping
    if len(frameworks) == 1:
        framework = frameworks[0]
        template = get_template_for_framework(framework)
        if template:
            template_file = templates_dir / f"{template}.yaml"
            if template_file.exists():
                return (
                    template,
                    f"Selected {template} for detected framework: {framework}",
                )
            else:
                logger.warning(f"Template {template} mapped but file not found: {template_file}")
                return None, f"Template {template} not found for framework: {framework}"
        else:
            return None, f"No template mapping for framework: {framework}"
    
    # Multiple frameworks - use priority-based selection
    return select_template_for_frameworks(frameworks, templates_dir)


def get_template_path(template_name: str, templates_dir: Path | None = None) -> Path | None:
    """
    Get full path to template file.
    
    Args:
        template_name: Template name (without .yaml extension)
        templates_dir: Directory containing templates (optional)
    
    Returns:
        Path to template file or None if not found
    """
    if templates_dir is None:
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        templates_dir = framework_root / "templates" / "tech_stacks"
    
    template_file = templates_dir / f"{template_name}.yaml"
    if template_file.exists():
        return template_file
    
    return None


def get_available_templates(templates_dir: Path | None = None) -> list[str]:
    """
    Get list of available template names.
    
    Args:
        templates_dir: Directory containing templates (optional)
    
    Returns:
        List of template names (without .yaml extension)
    """
    if templates_dir is None:
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        templates_dir = framework_root / "templates" / "tech_stacks"
    
    if not templates_dir.exists():
        return []
    
    templates = []
    for template_file in templates_dir.glob("*.yaml"):
        if template_file.name != "README.md":  # Skip README if it has .yaml extension
            templates.append(template_file.stem)
    
    return sorted(templates)

