"""
Validation functions for Cursor and Claude configuration setup.

Verifies that all required files and directories are properly configured
according to Cursor IDE best practices.
"""

from pathlib import Path
from typing import Any

import yaml


def validate_cursor_rules(project_root: Path) -> dict[str, Any]:
    """
    Validate Cursor Rules directory and files.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with validation results
    """
    rules_dir = project_root / ".cursor" / "rules"
    results: dict[str, Any] = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "rules_found": [],
    }

    if not rules_dir.exists():
        results["valid"] = False
        results["errors"].append(".cursor/rules/ directory does not exist")
        return results

    # Check for .mdc files
    mdc_files = list(rules_dir.glob("*.mdc"))
    if not mdc_files:
        results["valid"] = False
        results["errors"].append("No .mdc files found in .cursor/rules/")
        return results

    # Validate each .mdc file has YAML frontmatter
    for mdc_file in mdc_files:
        results["rules_found"].append(mdc_file.name)
        try:
            content = mdc_file.read_text(encoding="utf-8")
            if not content.startswith("---\n"):
                results["warnings"].append(
                    f"{mdc_file.name} does not start with YAML frontmatter (---)"
                )
            else:
                # Try to parse frontmatter
                parts = content.split("---\n", 2)
                if len(parts) >= 2:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        if not isinstance(frontmatter, dict):
                            results["warnings"].append(
                                f"{mdc_file.name} frontmatter is not a valid YAML dictionary"
                            )
                        elif "description" not in frontmatter:
                            results["warnings"].append(
                                f"{mdc_file.name} frontmatter missing 'description' field"
                            )
                        # Check for alwaysApply field (2025 best practice)
                        if "alwaysApply" not in frontmatter:
                            results["warnings"].append(
                                f"{mdc_file.name} frontmatter missing 'alwaysApply' field (recommended for 2025 best practices)"
                            )
                        # Check file size (2025 best practice: keep under 500 lines)
                        line_count = len(content.splitlines())
                        if line_count > 500:
                            results["warnings"].append(
                                f"{mdc_file.name} is {line_count} lines (recommended: <500 lines for 2025 best practices)"
                            )
                    except yaml.YAMLError as e:
                        results["warnings"].append(
                            f"{mdc_file.name} has invalid YAML frontmatter: {e}"
                        )
        except Exception as e:
            results["warnings"].append(f"Error reading {mdc_file.name}: {e}")

    return results


def validate_claude_skills(project_root: Path) -> dict[str, Any]:
    """
    Validate Claude Skills directory and files.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with validation results
    """
    skills_dir = project_root / ".claude" / "skills"
    results: dict[str, Any] = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "skills_found": [],
    }

    if not skills_dir.exists():
        results["valid"] = False
        results["errors"].append(".claude/skills/ directory does not exist")
        return results

    # Check for skill directories
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    if not skill_dirs:
        results["valid"] = False
        results["errors"].append("No skill directories found in .claude/skills/")
        return results

    # Validate each skill has SKILL.md with frontmatter
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            results["warnings"].append(
                f"Skill {skill_dir.name} missing SKILL.md file"
            )
            continue

        results["skills_found"].append(skill_dir.name)
        try:
            content = skill_file.read_text(encoding="utf-8")
            if not content.startswith("---\n"):
                results["warnings"].append(
                    f"Skill {skill_dir.name}/SKILL.md does not start with YAML frontmatter (---)"
                )
            else:
                # Try to parse frontmatter
                parts = content.split("---\n", 2)
                if len(parts) >= 2:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        if not isinstance(frontmatter, dict):
                            results["warnings"].append(
                                f"Skill {skill_dir.name} frontmatter is not a valid YAML dictionary"
                            )
                        else:
                            required_fields = ["name", "description"]
                            for field in required_fields:
                                if field not in frontmatter:
                                    results["warnings"].append(
                                        f"Skill {skill_dir.name} frontmatter missing '{field}' field"
                                    )
                    except yaml.YAMLError as e:
                        results["warnings"].append(
                            f"Skill {skill_dir.name} has invalid YAML frontmatter: {e}"
                        )
        except Exception as e:
            results["warnings"].append(f"Error reading {skill_dir.name}/SKILL.md: {e}")

    return results


def validate_cursorignore(project_root: Path) -> dict[str, Any]:
    """
    Validate .cursorignore file.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with validation results
    """
    ignore_file = project_root / ".cursorignore"
    results: dict[str, Any] = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    if not ignore_file.exists():
        results["warnings"].append(
            ".cursorignore does not exist (optional but recommended for performance)"
        )
        return results

    # Basic validation - check it's not empty
    try:
        content = ignore_file.read_text(encoding="utf-8")
        if not content.strip():
            results["warnings"].append(".cursorignore file is empty")
    except Exception as e:
        results["warnings"].append(f"Error reading .cursorignore: {e}")

    return results


def validate_cursor_setup(project_root: Path | None = None) -> dict[str, Any]:
    """
    Validate complete Cursor and Claude setup.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Dictionary with comprehensive validation results
    """
    if project_root is None:
        project_root = Path.cwd()

    results: dict[str, Any] = {
        "project_root": str(project_root),
        "overall_valid": True,
        "cursor_rules": validate_cursor_rules(project_root),
        "claude_skills": validate_claude_skills(project_root),
        "cursorignore": validate_cursorignore(project_root),
    }

    # Determine overall validity
    all_valid = (
        results["cursor_rules"]["valid"]
        and results["claude_skills"]["valid"]
    )

    results["overall_valid"] = all_valid

    # Collect all errors and warnings
    all_errors: list[str] = []
    all_warnings: list[str] = []

    for section in ["cursor_rules", "claude_skills", "cursorignore"]:
        section_results = results[section]
        all_errors.extend(section_results.get("errors", []))
        all_warnings.extend(section_results.get("warnings", []))

    results["all_errors"] = all_errors
    results["all_warnings"] = all_warnings

    return results

