"""
Custom Skill Integration System.

Provides integration between custom Skills and framework agents/workflows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .skill_loader import SkillMetadata, SkillRegistry, get_skill_registry, initialize_skill_registry

logger = logging.getLogger(__name__)


@dataclass
class SkillContext:
    """Context provided to Skills for accessing framework features."""

    project_root: Path
    workflow_id: str | None = None
    step_id: str | None = None
    state: dict[str, Any] | None = None
    artifacts: dict[str, Any] | None = None
    project_profile: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "project_root": str(self.project_root),
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "state": self.state or {},
            "artifacts": self.artifacts or {},
            "project_profile": self.project_profile or {},
        }


class SkillIntegrationManager:
    """
    Manages integration between custom Skills and framework components.
    
    Provides:
    - Skill-to-agent mapping
    - Workflow integration
    - Context access for Skills
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize Skill Integration Manager.

        Args:
            project_root: Project root directory
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.registry = initialize_skill_registry(project_root=project_root)
        self._skill_to_agent_map: dict[str, list[str]] = {}
        self._build_skill_to_agent_mapping()

    def _build_skill_to_agent_mapping(self) -> None:
        """Build mapping from Skills to agent names."""
        # Custom Skills can be used by any agent, but we can infer agent names
        # from the Skill name (e.g., "my-custom-analyst" -> "analyst")
        for skill in self.registry.list_skills(include_custom=True, include_builtin=False):
            # Extract potential agent name from Skill name
            # Skills can be named like "my-custom-analyst" or "custom-implementer"
            skill_name = skill.name.lower()
            
            # Check if Skill name contains a known agent type
            known_agents = [
                "analyst", "architect", "debugger", "designer", "documenter",
                "enhancer", "implementer", "improver", "ops", "orchestrator",
                "planner", "reviewer", "tester",
            ]
            
            for agent in known_agents:
                if agent in skill_name:
                    if agent not in self._skill_to_agent_map:
                        self._skill_to_agent_map[agent] = []
                    if skill.name not in self._skill_to_agent_map[agent]:
                        self._skill_to_agent_map[agent].append(skill.name)
                    break
            else:
                # If no agent type found, allow Skill to be used by any agent
                # Store as "universal" mapping
                if "universal" not in self._skill_to_agent_map:
                    self._skill_to_agent_map["universal"] = []
                if skill.name not in self._skill_to_agent_map["universal"]:
                    self._skill_to_agent_map["universal"].append(skill.name)

    def get_skills_for_agent(self, agent_name: str) -> list[SkillMetadata]:
        """
        Get custom Skills available for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of Skill metadata
        """
        skills = []
        
        # Get Skills specifically mapped to this agent
        if agent_name in self._skill_to_agent_map:
            for skill_name in self._skill_to_agent_map[agent_name]:
                skill = self.registry.get_skill(skill_name)
                if skill and skill.is_custom:
                    skills.append(skill)
        
        # Also include universal Skills
        if "universal" in self._skill_to_agent_map:
            for skill_name in self._skill_to_agent_map["universal"]:
                skill = self.registry.get_skill(skill_name)
                if skill and skill.is_custom:
                    skills.append(skill)
        
        return skills

    def get_all_custom_skills(self) -> list[SkillMetadata]:
        """
        Get all custom Skills.

        Returns:
            List of custom Skill metadata
        """
        return self.registry.get_custom_skills()

    def is_custom_skill(self, skill_name: str) -> bool:
        """
        Check if a Skill is a custom Skill.

        Args:
            skill_name: Name of the Skill

        Returns:
            True if Skill is custom
        """
        skill = self.registry.get_skill(skill_name)
        return skill is not None and skill.is_custom

    def get_skill_metadata(self, skill_name: str) -> SkillMetadata | None:
        """
        Get Skill metadata by name.

        Args:
            skill_name: Name of the Skill

        Returns:
            Skill metadata or None if not found
        """
        return self.registry.get_skill(skill_name)

    def create_skill_context(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        state: dict[str, Any] | None = None,
        artifacts: dict[str, Any] | None = None,
        project_profile: dict[str, Any] | None = None,
    ) -> SkillContext:
        """
        Create a Skill context for framework access.

        Args:
            workflow_id: Current workflow ID
            step_id: Current step ID
            state: Workflow state dictionary
            artifacts: Artifacts dictionary
            project_profile: Project profile dictionary

        Returns:
            Skill context
        """
        return SkillContext(
            project_root=self.project_root,
            workflow_id=workflow_id,
            step_id=step_id,
            state=state or {},
            artifacts=artifacts or {},
            project_profile=project_profile or {},
        )


# Global integration manager instance
_global_integration_manager: SkillIntegrationManager | None = None


def get_skill_integration_manager(project_root: Path | None = None) -> SkillIntegrationManager:
    """
    Get global Skill integration manager instance.

    Args:
        project_root: Project root directory (used for initialization if not already initialized)

    Returns:
        Global Skill integration manager
    """
    global _global_integration_manager
    if _global_integration_manager is None:
        _global_integration_manager = SkillIntegrationManager(project_root=project_root)
    return _global_integration_manager

