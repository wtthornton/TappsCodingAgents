"""
Beads (bd) integration: optional task-tracking for agents.

Use is_available(project_root) before run_bd. See docs/BEADS_INTEGRATION.md.
"""

from .client import is_available, is_ready, resolve_bd_path, run_bd
from .parse import parse_bd_id_from_stdout

__all__ = [
    "is_available",
    "is_ready",
    "parse_bd_id_from_stdout",
    "resolve_bd_path",
    "run_bd",
]
