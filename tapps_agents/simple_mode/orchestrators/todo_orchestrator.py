"""
Todo Orchestrator - *todo command. MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.5.

Forwards to Beads (bd): create, list, close, dep add. When bd not available, returns guidance.
"""

import shlex
from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class TodoOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for *todo: forwards to bd (Beads)."""

    def get_agent_sequence(self) -> list[str]:
        return ["beads"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        from ...beads import is_available, require_beads, run_bd
        from ...core.config import load_config

        parameters = parameters or {}
        rest = (parameters.get("todo_rest") or "").strip()
        bd_args = shlex.split(rest) if rest else ["ready"]

        config = self.config or load_config()
        try:
            require_beads(config, self.project_root)
        except Exception as e:
            return {
                "type": "todo",
                "success": False,
                "error": str(e),
            }

        if not is_available(self.project_root):
            return {
                "type": "todo",
                "success": False,
                "error": "bd not found. Install to tools/bd or add bd to PATH. See docs/BEADS_INTEGRATION.md.",
            }

        r = run_bd(self.project_root, bd_args, capture_output=True)
        out = (r.stdout or "").strip() if r.stdout else ""
        return {
            "type": "todo",
            "success": (r.returncode or 0) == 0,
            "output": out,
            "returncode": r.returncode,
            "agents_executed": 0,
        }
