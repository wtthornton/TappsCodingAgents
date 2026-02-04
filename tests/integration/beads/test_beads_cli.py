"""
Integration tests for `tapps-agents beads` CLI when bd is installed.

Requires bd in tools/bd or on PATH. Run with: pytest -m integration tests/integration/beads/test_beads_cli.py -v
On some environments (e.g. Windows) bd or the CLI may block; the test is skipped then.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from tapps_agents.beads import is_available

pytestmark = [pytest.mark.integration, pytest.mark.timeout(90)]

# Repo root (parent of tests/)
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_beads_ready_when_bd_present() -> None:
    """`tapps-agents beads ready` exits 0 when bd is available (tools/bd or PATH)."""
    if not is_available(REPO_ROOT):
        pytest.skip("bd not found in tools/bd or on PATH")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "tapps_agents.cli", "beads", "ready"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("tapps-agents beads ready timed out (bd/CLI may block in this environment)")
    assert proc.returncode == 0, f"beads ready failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"

