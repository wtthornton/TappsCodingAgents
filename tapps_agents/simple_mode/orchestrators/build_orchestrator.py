"""
Build Orchestrator - Coordinates feature development workflow.

Coordinates: Enhancer → Planner → Architect → Designer → Implementer
"""

from pathlib import Path
from typing import Any

from tapps_agents.agents.enhancer.agent import EnhancerAgent
from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class BuildOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for building new features."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for build workflow."""
        return ["enhancer", "planner", "architect", "designer", "implementer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute build workflow with prompt enhancement.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        original_description = parameters.get("description") or intent.original_input

        # Step 1: Enhance the prompt using the enhancer agent
        enhanced_prompt = original_description
        enhancement_result = None
        
        try:
            enhancer = EnhancerAgent(config=self.config)
            await enhancer.activate(self.project_root)
            
            # Use full enhancement (all 7 stages: analysis, requirements, architecture, 
            # codebase context, quality standards, implementation strategy, synthesis)
            enhancement_result = await enhancer.run(
                "enhance",
                prompt=original_description,
                output_format="markdown"
            )
            
            # Extract enhanced prompt from result
            # The result can be a string (markdown) or dict with "enhanced_prompt" key
            if enhancement_result.get("success"):
                result_value = enhancement_result.get("enhanced_prompt")
                if isinstance(result_value, str):
                    # Direct string result (markdown format)
                    enhanced_prompt = result_value
                elif isinstance(result_value, dict):
                    # Nested dict with enhanced_prompt
                    enhanced_prompt = result_value.get("enhanced_prompt", original_description)
                elif result_value is None:
                    # No enhanced_prompt field, check for other fields
                    if "instruction" in enhancement_result:
                        enhanced_prompt = enhancement_result["instruction"]
                    elif "result" in enhancement_result and isinstance(enhancement_result["result"], str):
                        enhanced_prompt = enhancement_result["result"]
            else:
                # Enhancement didn't succeed, use original
                enhanced_prompt = original_description
            
            await enhancer.close()
        except Exception as e:
            # If enhancement fails, continue with original prompt
            # This ensures the build process continues even if enhancement has issues
            enhanced_prompt = original_description
            enhancement_result = {"error": str(e), "fallback": True}

        # Step 2: Use enhanced prompt for build workflow
        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=2,  # Allow some parallelization
        )

        # Prepare agent tasks using enhanced prompt
        agent_tasks = [
            {
                "agent_id": "planner-1",
                "agent": "planner",
                "command": "create-story",
                "args": {"description": enhanced_prompt},
            },
            {
                "agent_id": "architect-1",
                "agent": "architect",
                "command": "design",
                "args": {"specification": enhanced_prompt},
            },
            {
                "agent_id": "designer-1",
                "agent": "designer",
                "command": "design-api",
                "args": {"specification": enhanced_prompt},
            },
            {
                "agent_id": "implementer-1",
                "agent": "implementer",
                "command": "implement",
                "args": {"specification": enhanced_prompt},
            },
        ]

        # Execute in sequence (some steps can run in parallel)
        result = await orchestrator.execute_parallel(agent_tasks)

        return {
            "type": "build",
            "success": result.get("success", False),
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": result.get("summary", {}),
            "enhancement": {
                "original_prompt": original_description,
                "enhanced_prompt": enhanced_prompt,
                "enhancement_result": enhancement_result,
            },
        }

