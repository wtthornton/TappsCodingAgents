"""
Skill Invoker - Invokes Cursor Skills for workflow execution.

This module translates workflow actions to Cursor Skill commands and executes them.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - fixed args, no shell
from pathlib import Path
from typing import Any

from .background_agent_api import BackgroundAgentAPI
from .cursor_skill_helper import (
    check_skill_completion,
    create_skill_command_file,
    create_skill_execution_instructions,
)
from .models import WorkflowState, WorkflowStep


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
        # Get command mapping
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
        for artifact in state.artifacts:
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
        self, command: str, worktree_path: Path, step: WorkflowStep | None = None
    ) -> dict[str, Any]:
        """
        Execute Skill command via Cursor Background Agents.

        This implementation:
        1. Tries to use Background Agent API if available
        2. Falls back to file-based execution if API unavailable
        3. Creates structured command files and execution instructions

        Args:
            command: Skill command string
            worktree_path: Path to worktree
            step: Optional workflow step for tracking

        Returns:
            Result dictionary with execution status and details
        """
        # Try API-based execution first if enabled
        if self.use_api and self.background_agent_api:
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
                        
                        if trigger_result.get("status") != "error":
                            return {
                                "status": "triggered",
                                "method": "api",
                                "job_id": trigger_result.get("job_id"),
                                "command": command,
                                "worktree": str(worktree_path),
                                "message": "Background Agent triggered via API",
                            }
            except Exception as e:
                # Fall back to file-based execution if API fails
                pass
        
        # Fallback: Create structured command files
        command_file = create_skill_command_file(
            command=command,
            worktree_path=worktree_path,
            workflow_id=getattr(step, "id", None) if step else None,
            step_id=getattr(step, "id", None) if step else None,
        )
        
        # Create execution instructions
        expected_artifacts = step.creates if step else None
        instructions_file = create_skill_execution_instructions(
            worktree_path=worktree_path,
            command=command,
            expected_artifacts=expected_artifacts,
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

