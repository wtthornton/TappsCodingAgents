"""
Breakdown Orchestrator - *breakdown command. MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.4.

Runs @planner *plan with a breakdown-oriented description (task list with deps).
"""

from typing import Any

from tapps_agents.agents.planner.agent import PlannerAgent

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class BreakdownOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for *breakdown: task decomposition via PlannerAgent."""

    def get_agent_sequence(self) -> list[str]:
        return ["planner"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        parameters = parameters or {}
        prompt = parameters.get("prompt") or parameters.get("description") or intent.original_input
        if not prompt or not str(prompt).strip():
            return {"success": False, "error": "Prompt required. Use: @simple-mode *breakdown \"your goal\""}

        # Ask planner for a task-oriented plan (breakdown)
        description = f"Break down into ordered tasks with dependencies: {str(prompt).strip()}"

        agent = PlannerAgent(config=self.config)
        try:
            out = await agent.run("plan", description=description)
        except Exception as e:
            return {"success": False, "error": str(e), "type": "breakdown"}

        if out.get("error"):
            return {"success": False, "error": out["error"], "type": "breakdown"}

        return {
            "type": "breakdown",
            "success": True,
            "plan": out,
            "agents_executed": 1,
            "summary": {"breakdown": True},
        }
