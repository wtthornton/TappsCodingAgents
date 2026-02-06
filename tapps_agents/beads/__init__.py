"""
Beads (bd) integration: task-tracking for agents (required by default).

Use is_available(project_root) before run_bd. See docs/BEADS_INTEGRATION.md.
Task specs: .tapps-agents/task-specs/ for hydration/dehydration.
"""

from .client import (
    BeadsRequiredError,
    is_available,
    is_ready,
    require_beads,
    resolve_bd_path,
    run_bd,
)
from .hydration import HydrationReport, dehydrate_from_beads, hydrate_to_beads
from .parse import parse_bd_id_from_stdout
from .specs import TaskSpec, load_task_spec, load_task_specs, save_task_spec

__all__ = [
    "BeadsRequiredError",
    "HydrationReport",
    "TaskSpec",
    "dehydrate_from_beads",
    "hydrate_to_beads",
    "is_available",
    "is_ready",
    "load_task_spec",
    "load_task_specs",
    "parse_bd_id_from_stdout",
    "require_beads",
    "resolve_bd_path",
    "run_bd",
    "save_task_spec",
]
