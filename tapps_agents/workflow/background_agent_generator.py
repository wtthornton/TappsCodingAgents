"""
Background Agent Generator - Generates Background Agent configs for workflow steps.

This module creates dynamic Background Agent YAML configurations for executing
workflow steps via Cursor Skills.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any


class BackgroundAgentGenerator:
    """
    Generates Background Agent YAML configurations for workflow steps.
    
    Each workflow step gets its own Background Agent configuration that
    invokes the appropriate Cursor Skill.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Background Agent Generator.

        Args:
            project_root: Root directory for the project
        """
        self.project_root = project_root
        self.background_agents_dir = project_root / ".cursor" / "background-agents"

    def generate_step_agent(
        self,
        workflow_id: str,
        step_id: str,
        agent_name: str,
        skill_command: str,
        worktree_name: str,
        environment_vars: dict[str, str] | None = None,
    ) -> Path:
        """
        Generate Background Agent YAML for a workflow step.

        Args:
            workflow_id: Workflow identifier
            step_id: Step identifier
            agent_name: Agent name (e.g., "analyst")
            skill_command: Skill command string (e.g., "@analyst gather-requirements ...")
            worktree_name: Name of the worktree for this step
            environment_vars: Additional environment variables

        Returns:
            Path to generated YAML file
        """
        self.background_agents_dir.mkdir(parents=True, exist_ok=True)

        agent_name_full = f"tapps-workflow-{workflow_id}-{step_id}"
        yaml_file = self.background_agents_dir / f"{agent_name_full}.yaml"

        env_vars = {
            "TAPPS_AGENTS_MODE": "cursor",
            "WORKFLOW_ID": workflow_id,
            "STEP_ID": step_id,
            "WORKTREE": worktree_name,
        }
        if environment_vars:
            env_vars.update(environment_vars)

        # Create Background Agent configuration
        config = {
            "agents": [
                {
                    "name": f"TappsCodingAgents Workflow: {workflow_id} - Step {step_id}",
                    "type": "background",
                    "description": f"Execute {agent_name} agent for workflow step {step_id}",
                    "working_directory": str(self.project_root),
                    "commands": [
                        # Use a helper script to invoke the Skill
                        f'python -m tapps_agents.cli cursor-invoke "{skill_command}"',
                    ],
                    "environment": [f"{k}={v}" for k, v in env_vars.items()],
                    "triggers": [
                        f"Execute workflow step {step_id}",
                    ],
                    "worktree": worktree_name,
                    "output": {
                        "format": "json",
                        "location": f".tapps-agents/workflow-state/{workflow_id}/step-{step_id}",
                    },
                }
            ]
        }

        # Write YAML file
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        return yaml_file

    def cleanup_step_agent(self, workflow_id: str, step_id: str) -> None:
        """
        Remove Background Agent YAML for a workflow step.

        Args:
            workflow_id: Workflow identifier
            step_id: Step identifier
        """
        agent_name_full = f"tapps-workflow-{workflow_id}-{step_id}"
        yaml_file = self.background_agents_dir / f"{agent_name_full}.yaml"

        if yaml_file.exists():
            yaml_file.unlink()

