"""
Enhancer Agent Handler

Handles execution of enhancer agent steps for prompt enhancement in workflows.
Supports enhance, enhance_prompt, and enhance-quick. Used by rapid-dev, Epic,
and full-sdlc (optional) presets.
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class EnhancerHandler(AgentExecutionHandler):
    """Handler for enhancer agent execution."""

    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports enhancer agent."""
        return agent_name == "enhancer" and action in {
            "enhance",
            "enhance_prompt",
            "enhance_quick",
        }

    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute enhancer step.

        Resolves prompt from state (description, story_description, user_prompt).
        Maps enhance_prompt -> enhance, enhance_quick -> enhance-quick.
        Stores enhanced_prompt in state and enhancer_result for output_passer.
        """
        # Resolve prompt from state (Epic sets description/story_description; executor sets user_prompt)
        prompt = (
            self.state.variables.get("description")
            or self.state.variables.get("story_description")
            or self.state.variables.get("user_prompt")
            or ""
        )
        if not (prompt and str(prompt).strip()):
            prompt = "Enhance this project or feature description."

        # Map normalized action to EnhancerAgent command (enhance, enhance-quick)
        if action == "enhance_quick":
            agent_command = "enhance-quick"
        else:
            # enhance, enhance_prompt -> enhance
            agent_command = "enhance"

        # Optional output file when step creates enhanced-requirements.md
        creates = step.creates or []
        output_file = None
        if "enhanced-requirements.md" in creates or "enhanced_prompt" in creates:
            output_file = str(self.project_root / "enhanced-requirements.md")

        kwargs: dict[str, Any] = {
            "prompt": str(prompt).strip(),
            "output_format": "markdown",
        }
        if output_file:
            kwargs["output_file"] = output_file

        result = await self.run_agent("enhancer", agent_command, **kwargs)

        # Extract enhanced_prompt (same logic as BuildOrchestrator and prompt_enhancer)
        enhanced_prompt = ""
        if isinstance(result, dict):
            raw = result.get("enhanced_prompt")
            if isinstance(raw, str):
                enhanced_prompt = raw
            elif isinstance(raw, dict) and "enhanced_prompt" in raw:
                enhanced_prompt = raw.get("enhanced_prompt") or ""
            if not enhanced_prompt:
                enhanced_prompt = result.get("instruction") or ""
            if not enhanced_prompt and isinstance(result.get("result"), str):
                enhanced_prompt = result["result"]
            if not enhanced_prompt and isinstance(result.get("result"), dict):
                enhanced_prompt = (result.get("result") or {}).get("enhanced_prompt") or ""
        if not enhanced_prompt:
            enhanced_prompt = str(prompt).strip()

        # Build stored result for output contracts and downstream handlers
        stored = dict(result) if isinstance(result, dict) else {"result": result}
        if "enhanced_prompt" not in stored or not stored["enhanced_prompt"]:
            stored["enhanced_prompt"] = enhanced_prompt
        stored["description"] = enhanced_prompt
        stored["enhancer_description"] = enhanced_prompt

        self.state.variables["enhancer_result"] = stored
        self.state.variables["enhanced_prompt"] = enhanced_prompt
        self.state.variables["description"] = enhanced_prompt

        # Created artifacts
        created_artifacts: list[dict[str, Any]] = []
        out_path = self.project_root / "enhanced-requirements.md"
        if out_path.exists() and ("enhanced-requirements.md" in creates or "enhanced_prompt" in creates):
            created_artifacts.append({"name": "enhanced-requirements.md", "path": str(out_path)})

        return created_artifacts
