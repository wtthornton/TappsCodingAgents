"""
Unit tests for tapps_agents.beads.specs: load, save, validation.
"""

from pathlib import Path

import pytest

from tapps_agents.beads.specs import (
    TaskSpec,
    load_task_spec,
    load_task_specs,
    save_task_spec,
    validate_task_spec_file,
)


@pytest.mark.unit
class TestTaskSpec:
    """Tests for TaskSpec schema."""

    def test_required_fields(self) -> None:
        """id and title are required."""
        s = TaskSpec(id="t1", title="My task")
        assert s.id == "t1"
        assert s.title == "My task"
        assert s.type == "story"
        assert s.status == "todo"
        assert s.dependencies == []

    def test_all_fields(self) -> None:
        """All schema fields accepted."""
        s = TaskSpec(
            id="enh-002-s1",
            title="Implement hooks",
            description="Add 5 core events",
            type="story",
            priority=0,
            story_points=3,
            epic="enh-002",
            dependencies=["enh-002-s0"],
            github_issue=25,
            beads_issue="bd-abc",
            status="in-progress",
            workflow="build",
            files=["tapps_agents/hooks/"],
            tests=["tests/unit/hooks/"],
        )
        assert s.epic == "enh-002"
        assert s.beads_issue == "bd-abc"
        assert s.files == ["tapps_agents/hooks/"]
        assert s.tests == ["tests/unit/hooks/"]

    def test_type_literal(self) -> None:
        """type must be story, epic, or task."""
        TaskSpec(id="x", title="t", type="story")
        TaskSpec(id="x", title="t", type="epic")
        TaskSpec(id="x", title="t", type="task")
        with pytest.raises(Exception):
            TaskSpec(id="x", title="t", type="invalid")

    def test_status_literal(self) -> None:
        """status must be todo, in-progress, done, or blocked."""
        for status in ("todo", "in-progress", "done", "blocked"):
            s = TaskSpec(id="x", title="t", status=status)
            assert s.status == status
        with pytest.raises(Exception):
            TaskSpec(id="x", title="t", status="invalid")


@pytest.mark.unit
class TestLoadTaskSpecs:
    """Tests for load_task_specs."""

    def test_empty_when_dir_missing(self, tmp_path: Path) -> None:
        """Returns [] when task-specs directory does not exist."""
        assert load_task_specs(tmp_path) == []

    def test_load_valid_specs(self, tmp_path: Path) -> None:
        """Loads valid YAML specs from task-specs directory."""
        specs_dir = tmp_path / ".tapps-agents" / "task-specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "enh-002-s1.yaml").write_text(
            """
task:
  id: enh-002-s1
  title: Hook config
  type: story
  epic: enh-002
  status: todo
""",
            encoding="utf-8",
        )
        (specs_dir / "enh-002-s2.yaml").write_text(
            """
task:
  id: enh-002-s2
  title: Hook executor
  dependencies: [enh-002-s1]
""",
            encoding="utf-8",
        )
        specs = load_task_specs(tmp_path)
        assert len(specs) == 2
        ids = {s.id for s in specs}
        assert "enh-002-s1" in ids
        assert "enh-002-s2" in ids

    def test_skips_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML files are skipped (not raised)."""
        specs_dir = tmp_path / ".tapps-agents" / "task-specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "valid.yaml").write_text(
            "task:\n  id: v1\n  title: Valid",
            encoding="utf-8",
        )
        (specs_dir / "invalid.yaml").write_text("bad: [\n  unfinished", encoding="utf-8")
        specs = load_task_specs(tmp_path)
        assert len(specs) == 1
        assert specs[0].id == "v1"


@pytest.mark.unit
class TestLoadTaskSpec:
    """Tests for load_task_spec (single by ID)."""

    def test_load_by_id(self, tmp_path: Path) -> None:
        """Load single spec by ID from direct filename."""
        specs_dir = tmp_path / ".tapps-agents" / "task-specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "my-task.yaml").write_text(
            "task:\n  id: my-task\n  title: My Task",
            encoding="utf-8",
        )
        spec = load_task_spec("my-task", tmp_path)
        assert spec is not None
        assert spec.id == "my-task"
        assert spec.title == "My Task"

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        """Returns None when spec not found."""
        assert load_task_spec("nonexistent", tmp_path) is None


@pytest.mark.unit
class TestSaveTaskSpec:
    """Tests for save_task_spec."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Save creates task-specs dir and file."""
        spec = TaskSpec(id="s1", title="Save test")
        out = save_task_spec(spec, tmp_path)
        assert out.exists()
        assert out.name == "s1.yaml"
        content = out.read_text(encoding="utf-8")
        assert "task:" in content
        assert "id: s1" in content
        assert "title: Save test" in content

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Save then load returns equivalent spec."""
        spec = TaskSpec(
            id="r1",
            title="Roundtrip",
            dependencies=["d1"],
            files=["a.py"],
        )
        save_task_spec(spec, tmp_path)
        loaded = load_task_spec("r1", tmp_path)
        assert loaded is not None
        assert loaded.id == spec.id
        assert loaded.title == spec.title
        assert loaded.dependencies == spec.dependencies
        assert loaded.files == spec.files


@pytest.mark.unit
class TestValidateTaskSpecFile:
    """Tests for validate_task_spec_file."""

    def test_valid_returns_spec(self, tmp_path: Path) -> None:
        """Valid file returns (TaskSpec, None)."""
        f = tmp_path / "t.yaml"
        f.write_text("task:\n  id: v\n  title: Valid", encoding="utf-8")
        spec, err = validate_task_spec_file(f)
        assert spec is not None
        assert spec.id == "v"
        assert err is None

    def test_invalid_returns_error(self, tmp_path: Path) -> None:
        """Invalid file returns (None, error_message)."""
        f = tmp_path / "bad.yaml"
        f.write_text("task:\n  id: x\n  type: invalid", encoding="utf-8")
        spec, err = validate_task_spec_file(f)
        assert spec is None
        assert err is not None
        assert "invalid" in err or "type" in err
