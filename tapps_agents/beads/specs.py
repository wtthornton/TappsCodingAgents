"""
Task specification schema and loader.

Loads and saves task specification YAML files from .tapps-agents/task-specs/
with validation. Supports hydration/dehydration pattern for multi-session workflows.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import yaml

logger = logging.getLogger(__name__)
from pydantic import BaseModel, Field, field_validator


class TaskSpec(BaseModel):
    """Task specification schema for .tapps-agents/task-specs/ YAML files."""

    id: str = Field(..., min_length=1, description="Unique task ID (e.g. enh-002-s1)")
    title: str = Field(..., min_length=1, description="Task title")
    description: str = Field(default="", description="Task description")
    type: Literal["story", "epic", "task"] = Field(
        default="story",
        description="Task type",
    )
    priority: int = Field(default=0, ge=0, description="Priority (0=highest)")
    story_points: int | None = Field(default=None, ge=0, description="Story points estimate")
    epic: str | None = Field(default=None, description="Epic ID this task belongs to")
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of tasks this depends on",
    )
    github_issue: str | int | None = Field(default=None, description="GitHub issue number or ID")
    beads_issue: str | None = Field(default=None, description="Beads issue ID (populated after create)")
    status: Literal["todo", "in-progress", "done", "blocked"] = Field(
        default="todo",
        description="Current status",
    )
    workflow: str | None = Field(
        default=None,
        description="Workflow to run (build, fix, review, test, full)",
    )
    files: list[str] = Field(default_factory=list, description="Files or paths affected")
    tests: list[str] = Field(default_factory=list, description="Test paths")

    model_config = {"extra": "forbid"}

    @field_validator("id", mode="before")
    @classmethod
    def id_stripped(cls, v: object) -> str:
        """Strip whitespace from id."""
        if isinstance(v, str):
            return v.strip()
        return str(v)


def _task_specs_dir(project_root: Path) -> Path:
    """Return path to .tapps-agents/task-specs/."""
    return project_root / ".tapps-agents" / "task-specs"


def load_task_specs(project_root: Path | None = None) -> list[TaskSpec]:
    """
    Load all task specs from .tapps-agents/task-specs/.

    Scans the directory for YAML files, parses valid ones, and returns a list
    of validated TaskSpec. Validation errors are reported with file/field;
    invalid files are skipped (not raised).

    Args:
        project_root: Project root (default: cwd).

    Returns:
        List of successfully loaded TaskSpec. Empty if directory missing or no valid files.
    """
    project_root = project_root or Path.cwd()
    specs_dir = _task_specs_dir(project_root)
    if not specs_dir.exists():
        return []

    result: list[TaskSpec] = []
    for path in sorted(specs_dir.glob("*.yaml")):
        try:
            spec = _load_single_spec(path)
            if spec:
                result.append(spec)
        except Exception as e:
            logger.warning("Task spec validation failed %s: %s", path, e)
            continue
    return result


def _load_single_spec(path: Path) -> TaskSpec | None:
    """Load and validate a single task spec file."""
    content = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(content)
    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML object at {path}, got {type(raw).__name__}")

    # Support both top-level "task" key and flat structure
    data = raw.get("task", raw)
    if not isinstance(data, dict):
        raise ValueError(f"Expected task object at {path}")

    return TaskSpec.model_validate(data)


def load_task_spec(
    spec_id: str,
    project_root: Path | None = None,
) -> TaskSpec | None:
    """
    Load a single task spec by ID.

    Searches .tapps-agents/task-specs/ for a file containing the given id.
    Naming convention: <epic-id>-<story-id>.yaml (e.g. enh-002-s1.yaml).

    Args:
        spec_id: Task ID (e.g. enh-002-s1).
        project_root: Project root (default: cwd).

    Returns:
        TaskSpec if found and valid, else None.
    """
    project_root = project_root or Path.cwd()
    specs_dir = _task_specs_dir(project_root)
    if not specs_dir.exists():
        return None

    # Try direct filename: spec_id.yaml
    candidate = specs_dir / f"{spec_id}.yaml"
    if candidate.exists():
        try:
            return _load_single_spec(candidate)
        except Exception:
            return None

    # Scan files for matching id
    for path in specs_dir.glob("*.yaml"):
        try:
            spec = _load_single_spec(path)
            if spec and spec.id == spec_id:
                return spec
        except Exception:
            continue
    return None


def save_task_spec(
    spec: TaskSpec,
    project_root: Path | None = None,
) -> Path:
    """
    Save task spec to .tapps-agents/task-specs/.

    Uses naming convention <epic-id>-<story-id>.yaml when epic can be derived,
    otherwise <spec.id>.yaml. Creates directory if needed.

    Args:
        spec: TaskSpec to save.
        project_root: Project root (default: cwd).

    Returns:
        Path where spec was written.

    Raises:
        ValueError: On validation failure (should not occur for valid TaskSpec).
    """
    project_root = project_root or Path.cwd()
    specs_dir = _task_specs_dir(project_root)
    specs_dir.mkdir(parents=True, exist_ok=True)

    # Naming: epic-id-story-id or spec.id
    filename = f"{spec.id}.yaml"
    out_path = specs_dir / filename

    payload = {"task": spec.model_dump()}
    out_path.write_text(
        yaml.dump(payload, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return out_path


def validate_task_spec_file(path: Path) -> tuple[TaskSpec | None, str | None]:
    """
    Validate a task spec file without loading into global list.

    Args:
        path: Path to YAML file.

    Returns:
        (TaskSpec, None) if valid, (None, error_message) if invalid.
    """
    try:
        spec = _load_single_spec(path)
        return (spec, None)
    except Exception as e:
        return (None, f"{path}: {e}")
