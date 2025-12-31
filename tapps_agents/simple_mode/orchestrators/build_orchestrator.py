"""
Build Orchestrator - Coordinates feature development workflow.

Coordinates: Enhancer → Planner → Architect → Designer → Implementer
"""

import logging
from pathlib import Path
from typing import Any

from tapps_agents.agents.enhancer.agent import EnhancerAgent
from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from tapps_agents.simple_mode.documentation_manager import (
    WorkflowDocumentationManager,
)
from tapps_agents.workflow.models import Artifact
from tapps_agents.workflow.step_checkpoint import StepCheckpointManager
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator

logger = logging.getLogger(__name__)


class BuildOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for building new features."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for build workflow."""
        return ["enhancer", "planner", "architect", "designer", "implementer"]

    async def execute(
        self,
        intent: Intent,
        parameters: dict[str, Any] | None = None,
        fast_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Execute build workflow with prompt enhancement.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input
            fast_mode: If True, skip steps 1-4 (enhance, plan, architect, design)

        Returns:
            Dictionary with execution results including:
            - type: "build"
            - success: bool
            - fast_mode: bool
            - workflow_id: str
            - steps_executed: list[str]
            - results: dict[str, Any]
        """
        parameters = parameters or {}
        original_description = parameters.get("description") or intent.original_input

        # Generate workflow ID and initialize documentation manager
        workflow_id = WorkflowDocumentationManager.generate_workflow_id("build")
        doc_manager: WorkflowDocumentationManager | None = None
        checkpoint_manager: StepCheckpointManager | None = None

        # Initialize documentation manager if organized documentation is enabled
        if self.config and self.config.simple_mode.documentation_organized:
            base_dir = self.project_root / "docs" / "workflows" / "simple-mode"
            doc_manager = WorkflowDocumentationManager(
                base_dir=base_dir,
                workflow_id=workflow_id,
                create_symlink=self.config.simple_mode.create_latest_symlink,
            )
            doc_manager.create_directory()
            logger.info(f"Created documentation directory for workflow: {workflow_id}")

        # Initialize checkpoint manager if state persistence is enabled
        if self.config and self.config.simple_mode.state_persistence_enabled:
            state_dir = self.project_root / ".tapps-agents" / "workflow-state"
            checkpoint_manager = StepCheckpointManager(
                state_dir=state_dir,
                workflow_id=workflow_id,
            )
            logger.info(f"Initialized checkpoint manager for workflow: {workflow_id}")

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

        # Step 1: Enhance the prompt using the enhancer agent (skip in fast mode)
        enhanced_prompt = original_description
        enhancement_result = None
        steps_executed = []

        if not fast_mode:
            # Step 1: Enhancement
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
                if enhancement_result.get("success"):
                    result_value = enhancement_result.get("enhanced_prompt")
                    if isinstance(result_value, str):
                        enhanced_prompt = result_value
                    elif isinstance(result_value, dict):
                        enhanced_prompt = result_value.get("enhanced_prompt", original_description)
                    elif result_value is None:
                        if "instruction" in enhancement_result:
                            enhanced_prompt = enhancement_result["instruction"]
                        elif "result" in enhancement_result and isinstance(enhancement_result["result"], str):
                            enhanced_prompt = enhancement_result["result"]
                
                await enhancer.close()
                steps_executed.append("enhance")
                
                # Save checkpoint and documentation
                if checkpoint_manager:
                    checkpoint_manager.save_checkpoint(
                        step_id="enhance",
                        step_number=1,
                        step_output={"enhanced_prompt": enhanced_prompt},
                        artifacts={},
                        step_name="enhanced-prompt",
                    )
                if doc_manager and isinstance(enhanced_prompt, str):
                    doc_manager.save_step_documentation(
                        step_number=1,
                        content=enhanced_prompt,
                        step_name="enhanced-prompt",
                    )
            except Exception as e:
                # If enhancement fails, continue with original prompt
                enhanced_prompt = original_description
                enhancement_result = {"error": str(e), "fallback": True}
                logger.warning(f"Enhancement failed, continuing with original prompt: {e}")
        else:
            logger.info("Fast mode: Skipping enhancement step")

        # Step 2-4: Planning, Architecture, Design (skip in fast mode)
        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=2,  # Allow some parallelization
        )

        # Prepare agent tasks - skip steps 2-4 in fast mode
        agent_tasks = []
        if not fast_mode:
            # Steps 2-4: Plan, Architect, Design
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
            ]
        
        # Step 5: Implementation (always execute)
        agent_tasks.append({
            "agent_id": "implementer-1",
            "agent": "implementer",
            "command": "implement",
            "args": {"specification": enhanced_prompt if not fast_mode else original_description},
        })

        # Execute agent tasks
        if agent_tasks:
            result = await orchestrator.execute_parallel(agent_tasks)
            
            # Track executed steps and save checkpoints
            step_number = 2 if not fast_mode else 1
            for task in agent_tasks:
                agent_name = task["agent"]
                if agent_name in ["planner", "architect", "designer"]:
                    steps_executed.append(agent_name)
                    # Save checkpoint and documentation for each step
                    if checkpoint_manager:
                        step_result = result.get("results", {}).get(task["agent_id"], {})
                        checkpoint_manager.save_checkpoint(
                            step_id=agent_name,
                            step_number=step_number,
                            step_output=step_result,
                            artifacts={},
                            step_name=f"{agent_name}-result",
                        )
                    if doc_manager:
                        step_result = result.get("results", {}).get(task["agent_id"], {})
                        doc_content = f"# Step {step_number}: {agent_name.title()} Result\n\n{step_result}"
                        doc_manager.save_step_documentation(
                            step_number=step_number,
                            content=doc_content,
                            step_name=f"{agent_name}-result",
                        )
                    step_number += 1
        else:
            # Fast mode: Only implementation
            result = await orchestrator.execute_parallel(agent_tasks)
        
        steps_executed.append("implement")

        # Optional: Run evaluator at end if enabled
        evaluation_result = None
        if (self.config and 
            hasattr(self.config, 'agents') and 
            hasattr(self.config.agents, 'evaluator') and 
            getattr(self.config.agents.evaluator, 'auto_run', False)):
            try:
                from tapps_agents.agents.evaluator.agent import EvaluatorAgent
                evaluator = EvaluatorAgent(config=self.config)
                await evaluator.activate(self.project_root, offline_mode=True)
                # Use workflow_id from result if available, or generate one
                import time
                workflow_id = result.get("workflow_id") or f"build-{int(time.time())}"
                evaluation_result = await evaluator.run("evaluate", workflow_id=workflow_id)
                await evaluator.close()
            except Exception as e:
                # Evaluator is optional - log but don't fail workflow
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Evaluator auto-run failed: {e}")

        # Create latest symlink if enabled
        if doc_manager:
            doc_manager.create_latest_symlink()

        return {
            "type": "build",
            "success": result.get("success", False),
            "fast_mode": fast_mode,
            "workflow_id": workflow_id,
            "steps_executed": steps_executed,
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": result.get("summary", {}),
            "enhancement": {
                "original_prompt": original_description,
                "enhanced_prompt": enhanced_prompt,
                "enhancement_result": enhancement_result,
            },
            "context7": context7_info,  # Enhancement 3: Include Context7 detection info
            "evaluation": evaluation_result,  # Optional evaluation result
        }

