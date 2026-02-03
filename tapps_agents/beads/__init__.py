"""
Beads (bd) integration: optional task-tracking for agents.

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
from .parse import parse_bd_id_from_stdout
from .specs import TaskSpec, load_task_spec, load_task_specs, save_task_spec

from .hydration import HydrationReport, dehydrate_from_beads, hydrate_to_beads

__all__ = [
    "BeadsRequiredError",
    "is_available",
    "is_ready",
    "parse_bd_id_from_stdout",
    "require_beads",
    "resolve_bd_path",
    "run_bd",
    "TaskSpec",
    "HydrationReport",
    "dehydrate_from_beads",
    "hydrate_to_beads",
    "load_task_spec",
    "load_task_specs",
    "save_task_spec",
]
