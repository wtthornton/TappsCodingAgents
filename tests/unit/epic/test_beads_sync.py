"""
Unit tests for tapps_agents.epic.beads_sync: sync_epic_to_beads with a mock run_bd.
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from tapps_agents.epic.beads_sync import sync_epic_to_beads
from tapps_agents.epic.models import EpicDocument, Story
from tapps_agents.workflow.common_enums import StoryStatus


def _story(epic: int, num: int, title: str, desc: str = "", deps: list[str] | None = None) -> Story:
    return Story(
        epic_number=epic,
        story_number=num,
        title=title,
        description=desc,
        dependencies=deps or [],
        status=StoryStatus.NOT_STARTED,
    )


def _make_epic() -> EpicDocument:
    return EpicDocument(
        epic_number=8,
        title="Test Epic",
        goal="Test",
        description="Test epic for beads_sync",
        stories=[
            _story(8, 1, "Story A", "Desc A"),
            _story(8, 2, "Story B", "Desc B", deps=["8.1"]),
            _story(8, 3, "Story C", "Desc C"),
        ],
    )


@pytest.mark.unit
class TestSyncEpicToBeads:
    """Tests for sync_epic_to_beads."""

    def test_creates_issues_and_mapping(self, tmp_path: Path) -> None:
        """sync_epic_to_beads creates bd issues and returns story_id -> bd_id."""
        created: dict[str, str] = {}
        bd_ids = ["Proj-a1b2", "Proj-c3d4", "Proj-e5f6"]

        def run_bd(args: list[str], cwd: Path | None = None) -> Any:
            r = Mock(returncode=0, stdout="", stderr="")
            if args[0] == "create":
                # Map by title for deterministic id assignment
                idx = 0
                if "Story A" in (args[1] if len(args) > 1 else ""):
                    idx = 0
                elif "Story B" in (args[1] if len(args) > 1 else ""):
                    idx = 1
                elif "Story C" in (args[1] if len(args) > 1 else ""):
                    idx = 2
                r.stdout = f"Created issue: {bd_ids[idx]}"
                created[args[1]] = bd_ids[idx]
            return r

        epic = _make_epic()
        story_to_bd, epic_parent_id = sync_epic_to_beads(epic, tmp_path, run_bd, create_parent=False)

        assert story_to_bd["8.1"] == "Proj-a1b2"
        assert story_to_bd["8.2"] == "Proj-c3d4"
        assert story_to_bd["8.3"] == "Proj-e5f6"
        assert epic_parent_id is None

    def test_dep_add_called_for_dependencies(self, tmp_path: Path) -> None:
        """sync_epic_to_beads calls run_bd with dep add child parent for dependencies."""
        dep_add_calls: list[tuple[str, str]] = []
        bd_ids = ["Proj-a1b2", "Proj-c3d4", "Proj-e5f6"]
        idx = [0]

        def run_bd(args: list[str], cwd: Path | None = None) -> Any:
            r = Mock(returncode=0, stdout="", stderr="")
            if args[0] == "create":
                i = min(idx[0], 2)
                r.stdout = f"Created issue: {bd_ids[i]}"
                idx[0] += 1
            elif args[0] == "dep" and args[1] == "add" and len(args) >= 4:
                # dep add child parent -> args[2]=child, args[3]=parent
                dep_add_calls.append((args[2], args[3]))
            return r

        epic = _make_epic()
        sync_epic_to_beads(epic, tmp_path, run_bd, create_parent=False)

        # 8.2 depends on 8.1 -> dep add 8.2_bd 8.1_bd (child, parent)
        assert ("Proj-c3d4", "Proj-a1b2") in dep_add_calls or any(
            c[0] == "Proj-c3d4" and c[1] == "Proj-a1b2" for c in dep_add_calls
        )

    def test_parses_bd_id_from_created_line(self, tmp_path: Path) -> None:
        """sync_epic_to_beads parses bd id from stdout like 'Created issue: ID'."""
        call_count = [0]
        ids = ["Repo-xyz99", "Repo-abc12"]

        def run_bd(args: list[str], cwd: Path | None = None) -> Any:
            r = Mock(returncode=0, stdout="", stderr="")
            if args[0] == "create":
                r.stdout = f"Created issue: {ids[call_count[0] % 2]}"
                call_count[0] += 1
            return r

        epic = EpicDocument(
            epic_number=1,
            title="E",
            goal="G",
            description="D",
            stories=[_story(1, 1, "S1"), _story(1, 2, "S2")],
        )
        story_to_bd, _ = sync_epic_to_beads(epic, tmp_path, run_bd, create_parent=False)
        assert "1.1" in story_to_bd and story_to_bd["1.1"] in ids
        assert "1.2" in story_to_bd and story_to_bd["1.2"] in ids

    def test_partial_mapping_on_create_failure(self, tmp_path: Path) -> None:
        """When one create fails (returncode!=0), that story is omitted; partial mapping returned."""
        call_count = [0]

        def run_bd(args: list[str], cwd: Path | None = None) -> Any:
            r = Mock(returncode=0, stdout="Created issue: Proj-xyz1", stderr="")
            if args[0] == "create":
                call_count[0] += 1
                if call_count[0] == 2:
                    r.returncode = 1
                    r.stderr = "error"
            return r

        epic = EpicDocument(
            epic_number=1,
            title="E",
            goal="G",
            description="D",
            stories=[_story(1, 1, "S1"), _story(1, 2, "S2"), _story(1, 3, "S3")],
        )
        story_to_bd, _ = sync_epic_to_beads(epic, tmp_path, run_bd, create_parent=False)
        assert "1.1" in story_to_bd
        assert "1.2" not in story_to_bd
        assert "1.3" in story_to_bd

    def test_create_parent_returns_epic_parent_id(self, tmp_path: Path) -> None:
        """When create_parent=True, first create is Epic parent; epic_parent_id is parsed and returned."""
        call_order: list[str] = []
        ids = ["EpicParent-a1b2", "Proj-c3d4", "Proj-e5f6"]

        def run_bd(args: list[str], cwd: Path | None = None) -> Any:
            r = Mock(returncode=0, stdout="", stderr="")
            if args[0] == "create":
                # First create = parent ("Epic 8:"), then stories
                if "Epic 8:" in (args[1] if len(args) > 1 else ""):
                    r.stdout = f"Created issue: {ids[0]}"
                    call_order.append("parent")
                else:
                    i = len(call_order) - 1
                    r.stdout = f"Created issue: {ids[1 + (i % 2)]}"
                    call_order.append("story")
            return r

        epic = _make_epic()
        story_to_bd, epic_parent_id = sync_epic_to_beads(epic, tmp_path, run_bd, create_parent=True)

        assert epic_parent_id == "EpicParent-a1b2"
        assert "8.1" in story_to_bd and "8.2" in story_to_bd and "8.3" in story_to_bd
        assert call_order[0] == "parent"
