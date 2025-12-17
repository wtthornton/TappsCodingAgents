"""
Role file loader for agent role definitions.

Loads and parses agent role files from templates/agent_roles/ directory.
Role files define agent identity, principles, communication style, expertise areas,
and interaction patterns using markdown with YAML frontmatter.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter dict, markdown content without frontmatter)
        Returns (None, content) if no frontmatter found
    """
    # Match YAML frontmatter pattern: --- ... ---
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return None, content

    frontmatter_str = match.group(1)
    markdown_content = match.group(2)

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if not isinstance(frontmatter, dict):
            return None, content
        return frontmatter, markdown_content
    except yaml.YAMLError as e:
        logger.warning(f"Error parsing YAML frontmatter: {e}")
        return None, content


def _parse_markdown_sections(content: str) -> dict[str, str]:
    """
    Parse markdown content into sections.

    Sections are identified by level 2 headers (## Section Name).

    Args:
        content: Markdown content

    Returns:
        Dictionary mapping section names to section content
    """
    sections: dict[str, str] = {}

    # Pattern to match level 2 headers and their content
    # Matches: ## Section Name\n\ncontent...
    pattern = r"^##\s+(.+?)$\n\n(.*?)(?=^##\s+|\Z)"
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

    for match in matches:
        section_name = match.group(1).strip()
        section_content = match.group(2).strip()
        # Normalize section name (lowercase, replace spaces with underscores)
        normalized_name = section_name.lower().replace(" ", "_")
        sections[normalized_name] = section_content

    # If no sections found, treat entire content as a single section
    if not sections:
        sections["content"] = content.strip()

    return sections


def load_role_file(
    agent_id: str, project_root: Path | None = None
) -> dict[str, Any] | None:
    """
    Load role file for an agent.

    Args:
        agent_id: Agent identifier (e.g., "implementer", "architect")
        project_root: Project root directory (defaults to cwd)

    Returns:
        Parsed role file data or None if not found/invalid

    Role file structure:
    {
        "metadata": {
            "role_id": "...",
            "version": "...",
            "description": "...",
            ...
        },
        "sections": {
            "identity": "...",
            "principles": "...",
            "communication_style": "...",
            "expertise_areas": "...",
            "interaction_patterns": "...",
            "notes": "..." (optional)
        }
    }
    """
    if project_root is None:
        project_root = Path.cwd()

    # Determine role file path
    # Try project-specific first, then framework default
    role_paths = [
        project_root / "templates" / "agent_roles" / f"{agent_id}-role.md",
        Path(__file__).parent.parent.parent / "templates" / "agent_roles" / f"{agent_id}-role.md",
    ]

    role_path = None
    for path in role_paths:
        if path.exists():
            role_path = path
            break

    if role_path is None:
        logger.debug(f"Role file not found for agent {agent_id}")
        return None

    # Read file content
    try:
        content = role_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning(f"Error reading role file {role_path}: {e}")
        return None

    # Parse YAML frontmatter
    frontmatter, markdown_content = _parse_frontmatter(content)

    if frontmatter is None:
        logger.warning(f"No valid YAML frontmatter found in role file {role_path}")
        # Could still proceed with just markdown content, but for now return None
        return None

    # Validate required fields
    if "role_id" not in frontmatter:
        logger.warning(f"Missing required field 'role_id' in role file {role_path}")
        return None

    if frontmatter["role_id"] != agent_id:
        logger.warning(
            f"Role file role_id '{frontmatter['role_id']}' does not match agent_id '{agent_id}'"
        )
        # Still proceed, but log warning

    # Parse markdown sections
    sections = _parse_markdown_sections(markdown_content)

    # Structure result
    result = {
        "metadata": frontmatter,
        "sections": sections,
        "file_path": str(role_path),
    }

    return result


def get_role_file_path(
    agent_id: str, project_root: Path | None = None
) -> Path | None:
    """
    Get the path to a role file for an agent (without loading it).

    Args:
        agent_id: Agent identifier
        project_root: Project root directory (defaults to cwd)

    Returns:
        Path to role file or None if not found
    """
    if project_root is None:
        project_root = Path.cwd()

    role_paths = [
        project_root / "templates" / "agent_roles" / f"{agent_id}-role.md",
        Path(__file__).parent.parent.parent / "templates" / "agent_roles" / f"{agent_id}-role.md",
    ]

    for path in role_paths:
        if path.exists():
            return path

    return None

