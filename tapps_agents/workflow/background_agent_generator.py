"""
Background Agent Generator - Generates Background Agent configs for workflow steps.

This module creates dynamic Background Agent YAML configurations for executing
workflow steps via Cursor Skills. Configs are merged into the unified
.cursor/background-agents.yaml file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GeneratedAgentConfig:
    """Generated Background Agent configuration for a workflow step."""

    name: str
    workflow_id: str
    step_id: str
    agent: str
    action: str
    watch_paths: list[str]
    triggers: list[str]
    commands: list[str]
    environment: list[str]
    worktree: str
    output_location: str
    metadata: dict[str, Any]


class BackgroundAgentGenerator:
    """
    Generates Background Agent YAML configurations for workflow steps.
    
    Configs are merged into the unified .cursor/background-agents.yaml file,
    preserving manual configurations.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Background Agent Generator.

        Args:
            project_root: Root directory for the project
        """
        self.project_root = project_root
        self.config_file = project_root / ".cursor" / "background-agents.yaml"
        self._ensure_config_file()

    def _ensure_config_file(self) -> None:
        """Ensure background-agents.yaml exists with basic structure."""
        if not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            initial_config = {
                "agents": [],
                "global": {
                    "context7_cache": ".tapps-agents/kb/context7-cache",
                    "output_directory": ".tapps-agents/reports",
                    "worktree_base": ".tapps-agents/worktrees",
                    "progress_reporting": True,
                    "result_delivery": ["file"],
                    "max_parallel_agents": 4,
                    "timeout_seconds": 3600,
                },
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(initial_config, f, default_flow_style=False, sort_keys=False)

    def _load_config(self) -> dict[str, Any]:
        """Load current background-agents.yaml config."""
        if not self.config_file.exists():
            return {"agents": [], "global": {}}
        
        with open(self.config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"agents": [], "global": {}}

    def _save_config(self, config: dict[str, Any]) -> None:
        """Save background-agents.yaml config."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def _backup_config(self) -> Path:
        """Create backup of current config before modification."""
        backup_file = self.config_file.with_suffix(
            f".backup.{datetime.now().strftime('%Y%m%d-%H%M%S')}.yaml"
        )
        if self.config_file.exists():
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "r", encoding="utf-8") as src:
                with open(backup_file, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
        return backup_file

    def _extract_watch_paths(self, step: Any) -> list[str]:
        """
        Extract watch paths from step requires and creates artifacts.
        
        Args:
            step: WorkflowStep with requires and creates fields
            
        Returns:
            List of normalized watch path patterns
        """
        watch_paths: list[str] = []
        
        # Watch paths from requires (artifacts this step depends on)
        for artifact in step.requires:
            watch_paths.append(self._normalize_watch_path(artifact))
        
        # Watch paths from creates (outputs this step produces)
        for artifact in step.creates:
            watch_paths.append(self._normalize_watch_path(artifact))
        
        # Deduplicate while preserving order
        seen = set()
        unique_paths = []
        for path in watch_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        return unique_paths

    def _normalize_watch_path(self, artifact: str) -> str:
        """
        Normalize artifact path to watch path pattern.
        
        Args:
            artifact: Artifact path from requires/creates
            
        Returns:
            Normalized watch path pattern
        """
        # If it ends with /, it's a directory - watch all files
        if artifact.endswith("/"):
            path = artifact.rstrip("/")
            return f"{path}/**"
        
        # Remove leading/trailing slashes for files
        path = artifact.strip("/")
        
        # If it's a file with path, return as-is
        if "/" in path:
            return path
        
        # Simple file/directory name - watch in project root
        return path

    def _generate_triggers(self, step: Any, workflow: Any) -> list[str]:
        """
        Generate natural language triggers from step metadata.
        
        Args:
            step: WorkflowStep with agent, action, and metadata
            workflow: Workflow with name and description
            
        Returns:
            List of natural language trigger phrases
        """
        triggers: list[str] = []
        
        # Base triggers from step description/notes
        if step.notes:
            triggers.append(step.notes)
        
        # Agent-action based triggers
        action_verbs = {
            "gather_requirements": ["gather requirements", "collect requirements"],
            "create_stories": ["create stories", "generate user stories"],
            "write_code": ["write code", "implement", "code"],
            "review_code": ["review code", "code review", "review"],
            "write_tests": ["write tests", "create tests", "test"],
            "analyze": ["analyze", "analysis"],
            "refactor": ["refactor", "refactoring"],
            "enhance_prompt": ["enhance prompt", "improve prompt"],
            "finalize": ["finalize", "complete"],
        }
        
        action_key = step.action.lower().replace("-", "_")
        if action_key in action_verbs:
            triggers.extend(action_verbs[action_key])
        
        # Workflow context triggers
        triggers.append(f"{workflow.name} - {step.id}")
        triggers.append(f"Execute {step.agent} {step.action}")
        
        # Step-specific triggers
        triggers.append(f"Run step {step.id}")
        triggers.append(f"Execute {step.id}")
        
        # Deduplicate while preserving order
        seen = set()
        unique_triggers = []
        for trigger in triggers:
            trigger_lower = trigger.lower()
            if trigger_lower not in seen:
                seen.add(trigger_lower)
                unique_triggers.append(trigger)
        
        return unique_triggers[:10]  # Limit to 10 triggers

    def _generate_commands(self, step: Any, workflow_id: str) -> list[str]:
        """
        Generate command list for Background Agent.
        
        Background Agents execute shell commands. For workflow steps, we create
        a command file that Cursor reads to execute the skill.
        
        Args:
            step: WorkflowStep with agent and action
            workflow_id: Workflow identifier for context
            
        Returns:
            List of command strings
        """
        # Build skill command: @{agent} {action}
        # This is the format Cursor Skills expect
        skill_command = f"@{step.agent} {step.action}"
        
        # Create command file in worktree for Cursor to read
        # Use the existing helper function via Python import
        command_dir = f".tapps-agents/workflow-state/{workflow_id}/step-{step.id}"
        worktree_path = self.project_root / command_dir
        
        # Import and use the helper function
        # Escape quotes properly for shell execution
        escaped_command = skill_command.replace('"', '\\"')
        escaped_worktree = str(worktree_path).replace('\\', '\\\\').replace('"', '\\"')
        
        return [
            (
                f'python -c "'
                f'from pathlib import Path; '
                f'from tapps_agents.workflow.cursor_skill_helper import create_skill_command_file; '
                f'create_skill_command_file('
                f'command=\\"{escaped_command}\\", '
                f'worktree_path=Path(\\"{escaped_worktree}\\"), '
                f'workflow_id=\\"{workflow_id}\\", '
                f'step_id=\\"{step.id}\\"'
                f')"'
            ),
        ]

    def generate_workflow_configs(
        self,
        workflow: Any,
        workflow_id: str,
    ) -> list[GeneratedAgentConfig]:
        """
        Generate Background Agent configs for all workflow steps.
        
        Args:
            workflow: Workflow object with steps
            workflow_id: Workflow execution identifier
            
        Returns:
            List of generated agent configs
        """
        configs: list[GeneratedAgentConfig] = []
        
        for step in workflow.steps:
            # Extract watch paths
            watch_paths = self._extract_watch_paths(step)
            
            # Generate triggers
            triggers = self._generate_triggers(step, workflow)
            
            # Generate commands
            commands = self._generate_commands(step, workflow_id)
            
            # Generate worktree name
            worktree_name = f"workflow-{workflow_id}-{step.id}"
            
            # Build environment variables
            env_vars = [
                "TAPPS_AGENTS_MODE=cursor",
                f"WORKFLOW_ID={workflow_id}",
                f"STEP_ID={step.id}",
                f"WORKTREE={worktree_name}",
            ]
            
            # Create config
            config = GeneratedAgentConfig(
                name=f"TappsCodingAgents Workflow: {workflow.name} - {step.id}",
                workflow_id=workflow_id,
                step_id=step.id,
                agent=step.agent,
                action=step.action,
                watch_paths=watch_paths,
                triggers=triggers,
                commands=commands,
                environment=env_vars,
                worktree=worktree_name,
                output_location=f".tapps-agents/workflow-state/{workflow_id}/step-{step.id}",
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "workflow_name": workflow.name,
                    "workflow_version": workflow.version,
                },
            )
            configs.append(config)
        
        return configs

    def _is_generated_agent(self, agent: dict[str, Any]) -> bool:
        """Check if agent config was generated (has workflow metadata)."""
        return (
            "metadata" in agent
            and isinstance(agent["metadata"], dict)
            and "workflow_id" in agent["metadata"]
        )

    def _agent_matches_workflow(self, agent: dict[str, Any], workflow_id: str) -> bool:
        """Check if agent belongs to a specific workflow."""
        return (
            self._is_generated_agent(agent)
            and agent["metadata"].get("workflow_id") == workflow_id
        )

    def apply_workflow_configs(
        self,
        configs: list[GeneratedAgentConfig],
        workflow_id: str,
    ) -> None:
        """
        Apply generated configs to background-agents.yaml.
        
        Removes existing configs for this workflow and adds new ones,
        preserving manual (non-generated) configs.
        
        Args:
            configs: List of generated agent configs
            workflow_id: Workflow identifier
        """
        # Backup before modification
        self._backup_config()
        
        # Load current config
        current_config = self._load_config()
        
        # Filter out existing generated agents for this workflow
        agents = current_config.get("agents", [])
        manual_agents = [
            agent for agent in agents
            if not self._agent_matches_workflow(agent, workflow_id)
        ]
        
        # Convert generated configs to agent dicts
        generated_agents = []
        for config in configs:
            agent_dict: dict[str, Any] = {
                "name": config.name,
                "type": "background",
                "description": f"Execute {config.agent} agent for workflow step {config.step_id}",
                "working_directory": str(self.project_root),
                "commands": config.commands,
                "environment": config.environment,
                "triggers": config.triggers,
                "worktree": config.worktree,
                "output": {
                    "format": "json",
                    "location": config.output_location,
                },
                "metadata": {
                    **config.metadata,
                    "workflow_id": config.workflow_id,
                    "step_id": config.step_id,
                    "generated": True,
                },
            }
            
            # Add watch paths if present
            if config.watch_paths:
                agent_dict["watch"] = config.watch_paths
            
            generated_agents.append(agent_dict)
        
        # Merge: manual agents first, then generated agents
        current_config["agents"] = manual_agents + generated_agents
        
        # Save updated config
        self._save_config(current_config)

    def cleanup_workflow_configs(self, workflow_id: str) -> None:
        """
        Remove generated configs for a workflow.
        
        Args:
            workflow_id: Workflow identifier
        """
        # Backup before modification
        self._backup_config()
        
        # Load current config
        current_config = self._load_config()
        
        # Filter out generated agents for this workflow
        agents = current_config.get("agents", [])
        remaining_agents = [
            agent for agent in agents
            if not self._agent_matches_workflow(agent, workflow_id)
        ]
        
        current_config["agents"] = remaining_agents
        
        # Save updated config
        self._save_config(current_config)

    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate generated configs against Background Agents schema.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []
        
        try:
            config = self._load_config()
            
            # Basic structure validation
            if "agents" not in config:
                errors.append("Missing 'agents' key in config")
            
            agents = config.get("agents", [])
            if not isinstance(agents, list):
                errors.append("'agents' must be a list")
            
            # Validate each agent
            for i, agent in enumerate(agents):
                if not isinstance(agent, dict):
                    errors.append(f"Agent {i} is not a dictionary")
                    continue
                
                required_fields = ["name", "type", "commands"]
                for field in required_fields:
                    if field not in agent:
                        errors.append(f"Agent {i} ({agent.get('name', 'unknown')}) missing required field: {field}")
                
                # Validate commands
                if "commands" in agent:
                    if not isinstance(agent["commands"], list):
                        errors.append(f"Agent {i} commands must be a list")
                    elif not agent["commands"]:
                        errors.append(f"Agent {i} must have at least one command")
            
        except Exception as e:
            errors.append(f"Config validation error: {e}")
        
        return len(errors) == 0, errors
