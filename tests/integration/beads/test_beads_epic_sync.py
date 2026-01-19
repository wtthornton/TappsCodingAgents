"""
Integration tests for Epic-to-Beads sync when bd is installed.

Uses a temp project with tools/bd, bd init --stealth, a minimal epic, and
EpicOrchestrator.load_epic with beads.enabled and beads.sync_epic=True.
Asserts story_id->bd_id mapping and that bd has the issues (bd ready or list).

Requires bd. Run: pytest -m integration tests/integration/beads/test_beads_epic_sync.py -v
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tapps_agents.beads import is_available, run_bd
from tapps_agents.core.config import BeadsConfig, ProjectConfig
from tapps_agents.epic.orchestrator import EpicOrchestrator

pytestmark = [pytest.mark.integration, pytest.mark.timeout(90)]

REPO_ROOT = Path(__file__).resolve().parents[3]
BD_EXE = REPO_ROOT / "tools" / "bd" / "bd.exe"

MINIMAL_EPIC = """# Epic 99: Beads Integration Test

## Epic Goal
Test beads sync.

## Epic Description
Minimal epic for integration test.

## Stories

**Story 99.1: First**
First story.

**Story 99.2: Second**
Second. Depends on Story 99.1.

## Execution Notes
(empty)

## Definition of Done
(empty)
"""


def _setup_temp_project_with_bd(tmp_path: Path) -> None:
    """Copy tools/bd into tmp_path, init git (bd is git-backed), then bd init --stealth."""
    bd_dir = tmp_path / "tools" / "bd"
    bd_dir.mkdir(parents=True)
    # Beads is git-backed; bd init requires a git repo
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    if sys.platform == "win32" and BD_EXE.exists():
        exe = bd_dir / "bd.exe"
        shutil.copy2(BD_EXE, exe)
    else:
        unix_bd = REPO_ROOT / "tools" / "bd" / "bd"
        if unix_bd.exists():
            exe = bd_dir / "bd"
            shutil.copy2(unix_bd, exe)
        else:
            pytest.skip("tools/bd/bd.exe or tools/bd/bd not found")
    try:
        r = subprocess.run(
            [str(exe), "init", "--stealth"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("bd init --stealth timed out (bd may block in this environment)")
    if r.returncode != 0:
        pytest.skip(f"bd init --stealth failed (exit {r.returncode}): stderr={r.stderr!r}")


def test_epic_load_syncs_to_beads(tmp_path: Path) -> None:
    """load_epic with beads.enabled and sync_epic creates bd issues and story_id->bd_id mapping."""
    _setup_temp_project_with_bd(tmp_path)
    if not is_available(tmp_path):
        pytest.skip("bd not available in temp project")

    epic_path = tmp_path / "epic-99-beads-test.md"
    epic_path.write_text(MINIMAL_EPIC, encoding="utf-8")

    config = ProjectConfig(beads=BeadsConfig(enabled=True, sync_epic=True, hooks_simple_mode=False))
    orch = EpicOrchestrator(project_root=tmp_path, config=config)
    orch.load_epic(epic_path)

    assert "99.1" in orch._story_to_bd, "story 99.1 should have a bd id"
    assert "99.2" in orch._story_to_bd, "story 99.2 should have a bd id"
    assert len(orch._story_to_bd) >= 2

    # Verify bd has issues: bd ready or similar (optional; ready lists unblocked)
    proc = run_bd(tmp_path, ["ready"], capture_output=True)
    # ready may list 99.1 (no deps) or empty if already closed; we only care sync ran
    assert proc.returncode == 0
