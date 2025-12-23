"""
Skill Invoker - Invokes Cursor Skills for workflow execution.

This module translates workflow actions to Cursor Skill commands and executes them.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

from ..core.skill_integration import (
    get_skill_integration_manager,
)
from .background_agent_api import BackgroundAgentAPI
from .background_quality_agent import BackgroundQualityAgent
from .background_testing_agent import BackgroundTestingAgent
from .cursor_skill_helper import (
    create_skill_command_file,
    create_skill_execution_instructions,
)
from .models import Artifact, WorkflowState, WorkflowStep


class SkillInvoker:
    """
    Invokes Cursor Skills for workflow execution.
    
    Translates workflow actions to Skill commands and executes them.
    Supports both Background Agent API and file-based execution.
    """

    def __init__(self, project_root: Path | None = None, use_api: bool = True):
        """
        Initialize Skill Invoker.

        Args:
            project_root: Root directory for the project
            use_api: Whether to use Background Agent API (True) or file-based (False)
        """
        self.project_root = project_root or Path.cwd()
        self.use_api = use_api
        self.background_agent_api = BackgroundAgentAPI() if use_api else None
        self.skill_integration = get_skill_integration_manager(project_root=self.project_root)

    # Command mapping: (agent_name, action) -> (skill_command, parameters)
    COMMAND_MAPPING: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {
        # Analyst
        ("analyst", "gather-requirements"): (
            "gather-requirements",
            {"description": "user_prompt", "output_file": "requirements.md"},
        ),
        ("analyst", "gather_requirements"): (
            "gather-requirements",
            {"description": "user_prompt", "output_file": "requirements.md"},
        ),
        
        # Planner
        ("planner", "plan"): (
            "plan",
            {"description": "requirements_content"},
        ),
        ("planner", "create-stories"): (
            "plan",
            {"description": "requirements_content"},
        ),
        ("planner", "create_stories"): (
            "plan",
            {"description": "requirements_content"},
        ),
        
        # Architect
        ("architect", "design-system"): (
            "design-system",
            {"requirements": "requirements_file", "context": "stories_content", "output_file": "architecture.md"},
        ),
        ("architect", "design_system"): (
            "design-system",
            {"requirements": "requirements_file", "context": "stories_content", "output_file": "architecture.md"},
        ),
        
        # Designer
        ("designer", "design-api"): (
            "design-api",
            {"requirements": "requirements_file", "architecture": "architecture_file"},
        ),
        ("designer", "api_design"): (
            "design-api",
            {"requirements": "requirements_file", "architecture": "architecture_file"},
        ),
        ("designer", "api-design"): (
            "design-api",
            {"requirements": "requirements_file", "architecture": "architecture_file"},
        ),
        
        # Implementer
        ("implementer", "implement"): (
            "implement",
            {"specification": "specification_content", "file_path": "target_file"},
        ),
        ("implementer", "write-code"): (
            "implement",
            {"specification": "specification_content", "file_path": "target_file"},
        ),
        ("implementer", "write_code"): (
            "implement",
            {"specification": "specification_content", "file_path": "target_file"},
        ),
        ("implementer", "refactor"): (
            "refactor",
            {"file": "target_file", "requirements": "requirements_file"},
        ),
        
        # Reviewer
        ("reviewer", "review"): (
            "review",
            {"file": "target_file"},
        ),
        ("reviewer", "review-code"): (
            "review",
            {"file": "target_file"},
        ),
        ("reviewer", "review_code"): (
            "review",
            {"file": "target_file"},
        ),
        
        # Tester
        ("tester", "test"): (
            "test",
            {"file": "target_file"},
        ),
        ("tester", "write-tests"): (
            "test",
            {"file": "target_file"},
        ),
        ("tester", "write_tests"): (
            "test",
            {"file": "target_file"},
        ),
        
        # Debugger
        ("debugger", "analyze-error"): (
            "analyze-error",
            {"error_message": "error_message", "stack_trace": "stack_trace"},
        ),
        ("debugger", "analyze_error"): (
            "analyze-error",
            {"error_message": "error_message", "stack_trace": "stack_trace"},
        ),
        
        # Documenter
        ("documenter", "document"): (
            "document",
            {"target": "target_file", "output_dir": "docs"},
        ),
        ("documenter", "generate-docs"): (
            "document",
            {"target": "target_file", "output_dir": "docs"},
        ),
        ("documenter", "generate_docs"): (
            "document",
            {"target": "target_file", "output_dir": "docs"},
        ),
        
        # Ops
        ("ops", "security-scan"): (
            "security-scan",
            {"target": "target_file", "type": "code"},
        ),
        ("ops", "security_scan"): (
            "security-scan",
            {"target": "target_file", "type": "code"},
        ),
        
        # Improver
        ("improver", "improve"): (
            "improve",
            {"file": "target_file", "feedback": "review_feedback"},
        ),
        
        # Enhancer
        ("enhancer", "enhance"): (
            "enhance",
            {"prompt": "user_prompt", "format": "markdown"},
        ),
        ("enhancer", "enhance_prompt"): (
            "enhance",
            {"prompt": "user_prompt", "format": "markdown"},
        ),
        ("enhancer", "enhance-prompt"): (
            "enhance",
            {"prompt": "user_prompt", "format": "markdown"},
        ),
        
        # Quality Agent (Background Cloud)
        ("quality", "analyze"): (
            "quality-analyze",
            {"target": "target_file"},
        ),
        ("quality", "quality-check"): (
            "quality-analyze",
            {"target": "target_file"},
        ),
        ("quality", "quality_check"): (
            "quality-analyze",
            {"target": "target_file"},
        ),
        
        # Testing Agent (Background Cloud)
        ("testing", "run-tests"): (
            "testing-run",
            {"test_path": "target_file", "coverage": True},
        ),
        ("testing", "run_tests"): (
            "testing-run",
            {"test_path": "target_file", "coverage": True},
        ),
        ("testing", "test"): (
            "testing-run",
            {"test_path": "target_file", "coverage": True},
        ),
    }


    async def invoke_skill(
        self,
        agent_name: str,
        action: str,
        step: WorkflowStep,
        target_path: Path | None,
        worktree_path: Path,
        state: WorkflowState,
    ) -> dict[str, Any]:
        """
        Invoke a Cursor Skill for a workflow step.

        Supports both built-in and custom Skills. Custom Skills are checked first.

        Args:
            agent_name: Name of the agent (e.g., "analyst")
            action: Action to perform (e.g., "gather-requirements")
            step: Workflow step definition
            target_path: Optional target file path
            worktree_path: Path to worktree for this step
            state: Current workflow state

        Returns:
            Result dictionary from Skill execution
        """
        # Check if step specifies a custom Skill (in metadata or as attribute)
        custom_skill_name = None
        if step:
            # Check metadata first
            if hasattr(step, "metadata") and step.metadata:
                custom_skill_name = step.metadata.get("skill")
            # Also check direct attribute (for future extension)
            if not custom_skill_name:
                custom_skill_name = getattr(step, "skill", None)
        
        # If custom Skill is specified, use it
        if custom_skill_name and self.skill_integration.is_custom_skill(custom_skill_name):
            return await self._invoke_custom_skill(
                skill_name=custom_skill_name,
                action=action,
                step=step,
                target_path=target_path,
                worktree_path=worktree_path,
                state=state,
            )
        
        # Check for custom Skills that match agent/action pattern
        custom_skills = self.skill_integration.get_skills_for_agent(agent_name.lower())
        for skill in custom_skills:
            # Try to match action to Skill commands (simplified matching)
            # In a full implementation, we'd parse the Skill's command definitions
            # For now, we'll use the Skill name as the agent name if it matches
            if skill.name.lower().startswith(agent_name.lower()) or agent_name.lower() in skill.name.lower():
                return await self._invoke_custom_skill(
                    skill_name=skill.name,
                    action=action,
                    step=step,
                    target_path=target_path,
                    worktree_path=worktree_path,
                    state=state,
                )
        
        # Fall back to built-in command mapping
        key = (agent_name.lower(), action.lower())
        if key not in self.COMMAND_MAPPING:
            raise ValueError(
                f"Unknown command: {agent_name}/{action}. "
                f"Available: {list(self.COMMAND_MAPPING.keys())}"
            )

        skill_command, param_mapping = self.COMMAND_MAPPING[key]

        # Build parameters from state and context
        params = self._build_parameters(
            param_mapping=param_mapping,
            step=step,
            target_path=target_path,
            worktree_path=worktree_path,
            state=state,
        )

        # Build Skill command string
        command_str = self._build_command(
            agent_name=agent_name,
            skill_command=skill_command,
            params=params,
        )

        # Execute via Cursor chat (using Background Agent or direct invocation)
        result = await self._execute_skill_command(
            command=command_str,
            worktree_path=worktree_path,
            step=step,
            workflow_id=getattr(state, "workflow_id", None),
        )
        
        # Store result in state for tracking
        if state:
            state.variables[f"{agent_name}_{action}_result"] = result

        return result

    def _build_parameters(
        self,
        param_mapping: dict[str, str],
        step: WorkflowStep,
        target_path: Path | None,
        worktree_path: Path,
        state: WorkflowState,
    ) -> dict[str, Any]:
        """
        Build parameters for Skill command from workflow state.

        Args:
            param_mapping: Mapping from parameter names to state keys
            step: Workflow step
            target_path: Optional target file path
            worktree_path: Path to worktree
            state: Workflow state

        Returns:
            Dictionary of parameter values
        """
        params: dict[str, Any] = {}

        for param_name, state_key in param_mapping.items():
            if state_key == "user_prompt":
                params[param_name] = state.variables.get("user_prompt", "")
            elif state_key == "target_file":
                params[param_name] = str(target_path) if target_path else None
            elif state_key == "requirements_file":
                # Find requirements.md artifact
                req_file = self._find_artifact(state, "requirements.md")
                params[param_name] = str(req_file) if req_file else None
            elif state_key == "requirements_content":
                req_file = self._find_artifact(state, "requirements.md")
                if req_file and req_file.exists():
                    params[param_name] = req_file.read_text(encoding="utf-8")
                else:
                    params[param_name] = ""
            elif state_key == "architecture_file":
                arch_file = self._find_artifact(state, "architecture.md")
                params[param_name] = str(arch_file) if arch_file else None
            elif state_key == "stories_content":
                # Find stories directory
                stories_dir = worktree_path / "stories"
                if stories_dir.exists():
                    # Read all story files
                    story_files = list(stories_dir.glob("*.md"))
                    content = "\n\n".join(
                        f.read_text(encoding="utf-8") for f in story_files
                    )
                    params[param_name] = content
                else:
                    params[param_name] = ""
            elif state_key == "specification_content":
                # Combine requirements and architecture
                req_content = ""
                arch_content = ""
                req_file = self._find_artifact(state, "requirements.md")
                arch_file = self._find_artifact(state, "architecture.md")
                if req_file and req_file.exists():
                    req_content = req_file.read_text(encoding="utf-8")
                if arch_file and arch_file.exists():
                    arch_content = arch_file.read_text(encoding="utf-8")
                params[param_name] = f"{req_content}\n\n{arch_content}"
            elif state_key == "review_feedback":
                # Get reviewer result from state
                params[param_name] = state.variables.get("reviewer_result", {})
            elif state_key == "error_message":
                params[param_name] = state.variables.get("error_message", "")
            elif state_key == "stack_trace":
                params[param_name] = state.variables.get("stack_trace", "")
            elif state_key == "project_profile":
                # Get project profile from state
                profile_dict = state.variables.get("project_profile")
                if profile_dict:
                    from ..core.project_profile import ProjectProfile
                    profile = ProjectProfile.from_dict(profile_dict)
                    params[param_name] = profile.format_context(min_confidence=0.7)
                else:
                    params[param_name] = ""
            else:
                # Try to get from state variables
                params[param_name] = state.variables.get(state_key, "")

        # Automatically append project profile to context parameters
        profile_dict = state.variables.get("project_profile")
        if profile_dict:
            from ..core.project_profile import ProjectProfile
            profile = ProjectProfile.from_dict(profile_dict)
            profile_context = profile.format_context(min_confidence=0.7)
            if profile_context:
                # Append to any existing context parameter
                if "context" in params:
                    existing_context = params.get("context", "")
                    if existing_context:
                        params["context"] = f"{existing_context}\n\n{profile_context}"
                    else:
                        params["context"] = profile_context
                # Also add to description if it exists (for analyst, planner)
                if "description" in params and isinstance(params["description"], str):
                    params["description"] = f"{params['description']}\n\n{profile_context}"

        return params

    def _find_artifact(
        self, state: WorkflowState, filename: str
    ) -> Path | None:
        """Find artifact by filename in workflow state."""
        for artifact in state.artifacts.values():
            if isinstance(artifact, Artifact) and artifact.path:
                if Path(artifact.path).name == filename:
                    return Path(artifact.path)
        return None

    def _build_command(
        self, agent_name: str, skill_command: str, params: dict[str, Any]
    ) -> str:
        """
        Build Cursor Skill command string.

        Format: @agent-name command-name [--flag value]...

        Args:
            agent_name: Agent name (e.g., "analyst")
            skill_command: Skill command name
            params: Parameters for the command

        Returns:
            Command string
        """
        parts = [f"@{agent_name}", skill_command]

        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                if value:
                    parts.append(f"--{key}")
            elif isinstance(value, (str, int, float)):
                # Quote string values if they contain spaces
                if isinstance(value, str) and " " in value:
                    parts.append(f'--{key} "{value}"')
                else:
                    parts.append(f"--{key} {value}")
            elif isinstance(value, dict):
                # Convert dict to JSON string
                parts.append(f'--{key} \'{json.dumps(value)}\'')
            else:
                parts.append(f"--{key} {value}")

        return " ".join(parts)

    async def _execute_skill_command(
        self,
        command: str,
        worktree_path: Path,
        step: WorkflowStep | None = None,
        workflow_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute Skill command via Cursor Background Agents.

        This implementation:
        1. For quality/testing agents: Directly executes background agents
        2. Tries to use Background Agent API if available
        3. Falls back to file-based execution if API unavailable
        4. Creates structured command files and execution instructions

        Args:
            command: Skill command string
            worktree_path: Path to worktree
            step: Optional workflow step for tracking

        Returns:
            Result dictionary with execution status and details
        """
        # Extract agent name and action from command
        agent_name = None
        action = None
        if command.startswith("@"):
            parts = command.split()
            if parts:
                agent_name = parts[0][1:]  # Remove "@"
                if len(parts) > 1:
                    action = parts[1]

        # Special handling for quality and testing background agents
        if agent_name in ["quality", "testing"]:
            return await self._execute_background_agent(
                agent_name=agent_name,
                action=action or "analyze" if agent_name == "quality" else "run-tests",
                command=command,
                worktree_path=worktree_path,
                step=step,
            )

        # Try API-based execution first if enabled (Phase 3)
        if self.use_api and self.background_agent_api:
            import logging
            logger = logging.getLogger(__name__)
            
            try:
                # Extract agent name from command (e.g., "@analyst" from "@analyst gather-requirements")
                agent_name = None
                if command.startswith("@"):
                    parts = command.split()
                    if parts:
                        agent_name = parts[0][1:]  # Remove "@"
                
                if agent_name:
                    # Try to find or create a Background Agent for this skill
                    agents = self.background_agent_api.list_agents()
                    
                    # Log API availability status
                    if agents:
                        logger.debug(
                            f"Background Agent API available: {len(agents)} agents found",
                            extra={"agent_count": len(agents)},
                        )
                    else:
                        logger.debug(
                            "Background Agent API returned empty list - may not be available",
                            extra={"fallback": "file-based"},
                        )
                    
                    # Look for existing agent or use a default one
                    agent_id = None
                    for agent in agents:
                        if agent.get("name", "").lower().find(agent_name.lower()) >= 0:
                            agent_id = agent.get("id")
                            break
                    
                    # If no specific agent found, try to trigger with agent name
                    if agent_id or agent_name:
                        trigger_result = self.background_agent_api.trigger_agent(
                            agent_id=agent_id or agent_name,
                            command=command,
                            worktree_path=str(worktree_path),
                            environment={
                                "TAPPS_AGENTS_MODE": "cursor",
                                "WORKTREE_PATH": str(worktree_path),
                            },
                        )
                        
                        # Check if API call succeeded (not fallback mode)
                        if trigger_result.get("status") != "error" and not trigger_result.get("fallback_mode"):
                            logger.info(
                                f"Background Agent triggered via API: {agent_id or agent_name}",
                                extra={
                                    "agent_id": agent_id or agent_name,
                                    "job_id": trigger_result.get("job_id"),
                                    "method": "api",
                                },
                            )
                            return {
                                "status": "triggered",
                                "method": "api",
                                "job_id": trigger_result.get("job_id"),
                                "command": command,
                                "worktree": str(worktree_path),
                                "message": "Background Agent triggered via API",
                            }
                        else:
                            # API returned fallback mode - log and continue to file-based
                            logger.debug(
                                f"Background Agent API returned fallback mode for {agent_id or agent_name}",
                                extra={"fallback": "file-based"},
                            )
            except requests.RequestException as e:
                # Network/HTTP errors - log and fall back
                logger.debug(
                    f"Background Agent API request failed: {e}",
                    extra={"fallback": "file-based", "error": str(e)},
                )
            except Exception as e:
                # Other errors - log and fall back
                logger.warning(
                    f"Unexpected error using Background Agent API: {e}",
                    extra={"fallback": "file-based", "error": str(e)},
                    exc_info=True,
                )
        
        # Create execution instructions
        expected_artifacts = step.creates if step else None
        
        # Fallback: Create structured command files with metadata
        command_file, metadata_file = create_skill_command_file(
            command=command,
            worktree_path=worktree_path,
            workflow_id=workflow_id,
            step_id=getattr(step, "id", None) if step else None,
            expected_artifacts=expected_artifacts,
        )
        instructions_file = create_skill_execution_instructions(
            worktree_path=worktree_path,
            command=command,
            expected_artifacts=expected_artifacts,
            workflow_id=workflow_id,
            step_id=getattr(step, "id", None) if step else None,
        )

        # Also create a simple script that can execute the command
        # This will be used by Background Agents
        script_file = worktree_path / ".execute-skill.sh"
        if not script_file.exists():
            script_content = f"""#!/bin/bash
# Execute Cursor Skill command
# This script is generated by TappsCodingAgents workflow executor

cd "{worktree_path}"
echo "Executing: {command}"

# In Cursor, this would invoke the Skill via chat API
# For now, we write the command to a file that Cursor can process
echo "{command}" > .skill-command-executed.txt

# Return success
exit 0
"""
            script_file.write_text(script_content, encoding="utf-8")
            script_file.chmod(0o755)

        # Return result indicating command is ready
        return {
            "status": "ready",
            "command": command,
            "worktree": str(worktree_path),
            "command_file": str(command_file),
            "instructions_file": str(instructions_file),
            "note": (
                "Command files created. "
                "See .cursor-skill-instructions.md for execution instructions. "
                "Command can be executed in Cursor chat or via Background Agent."
            ),
        }

    async def _execute_background_agent(
        self,
        agent_name: str,
        action: str,
        command: str,
        worktree_path: Path,
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        """
        Execute quality or testing background agent directly.

        Args:
            agent_name: "quality" or "testing"
            action: Action to perform
            command: Full command string
            worktree_path: Path to worktree
            step: Optional workflow step

        Returns:
            Result dictionary
        """
        correlation_id = None
        if step:
            correlation_id = f"{step.id}-{getattr(step, 'workflow_id', 'unknown')}"

        try:
            if agent_name == "quality":
                # Extract target path from command if present
                target_path = None
                if "--target" in command or "--file" in command:
                    # Simple parsing - in production would use proper argument parsing
                    parts = command.split()
                    for i, part in enumerate(parts):
                        if part in ["--target", "--file"] and i + 1 < len(parts):
                            target_path = Path(parts[i + 1].strip('"'))
                            break

                quality_agent = BackgroundQualityAgent(
                    worktree_path=worktree_path,
                    correlation_id=correlation_id,
                    timeout_seconds=600.0,
                )

                artifact = await quality_agent.run_quality_analysis(
                    target_path=target_path,
                )

                return {
                    "status": artifact.status,
                    "method": "background_agent",
                    "agent": "quality",
                    "worktree": str(worktree_path),
                    "artifact_path": str(
                        worktree_path / "reports" / "quality" / "quality-report.json"
                    ),
                    "artifact": artifact.to_dict(),
                    "message": f"Quality analysis {artifact.status}",
                }

            elif agent_name == "testing":
                # Extract test path from command if present
                test_path = None
                coverage = True
                if "--test_path" in command or "--test-path" in command:
                    parts = command.split()
                    for i, part in enumerate(parts):
                        if part in ["--test_path", "--test-path"] and i + 1 < len(parts):
                            test_path = Path(parts[i + 1].strip('"'))
                            break
                if "--no-coverage" in command:
                    coverage = False

                testing_agent = BackgroundTestingAgent(
                    worktree_path=worktree_path,
                    correlation_id=correlation_id,
                    timeout_seconds=600.0,
                )

                artifact = await testing_agent.run_tests(
                    test_path=test_path,
                    coverage=coverage,
                )

                return {
                    "status": artifact.status,
                    "method": "background_agent",
                    "agent": "testing",
                    "worktree": str(worktree_path),
                    "artifact_path": str(
                        worktree_path / "reports" / "tests" / "test-report.json"
                    ),
                    "artifact": artifact.to_dict(),
                    "message": f"Test execution {artifact.status}",
                }

        except Exception as e:
            return {
                "status": "error",
                "method": "background_agent",
                "agent": agent_name,
                "worktree": str(worktree_path),
                "error": str(e),
                "message": f"Background agent execution failed: {e}",
            }

        return {
            "status": "error",
            "method": "background_agent",
            "agent": agent_name,
            "error": f"Unknown agent: {agent_name}",
        }

    async def _invoke_custom_skill(
        self,
        skill_name: str,
        action: str,
        step: WorkflowStep,
        target_path: Path | None,
        worktree_path: Path,
        state: WorkflowState,
    ) -> dict[str, Any]:
        """
        Invoke a custom Skill for a workflow step.

        Args:
            skill_name: Name of the custom Skill
            action: Action/command to perform
            step: Workflow step definition
            target_path: Optional target file path
            worktree_path: Path to worktree for this step
            state: Current workflow state

        Returns:
            Result dictionary from Skill execution
        """
        # Get Skill metadata
        skill_metadata = self.skill_integration.get_skill_metadata(skill_name)
        if not skill_metadata:
            raise ValueError(f"Custom Skill not found: {skill_name}")

        # Create Skill context
        skill_context = self.skill_integration.create_skill_context(
            workflow_id=getattr(step, "workflow_id", None) if step else None,
            step_id=getattr(step, "id", None) if step else None,
            state=state.variables if state else None,
            artifacts={k: v.to_dict() if hasattr(v, "to_dict") else str(v) for k, v in state.artifacts.items()} if state else None,
            project_profile=state.variables.get("project_profile") if state else None,
        )

        # Build parameters from step params and state
        params: dict[str, Any] = {}
        if step and hasattr(step, "params") and step.params:
            params.update(step.params)
        
        # Add common parameters
        if target_path:
            params["file"] = str(target_path)
            params["target"] = str(target_path)
        
        # Add context as JSON string for Skills to parse
        params["context"] = json.dumps(skill_context.to_dict())

        # Build command string using custom Skill name
        command_str = self._build_command(
            agent_name=skill_name,  # Use Skill name as agent name
            skill_command=action,
            params=params,
        )

        # Execute via Cursor (using Background Agent or direct invocation)
        result = await self._execute_skill_command(
            command=command_str,
            worktree_path=worktree_path,
            step=step,
        )
        
        # Store result in state for tracking
        if state:
            state.variables[f"{skill_name}_{action}_result"] = result

        return result

