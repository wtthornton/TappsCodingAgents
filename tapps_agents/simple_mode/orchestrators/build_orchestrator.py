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
        return ["enhancer", "planner", "architect", "designer", "implementer", "reviewer", "tester", "documenter"]

    def _detect_framework_change(self, intent: Intent, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Detect if this build workflow involves framework changes (new agents, core changes, etc.).
        
        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input
            
        Returns:
            Dictionary with framework change detection results:
            - is_framework_change: bool
            - new_agents: list[str] - List of new agent names detected
            - modified_core: bool - Whether core framework files were modified
            - modified_cli: bool - Whether CLI files were modified
        """
        changes = {
            "is_framework_change": False,
            "new_agents": [],
            "modified_core": False,
            "modified_cli": False,
        }
        
        description = (parameters or {}).get("description", "") or intent.original_input.lower()
        
        # Check for framework-related keywords
        framework_keywords = [
            "new agent", "add agent", "create agent", "framework",
            "tapps_agents/agents", "tapps_agents/core", "tapps_agents/cli",
            "build orchestrator", "simple mode", "workflow"
        ]
        
        if any(keyword in description for keyword in framework_keywords):
            changes["is_framework_change"] = True
        
        # Check for new agent directories
        agents_dir = self.project_root / "tapps_agents" / "agents"
        if agents_dir.exists():
            # Get list of agent directories
            agent_dirs = [d.name for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
            
            # Known agents from config (approximate list)
            known_agents = {
                "analyst", "planner", "architect", "designer", "implementer",
                "debugger", "documenter", "tester", "reviewer", "improver",
                "ops", "orchestrator", "enhancer", "evaluator"
            }
            
            # Detect new agents (not in known list)
            new_agents = [agent for agent in agent_dirs if agent not in known_agents]
            if new_agents:
                changes["new_agents"] = new_agents
                changes["is_framework_change"] = True
        
        # Check if core or CLI files were mentioned
        if "tapps_agents/core" in description or "core/" in description:
            changes["modified_core"] = True
            changes["is_framework_change"] = True
        
        if "tapps_agents/cli" in description or "cli/" in description:
            changes["modified_cli"] = True
            changes["is_framework_change"] = True
        
        return changes

    async def _validate_documentation_completeness(
        self,
        agent_name: str | None = None,
        framework_changes: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """
        Validate that all documentation mentions new agents or framework changes.
        
        Args:
            agent_name: Name of new agent (if applicable)
            framework_changes: Framework change detection results
            
        Returns:
            Dictionary with validation results for each documentation file
        """
        checks = {
            "readme_mentions_agent": True,  # Default to True if no agent
            "api_docs_agent": True,
            "architecture_mentions_agent": True,
            "agent_capabilities_has_section": True,
            "agent_count_consistent": True,
        }
        
        if not agent_name and not framework_changes:
            # No validation needed
            return checks
        
        # Check README.md
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding="utf-8")
            if agent_name:
                checks["readme_mentions_agent"] = agent_name in readme_content or agent_name.title() in readme_content
        
        # Check API.md
        api_path = self.project_root / "docs" / "API.md"
        if api_path.exists():
            api_content = api_path.read_text(encoding="utf-8")
            if agent_name:
                checks["api_docs_agent"] = agent_name in api_content
        
        # Check ARCHITECTURE.md
        arch_path = self.project_root / "docs" / "ARCHITECTURE.md"
        if arch_path.exists():
            arch_content = arch_path.read_text(encoding="utf-8")
            if agent_name:
                checks["architecture_mentions_agent"] = agent_name in arch_content
        
        # Check agent-capabilities.mdc
        capabilities_path = self.project_root / ".cursor" / "rules" / "agent-capabilities.mdc"
        if capabilities_path.exists():
            capabilities_content = capabilities_path.read_text(encoding="utf-8")
            if agent_name:
                checks["agent_capabilities_has_section"] = (
                    f"### {agent_name.title()} Agent" in capabilities_content or
                    f"## {agent_name.title()} Agent" in capabilities_content
                )
        
        return checks

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

        # Step 6-7: Review and Test (if not in fast mode)
        if not fast_mode:
            # Add reviewer and tester steps
            review_test_tasks = [
                {
                    "agent_id": "reviewer-1",
                    "agent": "reviewer",
                    "command": "score",  # Quick score for workflow
                    "args": {},
                },
                {
                    "agent_id": "tester-1",
                    "agent": "tester",
                    "command": "generate-tests",  # Generate tests
                    "args": {},
                },
            ]
            # Note: These would need actual file paths from implementation results
            # For now, we'll skip if no files were created
            if result.get("results"):
                # Execute review and test if we have implementation results
                try:
                    review_test_result = await orchestrator.execute_parallel(review_test_tasks)
                    steps_executed.extend(["review", "test"])
                except Exception as e:
                    logger.warning(f"Review/test steps failed: {e}")

        # Step 8: Framework change detection and documentation update
        doc_update_result = None
        try:
            doc_update_result = await self._execute_documenter_step(
                workflow_id=workflow_id,
                project_root=self.project_root,
                implementation_result=result,
            )
            if doc_update_result and doc_update_result.get("framework_changes_detected"):
                steps_executed.append("documenter")
                logger.info(
                    f"Documentation updated for {len(doc_update_result.get('new_agents', []))} new agent(s)"
                )
        except Exception as e:
            # Documentation updates are optional - log but don't fail workflow
            logger.warning(f"Documentation update step failed: {e}")

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
            "documentation": doc_update_result,  # Documentation update result
        }

    async def _execute_documenter_step(
        self,
        workflow_id: str,
        project_root: Path,
        implementation_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute documenter step for framework changes.

        Detects if new agents were created and updates project documentation.

        Args:
            workflow_id: Workflow ID
            project_root: Project root directory
            implementation_result: Result from implementation step

        Returns:
            Dictionary with documentation update results
        """
        try:
            from tapps_agents.simple_mode.framework_change_detector import (
                FrameworkChangeDetector,
            )
            from tapps_agents.agents.documenter.framework_doc_updater import (
                FrameworkDocUpdater,
            )
            from tapps_agents.agents.documenter.doc_validator import DocValidator

            # 1. Detect framework changes
            detector = FrameworkChangeDetector(project_root)
            # Get known agents from config or previous state
            # For now, we'll detect all current agents and compare with a baseline
            # In the future, we could store known agents in workflow state
            changes = detector.detect_changes(known_agents=None)

            if not changes.new_agents:
                # No framework changes detected, skip documentation updates
                logger.debug("No framework changes detected, skipping documentation updates")
                return {
                    "type": "documenter",
                    "framework_changes_detected": False,
                    "skipped": True,
                }

            logger.info(f"Detected {len(changes.new_agents)} new agent(s): {changes.new_agents}")

            # 2. Update documentation for each new agent
            updater = FrameworkDocUpdater(project_root)
            update_results = {}

            for agent_name in changes.new_agents:
                agent_info = changes.agent_info.get(agent_name)
                if agent_info:
                    result = updater.update_all_docs(agent_name, agent_info)
                    update_results[agent_name] = {
                        "readme_updated": result.readme_updated,
                        "api_updated": result.api_updated,
                        "architecture_updated": result.architecture_updated,
                        "capabilities_updated": result.capabilities_updated,
                        "success": result.success,
                        "errors": result.errors,
                        "warnings": result.warnings,
                    }
                    if result.success:
                        logger.info(f"Successfully updated documentation for {agent_name}")
                    else:
                        logger.warning(
                            f"Documentation update incomplete for {agent_name}: {result.errors}"
                        )

            # 3. Validate documentation
            validator = DocValidator(project_root)
            validation_results = {}

            for agent_name in changes.new_agents:
                result = validator.validate_completeness(agent_name)
                validation_results[agent_name] = {
                    "readme_valid": result.readme_valid,
                    "api_valid": result.api_valid,
                    "architecture_valid": result.architecture_valid,
                    "capabilities_valid": result.capabilities_valid,
                    "consistency_valid": result.consistency_valid,
                    "is_complete": result.is_complete,
                    "errors": result.errors,
                    "warnings": result.warnings,
                }

            # 4. Check consistency
            consistency = validator.check_consistency()

            # 5. Generate report
            # Aggregate validation results
            all_readme_valid = all(
                r["readme_valid"] for r in validation_results.values()
            )
            all_api_valid = all(r["api_valid"] for r in validation_results.values())
            all_arch_valid = all(
                r["architecture_valid"] for r in validation_results.values()
            )
            all_cap_valid = all(
                r["capabilities_valid"] for r in validation_results.values()
            )

            from tapps_agents.agents.documenter.doc_validator import ValidationResult

            aggregated_result = ValidationResult(
                readme_valid=all_readme_valid,
                api_valid=all_api_valid,
                architecture_valid=all_arch_valid,
                capabilities_valid=all_cap_valid,
                consistency_valid=consistency.is_consistent,
                agent_count=consistency.counts,
                errors=[],
                warnings=[],
            )

            # Collect all errors and warnings
            for agent_result in validation_results.values():
                aggregated_result.errors.extend(agent_result.get("errors", []))
                aggregated_result.warnings.extend(agent_result.get("warnings", []))

            report = validator.generate_report(aggregated_result)

            return {
                "type": "documenter",
                "framework_changes_detected": True,
                "new_agents": changes.new_agents,
                "update_results": update_results,
                "validation_results": validation_results,
                "consistency": {
                    "is_consistent": consistency.is_consistent,
                    "counts": consistency.counts,
                    "discrepancies": consistency.discrepancies,
                },
                "report": report,
                "success": aggregated_result.is_complete,
            }
        except ImportError as e:
            logger.warning(f"Documentation update components not available: {e}")
            return {
                "type": "documenter",
                "framework_changes_detected": False,
                "skipped": True,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Documentation update step failed: {e}", exc_info=True)
            return {
                "type": "documenter",
                "framework_changes_detected": False,
                "error": str(e),
            }

