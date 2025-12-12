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


def init_cursor_rules(
    project_root: Path | None = None, source_dir: Path | None = None
):
    """
    Initialize Cursor Rules for the project.

    Args:
        project_root: Project root directory (defaults to cwd)
        source_dir: Source directory for rules (defaults to framework's .cursor/rules)
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        # Find framework's .cursor/rules directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        source_dir = framework_root / ".cursor" / "rules"

    project_rules_dir = project_root / ".cursor" / "rules"
    project_rules_dir.mkdir(parents=True, exist_ok=True)

    # Copy workflow presets rule
    workflow_rule = source_dir / "workflow-presets.mdc"
    if workflow_rule.exists():
        dest_rule = project_rules_dir / "workflow-presets.mdc"
        if not dest_rule.exists():
            shutil.copy2(workflow_rule, dest_rule)
            return True, str(dest_rule)

    return False, None


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
        # Find framework's workflows/presets directory
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        source_dir = framework_root / "workflows" / "presets"

    project_presets_dir = project_root / "workflows" / "presets"
    project_presets_dir.mkdir(parents=True, exist_ok=True)

    # Copy preset files
    copied = []
    if source_dir.exists():
        for preset_file in source_dir.glob("*.yaml"):
            dest_file = project_presets_dir / preset_file.name
            if not dest_file.exists():
                shutil.copy2(preset_file, dest_file)
                copied.append(preset_file.name)

    return len(copied) > 0, copied


def init_project(
    project_root: Path | None = None,
    include_cursor_rules: bool = True,
    include_workflow_presets: bool = True,
    include_config: bool = True,
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
        success, rule_path = init_cursor_rules(project_root)
        results["cursor_rules"] = success
        if rule_path:
            results["files_created"].append(rule_path)

    # Initialize workflow presets
    if include_workflow_presets:
        success, preset_files = init_workflow_presets(project_root)
        results["workflow_presets"] = success
        if preset_files:
            results["files_created"].extend(
                [f"workflows/presets/{f}" for f in preset_files]
            )

    return results
