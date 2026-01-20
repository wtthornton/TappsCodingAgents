"""
Beads (bd) integration: optional task-tracking for agents.

Use is_available(project_root) before run_bd. See docs/BEADS_INTEGRATION.md.
"""

from .client import is_available, is_ready, resolve_bd_path, run_bd

__all__ = ["is_available", "is_ready", "resolve_bd_path", "run_bd"]
