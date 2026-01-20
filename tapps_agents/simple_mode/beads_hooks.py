"""
Optional Beads (bd) hooks for Simple Mode *build and *fix: create at start, close at end.

Used only when config.beads.enabled and config.beads.hooks_simple_mode are true
and bd is available. On failures we log and continue (no raise).
"""

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from ..beads import is_available, run_bd

if TYPE_CHECKING:
    from ..core.config import ProjectConfig

logger = logging.getLogger(__name__)

_BD_ID_PATTERN = re.compile(r"([A-Za-z0-9]+-[a-zA-Z0-9]{4,})")


def _parse_bd_id(stdout: str) -> str | None:
    for line in (stdout or "").splitlines():
        if "reated" in line and "issue" in line.lower():
            m = _BD_ID_PATTERN.search(line)
            if m:
                return m.group(1)
    m = _BD_ID_PATTERN.search(stdout or "")
    return m.group(1) if m else None


def create_build_issue(
    project_root: Path, config: "ProjectConfig", description: str
) -> str | None:
    """Create a bd issue for a *build. Return bd id or None."""
    if not config.beads.enabled or not config.beads.hooks_simple_mode:
        return None
    if not is_available(project_root):
        return None
    title = f"Build: {(description or '')[:150]}".strip()
    try:
        r = run_bd(project_root, ["create", title, "-p", "0"])
        if r.returncode != 0:
            return None
        return _parse_bd_id(r.stdout)
    except Exception as e:
        logger.debug("beads create_build_issue: %s", e)
        return None


def create_fix_issue(
    project_root: Path, config: "ProjectConfig", file: str, description: str
) -> str | None:
    """Create a bd issue for a *fix. Return bd id or None."""
    if not config.beads.enabled or not config.beads.hooks_simple_mode:
        return None
    if not is_available(project_root):
        return None
    title = f"Fix: {file or 'unknown'} – {(description or '')[:100]}".strip()
    try:
        r = run_bd(project_root, ["create", title, "-p", "0"])
        if r.returncode != 0:
            return None
        return _parse_bd_id(r.stdout)
    except Exception as e:
        logger.debug("beads create_fix_issue: %s", e)
        return None


def create_review_issue(
    project_root: Path, config: "ProjectConfig", file_or_path: str
) -> str | None:
    """Create a bd issue for a *review. Return bd id or None."""
    if not config.beads.enabled or not config.beads.hooks_review:
        return None
    if not is_available(project_root):
        return None
    title = f"Review: {file_or_path or 'project'}"[:200]
    try:
        r = run_bd(project_root, ["create", title, "-p", "0"])
        if r.returncode != 0:
            return None
        return _parse_bd_id(r.stdout)
    except Exception as e:
        logger.debug("beads create_review_issue: %s", e)
        return None


def create_test_issue(
    project_root: Path, config: "ProjectConfig", file_or_path: str
) -> str | None:
    """Create a bd issue for a *test. Return bd id or None."""
    if not config.beads.enabled or not config.beads.hooks_test:
        return None
    if not is_available(project_root):
        return None
    title = f"Test: {file_or_path or 'project'}"[:200]
    try:
        r = run_bd(project_root, ["create", title, "-p", "0"])
        if r.returncode != 0:
            return None
        return _parse_bd_id(r.stdout)
    except Exception as e:
        logger.debug("beads create_test_issue: %s", e)
        return None


def create_refactor_issue(
    project_root: Path,
    config: "ProjectConfig",
    file_or_path: str,
    description: str,
) -> str | None:
    """Create a bd issue for a *refactor. Return bd id or None."""
    if not config.beads.enabled or not config.beads.hooks_refactor:
        return None
    if not is_available(project_root):
        return None
    base = f"Refactor: {file_or_path or 'project'}"
    suffix = f" – {(description or '')[:80]}".strip()
    title = (base + suffix)[:200]
    try:
        r = run_bd(project_root, ["create", title, "-p", "0"])
        if r.returncode != 0:
            return None
        return _parse_bd_id(r.stdout)
    except Exception as e:
        logger.debug("beads create_refactor_issue: %s", e)
        return None


def create_workflow_issue(
    project_root: Path,
    config: "ProjectConfig",
    workflow_name: str,
    prompt_or_target: str,
) -> str | None:
    """Create a bd issue for a CLI workflow run. Return bd id or None."""
    if not config.beads.enabled or not config.beads.hooks_workflow:
        return None
    if not is_available(project_root):
        return None
    title = f"Workflow: {workflow_name} – {(prompt_or_target or '')[:120]}".strip()[
        :200
    ]
    try:
        r = run_bd(project_root, ["create", title, "-p", "0"])
        if r.returncode != 0:
            return None
        return _parse_bd_id(r.stdout)
    except Exception as e:
        logger.debug("beads create_workflow_issue: %s", e)
        return None


def close_issue(project_root: Path, bd_id: str | None) -> None:
    """Close a bd issue. Log only on failure."""
    if not bd_id:
        return
    try:
        run_bd(project_root, ["close", bd_id])
    except Exception as e:
        logger.debug("beads close_issue %s: %s", bd_id, e)
