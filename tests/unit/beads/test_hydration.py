"""
Unit tests for tapps_agents.beads.hydration: hydrate_to_beads, dehydrate_from_beads.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.beads.specs import TaskSpec, save_task_spec
from tapps_agents.beads.hydration import (
    HydrationReport,
    dehydrate_from_beads,
    hydrate_to_beads,
)


@pytest.mark.unit
class TestHydrateToBeads:
    """Tests for hydrate_to_beads."""

    def test_bd_unavailable_returns_report_no_crash(self, tmp_path: Path) -> None:
        """When bd is not available, returns report with bd_unavailable and does not raise."""
        with patch("tapps_agents.beads.hydration.is_available", return_value=False):
            report = hydrate_to_beads(tmp_path)
        assert report.bd_unavailable is True
        assert report.created == 0

    def test_dry_run_does_not_call_bd(self, tmp_path: Path) -> None:
        """When dry_run=True, does not run bd or write files."""
        (tmp_path / ".tapps-agents" / "task-specs").mkdir(parents=True)
        spec = TaskSpec(id="t1", title="Task 1", status="todo")
        save_task_spec(spec, tmp_path)
        with patch("tapps_agents.beads.hydration.is_available", return_value=True):
            with patch("tapps_agents.beads.hydration.run_bd") as run_bd:
                report = hydrate_to_beads(tmp_path, dry_run=True)
        assert report.dry_run is True
        assert report.created == 1
        run_bd.assert_not_called()

    def test_skips_specs_with_beads_issue(self, tmp_path: Path) -> None:
        """Specs that already have beads_issue are skipped."""
        (tmp_path / ".tapps-agents" / "task-specs").mkdir(parents=True)
        spec = TaskSpec(id="t1", title="Task 1", beads_issue="bd-abc")
        save_task_spec(spec, tmp_path)
        with patch("tapps_agents.beads.hydration.is_available", return_value=True):
            with patch("tapps_agents.beads.hydration.run_bd") as run_bd:
                report = hydrate_to_beads(tmp_path)
        assert report.skipped == 1
        assert report.created == 0
        run_bd.assert_not_called()

    def test_creates_and_saves_beads_issue(self, tmp_path: Path) -> None:
        """When bd create succeeds, spec is updated with beads_issue and saved."""
        (tmp_path / ".tapps-agents" / "task-specs").mkdir(parents=True)
        spec = TaskSpec(id="t1", title="Task 1")
        save_task_spec(spec, tmp_path)
        fake_stdout = "Created issue TappsCodingAgents-xyz123\n"
        with patch("tapps_agents.beads.hydration.is_available", return_value=True):
            with patch("tapps_agents.beads.hydration.run_bd") as run_bd:
                run_bd.return_value = type("R", (), {"returncode": 0, "stdout": fake_stdout, "stderr": ""})()
                report = hydrate_to_beads(tmp_path)
        assert report.created == 1
        assert report.failed == 0
        run_bd.assert_called()
        # Reload spec and check beads_issue was saved
        from tapps_agents.beads.specs import load_task_spec
        loaded = load_task_spec("t1", tmp_path)
        assert loaded is not None
        assert loaded.beads_issue == "TappsCodingAgents-xyz123"


@pytest.mark.unit
class TestDehydrateFromBeads:
    """Tests for dehydrate_from_beads."""

    def test_bd_unavailable_returns_zero(self, tmp_path: Path) -> None:
        """When bd is not available, returns 0 without raising."""
        with patch("tapps_agents.beads.hydration.is_available", return_value=False):
            n = dehydrate_from_beads(tmp_path)
        assert n == 0

    def test_updates_spec_status_from_list_json(self, tmp_path: Path) -> None:
        """When bd list --json returns issue list, matching specs are updated."""
        (tmp_path / ".tapps-agents" / "task-specs").mkdir(parents=True)
        spec = TaskSpec(id="t1", title="Task 1", beads_issue="bd-abc", status="todo")
        save_task_spec(spec, tmp_path)
        fake_stdout = json.dumps([{"id": "bd-abc", "status": "done"}])
        with patch("tapps_agents.beads.hydration.is_available", return_value=True):
            with patch("tapps_agents.beads.hydration.run_bd") as run_bd:
                run_bd.return_value = type("R", (), {"returncode": 0, "stdout": fake_stdout, "stderr": ""})()
                n = dehydrate_from_beads(tmp_path)
        assert n == 1
        from tapps_agents.beads.specs import load_task_spec
        loaded = load_task_spec("t1", tmp_path)
        assert loaded is not None
        assert loaded.status == "done"
