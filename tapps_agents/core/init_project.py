"""
Project Initialization Module

Helps initialize a new project with TappsCodingAgents configuration,
Cursor Rules, and workflow presets.
"""

import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from .config import get_default_config
from .init_autofill import detect_tech_stack_enhanced
from .tech_stack_priorities import get_priorities_for_frameworks

logger = logging.getLogger(__name__)


def _safe_rmtree(path: Path, max_retries: int = 3) -> bool:
    """
    Remove directory with retries. Handles Windows file locks (WinError 5).

    Args:
        path: Directory path to remove
        max_retries: Number of retry attempts with backoff

    Returns:
        True if removed, False on persistent PermissionError/OSError
    """
    for attempt in range(max_retries):
        try:
            if path.exists():
                shutil.rmtree(path)
            return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
            else:
                logger.warning(
                    "Could not remove %s (access denied, possibly locked by IDE): %s",
                    path,
                    e,
                )
                return False
        except FileNotFoundError:
            return True  # Already gone
        except OSError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
            else:
                logger.warning("Could not remove %s: %s", path, e)
                return False
    return False


def _convert_paths_to_strings(obj: Any) -> Any:
    """
    Recursively convert Path objects to strings for YAML serialization.
    
    YAML's safe_dump cannot serialize Path objects (WindowsPath/PosixPath).
    This function walks through dicts and lists, converting any Path objects
    to their string representation.
    
    Args:
        obj: Any object (dict, list, Path, or primitive)
        
    Returns:
        The same structure with Path objects converted to strings
    """
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _convert_paths_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_paths_to_strings(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_convert_paths_to_strings(item) for item in obj)
    return obj


# Framework-managed file names (whitelist approach)
FRAMEWORK_CURSOR_RULES = {
    "workflow-presets.mdc",
    "quick-reference.mdc",
    "agent-capabilities.mdc",
    "when-to-use.mdc",
    "project-context.mdc",
    "project-profiling.mdc",
    "simple-mode.mdc",
    "command-reference.mdc",
    "cursor-mode-usage.mdc",
    "security.mdc",
    "coding-style.mdc",
    "testing.mdc",
    "git-workflow.mdc",
    "performance.mdc",
}

FRAMEWORK_SKILLS = {
    "analyst",
    "architect",
    "backend-patterns",
    "coding-standards",
    "debugger",
    "designer",
    "documenter",
    "enhancer",
    "evaluator",  # Added: Quality evaluation skill
    "frontend-patterns",
    "implementer",
    "improver",
    "ops",
    "orchestrator",
    "planner",
    "reviewer",
    "security-review",
    "simple-mode",
    "tester",
}

FRAMEWORK_WORKFLOW_PRESETS = {
    "full-sdlc.yaml",
    "rapid-dev.yaml",
    "fix.yaml",
    "quality.yaml",
    "brownfield-analysis.yaml",
}

try:
    # Python 3.9+: importlib.resources is the canonical way to ship non-code assets.
    from importlib import resources as importlib_resources
    from importlib.resources.abc import Traversable
except Exception:  # pragma: no cover - extremely defensive
    importlib_resources = None  # type: ignore[assignment]
    Traversable = object  # type: ignore[misc,assignment]


def _read_pyproject_name(path: Path) -> str | None:
    """Read [project] name from pyproject.toml if present."""
    pf = path / "pyproject.toml"
    if not pf.exists():
        return None
    try:
        import tomllib
        with open(pf, "rb") as f:
            data = tomllib.load(f)
        return (data.get("project") or {}).get("name")
    except Exception:
        return None


def is_framework_directory(path: Path) -> bool:
    """
    Return True if path is the TappsCodingAgents framework directory.

    Used to detect when init is run from the framework checkout (e.g. a
    TappsCodingAgents/ subdirectory) instead of the user's project root.
    """
    path = path.resolve()
    if path.name == "TappsCodingAgents":
        return True
    if not (path / "tapps_agents").exists() or not (path / "pyproject.toml").exists():
        return False
    name = _read_pyproject_name(path)
    return name == "tapps-agents"


def detect_project_root(start_path: Path) -> Path | None:
    """
    Walk up from the parent of start_path to find a likely project root.

    Looks for .git, src/, or app/ and excludes the framework directory.
    Returns None if not found.
    """
    current = start_path.resolve().parent
    while current != current.parent:
        if is_framework_directory(current):
            current = current.parent
            continue
        if (current / ".git").exists():
            return current
        if (current / "src").exists() or (current / "app").exists():
            return current
        current = current.parent
    return None


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


def init_project_config(
    project_root: Path | None = None,
    tech_stack: dict[str, Any] | None = None,
    apply_template: bool = True,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """
    Initialize `.tapps-agents/config.yaml` with a canonical default config.
    
    Optionally applies tech stack template if detected and apply_template is True.

    Args:
        project_root: Project root directory
        tech_stack: Pre-detected tech stack (optional, will detect if None)
        apply_template: Whether to apply tech stack template (default: True)

    Returns:
        Tuple of (created, path, template_info) where:
        - created: True if file was created, False if already existed
        - path: Path to config file
        - template_info: Dict with template selection info (template_name, reason) or None
    """
    if project_root is None:
        project_root = Path.cwd()

    config_dir = project_root / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.yaml"
    file_existed = config_file.exists()
    
    # Load existing user config if it exists (to preserve overrides)
    user_config: dict[str, Any] | None = None
    if file_existed:
        try:
            existing_content = config_file.read_text(encoding="utf-8")
            user_config = yaml.safe_load(existing_content) or {}
        except Exception:
            # If parsing fails, start fresh
            user_config = None

    # Get default config
    default_config = get_default_config()
    
    # Apply templates if enabled (project-type first, then tech-stack)
    template_info: dict[str, Any] | None = None
    project_type_info: dict[str, Any] | None = None
    final_config = default_config
    
    if apply_template:
        # Detect tech stack if not provided
        if tech_stack is None:
            tech_stack = detect_tech_stack(project_root)
        
        try:
            from .template_merger import apply_template_to_config
            
            # Step 1: Detect and apply project type template (if detected)
            try:
                from .project_type_detector import (
                    detect_project_type,
                    get_project_type_template_path,
                )
                
                project_type, confidence, reason = detect_project_type(project_root, tech_stack)
                
                if project_type and confidence >= 0.3:
                    project_type_path = get_project_type_template_path(project_type)
                    
                    if project_type_path:
                        # Apply project type template (merge: defaults < project-type)
                        final_config, _ = apply_template_to_config(
                            template_path=project_type_path,
                            default_config=default_config,
                            user_config=None,  # Don't apply user config yet
                            project_root=project_root,
                            tech_stack=tech_stack,
                            project_name=project_root.name,
                            enable_trace=False,
                        )
                        
                        project_type_info = {
                            "project_type": project_type,
                            "confidence": confidence,
                            "reason": reason,
                            "applied": True,
                        }
                    else:
                        project_type_info = {
                            "project_type": project_type,
                            "confidence": confidence,
                            "reason": f"{reason} (template file not found)",
                            "applied": False,
                        }
                else:
                    project_type_info = {
                        "project_type": None,
                        "confidence": confidence if project_type else 0.0,
                        "reason": reason,
                        "applied": False,
                    }
            except ImportError:
                # Project type detector not available, skip
                logger.debug("Project type detector not available, skipping project type template")
                project_type_info = None
            except Exception as e:
                logger.debug(f"Project type detection failed: {e}, continuing without project type template")
                project_type_info = None
            
            # Step 2: Apply tech stack template (merge: current config < tech-stack)
            if tech_stack.get("frameworks"):
                try:
                    from .template_selector import get_template_path, select_template
                    
                    # Select tech stack template
                    template_name, reason = select_template(tech_stack)
                    
                    if template_name:
                        # Get template path
                        template_path = get_template_path(template_name)
                        
                        if template_path:
                            # Apply tech stack template (merge: current < tech-stack)
                            # Note: final_config already has project-type applied (if any)
                            final_config, _ = apply_template_to_config(
                                template_path=template_path,
                                default_config=final_config,  # Use current config as base
                                user_config=None,  # Don't apply user config yet
                                project_root=project_root,
                                tech_stack=tech_stack,
                                project_name=project_root.name,
                                enable_trace=False,
                            )
                            
                            template_info = {
                                "template_name": template_name,
                                "reason": reason,
                                "applied": True,
                            }
                        else:
                            template_info = {
                                "template_name": template_name,
                                "reason": f"{reason} (template file not found)",
                                "applied": False,
                            }
                    else:
                        template_info = {
                            "template_name": None,
                            "reason": reason,
                            "applied": False,
                        }
                except ImportError:
                    # Template selector not available, skip
                    logger.debug("Template selector not available, skipping tech stack template")
                    template_info = None
                except Exception as e:
                    logger.debug(f"Tech stack template application failed: {e}, continuing without template")
                    template_info = None
            
            # Step 3: Apply user config last (highest precedence)
            if user_config:
                from .template_merger import deep_merge_dict
                final_config = deep_merge_dict(final_config, user_config)
                
        except ImportError:
            # Template modules not available, skip template application
            logger.warning("Template modules not available, skipping template application")
            template_info = None
            project_type_info = None
        except Exception as e:
            # Template application failed, use defaults
            logger.warning(f"Template application failed: {e}, using default config")
            template_info = None
            project_type_info = None
    
    # Write config file
    # Convert Path objects to strings before YAML serialization
    # (YAML safe_dump cannot handle WindowsPath/PosixPath objects)
    serializable_config = _convert_paths_to_strings(final_config)
    config_file.write_text(
        yaml.safe_dump(serializable_config, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    
    # Combine template info (project-type + tech-stack)
    combined_info = {
        "tech_stack_template": template_info,
        "project_type_template": project_type_info,
    }
    
    return not file_existed, str(config_file), combined_info


def _sync_directory_files(directory: Path, file_paths: list[str]) -> None:
    """
    Sync directory and files to ensure visibility before validation.

    Best-effort operation - will not raise exceptions on failure.
    Tries progressively more specific sync operations:
    1. System-wide sync (Unix: os.sync)
    2. Directory-level sync (Windows: fsync on directory)
    3. File-level sync (fallback: fsync on individual files)

    Args:
        directory: Directory to sync
        file_paths: List of file paths to sync if directory sync fails
    """
    import os

    # Try system-wide sync first (Unix)
    if hasattr(os, 'sync'):
        try:
            os.sync()
            return  # Success, no need for file-level sync
        except (OSError, AttributeError):
            pass  # Fall through to directory/file sync

    # Try directory-level sync (Windows)
    if hasattr(os, 'fsync'):
        try:
            fd = os.open(str(directory), os.O_RDONLY)
            try:
                os.fsync(fd)
                return  # Success
            finally:
                os.close(fd)
        except (OSError, AttributeError):
            pass  # Fall through to file-level sync

    # Last resort: Sync individual files
    for file_path_str in file_paths:
        try:
            file_path = Path(file_path_str)
            if file_path.exists():
                with open(file_path, 'r+b') as f:
                    os.fsync(f.fileno())
        except OSError:
            pass  # Best effort, continue with remaining files


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

    # Copy Cursor Rules (workflow-presets, quick-reference, agent-capabilities, when-to-use, project-context, project-profiling, simple-mode, command-reference, cursor-mode-usage, security, coding-style, testing, git-workflow, performance)
    rules_to_copy = [
        "workflow-presets.mdc",
        "quick-reference.mdc",
        "agent-capabilities.mdc",
        "when-to-use.mdc",
        "project-context.mdc",
        "project-profiling.mdc",
        "simple-mode.mdc",
        "command-reference.mdc",
        "cursor-mode-usage.mdc",
        "security.mdc",
        "coding-style.mdc",
        "testing.mdc",
        "git-workflow.mdc",
        "performance.mdc",
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

    # Always generate workflow-presets.mdc from YAML files (auto-generated)
    try:
        from tapps_agents.workflow.rules_generator import CursorRulesGenerator

        generator = CursorRulesGenerator(project_root=project_root)
        rules_path = project_rules_dir / "workflow-presets.mdc"
        generator.write(output_path=rules_path, backup=False)
        if rules_path.exists() and str(rules_path) not in copied_rules:
            copied_rules.append(str(rules_path))
            logger.debug("Generated workflow-presets.mdc from YAML files")
    except ValueError as e:
        # ValueError means no workflows found - this is expected in some cases
        logger.debug(f"Could not generate workflow-presets.mdc (no workflows found): {e}")
    except Exception as e:
        # Other errors should be logged but not fail init
        logger.warning(f"Could not generate workflow-presets.mdc: {e}")

    # Explicit file sync to ensure all writes are visible before validation
    # This prevents race conditions where validation runs before files are fully flushed to disk
    # Especially important on Windows with antivirus/indexing or slow filesystems
    if copied_rules:
        try:
            _sync_directory_files(project_rules_dir, copied_rules)
        except Exception as e:
            # File sync is best-effort, don't fail if it doesn't work
            logger.debug(f"File sync after init_cursor_rules failed (non-critical): {e}")

    return True if copied_rules else False, copied_rules


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


def init_user_skills_directory() -> Path:
    """Create USER scope skills directory if it doesn't exist.
    
    USER scope allows users to create personal skills that work across all projects.
    Location: ~/.tapps-agents/skills/
    
    Returns:
        Path to USER skills directory
    """
    user_skills_dir = Path.home() / ".tapps-agents" / "skills"
    user_skills_dir.mkdir(parents=True, exist_ok=True)
    return user_skills_dir


def init_claude_skills(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Claude/Cursor Skills directory for a project.

    Copies framework-provided Skills from `.claude/skills/` into the target project.
    This is intentionally model-agnostic: Cursor's configured model is used at runtime.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Create USER scope directory for personal skills
    init_user_skills_directory()

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
        # Copy each skill folder (idempotent). P2b: copy-then-swap - never leave empty dir.
        for skill_dir in packaged_skills.iterdir():
            if not skill_dir.is_dir():
                continue
            dest_dir = project_skills_dir / skill_dir.name
            # Check if skill directory exists and has SKILL.md
            skill_md = dest_dir / "SKILL.md"
            if dest_dir.exists() and skill_md.exists():
                continue  # Skip if complete skill already exists
            # Copy to temp first, then swap (P2b: copy-then-swap)
            dest_new = project_skills_dir / (skill_dir.name + ".tapps-new")
            try:
                if dest_new.exists():
                    _safe_rmtree(dest_new)
                created = _copy_traversable_tree(skill_dir, dest_new)
                if not created:
                    continue
                # Remove old dir and rename new into place
                if dest_dir.exists():
                    if not _safe_rmtree(dest_dir):
                        logger.warning(
                            "Skipping skill %s - directory could not be removed "
                            "(close Cursor/IDE and retry init --reset)",
                            dest_dir.name,
                        )
                        _safe_rmtree(dest_new)
                        continue
                dest_new.rename(dest_dir)
                copied.append(str(dest_dir))
            except OSError as e:
                logger.warning("Skipping skill %s: %s", skill_dir.name, e)
                _safe_rmtree(dest_new)
    else:
        if source_dir.exists():
            # Copy each skill folder (idempotent). P2b: copy-then-swap for non-packaged path.
            for skill_dir in source_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                dest_dir = project_skills_dir / skill_dir.name
                skill_md = dest_dir / "SKILL.md"
                if dest_dir.exists() and skill_md.exists():
                    continue
                dest_new = project_skills_dir / (skill_dir.name + ".tapps-new")
                try:
                    if dest_new.exists():
                        _safe_rmtree(dest_new)
                    shutil.copytree(skill_dir, dest_new)
                    if dest_dir.exists():
                        if not _safe_rmtree(dest_dir):
                            logger.warning(
                                "Skipping skill %s - directory could not be removed",
                                dest_dir.name,
                            )
                            _safe_rmtree(dest_new)
                            continue
                    dest_new.rename(dest_dir)
                    copied.append(str(dest_dir))
                except OSError as e:
                    logger.warning("Skipping skill %s: %s", skill_dir.name, e)
                    _safe_rmtree(dest_new)

    return len(copied) > 0, copied


def init_claude_commands(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Claude Desktop Commands directory for a project.

    Copies framework-provided Commands from `.claude/commands/` into the target project.
    These commands work alongside Cursor Skills for a unified experience.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        packaged = _resource_at("claude", "commands")
        if packaged is not None and packaged.is_dir():
            source_dir = None  # type: ignore[assignment]
            packaged_commands = packaged
        else:
            packaged_commands = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_dir = framework_root / ".claude" / "commands"
    else:
        packaged_commands = None

    project_commands_dir = project_root / ".claude" / "commands"
    project_commands_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    if packaged_commands is not None:
        # Copy each command file (idempotent).
        for cmd_file in packaged_commands.iterdir():
            if cmd_file.is_dir() or not cmd_file.name.endswith(".md"):
                continue
            dest_file = project_commands_dir / cmd_file.name
            if dest_file.exists():
                continue
            dest_file.write_bytes(cmd_file.read_bytes())
            copied.append(str(dest_file))
    else:
        if source_dir.exists():
            # Copy each command file (idempotent).
            for cmd_file in source_dir.glob("*.md"):
                dest_file = project_commands_dir / cmd_file.name
                if not dest_file.exists():
                    shutil.copy2(cmd_file, dest_file)
                    copied.append(str(dest_file))

    return len(copied) > 0, copied


def init_cursor_commands(project_root: Path | None = None, source_dir: Path | None = None):
    """
    Initialize Cursor slash commands directory for a project.

    Copies framework-provided commands from `tapps_agents/resources/cursor/commands/`
    into the project's `.cursor/commands/`. The "Import Claude Commands" toggle loads
    both `.claude/commands/` and `.cursor/commands/`; these provide /build, /fix, /review,
    /test in Cursor chat.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_dir is None:
        packaged = _resource_at("cursor", "commands")
        if packaged is not None and packaged.is_dir():
            packaged_commands = packaged
        else:
            packaged_commands = None
            current_file = Path(__file__)
            package_root = current_file.parent.parent
            source_dir = package_root / "resources" / "cursor" / "commands"
    else:
        packaged_commands = None

    project_commands_dir = project_root / ".cursor" / "commands"
    project_commands_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    if packaged_commands is not None:
        for cmd_file in packaged_commands.iterdir():
            if cmd_file.is_dir() or not cmd_file.name.endswith(".md"):
                continue
            dest_file = project_commands_dir / cmd_file.name
            if dest_file.exists():
                continue
            dest_file.write_bytes(cmd_file.read_bytes())
            copied.append(str(dest_file))
    else:
        src = source_dir if isinstance(source_dir, Path) else Path(source_dir) if source_dir else None
        if src is not None and src.exists():
            for cmd_file in src.glob("*.md"):
                dest_file = project_commands_dir / cmd_file.name
                if not dest_file.exists():
                    shutil.copy2(cmd_file, dest_file)
                    copied.append(str(dest_file))

    return len(copied) > 0, copied


# Background Agents removed - function no longer needed


def init_customizations_directory(project_root: Path | None = None) -> tuple[bool, str | None]:
    """
    Initialize `.tapps-agents/customizations/` directory for agent customizations.

    Creates the directory structure if it doesn't exist. This directory is
    gitignored by default to allow project-specific agent customizations.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Tuple of (created, directory_path)
    """
    if project_root is None:
        project_root = Path.cwd()

    customizations_dir = project_root / ".tapps-agents" / "customizations"
    
    # Create directory if it doesn't exist
    if not customizations_dir.exists():
        try:
            customizations_dir.mkdir(parents=True, exist_ok=True)
            return True, str(customizations_dir)
        except OSError:
            # Permission error or other OS error
            return False, None
    else:
        return False, str(customizations_dir)


def init_cursorignore(project_root: Path | None = None, source_file: Path | None = None):
    """
    Initialize .cursorignore file for a project.

    Copies `.cursorignore` into the target project if it doesn't exist.
    This file helps keep Cursor fast by excluding large/generated artifacts from indexing.
    Also adds `.tapps-agents/customizations/` to gitignore patterns.
    """
    if project_root is None:
        project_root = Path.cwd()

    if source_file is None:
        packaged = _resource_at("cursor", ".cursorignore")
        if packaged is not None and packaged.exists() and not packaged.is_dir():
            source_file = None  # type: ignore[assignment]
            packaged_ignore = packaged
        else:
            packaged_ignore = None
            current_file = Path(__file__)
            framework_root = current_file.parent.parent.parent
            source_file = framework_root / ".cursorignore"
    else:
        packaged_ignore = None

    dest_file = project_root / ".cursorignore"
    created = False

    if not dest_file.exists():
        if packaged_ignore is not None:
            dest_file.write_bytes(packaged_ignore.read_bytes())
            created = True
        elif source_file and source_file.exists():
            shutil.copy2(source_file, dest_file)
            created = True
        else:
            # Create new .cursorignore file
            dest_file.write_text("# Cursor ignore patterns\n", encoding="utf-8")
            created = True

    # Add customizations directory to gitignore if not already present
    if dest_file.exists():
        content = dest_file.read_text(encoding="utf-8")
        customizations_pattern = ".tapps-agents/customizations/"
        if customizations_pattern not in content:
            # Append to file
            with open(dest_file, "a", encoding="utf-8") as f:
                f.write("\n# Agent customizations (project-specific, gitignored by default)\n")
                f.write(f"{customizations_pattern}\n")
            created = True  # Mark as created if we modified it

    return created, str(dest_file)


def init_hooks_minimal(project_root: Path | None = None) -> tuple[bool, str | None]:
    """
    Create minimal empty hooks.yaml so hooks config exists but no hooks are enabled.

    Used by standard `tapps-agents init` (no --hooks). Does not overwrite existing file.
    """
    if project_root is None:
        project_root = Path.cwd()
    config_dir = project_root / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = config_dir / "hooks.yaml"
    if hooks_file.exists():
        return False, str(hooks_file)
    hooks_file.write_text("hooks: {}\n", encoding="utf-8")
    return True, str(hooks_file)


def init_hooks_and_context(
    project_root: Path | None = None,
) -> tuple[bool, str | None, bool, list[str]]:
    """
    Create hooks.yaml from packaged templates (all hooks disabled) and .tapps-agents/context/.

    Used by `tapps-agents init --hooks`. Merges all template YAMLs under
    tapps_agents/resources/hooks/templates/*.yaml into one hooks.yaml with every hook
    set to enabled: false. Also creates .tapps-agents/context/ with a README template.

    Returns:
        (hooks_created, hooks_path, context_created, files_created_list)
    """
    if project_root is None:
        project_root = Path.cwd()
    files_created: list[str] = []
    config_dir = project_root / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = config_dir / "hooks.yaml"

    try:
        from ..hooks.config import HOOK_EVENT_TYPES
    except ImportError:
        HOOK_EVENT_TYPES = frozenset(
            {"UserPromptSubmit", "PostToolUse", "SessionStart", "SessionEnd", "WorkflowComplete"}
        )

    # Load and merge template YAMLs from packaged resources
    merged: dict[str, list[dict[str, Any]]] = {}
    templates_root = _resource_at("hooks", "templates")
    if templates_root is not None and templates_root.is_dir():
        for entry in templates_root.iterdir():
            if not entry.name.endswith(".yaml") or not entry.is_file():
                continue
            try:
                raw = yaml.safe_load(entry.read_bytes())
                if not isinstance(raw, dict) or "hooks" not in raw:
                    continue
                for event_name, hook_list in raw["hooks"].items():
                    if event_name not in HOOK_EVENT_TYPES:
                        continue
                    if not isinstance(hook_list, list):
                        continue
                    for item in hook_list:
                        if not isinstance(item, dict):
                            continue
                        # Force disabled for init --hooks
                        hook_copy = dict(item)
                        hook_copy["enabled"] = False
                        merged.setdefault(event_name, []).append(hook_copy)
            except Exception as e:
                logger.debug("Skip template %s: %s", entry.name, e)

    out: dict[str, Any] = {"hooks": merged}
    hooks_file.write_text(
        yaml.safe_dump(out, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    hooks_created = True
    files_created.append(".tapps-agents/hooks.yaml")

    # Create .tapps-agents/context/ with template README
    context_dir = config_dir / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    context_readme = context_dir / "README.md"
    context_created = False
    if not context_readme.exists():
        context_readme.write_text(
            "# Project context\n\n"
            "Add markdown or text files here to inject project-specific context "
            "into UserPromptSubmit (e.g. via a hook that cats these files).\n",
            encoding="utf-8",
        )
        context_created = True
        files_created.append(".tapps-agents/context/README.md")

    return hooks_created, str(hooks_file), context_created, files_created


def _ensure_set_bd_path_script(project_root: Path) -> tuple[bool, str | None]:
    """
    If tools/bd exists, ensure scripts/set_bd_path.ps1 exists (copy from resources if missing).

    Does not overwrite an existing file. Returns (installed, path).
    """
    tools_bd = project_root / "tools" / "bd"
    if not tools_bd.is_dir():
        return False, None
    if not (tools_bd / "bd.exe").exists() and not (tools_bd / "bd").exists():
        return False, None
    packaged = _resource_at("scripts", "set_bd_path.ps1")
    if packaged is None:
        return False, None
    dest = project_root / "scripts" / "set_bd_path.ps1"
    if dest.exists():
        return False, None
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(packaged.read_bytes())
        return True, str(dest)
    except Exception as e:
        logger.debug("Could not install set_bd_path.ps1: %s", e)
        return False, None


# @note[2025-01-20]: Windows encoding workaround - handles UTF-8 BOM that Windows
# editors may add. This is required for cross-platform compatibility. See
# docs/architecture/coding-standards.md for Windows encoding requirements.
# @ai-dont-touch: This Windows encoding workaround is critical for cross-platform
# compatibility. Modifying this will break file reading on Windows systems that add
# UTF-8 BOM. See docs/architecture/coding-standards.md for complete Windows compatibility guidelines.

def normalize_config_encoding(file_path: Path) -> tuple[bool, str | None]:
    """
    Normalize encoding of a config file by removing UTF-8 BOM if present.
    
    On Windows, files may be saved with UTF-8 BOM (Byte Order Mark: \\xef\\xbb\\xbf)
    by editors like Notepad. This can cause JSON parsing failures. This function
    reads the file with utf-8-sig (which strips BOM) and rewrites with plain utf-8.
    
    Args:
        file_path: Path to the config file to normalize
        
    Returns:
        Tuple of (normalized, message) where:
        - normalized: True if file was modified, False if no changes needed
        - message: Description of what was done or None
    """
    if not file_path.exists():
        return False, None
    
    try:
        # Read with utf-8-sig to strip any BOM
        with open(file_path, encoding="utf-8-sig") as f:
            content = f.read()
        
        # Check if file had BOM by comparing raw bytes
        raw_bytes = file_path.read_bytes()
        has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
        
        if has_bom:
            # Rewrite without BOM using plain utf-8
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"Removed UTF-8 BOM from {file_path.name}"
        
        return False, None
    except Exception as e:
        logger.warning(f"Failed to normalize encoding for {file_path}: {e}")
        return False, None


def check_npx_available() -> tuple[bool, str | None]:
    """
    Check if npx is available.
    
    Returns:
        (available, error_message) tuple
    """
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, None
        else:
            return False, "npx command failed"
    except FileNotFoundError:
        return False, "npx not found (Node.js not installed)"
    except subprocess.TimeoutExpired:
        return False, "npx check timed out"
    except Exception as e:
        return False, str(e)


def validate_mcp_config(mcp_config_path: Path) -> dict[str, Any]:
    """
    Validate MCP configuration and return status.
    
    Args:
        mcp_config_path: Path to MCP config file
    
    Returns:
        {
            "valid": bool,
            "issues": list[str],
            "warnings": list[str],
            "recommendations": list[str]
        }
    """
    result: dict[str, Any] = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "recommendations": [],
    }
    
    # Check if file exists
    if not mcp_config_path.exists():
        result["valid"] = False
        result["issues"].append("MCP config file not found")
        return result
    
    # Load and validate JSON
    try:
        with open(mcp_config_path, encoding="utf-8-sig") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["issues"].append(f"Invalid JSON: {e}")
        return result
    except Exception as e:
        result["valid"] = False
        result["issues"].append(f"Failed to read config: {e}")
        return result
    
    # Check for Context7
    mcp_servers = config.get("mcpServers", {})
    if "Context7" in mcp_servers:
        context7_config = mcp_servers["Context7"]
        env_vars = context7_config.get("env", {})
        api_key_ref = env_vars.get("CONTEXT7_API_KEY", "")
        
        # Check if using environment variable reference
        if isinstance(api_key_ref, str) and api_key_ref.startswith("${") and api_key_ref.endswith("}"):
            var_name = api_key_ref[2:-1]  # Remove ${ and }
            if not os.getenv(var_name):
                result["valid"] = False
                result["issues"].append(
                    "CONTEXT7_API_KEY environment variable not set. "
                    "MCP server will not work without this."
                )
                result["recommendations"].append(
                    f"Set {var_name} environment variable or update MCP config with direct value"
                )
    
    # Check for GitHub MCP server
    if "GitHub" in mcp_servers:
        github_config = mcp_servers["GitHub"]
        env_vars = github_config.get("env", {})
        github_token = env_vars.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        
        # Check if token is set (either direct value or env var reference)
        if not github_token:
            result["warnings"].append(
                "GitHub MCP server configured but GITHUB_PERSONAL_ACCESS_TOKEN not set. "
                "GitHub MCP server will not work without a token."
            )
            result["recommendations"].append(
                "Set GITHUB_PERSONAL_ACCESS_TOKEN in GitHub MCP server env configuration"
            )
        elif isinstance(github_token, str) and github_token.startswith("${") and github_token.endswith("}"):
            # Using environment variable reference
            var_name = github_token[2:-1]  # Remove ${ and }
            if not os.getenv(var_name):
                result["warnings"].append(
                    f"GitHub MCP server uses {var_name} environment variable reference, but variable is not set. "
                    "GitHub MCP server will not work without this."
                )
                result["recommendations"].append(
                    f"Set {var_name} environment variable or update MCP config with direct token value"
                )
    
    # Check npx availability
    npx_available, npx_error = check_npx_available()
    if not npx_available:
        result["warnings"].append(
            f"npx not available ({npx_error}). "
            f"MCP servers that use npx will not work. "
            f"Install Node.js to enable MCP servers."
        )
        result["recommendations"].append("Install Node.js: https://nodejs.org/")
    
    return result


def merge_context7_into_mcp_config(mcp_config_path: Path) -> tuple[bool, str]:
    """
    Merge Context7 configuration into existing MCP config.
    
    Args:
        mcp_config_path: Path to MCP config file
    
    Returns:
        (merged, message) tuple
    """
    if not mcp_config_path.exists():
        return False, "MCP config file not found"
    
    try:
        with open(mcp_config_path, encoding="utf-8-sig") as f:
            config = json.load(f)
        
        mcp_servers = config.setdefault("mcpServers", {})
        
        # Check if Context7 already exists
        if "Context7" in mcp_servers:
            return False, "Context7 already configured"
        
        # Add Context7 configuration
        mcp_servers["Context7"] = {
            "command": "npx",
            "args": ["-y", "@context7/mcp-server"],
            "env": {
                "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
            }
        }
        
        # Write back
        with open(mcp_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
        
        return True, "Context7 configuration merged into existing MCP config"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in MCP config: {e}"
    except Exception as e:
        return False, f"Failed to merge: {e}"


def init_cursor_mcp_config(project_root: Path | None = None, overwrite: bool = False, merge: bool = True) -> tuple[bool, str | None, dict[str, Any] | None]:
    """
    Initialize `.cursor/mcp.json` with Context7 MCP server configuration.
    
    Creates a project-local MCP config file if it doesn't exist. If file exists
    and merge=True, merges Context7 into existing config. Never overwrites
    existing files unless overwrite=True. Uses environment variable references
    for API keys (no secrets embedded).
    
    Args:
        project_root: Project root directory (defaults to cwd)
        overwrite: If True, overwrite existing file (default: False)
        merge: If True and file exists, merge Context7 into existing config (default: True)
        
    Returns:
        Tuple of (created, path, validation) where:
        - created: True if file was created/merged, False if skipped
        - path: Path to mcp.json file or None if skipped
        - validation: Validation result dict or None
    """
    if project_root is None:
        project_root = Path.cwd()
    
    cursor_dir = project_root / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    
    mcp_config_file = cursor_dir / "mcp.json"
    
    # If file exists and not overwriting, try to merge if merge=True
    if mcp_config_file.exists() and not overwrite:
        if merge:
            merged, message = merge_context7_into_mcp_config(mcp_config_file)
            if merged:
                # Validate after merge
                validation = validate_mcp_config(mcp_config_file)
                return True, str(mcp_config_file), validation
            # Context7 already exists or merge failed
            validation = validate_mcp_config(mcp_config_file)
            return False, str(mcp_config_file), validation
        else:
            # Skip existing file
            validation = validate_mcp_config(mcp_config_file)
            return False, str(mcp_config_file), validation
    
    # Create MCP config with Context7 server
    mcp_config = {
        "mcpServers": {
            "Context7": {
                "command": "npx",
                "args": ["-y", "@context7/mcp-server"],
                "env": {
                    # Use environment variable reference - no secrets embedded
                    "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
                }
            }
        }
    }
    
    # Write config file
    try:
        mcp_config_file.write_text(
            json.dumps(mcp_config, indent=2) + "\n",
            encoding="utf-8"
        )
        # Validate after creation
        validation = validate_mcp_config(mcp_config_file)
        return True, str(mcp_config_file), validation
    except Exception as e:
        logger.warning(f"Failed to create MCP config: {e}")
        return False, None, None


def init_experts_scaffold(project_root: Path | None = None) -> dict[str, Any]:
    """
    Scaffold experts and RAG project files for business-domain experts.
    
    Creates:
    - `.tapps-agents/domains.md` - Business domains template
    - `.tapps-agents/experts.yaml` - Project experts configuration stub
    - `.tapps-agents/knowledge/` - Knowledge base directory structure
    - `.tapps-agents/knowledge/README.md` - Instructions for adding knowledge
    
    Note: Built-in technical experts are automatically loaded and don't need
    configuration. This scaffold is for project-specific business experts.
    
    Args:
        project_root: Project root directory (defaults to cwd)
        
    Returns:
        Dictionary with scaffold results:
        - created: List of created file paths
        - domains_md: Path to domains.md
        - experts_yaml: Path to experts.yaml
        - knowledge_dir: Path to knowledge directory
    """
    if project_root is None:
        project_root = Path.cwd()
    
    tapps_dir = project_root / ".tapps-agents"
    tapps_dir.mkdir(parents=True, exist_ok=True)
    
    results: dict[str, Any] = {
        "created": [],
        "domains_md": None,
        "experts_yaml": None,
        "knowledge_dir": None,
    }
    
    # Create domains.md template
    domains_file = tapps_dir / "domains.md"
    if not domains_file.exists():
        domains_content = """# Business Domains

This file maps your business domains to expert agents. Built-in technical experts
(python, fastapi, sqlalchemy, etc.) are automatically available and don't need
to be listed here.

## Domain to Expert Mapping

Add your business domains and their associated experts below:

```yaml
domains:
  e-commerce:
    experts:
      - expert-payment-processing
      - expert-inventory-management
    description: "E-commerce domain covering payments, inventory, and orders"
  
  analytics:
    experts:
      - expert-data-analysis
      - expert-reporting
    description: "Analytics and reporting domain"
```

## How It Works

1. **Built-in Technical Experts**: Automatically loaded based on your tech stack
   (detected from `requirements.txt`, `package.json`, etc.)

2. **Project Business Experts**: Configure in `.tapps-agents/experts.yaml`
   and add domain knowledge in `.tapps-agents/knowledge/<domain>/`

3. **Knowledge Base**: Add markdown files under `.tapps-agents/knowledge/<domain>/`
   to provide context for business-domain experts

## Next Steps

1. Edit `.tapps-agents/experts.yaml` to add your business experts
2. Add knowledge files in `.tapps-agents/knowledge/<domain>/`
3. Run `tapps-agents setup-experts add` for interactive configuration
"""
        domains_file.write_text(domains_content, encoding="utf-8")
        results["created"].append(str(domains_file))
    results["domains_md"] = str(domains_file)
    
    # Create experts.yaml stub
    experts_file = tapps_dir / "experts.yaml"
    if not experts_file.exists():
        experts_content = """# Project Business Experts Configuration

# Built-in technical experts are automatically loaded based on your tech stack.
# This file is for project-specific business-domain experts.

# Example expert configuration (commented out):
# experts:
#   - id: expert-payment-processing
#     name: Payment Processing Expert
#     description: "Expert in payment gateways, PCI compliance, and transaction processing"
#     knowledge_domains:
#       - payments
#       - compliance
#     priority: 0.9
#     enabled: true

# To add an expert, uncomment and modify the example above, or run:
#   tapps-agents setup-experts add

# For more information, see:
#   - .tapps-agents/domains.md (domain mapping)
#   - .tapps-agents/knowledge/README.md (knowledge base setup)
"""
        experts_file.write_text(experts_content, encoding="utf-8")
        results["created"].append(str(experts_file))
    results["experts_yaml"] = str(experts_file)
    
    # Create knowledge directory structure
    knowledge_dir = tapps_dir / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    results["knowledge_dir"] = str(knowledge_dir)
    
    # Create knowledge README
    knowledge_readme = knowledge_dir / "README.md"
    if not knowledge_readme.exists():
        readme_content = """# Knowledge Base

This directory contains domain-specific knowledge files for your business experts.

## Directory Structure

Organize knowledge by domain:

```
knowledge/
  payments/
    payment-gateways.md
    pci-compliance.md
  inventory/
    stock-management.md
    warehouse-operations.md
  analytics/
    reporting-requirements.md
    data-sources.md
```

## Adding Knowledge

1. Create a directory for each domain (e.g., `payments/`, `inventory/`)
2. Add markdown files with domain knowledge
3. Reference these domains in `.tapps-agents/experts.yaml`

## Knowledge File Format

Use standard markdown. Include:
- Domain concepts and terminology
- Business rules and constraints
- Integration patterns
- Common workflows
- Examples and use cases

## Example Knowledge File

```markdown
# Payment Processing Domain

## Overview
Our payment system integrates with Stripe and PayPal.

## Business Rules
- Minimum transaction amount: $0.50
- Maximum transaction amount: $10,000
- Refunds must be processed within 30 days

## Integration Points
- Stripe API for credit cards
- PayPal API for PayPal payments
- Internal accounting system for reconciliation
```

## How It's Used

Knowledge files are automatically indexed and made available to:
- Expert agents during code generation
- RAG (Retrieval-Augmented Generation) queries
- Context-aware code reviews and suggestions

For more information, see `.tapps-agents/domains.md`.
"""
        knowledge_readme.write_text(readme_content, encoding="utf-8")
        results["created"].append(str(knowledge_readme))
    
    # Optionally create a general knowledge example
    general_dir = knowledge_dir / "general"
    general_dir.mkdir(parents=True, exist_ok=True)
    general_example = general_dir / "project-overview.md"
    if not general_example.exists():
        example_content = """# Project Overview

Add general project knowledge here. This file serves as an example.

## Project Context

Describe your project's purpose, key features, and important context here.

## Key Concepts

- Concept 1: Description
- Concept 2: Description

## Important Notes

Add any important information that agents should know about your project.
"""
        general_example.write_text(example_content, encoding="utf-8")
        results["created"].append(str(general_example))
    
    return results


def init_tech_stack_config(
    project_root: Path | None = None,
    tech_stack: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """
    Initialize `.tapps-agents/tech-stack.yaml` with detected tech stack and expert priorities.

    If tech_stack is provided, uses it. Otherwise, detects tech stack from project.

    The config file structure:
    ```yaml
    frameworks:
      - FastAPI
      - React
    expert_priorities:
      expert-api-design: 1.0
      expert-observability: 0.9
      expert-performance: 0.8
    overrides:
      # User can override priorities here
      # expert-api-design: 0.8
    ```

    Args:
        project_root: Project root directory
        tech_stack: Optional pre-detected tech stack dict

    Returns:
        (created, path) tuple - created is True if file was created, False if updated
    """
    if project_root is None:
        project_root = Path.cwd()

    config_dir = project_root / ".tapps-agents"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "tech-stack.yaml"
    file_existed = config_file.exists()

    # Detect tech stack if not provided
    if tech_stack is None:
        tech_stack = detect_tech_stack(project_root)

    # Load existing config if it exists to preserve user overrides
    existing_config: dict[str, Any] = {}
    if file_existed:
        try:
            existing_content = config_file.read_text(encoding="utf-8")
            existing_config = yaml.safe_load(existing_content) or {}
        except Exception:
            # If parsing fails, start fresh
            existing_config = {}

    # Build config structure
    config: dict[str, Any] = {
        "frameworks": tech_stack.get("frameworks", []),
    }

    # Add expert priorities if available
    if tech_stack.get("expert_priorities"):
        # Merge with existing priorities, preserving user overrides
        default_priorities = tech_stack["expert_priorities"]
        existing_priorities = existing_config.get("expert_priorities", {})
        existing_overrides = existing_config.get("overrides", {})

        # Start with defaults, apply existing config, then apply overrides
        merged_priorities = default_priorities.copy()
        merged_priorities.update(existing_priorities)
        merged_priorities.update(existing_overrides)

        config["expert_priorities"] = merged_priorities

        # Preserve overrides section if it exists
        if existing_overrides:
            config["overrides"] = existing_overrides
    elif "expert_priorities" in existing_config:
        # Preserve existing priorities if no new ones detected
        config["expert_priorities"] = existing_config["expert_priorities"]
        if "overrides" in existing_config:
            config["overrides"] = existing_config["overrides"]

    # Write config file
    config_file.write_text(
        yaml.safe_dump(config, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    return not file_existed, str(config_file)


def detect_tech_stack(project_root: Path) -> dict[str, Any]:
    """
    Detect technology stack from project files.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with detected technologies and libraries
    """
    tech_stack: dict[str, Any] = {
        "languages": [],
        "frameworks": [],
        "libraries": set(),
        "package_managers": [],
        "detected_files": [],
    }

    # Python projects
    requirements_txt = project_root / "requirements.txt"
    if requirements_txt.exists():
        tech_stack["package_managers"].append("pip")
        tech_stack["languages"].append("python")
        tech_stack["detected_files"].append("requirements.txt")
        try:
            content = requirements_txt.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("git+") or line.startswith("http"):
                    continue
                match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if match:
                    lib_name = match.group(1).lower().replace("_", "-")
                    tech_stack["libraries"].add(lib_name)
        except Exception:
            pass

    pyproject_toml = project_root / "pyproject.toml"
    if pyproject_toml.exists():
        tech_stack["package_managers"].append("pip")
        tech_stack["languages"].append("python")
        tech_stack["detected_files"].append("pyproject.toml")
        try:
            content = pyproject_toml.read_text(encoding="utf-8")
            # Try to parse as TOML (simple regex-based extraction)
            deps_pattern = r'(?:dependencies|dev-dependencies)\s*=\s*\[(.*?)\]'
            matches = re.findall(deps_pattern, content, re.DOTALL)
            for match in matches:
                pkg_names = re.findall(r'["\']([^"\']+)["\']', match)
                for pkg_name in pkg_names:
                    tech_stack["libraries"].add(pkg_name.lower())
        except Exception:
            pass

    # Node.js/TypeScript projects
    package_json = project_root / "package.json"
    if package_json.exists():
        tech_stack["package_managers"].append("npm")
        tech_stack["languages"].append("javascript")
        tech_stack["detected_files"].append("package.json")
        try:
            with open(package_json, encoding="utf-8") as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}
                for dep_name in all_deps:
                    normalized = dep_name.replace("@types/", "").replace("@", "")
                    tech_stack["libraries"].add(normalized)
        except Exception:
            pass

    # Convert set to sorted list
    tech_stack["libraries"] = sorted(list(tech_stack["libraries"]))

    # Detect frameworks from libraries
    frameworks_map = {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "starlette": "Starlette",
        "react": "React",
        "vue": "Vue.js",
        "angular": "Angular",
        "next": "Next.js",
        "express": "Express",
        "nestjs": "NestJS",
    }

    for lib in tech_stack["libraries"]:
        lib_lower = lib.lower()
        for key, framework in frameworks_map.items():
            if key in lib_lower:
                if framework not in tech_stack["frameworks"]:
                    tech_stack["frameworks"].append(framework)

    # Add expert priorities based on detected frameworks
    if tech_stack["frameworks"]:
        expert_priorities = get_priorities_for_frameworks(tech_stack["frameworks"])
        if expert_priorities:
            tech_stack["expert_priorities"] = expert_priorities

    return tech_stack


def get_builtin_expert_libraries() -> list[str]:
    """
    Get libraries commonly used by built-in experts that should be pre-populated.

    Returns:
        List of library names used by built-in experts
    """
    expert_libraries = {
        # Security Expert
        "bandit",  # Security linter
        "safety",  # Dependency vulnerability scanner
        "cryptography",  # Cryptographic library
        "pyjwt",  # JWT handling
        "bcrypt",  # Password hashing
        # Performance Expert
        "cprofile",  # Profiling
        "memory-profiler",  # Memory profiling
        "line-profiler",  # Line-by-line profiling
        "cachetools",  # Caching utilities
        "diskcache",  # Disk-based caching
        # Testing Expert
        "pytest",  # Testing framework
        "pytest-cov",  # Coverage plugin
        "pytest-mock",  # Mocking plugin
        "pytest-asyncio",  # Async testing
        "coverage",  # Coverage analysis
        "unittest",  # Standard library testing
        "mock",  # Mocking library
        # Code Quality Expert
        "ruff",  # Fast linter
        "mypy",  # Type checker
        "pylint",  # Linter
        "black",  # Code formatter
        "radon",  # Complexity analysis
        # Database Expert
        "sqlalchemy",  # ORM
        "pymongo",  # MongoDB driver
        "psycopg2",  # PostgreSQL driver
        "redis",  # Redis client
        "sqlite3",  # SQLite (built-in, but docs available)
        # API Design Expert
        "fastapi",  # Web framework
        "flask",  # Web framework
        "django",  # Web framework
        "starlette",  # ASGI framework
        "httpx",  # HTTP client
        "requests",  # HTTP library
        "aiohttp",  # Async HTTP
        # Observability Expert
        "prometheus-client",  # Prometheus metrics
        "opentelemetry",  # Observability framework
        "structlog",  # Structured logging
        "sentry-sdk",  # Error tracking
        # Cloud Infrastructure Expert
        "boto3",  # AWS SDK
        "kubernetes",  # Kubernetes client
        "docker",  # Docker SDK
        # Data Processing (for various experts)
        "pandas",  # Data analysis
        "numpy",  # Numerical computing
        "pydantic",  # Data validation
        # CLI & Terminal (CLI Design Expert — Phase 1, 6)
        "click",  # CLI framework (used by tapps-agents)
        "rich",  # Terminal UI, tables, progress bars
        "typer",  # Modern CLI framework (Click-based)
        # Concurrency & Parallel Execution (Phase 3)
        "asyncio",  # Async/await concurrency (stdlib)
        "anyio",  # Async compatibility layer
        # Configuration & Serialization (Phase 1, 4, 6)
        "pyyaml",  # YAML parsing/generation
        "jsonschema",  # JSON Schema validation (Phase 7)
        "tomli",  # TOML parsing (pyproject.toml)
        # Graph Algorithms (Phase 3 — topological sort)
        "networkx",  # Graph library (topological sort, dependency resolution)
        # Template Rendering (Phase 4 — session handoff)
        "jinja2",  # Template engine
        # File System Monitoring
        "watchdog",  # File system monitoring
    }
    return sorted(list(expert_libraries))


def detect_mcp_servers(project_root: Path) -> dict[str, Any]:
    """
    Detect installed and configured EXTERNAL MCP servers.
    
    Note: This only checks for external MCP servers that need installation.
    Built-in MCP servers (Filesystem, Git, Analysis) are always available
    as part of the TappsCodingAgents framework and don't need detection.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with MCP server detection results
    """
    mcp_status: dict[str, Any] = {
        "note": "Checking external MCP servers only. Built-in servers (Filesystem, Git, Analysis) are always available.",
        "required_servers": [],
        "optional_servers": [],
        "detected_servers": [],
        "missing_servers": [],
        "configuration_files": [],
        "setup_instructions": {},
    }

    # Required MCP servers
    required_servers = {
        "Context7": {
            "name": "Context7 MCP Server",
            "package": "@context7/mcp-server",
            "command": "npx",
            "description": "Library documentation resolution and retrieval",
            "required": True,
        }
    }

    # Optional MCP servers
    optional_servers = {
        "Playwright": {
            "name": "Playwright MCP Server",
            # Support multiple package name variants - @playwright/mcp is the actual package,
            # @playwright/mcp-server was a previous/alternative name
            "packages": ["@playwright/mcp", "@playwright/mcp-server"],
            "command": "npx",
            "description": "Browser automation (optional, Cursor may provide this)",
            "required": False,
        },
        "GitHub": {
            "name": "GitHub MCP Server",
            "package": "@modelcontextprotocol/server-github",
            "command": "npx",
            "description": "GitHub repository operations (issues, PRs, code, etc.)",
            "required": False,
        }
    }

    all_servers = {**required_servers, **optional_servers}

    # Check for MCP configuration files
    mcp_config_paths = [
        project_root / ".cursor" / "mcp.json",
        project_root / ".vscode" / "mcp.json",
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / ".config" / "cursor" / "mcp.json",
    ]

    mcp_config = None
    for config_path in mcp_config_paths:
        if config_path.exists():
            mcp_status["configuration_files"].append(str(config_path))
            try:
                # Use utf-8-sig to automatically handle UTF-8 BOM (common on Windows)
                # This prevents JSON parsing failures when files have BOM prefix (\xef\xbb\xbf)
                with open(config_path, encoding="utf-8-sig") as f:
                    mcp_config = json.load(f)
                    break
            except Exception:
                pass

    # Check for npx (required for Context7 MCP server)
    npx_available = False
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        npx_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check each server
    for server_id, server_info in all_servers.items():
        detected = False
        reason = ""

        # Check if server is in MCP config
        if mcp_config:
            mcp_servers = mcp_config.get("mcpServers", {})
            # Check for exact server ID or name match
            if server_id in mcp_servers or server_info["name"] in mcp_servers:
                detected = True
                reason = "Configured in MCP settings"
            else:
                # Check all configured servers for matches
                for server_name, server_config in mcp_servers.items():
                    # Check for package name in args (npx format)
                    args = server_config.get("args", [])
                    # Support both single package and multiple package variants
                    packages_to_check = server_info.get("packages", [server_info.get("package")])
                    if isinstance(packages_to_check, str):
                        packages_to_check = [packages_to_check]
                    
                    # Check if any package variant is in args (including version suffixes like @0.0.35)
                    for pkg in packages_to_check:
                        if pkg and any(pkg in arg for arg in args):
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings (npx)"
                            break
                    if detected:
                        break
                    
                    # Check for URL-based configuration (Context7 can use URL format)
                    if server_id == "Context7":
                        url = server_config.get("url", "")
                        if url and ("context7.com" in url.lower() or "context7" in url.lower()):
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings (URL)"
                            break
                        
                        # Also check for Context7 in server name (case-insensitive)
                        if "context7" in server_name.lower():
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings"
                            break
                        
                        # Check headers for Context7 API key
                        headers = server_config.get("headers", {})
                        if "CONTEXT7_API_KEY" in headers or "context7" in str(headers).lower():
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings (with API key)"
                            break
                    
                    # Check for Playwright in server name (case-insensitive) - Cursor may provide natively
                    if server_id == "Playwright":
                        if "playwright" in server_name.lower():
                            detected = True
                            reason = f"Configured as '{server_name}' in MCP settings (may be Cursor native)"
                            break

        # Check environment variables for Context7
        if server_id == "Context7":
            if os.getenv("CONTEXT7_API_KEY"):
                detected = True
                reason = "API key found in environment"
            elif not npx_available:
                reason = "npx not available (required for installation)"

        if detected:
            mcp_status["detected_servers"].append(
                {
                    "id": server_id,
                    "name": server_info["name"],
                    "status": "installed",
                    "reason": reason,
                    "required": server_info["required"],
                }
            )
        else:
            # Get the primary package name (first from packages list or single package)
            packages = server_info.get("packages", [server_info.get("package")])
            primary_package = packages[0] if packages else server_info.get("package")
            
            status_entry = {
                "id": server_id,
                "name": server_info["name"],
                "status": "missing",
                "required": server_info["required"],
                "package": primary_package,
                "description": server_info["description"],
            }
            mcp_status["missing_servers"].append(status_entry)

            # Generate setup instructions
            if server_id == "Context7":
                mcp_status["setup_instructions"][server_id] = {
                    "method": "npx",
                    "steps": [
                        "1. Install Node.js and npm (if not already installed)",
                        "2. Configure Context7 MCP server in your MCP settings:",
                        "   Location: ~/.cursor/mcp.json or .cursor/mcp.json",
                        "   Configuration:",
                        "   {",
                        '     "mcpServers": {',
                        '       "Context7": {',
                        '         "command": "npx",',
                        '         "args": ["-y", "@context7/mcp-server"],',
                        '         "env": {',
                        '           "CONTEXT7_API_KEY": "your-api-key-here"',
                        "         }",
                        "       }",
                        "     }",
                        "   }",
                        "3. Set CONTEXT7_API_KEY environment variable:",
                        "   export CONTEXT7_API_KEY='your-api-key'",
                        "4. Restart Cursor/VS Code",
                    ],
                    "alternative": "Set CONTEXT7_API_KEY environment variable for direct API access",
                }
            elif server_id == "Playwright":
                mcp_status["setup_instructions"][server_id] = {
                    "method": "npx",
                    "steps": [
                        "1. Install Node.js and npm (if not already installed)",
                        "2. Configure Playwright MCP server in your MCP settings:",
                        "   Location: ~/.cursor/mcp.json or .cursor/mcp.json",
                        "   Configuration:",
                        "   {",
                        '     "mcpServers": {',
                        '       "Playwright": {',
                        '         "command": "npx",',
                        '         "args": ["-y", "@playwright/mcp-server"]',
                        "       }",
                        "     }",
                        "   }",
                        "3. Restart Cursor/VS Code",
                        "",
                        "Note: Playwright MCP is optional. Cursor may provide Playwright MCP natively.",
                        "If Playwright MCP is not configured, browser automation can still work via",
                        "the Python Playwright package (install with: pip install playwright).",
                    ],
                    "alternative": "Install Python Playwright package: pip install playwright && python -m playwright install",
                }

    # Categorize servers
    for server in mcp_status["detected_servers"] + mcp_status["missing_servers"]:
        if server["required"]:
            mcp_status["required_servers"].append(server)
        else:
            mcp_status["optional_servers"].append(server)

    return mcp_status


async def pre_populate_context7_cache(
    project_root: Path, libraries: list[str] | None = None
) -> dict[str, Any]:
    """
    Pre-populate Context7 cache with project dependencies.

    Args:
        project_root: Project root directory
        libraries: Optional list of libraries to cache (auto-detected if None)

    Returns:
        Dictionary with pre-population results
    """
    try:
        # Load API key from encrypted storage if not in environment
        # This ensures cache pre-population works even when run outside Cursor
        # #region agent log
        import json
        from datetime import datetime

        from tapps_agents.context7.commands import Context7Commands
        from tapps_agents.core.config import load_config
        try:
            log_path = project_root / ".cursor" / "debug.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "init_project.py:1026",
                    "message": "BEFORE API key check",
                    "data": {"env_key_exists": os.getenv("CONTEXT7_API_KEY") is not None, "project_root": str(project_root)},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except Exception as e: 
            import traceback
            try:
                log_path = project_root / ".cursor" / "debug.log"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "init_project.py:1026",
                        "message": "LOG ERROR",
                        "data": {"error": str(e), "traceback": traceback.format_exc()},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except OSError:  # Only catch file I/O errors, not KeyboardInterrupt/SystemExit
                pass
        # #endregion
        if not os.getenv("CONTEXT7_API_KEY"):
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "init_project.py:1027",
                        "message": "API key NOT in env, attempting load",
                        "data": {},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion
            try:
                from tapps_agents.context7.security import APIKeyManager
                api_key_manager = APIKeyManager()
                api_key = api_key_manager.load_api_key("context7")
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "E",
                            "location": "init_project.py:1030",
                            "message": "AFTER load_api_key",
                            "data": {"api_key_loaded": api_key is not None, "key_length": len(api_key) if api_key else 0},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + "\n")
                except: pass
                # #endregion
                if api_key:
                    os.environ["CONTEXT7_API_KEY"] = api_key
                    # #region agent log
                    try:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "A",
                                "location": "init_project.py:1032",
                                "message": "API key SET in os.environ",
                                "data": {"env_key_after_set": os.getenv("CONTEXT7_API_KEY") is not None, "key_length": len(api_key)},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + "\n")
                    except: pass
                    # #endregion
                    logger.debug("Loaded Context7 API key from encrypted storage")
            except Exception as e:
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "E",
                            "location": "init_project.py:1035",
                            "message": "EXCEPTION loading API key",
                            "data": {"error": str(e)},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + "\n")
                except: pass
                # #endregion
                logger.debug(f"Could not load API key from encrypted storage: {e}")
        else:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A",
                        "location": "init_project.py:1036",
                        "message": "API key already in env",
                        "data": {"key_length": len(os.getenv("CONTEXT7_API_KEY", ""))},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion

        # Load configuration
        try:
            # load_config expects None (auto-detect) or a Path to the config file, not project root
            # So we pass None and let it auto-detect from project_root
            config = load_config(None)
            if not config.context7 or not config.context7.enabled:
                return {
                    "success": False,
                    "error": "Context7 is not enabled in configuration",
                    "cached": 0,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading config: {e}",
                "cached": 0,
            }

        # Initialize Context7 commands
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "init_project.py:1056",
                    "message": "BEFORE Context7Commands init",
                    "data": {"env_key_at_init": os.getenv("CONTEXT7_API_KEY") is not None},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        context7_commands = Context7Commands(project_root=project_root, config=config)

        if not context7_commands.enabled:
            return {
                "success": False,
                "error": "Context7 is not enabled",
                "cached": 0,
            }

        # Try to initialize MCP Gateway for cache pre-population
        # Note: MCP Gateway is typically only available when running from Cursor
        # Cache pre-population will work best when run from within Cursor
        # But we'll try to use backup HTTP client if MCP is not available
        mcp_gateway = None
        try:
            from ..mcp.gateway import MCPGateway
            mcp_gateway = MCPGateway()
            context7_commands.set_mcp_gateway(mcp_gateway)
        except Exception:
            # MCP Gateway not available - will use backup HTTP client via backup_client module
            # The backup_client will handle fallback automatically
            pass

        # Try Context7 bundle copy when cache is empty (offline / no-API support)
        # When tapps-agents[context7-bundle] or tapps-agents-context7-bundle is installed
        try:
            from ..context7.bundle_loader import try_copy_context7_bundle

            kb_loc = None
            if config.context7:
                kb = getattr(config.context7, "knowledge_base", None)
                kb_loc = getattr(kb, "location", None) if kb else None
            cache_root = (
                (project_root / kb_loc)
                if isinstance(kb_loc, str)
                else project_root / ".tapps-agents" / "kb" / "context7-cache"
            )
            bundle_result = try_copy_context7_bundle(
                project_root=project_root, cache_root=cache_root
            )
            if bundle_result.get("success"):
                logger.info(
                    f"Context7 bundle copied ({bundle_result.get('copied', 0)} items) "
                    f"from {bundle_result.get('source', 'bundle')}"
                )
        except Exception as e:
            logger.debug(f"Context7 bundle copy skipped: {e}")

        # Auto-detect libraries if not provided
        project_libraries = []
        if libraries is None:
            tech_stack = detect_tech_stack(project_root)
            project_libraries = tech_stack["libraries"]
        else:
            project_libraries = libraries

        # Get built-in expert libraries
        expert_libraries = get_builtin_expert_libraries()

        # Combine project libraries with expert libraries (remove duplicates)
        all_libraries = sorted(list(set(project_libraries + expert_libraries)))

        if not all_libraries:
            return {
                "success": False,
                "error": "No libraries to cache",
                "cached": 0,
            }

        # Use CacheWarmer for staleness-aware pre-loading
        # CacheWarmer automatically checks staleness and skips fresh entries
        
        # Common topics to cache for popular libraries
        common_topics_map = {
            "fastapi": ["routing", "dependency-injection", "middleware", "errors"],
            "pytest": ["fixtures", "parametrize", "markers", "async"],
            "sqlalchemy": ["models", "queries", "sessions", "relationships"],
            "django": ["models", "views", "urls", "middleware"],
            "pydantic": ["models", "validation", "serialization"],
        }

        # Use CacheWarmer.warm_cache which checks staleness and skips fresh entries
        # Build list of libraries with their topics
        libraries_to_warm = []
        for library in all_libraries:
            lib_lower = library.lower()
            topics = None
            for key, topic_list in common_topics_map.items():
                if key in lib_lower:
                    topics = topic_list
                    break
            if topics:
                # Warm with specific topics
                for topic in topics:
                    libraries_to_warm.append((library, topic))
            else:
                # Warm with overview only
                libraries_to_warm.append((library, "overview"))
        
        # Warm cache using CacheWarmer (checks staleness automatically)
        # Process in batches to avoid overwhelming the API
        batch_size = 10
        success_count = 0
        fail_count = 0
        errors: list[str] = []
        
        for i in range(0, len(libraries_to_warm), batch_size):
            batch = libraries_to_warm[i:i + batch_size]
            for library, topic in batch:
                try:
                    # Use lookup which now has staleness checking
                    # CacheWarmer would be ideal but it processes libraries, not individual entries
                    # So we use cmd_docs which goes through lookup (now staleness-aware)
                    result = await context7_commands.cmd_docs(library, topic=topic)
                    if result.get("success"):
                        success_count += 1
                    else:
                        fail_count += 1
                        error_msg = result.get('error') or result.get('message') or 'Unknown error'
                        errors.append(f"{library}/{topic}: {error_msg}")
                except ImportError as e:
                    # Handle import errors from Context7 MCP server (known issue with library resolution)
                    fail_count += 1
                    if "attempted relative import" in str(e).lower():
                        # This is a Context7 MCP server issue, not our code - provide clear message
                        errors.append(
                            f"{library}/{topic}: Context7 MCP server import error (non-critical)"
                        )
                    else:
                        errors.append(f"{library}/{topic}: ImportError - {e!s}")
                except Exception as e:
                    fail_count += 1
                    errors.append(f"{library}/{topic}: Exception - {e!s}")

        # Determine overall error message
        error_msg = None
        if success_count == 0 and fail_count > 0:
            # All failed - check if it's because Context7 is unavailable
            # But first check if API key is actually available to avoid misleading error message
            api_key_available = os.getenv("CONTEXT7_API_KEY") is not None
            if not api_key_available:
                # Try loading from encrypted storage
                try:
                    from tapps_agents.context7.security import APIKeyManager
                    api_key_manager = APIKeyManager()
                    api_key_available = api_key_manager.load_api_key("context7") is not None
                except Exception:
                    pass
            
            # Check for import errors (Context7 MCP server issue)
            import_errors = [
                e for e in errors 
                if "import error" in e.lower() or "attempted relative import" in e.lower()
            ]
            if import_errors:
                error_msg = (
                    f"Context7 cache pre-population failed due to MCP server import issue (non-critical).\n"
                    f"All {fail_count} library lookups failed with: {errors[0]}\n"
                    f"This is a known issue with Context7 MCP server library resolution.\n"
                    f"Context7 will continue to work normally via on-demand lookups.\n"
                    f"To skip pre-population in future runs, use: --no-cache"
                )
            # Check for quota exceeded errors
            elif any("quota exceeded" in e.lower() or "429" in e for e in errors):
                quota_errors = [e for e in errors if "quota exceeded" in e.lower() or "429" in e]
                error_msg = f"Context7 API quota exceeded. {quota_errors[0]}. Cache pre-population requires available API quota. Consider upgrading your plan or running pre-population later."
            elif all("No documentation found in cache or API unavailable" in e for e in errors[:5]):
                if not api_key_available:
                    error_msg = "Context7 API unavailable: MCP Gateway not available and CONTEXT7_API_KEY not set. Cache pre-population requires either MCP Gateway (when running from Cursor) or CONTEXT7_API_KEY environment variable."
                else:
                    # API key is available but calls are still failing - different issue
                    error_msg = f"Context7 API calls failed despite API key being available. This may indicate API connectivity issues, invalid library names, or API rate limits. First error: {errors[0] if errors else 'Unknown error'}"
            elif errors:
                error_msg = f"All {fail_count} library lookups failed. First error: {errors[0]}"
        
        result = {
            "success": success_count > 0,
            "cached": success_count,
            "failed": fail_count,
            "total": len(all_libraries),
            "project_libraries": len(project_libraries),
            "expert_libraries": len(expert_libraries),
            "errors": errors[:10],  # Limit errors shown
        }
        
        if error_msg:
            result["error"] = error_msg
        
        return result

    except ImportError as e:
        return {
            "success": False,
            "error": f"Context7 module not available: {e}",
            "cached": 0,
        }
    except Exception as e:
        import traceback
        error_msg = str(e) or "Unknown error"
        # Provide more context for common errors
        if "MCP" in error_msg or "gateway" in error_msg.lower():
            error_msg = f"MCP Gateway not available: {error_msg}. Cache pre-population requires Context7 MCP server to be configured and running (typically available when running from Cursor)."
        return {
            "success": False,
            "error": f"Error during cache pre-population: {error_msg}",
            "cached": 0,
            "traceback": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None,
        }


def get_framework_version() -> str | None:
    """
    Get the current framework version from the installed package.
    
    Uses multiple fallback strategies to ensure version can be determined
    even in problematic editable install scenarios.
    
    Returns:
        Version string (e.g., "3.0.1") or None if version cannot be determined
    """
    # Strategy 1: Try direct import from package (most reliable for editable installs)
    try:
        from .. import __version__
        return __version__
    except (ImportError, AttributeError):
        pass
    
    # Strategy 2: Use importlib.metadata (works for installed packages)
    try:
        import importlib.metadata
        version = importlib.metadata.version("tapps-agents")
        return version
    except Exception:
        pass
    
    # Strategy 3: Try reading from __init__.py directly (last resort)
    try:
        import importlib.util
        import pathlib
        init_path = pathlib.Path(__file__).parent.parent / "__init__.py"
        if init_path.exists():
            spec = importlib.util.spec_from_file_location("tapps_agents_init", init_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                version = getattr(module, "__version__", None)
                if version:
                    return version
    except Exception:
        pass
    
    # All strategies failed
    logger.debug("Could not determine framework version")
    return None


def detect_existing_installation(project_root: Path) -> dict[str, Any]:
    """
    Detect if tapps-agents is already installed in the project.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Dictionary with detection results:
        - installed: bool - Whether installation detected
        - indicators: list[str] - What indicators were found
        - config_exists: bool
        - skills_exist: bool
        - rules_exist: bool
        - presets_exist: bool
    """
    result: dict[str, Any] = {
        "installed": False,
        "indicators": [],
        "config_exists": False,
        "skills_exist": False,
        "rules_exist": False,
        "presets_exist": False,
    }
    
    # Check for config file
    config_file = project_root / ".tapps-agents" / "config.yaml"
    if config_file.exists():
        result["config_exists"] = True
        result["indicators"].append(".tapps-agents/config.yaml")
        result["installed"] = True
    
    # Check for Skills directory with framework skills
    skills_dir = project_root / ".claude" / "skills"
    if skills_dir.exists():
        framework_skills_found = False
        for skill_name in FRAMEWORK_SKILLS:
            skill_path = skills_dir / skill_name
            if skill_path.exists() and skill_path.is_dir():
                framework_skills_found = True
                break
        if framework_skills_found:
            result["skills_exist"] = True
            result["indicators"].append(".claude/skills/ (framework skills)")
            result["installed"] = True
    
    # Check for Cursor Rules directory with framework rules
    rules_dir = project_root / ".cursor" / "rules"
    if rules_dir.exists():
        framework_rules_found = False
        for rule_name in FRAMEWORK_CURSOR_RULES:
            rule_path = rules_dir / rule_name
            if rule_path.exists():
                framework_rules_found = True
                break
        if framework_rules_found:
            result["rules_exist"] = True
            result["indicators"].append(".cursor/rules/ (framework rules)")
            result["installed"] = True
    
    # Check for workflow presets directory with framework presets
    presets_dir = project_root / "workflows" / "presets"
    if presets_dir.exists():
        framework_presets_found = False
        for preset_name in FRAMEWORK_WORKFLOW_PRESETS:
            preset_path = presets_dir / preset_name
            if preset_path.exists():
                framework_presets_found = True
                break
        if framework_presets_found:
            result["presets_exist"] = True
            result["indicators"].append("workflows/presets/ (framework presets)")
            result["installed"] = True
    
    
    return result


def _validate_packaged_presets(project_root: Path) -> tuple[bool, list[str]]:
    """
    Validate packaged workflow presets parse correctly (P2a: pre-reset validation).

    Returns:
        (all_valid, list of error messages)
    """
    errors: list[str] = []
    preset_items: list[tuple[str, Any]] = []
    packaged = _resource_at("workflows", "presets")
    if packaged is not None and packaged.is_dir():
        for p in packaged.iterdir():
            name = getattr(p, "name", "")
            if name.endswith(".yaml") and name in FRAMEWORK_WORKFLOW_PRESETS:
                preset_items.append((name, p))
    else:
        current_file = Path(__file__)
        framework_root = current_file.parent.parent.parent
        presets_dir = framework_root / "workflows" / "presets"
        if presets_dir.exists():
            for path in presets_dir.glob("*.yaml"):
                if path.name in FRAMEWORK_WORKFLOW_PRESETS:
                    preset_items.append((path.name, path))
    if not preset_items:
        return True, []
    try:
        from tapps_agents.workflow.parser import WorkflowParser

        parser = WorkflowParser()
        for name, item in preset_items:
            try:
                if hasattr(item, "read_bytes"):
                    content = item.read_bytes()
                    parser.parse_yaml(content.decode("utf-8"), file_path=Path(name))
                elif isinstance(item, Path) and item.exists():
                    parser.parse_file(item)
            except Exception as e:
                errors.append(f"{name}: {e}")
    except ImportError:
        return True, []
    return len(errors) == 0, errors


def identify_framework_files(project_root: Path) -> dict[str, Any]:
    """
    Identify framework-managed files vs user-added files.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Dictionary with:
        - framework_files: list[Path] - Files to reset
        - user_files: list[Path] - Files to preserve
        - custom_skills: list[str] - Custom skill names
        - custom_rules: list[str] - Custom rule names
        - custom_presets: list[str] - Custom preset names
    """
    result: dict[str, Any] = {
        "framework_files": [],
        "user_files": [],
        "custom_skills": [],
        "custom_rules": [],
        "custom_presets": [],
    }
    
    # Identify framework Cursor Rules
    rules_dir = project_root / ".cursor" / "rules"
    if rules_dir.exists():
        for rule_file in rules_dir.glob("*.mdc"):
            if rule_file.name in FRAMEWORK_CURSOR_RULES:
                result["framework_files"].append(rule_file)
            else:
                result["custom_rules"].append(rule_file.name)
                result["user_files"].append(rule_file)
    
    # Identify framework Skills
    skills_dir = project_root / ".claude" / "skills"
    if skills_dir.exists():
        for skill_dir_item in skills_dir.iterdir():
            if skill_dir_item.is_dir():
                if skill_dir_item.name in FRAMEWORK_SKILLS:
                    # Add all files in framework skill directory
                    for skill_file in skill_dir_item.rglob("*"):
                        if skill_file.is_file():
                            result["framework_files"].append(skill_file)
                else:
                    result["custom_skills"].append(skill_dir_item.name)
                    result["user_files"].append(skill_dir_item)
    
    # Identify framework workflow presets
    presets_dir = project_root / "workflows" / "presets"
    if presets_dir.exists():
        for preset_file in presets_dir.glob("*.yaml"):
            if preset_file.name in FRAMEWORK_WORKFLOW_PRESETS:
                result["framework_files"].append(preset_file)
            else:
                result["custom_presets"].append(preset_file.name)
                result["user_files"].append(preset_file)
    
    # Framework .cursorignore (will be merged, not replaced)
    cursorignore_file = project_root / ".cursorignore"
    if cursorignore_file.exists():
        # Check if it contains framework patterns (heuristic)
        try:
            content = cursorignore_file.read_text(encoding="utf-8")
            if ".tapps-agents" in content or "worktrees" in content:
                result["framework_files"].append(cursorignore_file)
        except Exception:
            pass
    
    # Framework MCP config (optional, only if framework-managed)
    mcp_file = project_root / ".cursor" / "mcp.json"
    if mcp_file.exists():
        # Check if it's framework-managed (contains Context7 config)
        try:
            content = mcp_file.read_text(encoding="utf-8")
            if "Context7" in content or "context7" in content.lower():
                result["framework_files"].append(mcp_file)
        except Exception:
            pass
    
    return result


def create_backup(
    project_root: Path,
    framework_files: list[Path],
    version_before: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """
    Create a backup of files that will be reset.
    
    Args:
        project_root: Project root directory
        framework_files: List of framework files to backup
        version_before: Framework version before reset
        
    Returns:
        Tuple of (backup_path, manifest_dict)
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_id = f"init-reset-{timestamp}"
    backup_dir = project_root / ".tapps-agents" / "backups" / backup_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    manifest: dict[str, Any] = {
        "backup_id": backup_id,
        "timestamp": datetime.now().isoformat(),
        "framework_version_before": version_before,
        "framework_version_after": None,  # Will be set after reset
        "files": [],
        "preserved": [],
    }
    
    # Backup framework files (P0b: existence check before operations)
    for file_path in framework_files:
        try:
            if not file_path.exists():
                continue  # Already gone, skip
            # Calculate relative path from project root
            rel_path = file_path.relative_to(project_root)
            backup_path = backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            elif file_path.is_dir():
                shutil.copytree(file_path, backup_path, dirs_exist_ok=True)

            manifest["files"].append({
                "original_path": str(rel_path),
                "backup_path": str(backup_path.relative_to(backup_dir)),
                "action": "reset",
            })
        except FileNotFoundError:
            pass  # File disappeared, skip
        except Exception as e:
            logger.warning(f"Failed to backup {file_path}: {e}")
    
    # Save manifest
    manifest_path = backup_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    return backup_dir, manifest


def cleanup_framework_files(
    project_root: Path,
    framework_files: list[Path],
    reset_mcp: bool = False,
) -> list[str]:
    """
    Clean up (delete) framework-managed files.
    
    Args:
        project_root: Project root directory
        framework_files: List of framework files to delete
        reset_mcp: Whether to reset MCP config
        
    Returns:
        List of deleted file paths (as strings)
    """
    deleted: list[str] = []
    
    for file_path in framework_files:
        # Skip MCP config unless explicitly requested
        if file_path.name == "mcp.json" and not reset_mcp:
            continue
        
        try:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                    deleted.append(str(file_path.relative_to(project_root)))
                elif file_path.is_dir():
                    if _safe_rmtree(file_path):
                        deleted.append(str(file_path.relative_to(project_root)))
                    else:
                        logger.warning(
                            "Could not delete %s (access denied, skip)",
                            file_path.relative_to(project_root),
                        )
        except FileNotFoundError:
            pass  # Already gone
        except Exception as e:
            logger.warning(f"Failed to delete {file_path}: {e}")
    
    return deleted


def rollback_init_reset(project_root: Path, backup_path: Path) -> dict[str, Any]:
    """
    Rollback an init reset from a backup.
    
    Args:
        project_root: Project root directory
        backup_path: Path to backup directory
        
    Returns:
        Dictionary with rollback results
    """
    result: dict[str, Any] = {
        "success": False,
        "restored_files": [],
        "errors": [],
    }
    
    # Load manifest
    manifest_path = backup_path / "manifest.json"
    if not manifest_path.exists():
        result["errors"].append("Manifest file not found in backup")
        return result
    
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        result["errors"].append(f"Failed to load manifest: {e}")
        return result
    
    # Restore files
    for file_info in manifest.get("files", []):
        try:
            original_rel = file_info["original_path"]
            backup_rel = file_info["backup_path"]
            
            original_path = project_root / original_rel
            backup_file_path = backup_path / backup_rel
            
            if backup_file_path.exists():
                original_path.parent.mkdir(parents=True, exist_ok=True)
                if backup_file_path.is_file():
                    shutil.copy2(backup_file_path, original_path)
                elif backup_file_path.is_dir():
                    if original_path.exists():
                        _safe_rmtree(original_path)
                    shutil.copytree(backup_file_path, original_path)
                
                result["restored_files"].append(original_rel)
        except Exception as e:
            result["errors"].append(f"Failed to restore {file_info.get('original_path', 'unknown')}: {e}")
    
    result["success"] = len(result["errors"]) == 0
    return result


def _detect_claude_code() -> bool:
    """Detect if Claude Code CLI is available."""
    import shutil
    return shutil.which("claude") is not None


def _init_claude_code_settings(
    project_root: Path, results: dict[str, Any], reset_mode: bool
) -> None:
    """Phase 7.8: Create .claude/settings.json and settings.local.json.example."""
    settings_path = project_root / ".claude" / "settings.json"
    local_example = project_root / ".claude" / "settings.local.json.example"
    agents_dir = project_root / ".claude" / "agents"

    claude_available = _detect_claude_code()
    results["claude_code_available"] = claude_available

    # Create settings.json by default when .claude/ exists (e.g. after skills install),
    # so Cursor+Claude users get tapps-agents in the allow list without manual setup.
    # Do not overwrite on reset — user data.
    if not settings_path.exists():
        import json as _json
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {
            "$schema": "https://json.schemastore.org/claude-code-settings.json",
            "permissions": {
                "allow": [
                    "Read",
                    "Grep",
                    "Glob",
                    "Bash(tapps-agents:*)",
                    "Bash(tapps-agents *)",
                    "Bash(python -m tapps_agents *)",
                    "Bash(pytest *)",
                    "Bash(ruff *)",
                    "Bash(mypy *)",
                    "Bash(bd *)",
                    "Bash(git diff *)",
                    "Bash(git log *)",
                    "Bash(git status *)",
                ],
                "deny": [
                    "Read(./.env)",
                    "Read(./.env.*)",
                    "Read(./secrets/**)",
                ],
            },
            "env": {
                "TAPPS_AGENTS_MODE": "claude-code",
                "CONTEXT7_KB_CACHE": ".tapps-agents/kb/context7-cache",
            },
            "enableAllProjectMcpServers": True,
        }
        settings_path.write_text(
            _json.dumps(settings, indent=2), encoding="utf-8"
        )
        results["claude_code_settings"] = True
        logger.info("Created .claude/settings.json")

    # Create settings.local.json.example (always reset)
    if not local_example.exists() or reset_mode:
        import json as _json
        example = {
            "$schema": "https://json.schemastore.org/claude-code-settings.json",
            "env": {
                "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
                "ANTHROPIC_API_KEY": "sk-ant-...",
            },
            "permissions": {
                "defaultMode": "acceptEdits",
            },
        }
        local_example.write_text(
            _json.dumps(example, indent=2), encoding="utf-8"
        )

    # Ensure .gitignore entries
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        additions = []
        for entry in [".claude/settings.local.json", ".claude/agent-memory/", ".claude/agent-memory-local/"]:
            if entry not in content:
                additions.append(entry)
        if additions:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write("\n# Claude Code local settings\n")
                for a in additions:
                    f.write(f"{a}\n")


def _init_experts_available_rule(project_root: Path, results: dict[str, Any]) -> None:
    """Phase 8.1: Generate .cursor/rules/experts-available.mdc dynamically."""
    import yaml as _yaml

    rule_path = project_root / ".cursor" / "rules" / "experts-available.mdc"
    rule_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect experts from experts.yaml
    experts_yaml = project_root / ".tapps-agents" / "experts.yaml"
    expert_rows: list[str] = []
    if experts_yaml.exists():
        try:
            data = _yaml.safe_load(experts_yaml.read_text(encoding="utf-8")) or {}
            for name, config in data.items():
                if isinstance(config, dict):
                    domain = config.get("domain", "general")
                    triggers = ", ".join(config.get("triggers", [])[:5])
                    kf = len(config.get("knowledge_files", []))
                    expert_rows.append(f"| {name} | {domain} | {triggers} | {kf} |")
        except Exception:
            pass

    # Collect cached libraries
    cache_dir = project_root / ".tapps-agents" / "kb" / "context7-cache"
    if not cache_dir.exists():
        cache_dir = project_root / ".tapps-agents" / "context7-docs"
    cached_libs: list[str] = []
    if cache_dir.exists():
        for f in sorted(cache_dir.glob("*.json")):
            cached_libs.append(f.stem)

    # Generate rule content
    lines = [
        "---",
        "description: Available experts and cached libraries (auto-generated by init)",
        "globs: []",
        "alwaysApply: true",
        "---",
        "",
        "# Available Experts",
        "",
        "## How to Consult Experts",
        "",
        "Use `@expert *list` to see all available experts.",
        "Use `@expert *consult \"<question>\" --domain <domain>` for domain expert knowledge.",
        "Use `@expert *cached` to list cached library documentation.",
        "CLI: `tapps-agents expert list|consult|info|search|cached`",
        "",
    ]

    if expert_rows:
        lines.extend([
            "## Configured Experts",
            "",
            "| Expert | Domain | Triggers | Knowledge Files |",
            "|--------|--------|----------|-----------------|",
            *expert_rows,
            "",
        ])
    else:
        lines.extend([
            "## Configured Experts",
            "",
            "No project experts configured. Run `tapps-agents setup-experts init` to auto-generate.",
            "",
        ])

    if cached_libs:
        lines.extend([
            "## Context7 Cached Libraries",
            "",
            f"The following libraries have cached documentation: {', '.join(cached_libs[:30])}",
            "",
        ])

    rule_path.write_text("\n".join(lines), encoding="utf-8")
    results["experts_available_rule"] = True
    logger.info("Generated .cursor/rules/experts-available.mdc")


def init_project(
    project_root: Path | None = None,
    include_cursor_rules: bool = True,
    include_workflow_presets: bool = True,
    include_config: bool = True,
    include_skills: bool = True,
    include_cursorignore: bool = True,
    pre_populate_cache: bool = True,
    reset_mode: bool = False,
    backup_before_reset: bool = True,
    reset_mcp: bool = False,
    preserve_custom: bool = True,
    include_hooks_templates: bool = False,
    auto_experts: bool = False,
    use_enhanced_detection: bool = True,
):
    """
    Initialize a new project with TappsCodingAgents setup.

    Args:
        project_root: Project root directory (defaults to cwd)
        include_cursor_rules: Whether to copy Cursor Rules
        include_workflow_presets: Whether to copy workflow presets
        include_config: Whether to create project config
        include_skills: Whether to install Cursor Skills
        include_cursorignore: Whether to install .cursorignore file
        pre_populate_cache: Whether to pre-populate Context7 cache with detected tech stack
        reset_mode: Whether to reset framework-managed files (upgrade mode)
        backup_before_reset: Whether to create backup before reset (default: True)
        reset_mcp: Whether to reset MCP config (default: False)
        preserve_custom: Whether to preserve custom Skills, Rules, and presets (default: True)
        include_hooks_templates: If True, create hooks.yaml from templates and .tapps-agents/context/
            (init --hooks). If False, create minimal empty hooks.yaml (standard init).
        auto_experts: Whether to auto-generate experts from knowledge base (Phase 3)
        use_enhanced_detection: Whether to use enhanced tech stack detection from init_autofill module

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
        "customizations": False,
        "cursorignore": False,
        "tech_stack": None,
        "cache_prepopulated": False,
        "files_created": [],
        "reset_mode": reset_mode,
        "backup_path": None,
        "files_reset": [],
        "files_preserved": [],
        "custom_skills_preserved": [],
        "custom_rules_preserved": [],
        "custom_presets_preserved": [],
        "version_before": None,
        "version_after": None,
        "hooks": False,
        "hooks_templates": False,
    }
    
    # Handle reset mode
    if reset_mode:
        # P2a: Pre-reset preset validation - catch schema issues before destructive ops
        valid, preset_errors = _validate_packaged_presets(project_root)
        if not valid and preset_errors:
            logger.warning(
                "Packaged workflow presets have validation errors (will overwrite): %s",
                "; ".join(preset_errors[:3]),
            )

        # Get version before reset
        version_before = get_framework_version()
        results["version_before"] = version_before

        # Detect existing installation
        detection = detect_existing_installation(project_root)
        if not detection["installed"]:
            logger.info("Reset mode requested but no existing installation detected. Proceeding with normal init.")
        else:
            # Identify framework vs project files
            file_identification = identify_framework_files(project_root)
            # framework_files is already a list of Path objects
            framework_files = file_identification.get("framework_files", [])
            
            # Store preserved customizations
            results["custom_skills_preserved"] = file_identification.get("custom_skills", [])
            results["custom_rules_preserved"] = file_identification.get("custom_rules", [])
            results["custom_presets_preserved"] = file_identification.get("custom_presets", [])
            results["files_preserved"] = [str(f.relative_to(project_root)) for f in file_identification.get("user_files", [])]
            
            # Create backup if requested
            if backup_before_reset:
                try:
                    backup_dir, manifest = create_backup(project_root, framework_files, version_before)
                    results["backup_path"] = str(backup_dir.relative_to(project_root))
                    logger.info(f"Backup created at: {results['backup_path']}")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
                    if not backup_before_reset:  # Only warn if backup was requested
                        raise
            
            # Cleanup framework files
            deleted = cleanup_framework_files(project_root, framework_files, reset_mcp=reset_mcp)
            results["files_reset"] = deleted
            logger.info(f"Reset {len(deleted)} framework files")
    
    # Get version after reset (will be updated after init completes)
    version_after = get_framework_version()
    results["version_after"] = version_after

    # --- Step order (dependencies): tech_stack -> config -> MCP -> presets -> rules
    # -> skills -> customizations -> cursorignore -> tech_stack_config -> experts
    # -> cache (best-effort, non-blocking) -> validation
    # Presets before rules so workflow-presets.mdc can be generated from YAML (critical after reset).

    # Detect tech stack early (needed for template application)
    if use_enhanced_detection:
        logger.info("Using enhanced tech stack detection from init_autofill module")
        tech_stack_result = detect_tech_stack_enhanced(
            project_root=project_root,
            generate_yaml=True,  # Generate tech-stack.yaml for Phase 2
        )
        if tech_stack_result["success"]:
            tech_stack = {
                "languages": tech_stack_result["languages"],
                "libraries": tech_stack_result["libraries"],
                "frameworks": tech_stack_result["frameworks"],
                "domains": tech_stack_result["domains"],
            }
            results["tech_stack_yaml"] = tech_stack_result.get("tech_stack_yaml")
            logger.info(f"Enhanced detection: {len(tech_stack['languages'])} languages, "
                       f"{len(tech_stack['libraries'])} libraries, "
                       f"{len(tech_stack['frameworks'])} frameworks")
        else:
            logger.warning(f"Enhanced tech stack detection failed: {tech_stack_result.get('error')}. "
                          "Falling back to simple detection.")
            tech_stack = detect_tech_stack(project_root)
    else:
        tech_stack = detect_tech_stack(project_root)

    results["tech_stack"] = tech_stack
    
    # Initialize project config (with template application)
    if include_config:
        success, config_path, template_info = init_project_config(
            project_root, tech_stack=tech_stack, apply_template=True
        )
        results["config"] = success
        if config_path:
            results["files_created"].append(config_path)
        if template_info:
            # template_info is combined_info: {tech_stack_template, project_type_template}
            ts = template_info.get("tech_stack_template") or {}
            pt = template_info.get("project_type_template") or {}
            results["template_combined_info"] = template_info
            results["template_applied"] = bool(ts.get("applied") or pt.get("applied"))
            # Prefer tech-stack name; fallback to project-type
            results["template_name"] = ts.get("template_name") or (str(pt.get("project_type")) if pt.get("project_type") else None)
            results["template_reason"] = ts.get("reason") or pt.get("reason")

    # Initialize MCP config (project-local) — early so MCP validation surfaces before rules/presets/skills
    mcp_created, mcp_path, mcp_validation = init_cursor_mcp_config(
        project_root,
        overwrite=reset_mcp,
        merge=True
    )
    npx_available, npx_error = check_npx_available()
    results["mcp_config"] = {
        "created": mcp_created,
        "path": mcp_path,
        "validation": mcp_validation,
        "npx_available": npx_available,
        "npx_error": npx_error,
    }
    if mcp_path:
        results["files_created"].append(mcp_path)
    mcp_config_file = project_root / ".cursor" / "mcp.json"
    if mcp_config_file.exists():
        normalized, normalize_msg = normalize_config_encoding(mcp_config_file)
        if normalized:
            results["mcp_encoding_normalized"] = normalize_msg
            logger.info(normalize_msg)
    project_config_file = project_root / ".tapps-agents" / "config.yaml"
    if project_config_file.exists():
        normalized, normalize_msg = normalize_config_encoding(project_config_file)
        if normalized:
            results["config_encoding_normalized"] = normalize_msg
            logger.info(normalize_msg)
    mcp_status = detect_mcp_servers(project_root)
    results["mcp_servers"] = mcp_status
    if mcp_created and mcp_path:
        mcp_status["project_local_config"] = mcp_path
        mcp_status["note"] = "Project-local `.cursor/mcp.json` was created. Context7 MCP server configured."

    # Initialize workflow presets before Cursor Rules so workflow-presets.mdc can be
    # generated from YAML (required after init --reset when presets were just restored).
    if include_workflow_presets:
        success, preset_files = init_workflow_presets(project_root)
        results["workflow_presets"] = success
        if preset_files:
            results["files_created"].extend(
                [f"workflows/presets/{f}" for f in preset_files]
            )

    # Initialize Cursor Rules (depends on workflows/presets/*.yaml for workflow-presets.mdc)
    if include_cursor_rules:
        success, rule_paths = init_cursor_rules(project_root)
        results["cursor_rules"] = success
        if rule_paths:
            results["files_created"].extend(rule_paths)

    # Initialize Skills for Cursor/Claude
    if include_skills:
        success, copied_skills = init_claude_skills(project_root)
        results["skills"] = success
        if copied_skills:
            results["files_created"].extend(copied_skills)
        
        # Load and register custom Skills
        try:
            from .skill_loader import initialize_skill_registry
            registry = initialize_skill_registry(project_root=project_root)
            custom_skills = registry.get_custom_skills()
            if custom_skills:
                results["custom_skills"] = [skill.name for skill in custom_skills]
                results["custom_skills_count"] = len(custom_skills)
        except Exception as e:
            # Non-fatal: custom Skills loading failed, but built-in Skills still work
            results["custom_skills_error"] = str(e)
    
    # Initialize Claude Desktop Commands (works alongside Skills)
    if include_skills:  # Commands are installed with Skills
        success, copied_commands = init_claude_commands(project_root)
        results["claude_commands"] = success
        if copied_commands:
            results["files_created"].extend(copied_commands)
        # Initialize Cursor slash commands (Import Claude Commands also loads .cursor/commands)
        success, copied = init_cursor_commands(project_root)
        results["cursor_commands"] = success
        if copied:
            results["files_created"].extend(copied)

    # Initialize customizations directory
    success, customizations_path = init_customizations_directory(project_root)
    results["customizations"] = success
    if customizations_path:
        results["files_created"].append(customizations_path)

    # Initialize .cursorignore file
    if include_cursorignore:
        success, ignore_path = init_cursorignore(project_root)
        results["cursorignore"] = success
        if ignore_path:
            results["files_created"].append(ignore_path)

    # Initialize hooks: minimal empty hooks.yaml (standard init) or from templates + context (init --hooks)
    if include_hooks_templates:
        hooks_created, hooks_path, context_created, hooks_files = init_hooks_and_context(project_root)
        results["hooks"] = hooks_created
        results["hooks_templates"] = True
        results["context_created"] = context_created
        if hooks_files:
            results["files_created"].extend(hooks_files)
    else:
        success, hooks_path = init_hooks_minimal(project_root)
        results["hooks"] = success
        if success and hooks_path:
            results["files_created"].append(".tapps-agents/hooks.yaml")

    # Phase 1.1: Create .tapps-agents/epic-state/ directory
    epic_state_dir = project_root / ".tapps-agents" / "epic-state"
    epic_state_dir.mkdir(parents=True, exist_ok=True)
    results["epic_state_dir"] = True

    # Phase 7.8: Claude Code settings configuration
    _init_claude_code_settings(project_root, results, reset_mode)

    # Phase 8.1: Generate experts-available.mdc rule
    _init_experts_available_rule(project_root, results)

    # If tools/bd exists, ensure scripts/set_bd_path.ps1 (do not overwrite)
    set_bd_installed, set_bd_path = _ensure_set_bd_path_script(project_root)
    results["set_bd_path_installed"] = set_bd_installed
    if set_bd_path:
        try:
            rel = str(Path(set_bd_path).relative_to(project_root))
        except ValueError:
            rel = set_bd_path
        results["files_created"].append(rel)

    # Tech stack already detected above, use it for tech stack config

    # Initialize tech stack config with expert priorities
    success, tech_stack_path = init_tech_stack_config(project_root, tech_stack)
    results["tech_stack_config"] = success
    if tech_stack_path:
        results["files_created"].append(tech_stack_path)

    # Scaffold experts and RAG files
    experts_scaffold = init_experts_scaffold(project_root)
    results["experts_scaffold"] = experts_scaffold
    if experts_scaffold.get("created"):
        results["files_created"].extend(experts_scaffold["created"])

    # Auto-generate experts from knowledge base (Phase 3.1)
    if auto_experts:
        logger.info("Auto-generating experts from knowledge base (Phase 3.1)")
        try:
            from .init_autofill import generate_experts_from_knowledge

            expert_result = generate_experts_from_knowledge(
                project_root=project_root,
                auto_mode=True,  # Non-interactive
                skip_existing=True,  # Don't overwrite existing experts
            )

            results["auto_experts"] = expert_result
            if expert_result["success"]:
                logger.info(f"Generated {expert_result['generated']} experts, "
                           f"skipped {expert_result['skipped']} existing experts")
            else:
                logger.warning(f"Expert auto-generation failed: {expert_result.get('error')}")
        except Exception as e:
            logger.error(f"Failed to auto-generate experts: {e}")
            results["auto_experts"] = {
                "success": False,
                "error": str(e),
            }

    # Defer cache pre-population to CLI so core init completes first and cache runs
    # after "Init complete" (non-blocking from the user's view of core success).
    if pre_populate_cache:
        results["cache_requested"] = True
        results["cache_libraries"] = tech_stack.get("libraries", [])

    # Validate setup using comprehensive verification
    try:
        from .cursor_verification import verify_cursor_integration

        is_valid, verification_results = verify_cursor_integration(project_root)
        results["validation"] = {
            "overall_valid": is_valid,
            "verification_results": verification_results,
            "errors": verification_results.get("errors", []),
            "warnings": verification_results.get("warnings", []),
        }
        # Also include component-level results for backward compatibility
        if "components" in verification_results:
            results["validation"]["cursor_rules"] = verification_results["components"].get("rules", {})
            results["validation"]["claude_skills"] = verification_results["components"].get("skills", {})
            results["validation"]["cursorignore"] = verification_results["components"].get("cursorignore", {})
    except Exception as e:
        results["validation_error"] = str(e)
    
    # Update version tracking and backup manifest if in reset mode
    if reset_mode and results.get("backup_path"):
        try:
            version_after = get_framework_version()
            results["version_after"] = version_after
            
            # Update backup manifest with version_after
            backup_dir = project_root / results["backup_path"]
            manifest_path = backup_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["framework_version_after"] = version_after
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to update backup manifest: {e}")
    
    # Store framework version for future reference
    try:
        version_file = project_root / ".tapps-agents" / ".framework-version"
        current_version = get_framework_version()
        if current_version:
            version_file.write_text(current_version, encoding="utf-8")
    except Exception as e:
        logger.debug(f"Failed to store framework version: {e}")

    return results
