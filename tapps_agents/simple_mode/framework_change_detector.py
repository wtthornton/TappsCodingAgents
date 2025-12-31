"""
Framework Change Detector - Detects framework changes (new agents, etc.).

This module detects when new agents are added to the framework by scanning
agent directories, CLI registrations, and skill files.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Agent metadata extracted from code."""

    name: str
    purpose: str | None = None
    commands: list[str] = field(default_factory=list)
    description: str | None = None
    examples: list[str] = field(default_factory=list)

    @classmethod
    def from_agent_directory(cls, agent_dir: Path) -> "AgentInfo | None":
        """
        Extract agent info from agent directory.

        Args:
            agent_dir: Agent directory path

        Returns:
            AgentInfo object, or None if extraction fails
        """
        if not agent_dir.exists() or not agent_dir.is_dir():
            return None

        agent_name = agent_dir.name
        agent_info = cls(name=agent_name)

        # Try to extract purpose from agent.py docstring
        agent_py = agent_dir / "agent.py"
        if agent_py.exists():
            try:
                content = agent_py.read_text(encoding="utf-8")
                # Extract class docstring
                docstring_match = re.search(
                    r'class\s+\w+Agent.*?"""(.*?)"""', content, re.DOTALL
                )
                if docstring_match:
                    docstring = docstring_match.group(1).strip()
                    # Extract first line as purpose
                    first_line = docstring.split("\n")[0].strip()
                    if first_line:
                        agent_info.purpose = first_line
            except Exception as e:
                logger.debug(f"Failed to extract purpose from {agent_py}: {e}")

        # Try to extract commands from SKILL.md
        skill_md = agent_dir / "SKILL.md"
        if not skill_md.exists():
            # Check in resources/claude/skills/{agent_name}/
            skill_md = (
                agent_dir.parent.parent.parent
                / "resources"
                / "claude"
                / "skills"
                / agent_name
                / "SKILL.md"
            )

        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding="utf-8")
                # Extract commands from markdown
                command_matches = re.findall(r"`\*?(\w+)`", content)
                if command_matches:
                    agent_info.commands = list(set(command_matches))
            except Exception as e:
                logger.debug(f"Failed to extract commands from {skill_md}: {e}")

        return agent_info


@dataclass
class FrameworkChanges:
    """Detected framework changes."""

    new_agents: list[str] = field(default_factory=list)
    modified_agents: list[str] = field(default_factory=list)
    new_cli_commands: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    agent_info: dict[str, AgentInfo] = field(default_factory=dict)


class FrameworkChangeDetector:
    """Detect framework changes (new agents, modified agents, etc.)."""

    def __init__(self, project_root: Path):
        """
        Initialize framework change detector.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.agents_dir = project_root / "tapps_agents" / "agents"
        self.cli_file = project_root / "tapps_agents" / "cli" / "main.py"
        self.skills_dir = (
            project_root / "tapps_agents" / "resources" / "claude" / "skills"
        )

    def detect_changes(
        self, known_agents: set[str] | None = None
    ) -> FrameworkChanges:
        """
        Detect framework changes since last check.

        Args:
            known_agents: Set of known agent names (from config or previous scan)
                         If None, will scan and return all current agents

        Returns:
            FrameworkChanges object with detected changes
        """
        changes = FrameworkChanges()

        # Scan for current agents
        current_agents = self.scan_agent_directories()

        if known_agents is None:
            # No baseline, so all current agents are "new" (for initial setup)
            changes.new_agents = current_agents
        else:
            # Compare with known agents
            current_set = set(current_agents)
            known_set = set(known_agents)

            changes.new_agents = list(current_set - known_set)
            changes.modified_agents = list(current_set & known_set)  # Could enhance to detect actual modifications

        # Extract agent info for new agents
        for agent_name in changes.new_agents:
            agent_dir = self.agents_dir / agent_name
            agent_info = AgentInfo.from_agent_directory(agent_dir)
            if agent_info:
                changes.agent_info[agent_name] = agent_info

        # Detect CLI registrations
        for agent_name in changes.new_agents:
            if self.detect_cli_registration(agent_name):
                changes.new_cli_commands.append(agent_name)

        return changes

    def scan_agent_directories(
        self, agents_dir: Path | None = None
    ) -> list[str]:
        """
        Scan for agent directories in tapps_agents/agents/.

        Args:
            agents_dir: Agents directory path (default: self.agents_dir)

        Returns:
            List of agent names (directory names)
        """
        if agents_dir is None:
            agents_dir = self.agents_dir

        if not agents_dir.exists():
            logger.warning(f"Agents directory not found: {agents_dir}")
            return []

        agents = []
        for item in agents_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                # Check if it's a valid agent directory (has agent.py or __init__.py)
                if (item / "agent.py").exists() or (item / "__init__.py").exists():
                    agents.append(item.name)

        return sorted(agents)

    def detect_cli_registration(
        self, agent_name: str, cli_file: Path | None = None
    ) -> bool:
        """
        Check if agent is registered in CLI.

        Args:
            agent_name: Agent name to check
            cli_file: CLI main file path (default: self.cli_file)

        Returns:
            True if agent is registered in CLI
        """
        if cli_file is None:
            cli_file = self.cli_file

        if not cli_file.exists():
            logger.debug(f"CLI file not found: {cli_file}")
            return False

        try:
            content = cli_file.read_text(encoding="utf-8")
            # Look for agent name in various patterns
            patterns = [
                rf'"{agent_name}"',  # String literal
                rf"'{agent_name}'",  # String literal
                rf"\b{agent_name}\b",  # Word boundary
            ]
            return any(re.search(pattern, content) for pattern in patterns)
        except Exception as e:
            logger.warning(f"Failed to check CLI registration: {e}")
            return False

    def detect_skill_creation(
        self, agent_name: str, skills_dir: Path | None = None
    ) -> bool:
        """
        Check if agent skill file exists.

        Args:
            agent_name: Agent name to check
            skills_dir: Skills directory path (default: self.skills_dir)

        Returns:
            True if agent skill file exists
        """
        if skills_dir is None:
            skills_dir = self.skills_dir

        skill_file = skills_dir / agent_name / "SKILL.md"
        return skill_file.exists()

    def get_agent_info(self, agent_name: str) -> AgentInfo | None:
        """
        Extract agent information from agent directory.

        Args:
            agent_name: Agent name

        Returns:
            AgentInfo object with agent metadata, or None if not found
        """
        agent_dir = self.agents_dir / agent_name
        return AgentInfo.from_agent_directory(agent_dir)
