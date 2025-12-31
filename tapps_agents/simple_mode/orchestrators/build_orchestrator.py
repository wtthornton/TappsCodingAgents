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

        # Enhancement 3: Auto-detect libraries and fetch Context7 documentation
        context7_docs = {}
        context7_info = {}
        try:
            from tapps_agents.context7.agent_integration import get_context7_helper
            
            context7_helper = get_context7_helper(None, self.config, self.project_root)
            if context7_helper and context7_helper.enabled:
                # Detect libraries from the description
                # Detect libraries, but filter to only relevant ones
                # (Same filtering logic as enhancer agent - only fetch docs for libraries
                # that are in project deps, explicitly mentioned, or well-known)
                all_detected = context7_helper.detect_libraries(
                    prompt=original_description,
                    language="python"  # Default, can be enhanced to detect from project
                )
                
                # Filter to only relevant libraries
                project_libs = set(context7_helper.detect_libraries(
                    code=None, prompt=None, error_message=None
                ))
                
                filtered_libraries = []
                desc_lower = original_description.lower()
                for lib in all_detected:
                    if (lib in project_libs or
                        context7_helper.is_well_known_library(lib) or
                        any(keyword in desc_lower for keyword in [
                            f"{lib} library", f"{lib} framework", f"using {lib}"
                        ])):
                        filtered_libraries.append(lib)
                
                if filtered_libraries:
                    # Fetch documentation for filtered libraries only
                    context7_docs = await context7_helper.get_documentation_for_libraries(
                        libraries=filtered_libraries,
                        topic=None,
                        use_fuzzy_match=True,
                    )
                    detected_libraries = filtered_libraries  # For context7_info below
                    context7_info = {
                        "libraries_detected": detected_libraries,
                        "docs_available": len([d for d in context7_docs.values() if d is not None]),
                        "total_libraries": len(detected_libraries),
                    }
                    # Enhance description with Context7 guidance note
                    if context7_docs:
                        context7_note = f"\n\n[Context7: Detected {len(detected_libraries)} libraries. Documentation available for {context7_info['docs_available']} libraries.]"
                        original_description = original_description + context7_note
        except Exception as e:
            # Context7 is optional - continue without it
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Context7 auto-detection failed in build workflow: {e}")

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
            "context7": context7_info,  # Enhancement 3: Include Context7 detection info
        }

