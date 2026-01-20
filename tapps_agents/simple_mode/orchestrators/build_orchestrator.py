"""
Build Orchestrator - Coordinates feature development workflow.

Coordinates: Enhancer → Planner → Architect → Designer → Implementer

2025 Python 3.13+ patterns:
- Pydantic v2 for structured step results
- Decorator-based formatter registry
- Agent contract validation
- Step dependency management with failure cascades
"""

# @ai-prime-directive: This file implements the Build Orchestrator for Simple Mode feature development.
# The Build Orchestrator coordinates the complete 7-step workflow: enhance → plan → architect → design
# → implement → review → test. This is the primary workflow for new feature development in TappsCodingAgents.
# Do not modify the workflow sequence or step dependencies without updating Simple Mode documentation.

# @ai-constraints:
# - Must maintain the exact 7-step workflow sequence (enhance, plan, architect, design, implement, review, test)
# - Step dependencies must be enforced - earlier steps must complete before later steps
# - Workflow documentation must be generated for each step
# - Quality gates must be enforced (reviewer score ≥ 70, test coverage ≥ 75%)
# - Performance: Complete workflow execution should complete in <30 minutes for typical features

# @note[2025-02-01]: Build Orchestrator is the primary Simple Mode workflow for feature development.
# All new features should use this orchestrator via @simple-mode *build command.
# See docs/SIMPLE_MODE_GUIDE.md and .cursor/rules/simple-mode.mdc

import logging
import re
from pathlib import Path
from typing import Any, Callable

from tapps_agents.agents.enhancer.agent import EnhancerAgent
from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..output_aggregator import SimpleModeOutputAggregator
from tapps_agents.simple_mode.documentation_manager import (
    WorkflowDocumentationManager,
)
from tapps_agents.simple_mode.documentation_reader import (
    WorkflowDocumentationReader,
)
from tapps_agents.workflow.models import Artifact
from tapps_agents.workflow.step_checkpoint import StepCheckpointManager
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator
from .deliverable_checklist import DeliverableChecklist
from .requirements_tracer import RequirementsTracer

# New 2025 modules for workflow documentation quality
from ..agent_contracts import AgentContractValidator
from ..file_inference import TargetFileInferencer
from ..result_formatters import (
    FormatterRegistry,
    format_failed_step,
    format_skipped_step,
    format_step_result,
)
from ..step_dependencies import (
    StepDependencyManager,
    StepExecutionState,
    WorkflowStep,
)
from ..step_results import StepResultParser, StepStatus

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
        on_step_start: Callable[[int, str], None] | None = None,
        on_step_complete: Callable[[int, str, str], None] | None = None,
        on_step_error: Callable[[int, str, Exception], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute build workflow with prompt enhancement.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input
            fast_mode: If True, skip steps 1-4 (enhance, plan, architect, design)
            on_step_start: Optional callback when step starts (step_num, step_name)
            on_step_complete: Optional callback when step completes (step_num, step_name, status)
            on_step_error: Optional callback when step errors (step_num, step_name, error)

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

        from ..beads_hooks import create_build_issue, close_issue

        # Resolve workflow_id: reuse when resuming, otherwise generate
        workflow_id = parameters.get("workflow_id") or WorkflowDocumentationManager.generate_workflow_id("build")
        beads_issue_id: str | None = parameters.get("beads_issue_id")
        if beads_issue_id is None and self.config:
            beads_issue_id = create_build_issue(
                self.project_root, self.config, original_description
            )
        # Persist beads_issue_id for resume (avoid duplicate bd issues)
        if beads_issue_id and "beads_issue_id" not in (parameters or {}):
            try:
                state_dir = self.project_root / ".tapps-agents" / "workflow-state"
                wf_dir = state_dir / workflow_id
                wf_dir.mkdir(parents=True, exist_ok=True)
                (wf_dir / ".beads_issue_id").write_text(beads_issue_id, encoding="utf-8")
            except OSError as e:
                logger.debug("beads: could not persist beads_issue_id for resume: %s", e)

        doc_manager: WorkflowDocumentationManager | None = None
        checkpoint_manager: StepCheckpointManager | None = None

        try:
            # Initialize output aggregator for Simple Mode enhancements
            output_aggregator = SimpleModeOutputAggregator(
                workflow_id=workflow_id,
                workflow_type="build",
            )

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
                logger.debug(f"Context7 auto-detection failed in build workflow: {e}")

            # Step 1: Enhance the prompt using the enhancer agent (skip in fast mode)
            enhanced_prompt = original_description
            enhancement_result = None
            steps_executed = []

            if not fast_mode:
                # Step 1: Enhancement
                step_num = 1
                step_name = "Enhance prompt (requirements analysis)"
                if on_step_start:
                    on_step_start(step_num, step_name)
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
                
                    # Notify step completion
                    if on_step_complete:
                        on_step_complete(step_num, step_name, "success")
                
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
                    if on_step_error:
                        on_step_error(step_num, step_name, e)
                    elif on_step_complete:
                        on_step_complete(step_num, step_name, "failed")
            else:
                logger.info("Fast mode: Skipping enhancement step")

            # Initialize checklist and tracer for verification (after Step 1)
            checklist = DeliverableChecklist(requirements={"enhanced_prompt": enhanced_prompt})
            tracer = RequirementsTracer(requirements={})
            workflow_state = {
                "checklist": checklist,
                "tracer": tracer,
                "loopback_count": 0,
            }
        
            # Track documentation files created
            if doc_manager:
                checklist.add_deliverable(
                    "documentation",
                    "Step 1: Enhanced prompt",
                    doc_manager.get_step_file_path(1, "enhanced-prompt") if doc_manager else Path(),
                    status="complete",
                    metadata={"step_number": 1},
                )

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
                step_names = {
                    "planner": (2, "Create user stories"),
                    "architect": (3, "Design architecture"),
                    "designer": (4, "Design API/data models"),
                }
                # FIXED: Use correct command names and parameters per agent contracts
                # - Architect: "design-system" with "requirements" (not "design" with "specification")
                # - Designer: "design-api" with "requirements" (not "specification")
                agent_tasks = [
                    {
                        "agent_id": "planner-1",
                        "agent": "planner",
                        "command": "create-story",
                        "args": {"description": enhanced_prompt},
                        "step_num": 2,
                        "step_name": "Create user stories",
                    },
                    {
                        "agent_id": "architect-1",
                        "agent": "architect",
                        "command": "design-system",  # FIXED: was "design"
                        "args": {"requirements": enhanced_prompt},  # FIXED: was "specification"
                        "step_num": 3,
                        "step_name": "Design architecture",
                    },
                    {
                        "agent_id": "designer-1",
                        "agent": "designer",
                        "command": "design-api",
                        "args": {"requirements": enhanced_prompt},  # FIXED: was "specification"
                        "step_num": 4,
                        "step_name": "Design API/data models",
                    },
                ]
            
                # Validate agent tasks before execution (pre-execution contract validation)
                validator = AgentContractValidator()
                validation_result = validator.validate_tasks(agent_tasks)
                if not validation_result.valid:
                    logger.error(f"Agent task validation failed: {validation_result.errors}")
                    # Log errors but continue - let agents report their own errors
                    for error in validation_result.errors:
                        logger.warning(f"Contract validation error: {error}")
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        logger.debug(f"Contract validation warning: {warning}")
            
                # Notify step starts for steps 2-4
                for task in agent_tasks:
                    if on_step_start:
                        on_step_start(task["step_num"], task["step_name"])
        
            # Step 5: Implementation (always execute)
            # Enrich context with previous step documentation if available
            implementer_args = self._enrich_implementer_context(
                workflow_id=workflow_id,
                doc_manager=doc_manager,
                enhanced_prompt=enhanced_prompt if not fast_mode else original_description,
            )
        
            # FIXED: Implementer requires file_path parameter
            # Use TargetFileInferencer to infer target file from description
            if "file_path" not in implementer_args or not implementer_args.get("file_path"):
                file_inferencer = TargetFileInferencer(self.project_root)
                inferred_path = file_inferencer.infer_target_file(
                    description=original_description,
                    context={
                        "architecture": implementer_args.get("architecture"),
                        "api_design": implementer_args.get("api_design"),
                    },
                )
                implementer_args["file_path"] = inferred_path
                logger.info(f"Inferred target file path: {inferred_path}")
        
            step_5_num = 5 if not fast_mode else 1
            step_5_name = "Implement code"
            if on_step_start:
                on_step_start(step_5_num, step_5_name)
        
            agent_tasks.append({
                "agent_id": "implementer-1",
                "agent": "implementer",
                "command": "implement",
                "args": implementer_args,
                "step_num": step_5_num,
                "step_name": step_5_name,
            })

            # Execute agent tasks
            workflow_errors = []  # Track errors for final reporting
            result = {"success": True, "results": {}}  # Default result
            if agent_tasks:
                try:
                    result = await orchestrator.execute_parallel(agent_tasks)
                
                    # Track executed steps and save checkpoints
                    step_number = 2 if not fast_mode else 1
                    for task in agent_tasks:
                        agent_name = task["agent"]
                        task_step_num = task.get("step_num", step_number)
                        task_step_name = task.get("step_name", agent_name)
                    
                        # Check if task succeeded
                        task_result = result.get("results", {}).get(task["agent_id"], {})
                        task_success = result.get("success", True) and task_result.get("success", True)
                    
                        # Collect error information if task failed
                        if not task_success:
                            error_msg = self._extract_error_message(task_result)
                            workflow_errors.append({
                                "step": task_step_num,
                                "agent": agent_name,
                                "agent_id": task.get("agent_id"),
                                "error": error_msg,
                            })
                            logger.error(f"Step {task_step_num} ({agent_name}) failed: {error_msg}")
                    
                        if agent_name in ["planner", "architect", "designer", "implementer"]:
                            steps_executed.append(agent_name)
                        
                            # Add output to aggregator (Simple Mode Enhancement)
                            output_aggregator.add_step_output(
                                step_number=task_step_num,
                                step_name=task_step_name,
                                agent_name=agent_name,
                                output=task_result,
                                success=task_success,
                                metadata={
                                    "artifacts": task_result.get("artifacts", []),
                                    "file_paths": task_result.get("file_paths", []),
                                },
                            )
                        
                            # Notify step completion
                            if on_step_complete:
                                status = "success" if task_success else "failed"
                                on_step_complete(task_step_num, task_step_name, status)
                        
                            # Track documentation in checklist
                            if doc_manager:
                                doc_file_path = doc_manager.get_step_file_path(task_step_num, f"{agent_name}-result")
                                checklist.add_deliverable(
                                    "documentation",
                                    f"Step {task_step_num}: {agent_name.title()} Result",
                                    doc_file_path,
                                    status="complete",
                                    metadata={"step_number": task_step_num},
                                )
                        
                            # Extract requirement IDs from user stories (Step 2)
                            if agent_name == "planner" and task_success:
                                try:
                                    # Try to extract user stories from result
                                    user_stories_data = task_result.get("result") or task_result.get("output") or str(task_result)
                                    # Try to parse as JSON if possible, otherwise extract IDs from text
                                    import json
                                    try:
                                        if isinstance(user_stories_data, str):
                                            user_stories_parsed = json.loads(user_stories_data)
                                        else:
                                            user_stories_parsed = user_stories_data
                                    
                                        if isinstance(user_stories_parsed, list):
                                            req_ids = tracer.extract_requirement_ids(user_stories_parsed)
                                            # Build requirements dict from user stories
                                            requirements_dict = {}
                                            for story in user_stories_parsed:
                                                req_id = story.get("id") or story.get("requirement_id")
                                                if req_id:
                                                    requirements_dict[req_id] = story
                                            if requirements_dict:
                                                tracer.requirements = requirements_dict
                                                logger.info(f"Extracted {len(requirements_dict)} requirement IDs from user stories")
                                    except (json.JSONDecodeError, AttributeError, TypeError):
                                        # Fallback: extract IDs from text
                                        req_ids = tracer.extract_requirement_ids([{"id": None, "text": str(user_stories_data)}])
                                        logger.debug(f"Extracted {len(req_ids)} requirement IDs from user stories text")
                                except Exception as e:
                                    logger.debug(f"Failed to extract requirement IDs from planner result: {e}")
                        
                            # Track implemented files (Step 5)
                            if agent_name == "implementer" and task_success:
                                implemented_files_list = self._extract_implemented_files(task_result)
                                for file_path in implemented_files_list:
                                    checklist.add_deliverable(
                                        "core_code",
                                        f"Implementation: {file_path.name}",
                                        file_path,
                                        status="complete",
                                        metadata={"step_number": 5},
                                    )
                                    # Link to requirements (if we have any)
                                    for req_id in tracer.requirements.keys():
                                        tracer.add_trace(req_id, "code", file_path)
                        
                            # Save checkpoint and documentation for each step
                            if checkpoint_manager:
                                checkpoint_manager.save_checkpoint(
                                    step_id=agent_name,
                                    step_number=task_step_num,
                                    step_output=task_result,
                                    artifacts={},
                                    step_name=f"{agent_name}-result",
                                )
                            if doc_manager:
                                # FIXED: Use structured result parser and formatters
                                # instead of raw JSON dumps
                                parsed_result = StepResultParser.parse(
                                    agent_name=agent_name,
                                    raw=task_result,
                                    step_number=task_step_num,
                                )
                            
                                # FIXED: Save appropriate documentation based on success/failure
                                if task_success:
                                    doc_content = format_step_result(parsed_result)
                                else:
                                    # Extract error message for placeholder documentation
                                    error_msg = self._extract_error_message(task_result)
                                    doc_content = format_failed_step(
                                        step_number=task_step_num,
                                        agent_name=agent_name,
                                        error_message=error_msg,
                                    )
                            
                                doc_manager.save_step_documentation(
                                    step_number=task_step_num,
                                    content=doc_content,
                                    step_name=f"{agent_name}-result",
                                )
                            step_number += 1
                except Exception as e:
                    # Handle execution errors - capture exception as workflow error
                    error_str = str(e)
                    workflow_errors.append({
                        "step": 0,  # Unknown step
                        "agent": "orchestrator",
                        "agent_id": "orchestrator",
                        "error": f"Workflow execution exception: {error_str}",
                    })
                    logger.error(f"Workflow execution failed: {e}", exc_info=True)
                
                    # Notify step errors
                    for task in agent_tasks:
                        task_step_num = task.get("step_num", 0)
                        task_step_name = task.get("step_name", task["agent"])
                        if on_step_error:
                            on_step_error(task_step_num, task_step_name, e)
                        elif on_step_complete:
                            on_step_complete(task_step_num, task_step_name, "failed")
                
                    # Set result to indicate failure
                    result = {
                        "success": False,
                        "error": error_str,
                        "results": {},
                    }
            else:
                # Fast mode: Only implementation
                result = await orchestrator.execute_parallel(agent_tasks)
        
            steps_executed.append("implement")

            # Step 6-7: Review and Test (if not in fast_mode)
            implemented_files_list = []
            if not fast_mode:
                # Extract implemented files from result
                implemented_files_list = self._extract_implemented_files(result)
            
                # Add reviewer and tester steps
                step_6_name = "Review code quality"
                step_7_name = "Generate tests"
            
                if on_step_start:
                    on_step_start(6, step_6_name)
                    on_step_start(7, step_7_name)
            
                review_test_tasks = [
                    {
                        "agent_id": "reviewer-1",
                        "agent": "reviewer",
                        "command": "score",  # Quick score for workflow
                        "args": {},
                        "step_num": 6,
                        "step_name": step_6_name,
                    },
                    {
                        "agent_id": "tester-1",
                        "agent": "tester",
                        "command": "generate-tests",  # Generate tests
                        "args": {},
                        "step_num": 7,
                        "step_name": step_7_name,
                    },
                ]
                # Note: These would need actual file paths from implementation results
                # For now, we'll skip if no files were created
                if result.get("results"):
                    # Execute review and test if we have implementation results
                    try:
                        review_test_result = await orchestrator.execute_parallel(review_test_tasks)
                        steps_executed.extend(["review", "test"])
                    
                        # Track test files from tester result (Step 7 enhancement)
                        tester_result = review_test_result.get("results", {}).get("tester-1", {})
                        if tester_result:
                            test_files_list = self._extract_test_files(tester_result)
                            for test_file in test_files_list:
                                checklist.add_deliverable(
                                    "tests",
                                    f"Test: {test_file.name}",
                                    test_file,
                                    status="complete",
                                    metadata={"step_number": 7},
                                )
                                # Link tests to requirements
                                for req_id in tracer.requirements.keys():
                                    tracer.add_trace(req_id, "tests", test_file)
                    
                        # Add review/test outputs to aggregator
                        reviewer_result = review_test_result.get("results", {}).get("reviewer-1", {})
                        if reviewer_result:
                            output_aggregator.add_step_output(
                                step_number=6,
                                step_name=step_6_name,
                                agent_name="reviewer",
                                output=reviewer_result,
                                success=reviewer_result.get("success", True),
                            )
                        if tester_result:
                            output_aggregator.add_step_output(
                                step_number=7,
                                step_name=step_7_name,
                                agent_name="tester",
                                output=tester_result,
                                success=tester_result.get("success", True),
                                metadata={"test_files": test_files_list if tester_result else []},
                            )
                    
                        # Notify step completions
                        if on_step_complete:
                            on_step_complete(6, step_6_name, "success")
                            on_step_complete(7, step_7_name, "success")
                    except Exception as e:
                        logger.warning(f"Review/test steps failed: {e}")
                        if on_step_error:
                            on_step_error(6, step_6_name, e)
                            on_step_error(7, step_7_name, e)
                        elif on_step_complete:
                            on_step_complete(6, step_6_name, "failed")
                            on_step_complete(7, step_7_name, "failed")

            # Step 8: Comprehensive Verification (NEW)
            verification_result = None
            if not fast_mode:
                step_8_name = "Comprehensive verification"
                if on_step_start:
                    on_step_start(8, step_8_name)
                try:
                    # Prepare requirements dict from tracer
                    requirements_dict = tracer.requirements or {}
                
                    # FIXED: Pass agent results to enable failure detection
                    verification_result = await self._step_8_verification(
                        workflow_id=workflow_id,
                        requirements=requirements_dict,
                        checklist=checklist,
                        tracer=tracer,
                        implemented_files=implemented_files_list,
                        doc_manager=doc_manager,
                        agent_results=result.get("results", {}),
                    )
                
                    steps_executed.append("verification")
                
                    # Handle gaps with loopback if needed
                    if not verification_result.get("complete") and verification_result.get("loopback_step"):
                        loopback_result = await self._handle_verification_gaps(
                            gaps=verification_result.get("gaps", []),
                            current_step=8,
                            checklist=checklist,
                            tracer=tracer,
                            workflow_state=workflow_state,
                        )
                    
                        if loopback_result.get("loopback"):
                            logger.warning(
                                f"Workflow verification incomplete. "
                                f"Loopback recommended to Step {loopback_result.get('loopback_step')}. "
                                f"Gaps: {len(verification_result.get('gaps', []))} items"
                            )
                
                    if on_step_complete:
                        status = "success" if verification_result.get("complete") else "warning"
                        on_step_complete(8, step_8_name, status)
                except Exception as e:
                    logger.warning(f"Step 8 verification failed: {e}")
                    if on_step_error:
                        on_step_error(8, step_8_name, e)
                    elif on_step_complete:
                        on_step_complete(8, step_8_name, "failed")

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
                    logger.debug(f"Evaluator auto-run failed: {e}")

            # Create latest symlink if enabled
            if doc_manager:
                doc_manager.create_latest_symlink()
                # Create workflow summary
                try:
                    doc_manager.create_workflow_summary()
                except Exception as e:
                    logger.warning(f"Failed to create workflow summary: {e}")

            # Determine overall success and collect error message
            overall_success = result.get("success", False) if agent_tasks else True
            error_message = None
        
            if workflow_errors:
                # Build error message from collected errors
                error_parts = []
                for err in workflow_errors:
                    error_parts.append(f"Step {err['step']} ({err['agent']}): {err['error']}")
                error_message = "; ".join(error_parts)
            elif not overall_success:
                # Fallback: extract error from result
                if "error" in result:
                    error_message = str(result["error"])
                else:
                    error_message = "Workflow execution failed (see results for details)"
        
            # Aggregate all outputs (Simple Mode Enhancement)
            aggregated_output = output_aggregator.aggregate()
            executable_instructions = output_aggregator.get_executable_instructions()

            return {
                "type": "build",
                "success": overall_success,
                "error": error_message,  # Include error message for reporting
                "errors": workflow_errors,  # Include detailed error list
                "fast_mode": fast_mode,
                "workflow_id": workflow_id,
                "steps_executed": steps_executed,
                "agents_executed": result.get("total_agents", 0) if agent_tasks else 0,
                "results": result.get("results", {}) if agent_tasks else {},
                "summary": result.get("summary", {}) if agent_tasks else {},
                "enhancement": {
                    "original_prompt": original_description,
                    "enhanced_prompt": enhanced_prompt,
                    "enhancement_result": enhancement_result,
                },
                "context7": context7_info,  # Enhancement 3: Include Context7 detection info
                "evaluation": evaluation_result,  # Optional evaluation result
                "documentation": doc_update_result,  # Documentation update result
                "verification": verification_result,  # Step 8 verification result
                "checklist": checklist.to_dict() if not fast_mode else None,  # Deliverable checklist
                "tracer": tracer.to_dict() if not fast_mode else None,  # Requirements tracer
                # Simple Mode Enhancements (Phase 6.1)
                "aggregated_output": aggregated_output,
                "executable_instructions": executable_instructions,
                "output_summary": output_aggregator.format_summary(),
            }
        finally:
            close_issue(self.project_root, beads_issue_id)

    def _enrich_implementer_context(
        self,
        workflow_id: str,
        doc_manager: WorkflowDocumentationManager | None,
        enhanced_prompt: str,
    ) -> dict[str, Any]:
        """
        Enrich implementer context with previous step documentation.

        Args:
            workflow_id: Workflow identifier
            doc_manager: Documentation manager instance (None if not enabled)
            enhanced_prompt: Enhanced prompt from step 1 (fallback)

        Returns:
            Dictionary with implementer arguments including all previous step outputs
        """
        # Start with enhanced prompt as base
        args = {"specification": enhanced_prompt}

        # If documentation manager is not available, return base args (backward compatible)
        if not doc_manager:
            logger.debug("Documentation manager not available, using in-memory enhanced_prompt only")
            return args

        # Create documentation reader
        try:
            reader = WorkflowDocumentationReader(
                base_dir=doc_manager.base_dir,
                workflow_id=workflow_id,
            )

            # Read previous step documentation
            # Step 1: Enhanced prompt
            step1_content = reader.read_step_documentation(1, "enhanced-prompt")
            if step1_content:
                # Extract enhanced prompt from content (first 2000 chars or full content)
                args["specification"] = step1_content[:2000] if len(step1_content) > 2000 else step1_content
                logger.debug("Read enhanced prompt from step1-enhanced-prompt.md")

            # Step 2: User stories
            step2_content = reader.read_step_documentation(2, "user-stories")
            if step2_content:
                args["user_stories"] = step2_content[:3000] if len(step2_content) > 3000 else step2_content
                logger.debug("Read user stories from step2-user-stories.md")

            # Step 3: Architecture
            step3_content = reader.read_step_documentation(3, "architecture")
            if step3_content:
                args["architecture"] = step3_content[:3000] if len(step3_content) > 3000 else step3_content
                logger.debug("Read architecture from step3-architecture.md")

            # Step 4: API Design
            step4_content = reader.read_step_documentation(4, "design")
            if step4_content:
                args["api_design"] = step4_content[:3000] if len(step4_content) > 3000 else step4_content
                logger.debug("Read API design from step4-design.md")

            logger.info(f"Enriched implementer context with {len([k for k in args.keys() if k != 'specification'])} previous step outputs")

        except Exception as e:
            logger.warning(f"Failed to enrich implementer context, using fallback: {e}")
            # Fallback to base args if reading fails

        return args

    def _find_last_completed_step(
        self,
        workflow_id: str,
    ) -> int:
        """
        Find last completed step by checking for step .md files.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Last completed step number (0 if no steps completed)
        """
        base_dir = self.project_root / "docs" / "workflows" / "simple-mode"
        doc_dir = base_dir / workflow_id

        if not doc_dir.exists():
            logger.debug(f"Workflow directory not found: {doc_dir}")
            return 0

        # Find all step files
        step_files = list(doc_dir.glob("step*.md"))
        if not step_files:
            return 0

        # Extract step numbers
        step_numbers = []
        for step_file in step_files:
            # Match: step{N}-{name}.md or step{N}.md
            import re
            match = re.match(r"step(\d+)", step_file.stem)
            if match:
                step_numbers.append(int(match.group(1)))

        if not step_numbers:
            return 0

        last_step = max(step_numbers)
        logger.debug(f"Last completed step: {last_step}")
        return last_step

    async def resume(
        self,
        workflow_id: str,
        from_step: int | None = None,
    ) -> dict[str, Any]:
        """
        Resume workflow from last completed step.

        Args:
            workflow_id: Workflow identifier
            from_step: Step to resume from (None = auto-detect)

        Returns:
            Dictionary with execution results

        Raises:
            ValueError: If workflow_id is invalid
            FileNotFoundError: If workflow directory doesn't exist
        """
        if not workflow_id or ".." in workflow_id or "/" in workflow_id:
            raise ValueError(f"Invalid workflow_id: {workflow_id}")

        base_dir = self.project_root / "docs" / "workflows" / "simple-mode"
        doc_dir = base_dir / workflow_id

        if not doc_dir.exists():
            raise FileNotFoundError(f"Workflow directory not found: {doc_dir}")

        # Find last completed step if not specified
        if from_step is None:
            from_step = self._find_last_completed_step(workflow_id)
            if from_step == 0:
                raise ValueError(f"No completed steps found for workflow: {workflow_id}")

        logger.info(f"Resuming workflow {workflow_id} from step {from_step + 1}")

        # Load state from previous steps
        doc_manager = WorkflowDocumentationManager(
            base_dir=base_dir,
            workflow_id=workflow_id,
        )
        reader = WorkflowDocumentationReader(
            base_dir=base_dir,
            workflow_id=workflow_id,
        )

        # Restore state
        state = {}
        for step_num in range(1, from_step + 1):
            step_state = reader.read_step_state(step_num)
            if step_state:
                state[f"step{step_num}"] = step_state

        # Restore context
        enhanced_prompt = state.get("step1", {}).get("agent_output", {}).get("enhanced_prompt", "")
        if not enhanced_prompt:
            # Fallback: read from markdown
            enhanced_prompt = reader.read_step_documentation(1, "enhanced-prompt")[:2000]

        # Create intent from restored state
        from ..intent_parser import Intent, IntentType
        intent = Intent(
            original_input=enhanced_prompt or "Resume workflow",
            type=IntentType.BUILD,
            confidence=1.0,
            parameters={},
        )

        # Load beads_issue_id from persistence so we reuse the same bd issue (no duplicate)
        beads_issue_id = None
        state_dir = self.project_root / ".tapps-agents" / "workflow-state"
        beads_file = state_dir / workflow_id / ".beads_issue_id"
        if beads_file.exists():
            try:
                beads_issue_id = beads_file.read_text(encoding="utf-8").strip() or None
            except OSError:
                pass

        # Execute from next step (pass workflow_id and beads_issue_id to avoid duplicate bd issues)
        parameters = {
            "description": enhanced_prompt,
            "resume_from_step": from_step + 1,
            "workflow_id": workflow_id,
            "beads_issue_id": beads_issue_id,
        }

        # Execute workflow (will use restored context)
        return await self.execute(intent, parameters, fast_mode=False)

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

    def _extract_implemented_files(self, result: dict[str, Any]) -> list[Path]:
        """Extract implemented file paths from implementation result.
        
        Args:
            result: Implementation result dictionary
            
        Returns:
            List of implemented file paths
        """
        files = []
        
        # Try to extract from results
        implementer_result = result.get("results", {}).get("implementer-1", {})
        if not implementer_result:
            # Try direct access
            implementer_result = result
        
        # Check for file paths in various formats
        # Format 1: Direct file_path or file_paths
        if "file_path" in implementer_result:
            file_path_str = implementer_result["file_path"]
            if isinstance(file_path_str, str):
                file_path = self.project_root / file_path_str
                if file_path.exists():
                    files.append(file_path)
        
        if "file_paths" in implementer_result:
            file_paths_list = implementer_result["file_paths"]
            if isinstance(file_paths_list, list):
                for fp in file_paths_list:
                    if isinstance(fp, str):
                        file_path = self.project_root / fp
                    elif isinstance(fp, Path):
                        file_path = fp
                    else:
                        continue
                    if file_path.exists():
                        files.append(file_path)
        
        # Format 2: Artifacts
        artifacts = implementer_result.get("artifacts", [])
        if isinstance(artifacts, list):
            for artifact in artifacts:
                if isinstance(artifact, dict) and "path" in artifact:
                    file_path = Path(artifact["path"])
                    if file_path.exists():
                        files.append(file_path)
        
        # Format 3: Check result text for file paths
        result_text = str(implementer_result.get("result", "")) or str(implementer_result.get("output", ""))
        if result_text:
            # Look for common file patterns
            import re
            # Match: file paths like "src/file.py" or "tapps_agents/..."
            pattern = r"(?:^|\s)([a-zA-Z0-9_/\\-]+\.(py|yaml|yml|md|txt|json))\b"
            matches = re.findall(pattern, result_text)
            for match in matches[:10]:  # Limit to 10 files
                file_path = self.project_root / match[0]
                if file_path.exists() and file_path not in files:
                    files.append(file_path)
        
        logger.debug(f"Extracted {len(files)} implemented files from result")
        return files

    def _extract_test_files(self, tester_result: dict[str, Any]) -> list[Path]:
        """Extract test file paths from tester result.
        
        Args:
            tester_result: Tester result dictionary
            
        Returns:
            List of test file paths
        """
        files = []
        
        # Similar extraction logic as _extract_implemented_files
        if "file_path" in tester_result:
            file_path_str = tester_result["file_path"]
            if isinstance(file_path_str, str):
                file_path = self.project_root / file_path_str
                if file_path.exists():
                    files.append(file_path)
        
        if "file_paths" in tester_result:
            file_paths_list = tester_result["file_paths"]
            if isinstance(file_paths_list, list):
                for fp in file_paths_list:
                    if isinstance(fp, str):
                        file_path = self.project_root / fp
                    elif isinstance(fp, Path):
                        file_path = fp
                    else:
                        continue
                    if file_path.exists():
                        files.append(file_path)
        
        # Check result text for test file patterns
        result_text = str(tester_result.get("result", "")) or str(tester_result.get("output", ""))
        if result_text:
            import re
            # Match test files: test_*.py or *_test.py
            pattern = r"(?:^|\s)((?:test_|_test)[a-zA-Z0-9_/\\-]+\.py)\b"
            matches = re.findall(pattern, result_text)
            for match in matches[:10]:  # Limit to 10 files
                file_path = self.project_root / match
                if file_path.exists() and file_path not in files:
                    files.append(file_path)
        
        logger.debug(f"Extracted {len(files)} test files from tester result")
        return files

    async def _step_8_verification(
        self,
        workflow_id: str,
        requirements: dict[str, Any],
        checklist: DeliverableChecklist,
        tracer: RequirementsTracer,
        implemented_files: list[Path],
        doc_manager: WorkflowDocumentationManager | None = None,
        agent_results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Verify all requirements are fully implemented.

        Args:
            workflow_id: Workflow ID
            requirements: Requirements dict
            checklist: DeliverableChecklist instance
            tracer: RequirementsTracer instance
            implemented_files: List of implemented files
            doc_manager: Documentation manager
            agent_results: Results from all agent steps (to detect failures)

        Returns:
            Dictionary with verification results and gaps
        """
        logger.info("Step 8: Running comprehensive verification")

        verification_results = {
            "core_implementation": self._verify_core_code(implemented_files),
            "related_files": self._verify_related_files(checklist, implemented_files),
            "documentation": self._verify_documentation(checklist),
            "tests": self._verify_tests(checklist),
            "templates": self._verify_templates(checklist),
            "requirements": tracer.verify_all_requirements(),
        }

        # Identify gaps
        gaps = []
        checklist_verification = checklist.verify_completeness()
        gaps.extend(checklist_verification.get("gaps", []))

        # Add requirement gaps
        req_verification = verification_results["requirements"]
        gaps.extend(req_verification.get("gaps", []))

        # FIXED: Check for agent failures (prevents false "All deliverables verified")
        agent_results = agent_results or {}
        agent_failures = self._detect_agent_failures(agent_results)
        if agent_failures:
            verification_results["agent_failures"] = agent_failures
            # Add agent failures as gaps
            for failure in agent_failures:
                gaps.append({
                    "category": "agent_failure",
                    "step": failure.get("step"),
                    "agent": failure.get("agent"),
                    "error": failure.get("error"),
                    "item": f"Step {failure.get('step')} ({failure.get('agent')}) failed: {failure.get('error', 'Unknown error')[:100]}",
                })

        # Determine loopback step
        loopback_step = None
        if gaps:
            loopback_step = self._determine_loopback_step(gaps)

        # Generate verification report
        report = self._generate_verification_report(
            verification_results, gaps, loopback_step
        )

        # Save verification report
        if doc_manager:
            doc_manager.save_step_documentation(
                step_number=8,
                content=report,
                step_name="verification",
            )

        return {
            "complete": len(gaps) == 0,
            "gaps": gaps,
            "verification_results": verification_results,
            "loopback_step": loopback_step,
            "report": report,
        }

    def _extract_error_message(self, task_result: dict[str, Any]) -> str:
        """Extract error message from a failed task result.

        Args:
            task_result: Result dictionary from agent execution

        Returns:
            Error message string
        """
        # Check if result is completely missing (empty dict with no keys)
        # This happens when agent_id is not found in results
        if not task_result or (isinstance(task_result, dict) and len(task_result) == 0):
            return "Agent execution result not found (agent may not have been executed or result was not returned)"
        
        # Try various formats agents use to report errors
        if "error" in task_result:
            error_val = task_result["error"]
            if isinstance(error_val, (str, int, float)):
                return str(error_val)
            elif isinstance(error_val, dict):
                # Try to extract message from error dict
                if "message" in error_val:
                    return str(error_val["message"])
                if "error" in error_val:
                    return str(error_val["error"])
                # Fall back to string representation
                return str(error_val)[:500]
        
        if "result" in task_result:
            nested = task_result["result"]
            if isinstance(nested, dict):
                # Check for nested error fields
                if "error" in nested:
                    error_val = nested["error"]
                    if isinstance(error_val, str):
                        return error_val
                    elif isinstance(error_val, dict) and "message" in error_val:
                        return str(error_val["message"])
                    return str(error_val)[:500]
                if "message" in nested:
                    return str(nested["message"])
                # Check for exception information
                if "exception" in nested:
                    return str(nested["exception"])
                if "traceback" in nested:
                    # Extract first line of traceback
                    tb = nested["traceback"]
                    if isinstance(tb, str):
                        lines = tb.split("\n")
                        if lines:
                            return lines[0][:500]
            elif isinstance(nested, str):
                if "error" in nested.lower() or "failed" in nested.lower() or "exception" in nested.lower():
                    return nested[:500]
        
        if "message" in task_result:
            return str(task_result["message"])
        
        # Check for exception info at top level
        if "exception" in task_result:
            return str(task_result["exception"])
        
        if "traceback" in task_result:
            tb = task_result["traceback"]
            if isinstance(tb, str):
                lines = tb.split("\n")
                if lines:
                    return lines[0][:500]
        
        # Check performance metrics for error info
        if "performance_metrics" in task_result:
            perf = task_result["performance_metrics"]
            if isinstance(perf, dict) and "error" in perf:
                return str(perf["error"])[:500]
        
        if task_result.get("success") is False:
            # Try to extract any useful info from the result structure
            result_str = str(task_result)
            if len(result_str) < 500:
                return f"Agent execution failed: {result_str}"
            return "Agent execution failed (no specific error message available)"
        
        # Last resort: return structured representation
        if task_result:
            # Return a summary of available keys
            keys = list(task_result.keys())[:5]
            return f"Unknown error (available keys: {', '.join(keys)})"
        
        return "Unknown error (empty result)"

    def _detect_agent_failures(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect agent failures from execution results.

        Args:
            results: Results dictionary from multi-agent orchestrator

        Returns:
            List of failure dictionaries with step, agent, and error info
        """
        failures = []
        
        # Step mapping for agent IDs
        step_mapping = {
            "planner-1": (2, "planner"),
            "architect-1": (3, "architect"),
            "designer-1": (4, "designer"),
            "implementer-1": (5, "implementer"),
            "reviewer-1": (6, "reviewer"),
            "tester-1": (7, "tester"),
        }
        
        # Check each agent result
        for agent_id, (step_num, agent_name) in step_mapping.items():
            agent_result = results.get(agent_id, {})
            
            # Check for error in various formats
            error = None
            
            # Format 1: Direct error field
            if "error" in agent_result:
                error = agent_result["error"]
            
            # Format 2: Nested result with error
            elif "result" in agent_result:
                nested = agent_result["result"]
                if isinstance(nested, dict) and "error" in nested:
                    error = nested["error"]
                elif isinstance(nested, str) and "error" in nested.lower():
                    # Check if result string contains error message
                    if "Unknown command" in nested or "required" in nested.lower():
                        error = nested
            
            # Format 3: Success flag is False
            elif agent_result.get("success") is False:
                error = agent_result.get("message", "Agent reported failure")
            
            if error:
                failures.append({
                    "step": step_num,
                    "agent": agent_name,
                    "agent_id": agent_id,
                    "error": str(error),
                })
        
        return failures

    def _verify_core_code(self, implemented_files: list[Path]) -> dict[str, Any]:
        """Verify core implementation exists."""
        return {
            "files_found": len(implemented_files),
            "files": [str(f) for f in implemented_files],
            "complete": len(implemented_files) > 0,
        }

    def _verify_related_files(
        self, checklist: DeliverableChecklist, core_files: list[Path]
    ) -> dict[str, Any]:
        """Verify related files are discovered and updated."""
        related_files = checklist.discover_related_files(
            core_files, self.project_root
        )
        return {
            "related_files_found": len(related_files),
            "files": [str(f) for f in related_files],
            "complete": True,  # Discovery is verification, not requirement
        }

    def _verify_documentation(self, checklist: DeliverableChecklist) -> dict[str, Any]:
        """Verify documentation completeness."""
        doc_items = checklist.checklist.get("documentation", [])
        complete_count = sum(1 for item in doc_items if item["status"] == "complete")
        return {
            "total": len(doc_items),
            "complete": complete_count,
            "complete_ratio": complete_count / len(doc_items) if doc_items else 1.0,
        }

    def _verify_tests(self, checklist: DeliverableChecklist) -> dict[str, Any]:
        """Verify test coverage."""
        test_items = checklist.checklist.get("tests", [])
        complete_count = sum(1 for item in test_items if item["status"] == "complete")
        return {
            "total": len(test_items),
            "complete": complete_count,
            "complete_ratio": complete_count / len(test_items) if test_items else 0.0,
        }

    def _verify_templates(self, checklist: DeliverableChecklist) -> dict[str, Any]:
        """Verify templates are updated."""
        template_items = checklist.checklist.get("templates", [])
        complete_count = sum(1 for item in template_items if item["status"] == "complete")
        return {
            "total": len(template_items),
            "complete": complete_count,
            "complete_ratio": complete_count / len(template_items) if template_items else 1.0,
        }

    def _determine_loopback_step(self, gaps: list[dict[str, Any]]) -> int:
        """Determine which step to loop back to based on gap types.

        Args:
            gaps: List of gap dictionaries

        Returns:
            Step number to loop back to (1-7)
        """
        gap_categories = set(gap.get("category", "") for gap in gaps)
        gap_types = set()
        for gap in gaps:
            if "missing_types" in gap:
                gap_types.update(gap["missing_types"])

        # Determine loopback based on gap types
        if "code" in gap_types or "core_code" in gap_categories:
            return 5  # Loop back to implementation
        if "tests" in gap_types or "tests" in gap_categories:
            return 7  # Loop back to testing
        if "docs" in gap_types or "documentation" in gap_categories:
            return 4  # Loop back to design (or could be Step 9 documenter)
        if "templates" in gap_categories:
            return 5  # Loop back to implementation
        if "related_files" in gap_categories:
            return 5  # Loop back to implementation

        # Default: loop back to planning if requirements missing
        return 2

    def _generate_verification_report(
        self,
        verification_results: dict[str, Any],
        gaps: list[dict[str, Any]],
        loopback_step: int | None,
    ) -> str:
        """Generate verification report in markdown format."""
        report_lines = [
            "# Step 8: Comprehensive Verification Report",
            "",
            "## Verification Results",
            "",
        ]

        # FIXED: Check for agent failures first (most critical issue)
        agent_failures = verification_results.get("agent_failures", [])
        if agent_failures:
            report_lines.extend([
                "## ❌ Agent Failures Detected",
                "",
                "The following workflow steps failed to execute:",
                "",
            ])
            for failure in agent_failures:
                step = failure.get("step", "?")
                agent = failure.get("agent", "unknown")
                error = failure.get("error", "Unknown error")
                # Truncate long error messages
                error_preview = error[:200] + "..." if len(error) > 200 else error
                report_lines.append(f"- **Step {step} ({agent})**: {error_preview}")
            report_lines.append("")

        # Core implementation
        core = verification_results.get("core_implementation", {})
        report_lines.append(f"- **Core Implementation**: {core.get('files_found', 0)} files")

        # Related files
        related = verification_results.get("related_files", {})
        report_lines.append(f"- **Related Files**: {related.get('related_files_found', 0)} files")

        # Documentation
        docs = verification_results.get("documentation", {})
        report_lines.append(
            f"- **Documentation**: {docs.get('complete', 0)}/{docs.get('total', 0)} complete"
        )

        # Tests
        tests = verification_results.get("tests", {})
        report_lines.append(
            f"- **Tests**: {tests.get('complete', 0)}/{tests.get('total', 0)} complete"
        )

        # Requirements
        reqs = verification_results.get("requirements", {})
        report_lines.append(f"- **Requirements**: {'Complete' if reqs.get('complete') else 'Incomplete'}")

        # Gaps (excluding agent failures which are shown above)
        non_failure_gaps = [g for g in gaps if g.get("category") != "agent_failure"]
        if non_failure_gaps:
            report_lines.extend([
                "",
                "## Gaps Found",
                "",
            ])
            for gap in non_failure_gaps:
                category = gap.get("category", gap.get("requirement_id", "Unknown"))
                item = gap.get("item", gap.get("missing_types", []))
                report_lines.append(f"- **{category}**: {item}")

        # Loopback decision
        if loopback_step:
            report_lines.extend([
                "",
                "## Loopback Decision",
                "",
                f"Gaps found. Loop back to **Step {loopback_step}** to fix issues.",
            ])
        else:
            report_lines.extend([
                "",
                "## Status",
                "",
                "✅ All deliverables verified. Workflow complete.",
            ])

        return "\n".join(report_lines)

    async def _handle_verification_gaps(
        self,
        gaps: list[dict[str, Any]],
        current_step: int,
        checklist: DeliverableChecklist,
        tracer: RequirementsTracer,
        workflow_state: dict[str, Any],
        max_iterations: int = 3,
    ) -> dict[str, Any]:
        """Handle gaps found during verification.

        Args:
            gaps: List of gap dictionaries
            current_step: Current step number
            checklist: DeliverableChecklist instance
            tracer: RequirementsTracer instance
            workflow_state: Current workflow state
            max_iterations: Maximum loopback iterations (default: 3)

        Returns:
            Dictionary with loopback decision and results
        """
        loopback_count = workflow_state.get("loopback_count", 0)

        if loopback_count >= max_iterations:
            logger.warning(
                f"Maximum loopback iterations ({max_iterations}) reached. Stopping."
            )
            return {
                "loopback": False,
                "reason": "max_iterations_reached",
                "loopback_count": loopback_count,
            }

        loopback_step = self._determine_loopback_step(gaps)

        if loopback_step < current_step:
            logger.info(
                f"Gaps found: {len(gaps)} items missing. "
                f"Looping back to Step {loopback_step} (iteration {loopback_count + 1})"
            )
            return {
                "loopback": True,
                "loopback_step": loopback_step,
                "loopback_count": loopback_count + 1,
                "gaps": gaps,
            }

        # Gaps can be fixed in current or next step
        return {
            "loopback": False,
            "reason": "gaps_fixable_in_current_step",
            "gaps": gaps,
        }
