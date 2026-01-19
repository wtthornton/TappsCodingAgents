"""
Beads (bd) client: resolve binary path, check availability, run bd.

All callers must use is_available(project_root) before run_bd. run_bd raises
FileNotFoundError when bd cannot be resolved.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def resolve_bd_path(project_root: Path) -> str | None:
    """
    Resolve the path to the bd binary.

    Prefer project-local tools/bd/bd.exe (Windows) or tools/bd/bd (Unix),
    then shutil.which("bd") on PATH.

    Args:
        project_root: Project root directory.

    Returns:
        Path to bd binary, or None if not found.
    """
    tools_bd = project_root / "tools" / "bd"
    if sys.platform == "win32":
        local = tools_bd / "bd.exe"
    else:
        local = tools_bd / "bd"
    if local.exists():
        return str(local)
    found = shutil.which("bd")
    return found


def is_available(project_root: Path) -> bool:
    """
    Return True if bd can be resolved for this project.

    Args:
        project_root: Project root directory.
    """
    return resolve_bd_path(project_root) is not None


def run_bd(
    project_root: Path,
    args: list[str],
    cwd: Path | None = None,
    *,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run bd with the given arguments.

    Args:
        project_root: Project root (used to resolve bd and as cwd when cwd is None).
        args: Arguments to pass to bd (e.g. ["ready"], ["create", "Title", "-p", "0"]).
        cwd: Working directory; defaults to project_root.
        capture_output: If True, capture stdout/stderr; if False, inherit. Default True.

    Returns:
        subprocess.CompletedProcess. Check .returncode.

    Raises:
        FileNotFoundError: If bd cannot be resolved (use is_available first).
    """
    path = resolve_bd_path(project_root)
    if path is None:
        raise FileNotFoundError(
            "bd not found. Install to tools/bd or add bd to PATH. See docs/BEADS_INTEGRATION.md."
        )
    workdir = cwd if cwd is not None else project_root
    return subprocess.run(
        [path, *args],
        cwd=workdir,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
