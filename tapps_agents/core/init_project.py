"""
Project Initialization Module

Helps initialize a new project with TappsCodingAgents configuration,
Cursor Rules, and workflow presets.
"""

import shutil
from pathlib import Path
from typing import Any

import yaml

from .config import get_default_config

try:
    # Python 3.9+: importlib.resources is the canonical way to ship non-code assets.
    from importlib import resources as importlib_resources
    from importlib.resources.abc import Traversable
except Exception:  # pragma: no cover - extremely defensive
    importlib_resources = None  # type: ignore[assignment]
    Traversable = object  # type: ignore[misc,assignment]


def _resource_at(*parts: str) -> "Traversable | None":
    """
    Return a Traversable pointing at packaged resources under `tapps_agents.resources`.

    This enables `tapps-agents init` to work when the framework is installed from PyPI
    (where repo-root dot-directories like `.cursor/` and `.claude/` are not present).
    """
    if importlib_resources is None:
        return None
    try:
        root = importlib_resources.files("tapps_agents.resources")
        node: Traversable = root
        for p in parts:
            node = node / p
        return node
    except Exception:
        return None


def _copy_traversable_tree(src: "Traversable", dest: Path) -> list[str]:
    """
    Recursively copy a Traversable directory tree to a filesystem path.

    Returns a list of created file paths (as strings).
    """
    created: list[str] = []
    dest.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        target = dest / entry.name
        if entry.is_dir():
            created.extend(_copy_traversable_tree(entry, target))
        else:
            if target.exists():
                continue
            target.write_bytes(entry.read_bytes())
            created.append(str(target))
    return created


def init_project_config(project_root: Path | None = None) -> tuple[bool, str | None]:
    """
    Initialize `.tapps-agents/config.yaml` with a canonical default config.

    Returns:
        (created, path)
    """
    if project_root is None:
        project_root = Path.cwd()

    config_dir = project_root / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.yaml"
    if config_file.exists():
        return False, str(config_file)

    default_config = get_default_config()
    config_file.write_text(
        yaml.safe_dump(default_config, sort_keys=False),
        encoding="utf-8",
    )
    return True, str(config_file)


def init_cursor_rules(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Cursor Rules for the project.

    Args:
        project_root: Project root directory (defaults to cwd)
        source_dir: Source directory for rules (defaults to framework's .cursor/rules)

    Returns:
        (success, list of copied rule paths)
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        # Prefer packaged resources (works when installed from PyPI).
        packaged = _resource_at("cursor", "rules")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_rules = packaged
        else:
            packaged_rules = None
            # Fall back to repo-root `.cursor/rules` (works in source checkout).
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / ".cursor" / "rules"
    else:
        packaged_rules = None

    project_rules_dir = project_root / ".cursor" / "rules"
    project_rules_dir.mkdir(parents=True, exist_ok=True)

    # Copy Cursor Rules (workflow-presets, quick-reference, and agent-capabilities)
    rules_to_copy = [
        "workflow-presets.mdc",
        "quick-reference.mdc",
        "agent-capabilities.mdc",
        "project-context.mdc",
        "project-profiling.mdc",
    ]
    copied_rules = []

    for rule_name in rules_to_copy:
        dest_rule = project_rules_dir / rule_name
        if dest_rule.exists():
            continue

        if packaged_rules is not None:
            source_rule = packaged_rules / rule_name
            if source_rule.exists():
                dest_rule.write_bytes(source_rule.read_bytes())
                copied_rules.append(str(dest_rule))
        else:
            source_rule = source_dir / rule_name
            if source_rule.exists():
                shutil.copy2(source_rule, dest_rule)
                copied_rules.append(str(dest_rule))

    if copied_rules:
        return True, copied_rules

    return False, []


def init_workflow_presets(
    project_root: Path | None = None, source_dir: Path | None = None
):
    """
    Initialize workflow presets directory.

    Args:
        project_root: Project root directory (defaults to cwd)
        source_dir: Source directory for presets (defaults to framework's workflows/presets)
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        packaged = _resource_at("workflows", "presets")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_presets = packaged
        else:
            packaged_presets = None
            # Find framework's workflows/presets directory (source checkout).
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / "workflows" / "presets"
    else:
        packaged_presets = None

    project_presets_dir = project_root / "workflows" / "presets"
    project_presets_dir.mkdir(parents=True, exist_ok=True)

    # Copy preset files
    copied = []
    if packaged_presets is not None:
        for preset_file in packaged_presets.iterdir():
            if preset_file.is_dir() or not preset_file.name.endswith(".yaml"):
                continue
            dest_file = project_presets_dir / preset_file.name
            if dest_file.exists():
                continue
            dest_file.write_bytes(preset_file.read_bytes())
            copied.append(preset_file.name)
    else:
        if source_dir.exists():
            for preset_file in source_dir.glob("*.yaml"):
                dest_file = project_presets_dir / preset_file.name
                if not dest_file.exists():
                    shutil.copy2(preset_file, dest_file)
                    copied.append(preset_file.name)

    return len(copied) > 0, copied


def init_claude_skills(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Claude/Cursor Skills directory for a project.

    Copies framework-provided Skills from `.claude/skills/` into the target project.
    This is intentionally model-agnostic: Cursor's configured model is used at runtime.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        packaged = _resource_at("claude", "skills")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_skills = packaged
        else:
            packaged_skills = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / ".claude" / "skills"
    else:
        packaged_skills = None

    project_skills_dir = project_root / ".claude" / "skills"
    project_skills_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    if packaged_skills is not None:
        # Copy each skill folder (idempotent).
        for skill_dir in packaged_skills.iterdir():
            if not skill_dir.is_dir():
                continue
            dest_dir = project_skills_dir / skill_dir.name
            if dest_dir.exists():
                continue
            created = _copy_traversable_tree(skill_dir, dest_dir)
            if created:
                copied.append(str(dest_dir))
    else:
        if source_dir.exists():
            # Copy each skill folder (idempotent).
            for skill_dir in source_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                dest_dir = project_skills_dir / skill_dir.name
                if dest_dir.exists():
                    continue
                shutil.copytree(skill_dir, dest_dir)
                copied.append(str(dest_dir))

    return len(copied) > 0, copied


def init_background_agents_config(
    project_root: Path | None = None, source_file: Path | None = None
):
    """
    Initialize Cursor Background Agents config for a project.

    Copies `.cursor/background-agents.yaml` into the target project if it doesn't exist.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_file is None:
        packaged = _resource_at("cursor", "background-agents.yaml")
        if packaged is not None and packaged.exists() and not packaged.is_dir():
            source_file = None  # type: ignore[assignment]
            packaged_bg = packaged
        else:
            packaged_bg = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_file = framework_root / ".cursor" / "background-agents.yaml"
    else:
        packaged_bg = None

    project_cursor_dir = project_root / ".cursor"
    project_cursor_dir.mkdir(parents=True, exist_ok=True)
    dest_file = project_cursor_dir / "background-agents.yaml"

    if dest_file.exists():
        return False, str(dest_file)

    if packaged_bg is not None:
        dest_file.write_bytes(packaged_bg.read_bytes())
        return True, str(dest_file)

    if source_file.exists():
        shutil.copy2(source_file, dest_file)
        return True, str(dest_file)

    return False, None


def init_project(
    project_root: Path | None = None,
    include_cursor_rules: bool = True,
    include_workflow_presets: bool = True,
    include_config: bool = True,
    include_skills: bool = True,
    include_background_agents: bool = True,
):
    """
    Initialize a new project with TappsCodingAgents setup.

    Args:
        project_root: Project root directory (defaults to cwd)
        include_cursor_rules: Whether to copy Cursor Rules
        include_workflow_presets: Whether to copy workflow presets

    Returns:
        Dictionary with initialization results
    """
    if project_root is None:
        project_root = Path.cwd()

    results: dict[str, Any] = {
        "project_root": str(project_root),
        "cursor_rules": False,
        "workflow_presets": False,
        "config": False,
        "skills": False,
        "background_agents": False,
        "files_created": [],
    }

    # Initialize project config
    if include_config:
        success, config_path = init_project_config(project_root)
        results["config"] = success
        if config_path:
            results["files_created"].append(config_path)

    # Initialize Cursor Rules
    if include_cursor_rules:
        success, rule_paths = init_cursor_rules(project_root)
        results["cursor_rules"] = success
        if rule_paths:
            results["files_created"].extend(rule_paths)

    # Initialize workflow presets
    if include_workflow_presets:
        success, preset_files = init_workflow_presets(project_root)
        results["workflow_presets"] = success
        if preset_files:
            results["files_created"].extend(
                [f"workflows/presets/{f}" for f in preset_files]
            )

    # Initialize Skills for Cursor/Claude
    if include_skills:
        success, copied_skills = init_claude_skills(project_root)
        results["skills"] = success
        if copied_skills:
            results["files_created"].extend(copied_skills)

    # Initialize Cursor Background Agents config
    if include_background_agents:
        success, bg_path = init_background_agents_config(project_root)
        results["background_agents"] = success
        if bg_path:
            results["files_created"].append(bg_path)

    return results
