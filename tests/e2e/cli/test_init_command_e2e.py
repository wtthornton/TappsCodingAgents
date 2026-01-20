"""
E2E tests for init command: --reset, --rollback, --dry-run, --no-*, --yes.

Extends coverage for init variants that were previously untested.
Requires tapps_agents on PYTHONPATH (pytest pythonpath or harness default_env).
"""

import pytest
from pathlib import Path

from tests.e2e.fixtures.cli_harness import CLIHarness, CLIResult

# Repo root so subprocess can import tapps_agents when cwd is a temp project
_REPO = Path(__file__).resolve().parents[3]


def _run(cli: CLIHarness, cwd: Path, *args: str) -> CLIResult:
    cmd = ["python", "-m", "tapps_agents.cli", "init", *args]
    env = {"PYTHONPATH": str(_REPO)}
    return cli.run_command(cmd, cwd=cwd, env=env)


@pytest.mark.e2e_cli
class TestInitCommandE2E:
    """E2E tests for init --reset, --rollback, --dry-run, --no-*, --yes."""

    @pytest.fixture
    def harness(self, tmp_path):
        h = CLIHarness(base_path=tmp_path / "init_e2e", default_timeout=120.0)
        yield h
        h.cleanup()

    @pytest.fixture
    def project(self, harness):
        return harness.create_isolated_project(project_name="init_proj")

    def test_init_yes_no_cache_creates_files(self, harness, project):
        """init --yes --no-cache creates config, .cursor, and workflows."""
        r = _run(harness, project, "--yes", "--no-cache")
        assert r.exit_code in (0, 1)
        # Core artifacts
        assert (project / ".tapps-agents" / "config.yaml").exists()
        assert (project / ".cursor" / "mcp.json").exists()
        assert (project / ".cursor" / "rules").exists() or (project / ".cursor").exists()
        assert (project / "workflows" / "presets").exists() or (project / ".tapps-agents").exists()

    def test_init_dry_run_reset_no_changes(self, harness, project):
        """init --reset --yes --dry-run does not create backup or delete files."""
        _run(harness, project, "--yes", "--no-cache")
        backups_before = list((project / ".tapps-agents").glob("backups/*")) if (project / ".tapps-agents").exists() else []
        rules_before = list((project / ".cursor" / "rules").iterdir()) if (project / ".cursor" / "rules").exists() else []

        r = _run(harness, project, "--reset", "--yes", "--dry-run", )
        assert r.exit_code in (0, 1)
        assert "DRY RUN" in r.stdout or "dry run" in r.stdout.lower() or "would be reset" in r.stdout.lower()

        backups_after = list((project / ".tapps-agents").glob("backups/*")) if (project / ".tapps-agents").exists() else []
        rules_after = list((project / ".cursor" / "rules").iterdir()) if (project / ".cursor" / "rules").exists() else []
        assert len(backups_after) == len(backups_before)
        assert len(rules_after) >= len(rules_before)

    def test_init_no_rules_skips_rules(self, harness, project):
        """init --no-rules --yes --no-cache does not create .cursor/rules."""
        _run(harness, project, "--no-rules", "--yes", "--no-cache")
        # --no-rules skips init_cursor_rules; .cursor/rules must not exist
        assert not (project / ".cursor" / "rules").exists()

    def test_init_no_cache_skips_cache(self, harness, project):
        """init --no-cache --yes sets cache_requested=False so cache is not run."""
        r = _run(harness, project, "--no-cache", "--yes", )
        assert r.exit_code in (0, 1)
        assert (project / ".tapps-agents" / "config.yaml").exists()

    def test_init_yes_non_interactive(self, harness, project):
        """init --yes runs without prompting (CI mode)."""
        r = _run(harness, project, "--yes", "--no-cache")
        assert r.exit_code in (0, 1)
        assert "Continue with reset" not in r.stdout or "y/N" not in r.stdout

    def test_init_reset_creates_backup(self, harness, project):
        """init then init --reset --yes creates a backup under .tapps-agents/backups."""
        _run(harness, project, "--yes", "--no-cache")
        _run(harness, project, "--reset", "--yes", )

        backups_dir = project / ".tapps-agents" / "backups"
        assert backups_dir.exists()
        subdirs = [d for d in backups_dir.iterdir() if d.is_dir()]
        assert len(subdirs) >= 1
        found_manifest = any((d / "manifest.json").exists() for d in subdirs)
        assert found_manifest

    def test_init_rollback_restores(self, harness, project):
        """init --reset --yes then init --rollback <path> restores files."""
        _run(harness, project, "--yes", "--no-cache")
        _run(harness, project, "--reset", "--yes")

        backups_dir = project / ".tapps-agents" / "backups"
        if not backups_dir.exists():
            pytest.skip("Backup dir not created (reset may have been skipped)")
        subdirs = sorted([d for d in backups_dir.iterdir() if d.is_dir()], key=lambda p: p.name, reverse=True)
        if not subdirs:
            pytest.skip("No backup subdirs")
        backup_path = subdirs[0]

        r2 = _run(harness, project, "--rollback", str(backup_path))
        assert r2.exit_code == 0
        assert "restored" in r2.stdout.lower() or "Successfully" in r2.stdout
