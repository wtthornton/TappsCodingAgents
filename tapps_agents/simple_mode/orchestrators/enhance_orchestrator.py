"""
Enhance Orchestrator - *enhance command. MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.4.

Runs @enhancer *enhance (or *enhance-quick) with project context and Context7.
"""

from typing import Any

from tapps_agents.agents.enhancer.agent import EnhancerAgent

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class EnhanceOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for *enhance: prompt enhancement via EnhancerAgent."""

    def get_agent_sequence(self) -> list[str]:
        return ["enhancer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        parameters = parameters or {}
        prompt = parameters.get("prompt") or parameters.get("description") or intent.original_input
        if not prompt or not str(prompt).strip():
            return {"success": False, "error": "Prompt required. Use: @simple-mode *enhance \"your prompt\""}

        quick = parameters.get("quick", False)
        agent = EnhancerAgent(config=self.config)
        try:
            await agent.activate(self.project_root)
            out = await agent.run("enhance-quick" if quick else "enhance", prompt=str(prompt).strip())
            await agent.close()
        except Exception as e:
            return {"success": False, "error": str(e), "type": "enhance"}

        if out.get("error"):
            return {"success": False, "error": out["error"], "type": "enhance"}

        enhanced = out.get("enhanced_prompt") or out.get("instruction") or (out.get("result") if isinstance(out.get("result"), str) else None)
        if not enhanced and isinstance(out.get("result"), dict):
            enhanced = (out.get("result") or {}).get("enhanced_prompt")

        return {
            "type": "enhance",
            "success": True,
            "enhanced_prompt": enhanced or str(out),
            "agents_executed": 1,
            "summary": {"enhanced": bool(enhanced)},
        }
