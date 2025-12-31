"""
Framework Documentation Updater - Updates project documentation for framework changes.

This module updates README.md, API.md, ARCHITECTURE.md, and agent-capabilities.mdc
when new agents are added to the framework.
"""

import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...simple_mode.framework_change_detector import AgentInfo

logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    """Result of documentation updates."""

    readme_updated: bool = False
    api_updated: bool = False
    architecture_updated: bool = False
    capabilities_updated: bool = False
    backups_created: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if all updates were successful."""
        return (
            self.readme_updated
            and self.api_updated
            and self.architecture_updated
            and self.capabilities_updated
            and not self.errors
        )


class FrameworkDocUpdater:
    """Update project documentation files with new agent information."""

    def __init__(self, project_root: Path, create_backups: bool = True):
        """
        Initialize documentation updater.

        Args:
            project_root: Project root directory
            create_backups: Whether to create backups before updates
        """
        self.project_root = project_root
        self.create_backups = create_backups
        self.backup_dir = project_root / ".tapps-agents" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def update_all_docs(
        self, agent_name: str, agent_info: AgentInfo
    ) -> UpdateResult:
        """
        Update all project documentation for a new agent.

        Args:
            agent_name: Name of the new agent
            agent_info: Agent information

        Returns:
            UpdateResult with update status for each file
        """
        result = UpdateResult()

        # Update README.md
        try:
            result.readme_updated = self.update_readme(agent_name, agent_info)
        except Exception as e:
            result.errors.append(f"Failed to update README.md: {e}")
            logger.error(f"Failed to update README.md: {e}")

        # Update API.md
        try:
            result.api_updated = self.update_api_docs(agent_name, agent_info)
        except Exception as e:
            result.errors.append(f"Failed to update API.md: {e}")
            logger.error(f"Failed to update API.md: {e}")

        # Update ARCHITECTURE.md
        try:
            result.architecture_updated = self.update_architecture_docs(
                agent_name, agent_info
            )
        except Exception as e:
            result.errors.append(f"Failed to update ARCHITECTURE.md: {e}")
            logger.error(f"Failed to update ARCHITECTURE.md: {e}")

        # Update agent-capabilities.mdc
        try:
            result.capabilities_updated = self.update_agent_capabilities(
                agent_name, agent_info
            )
        except Exception as e:
            result.errors.append(f"Failed to update agent-capabilities.mdc: {e}")
            logger.error(f"Failed to update agent-capabilities.mdc: {e}")

        return result

    def update_readme(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        readme_path: Path | None = None,
    ) -> bool:
        """
        Update README.md with new agent.

        Updates:
        - Agent count: Increment from (N) to (N+1)
        - Agent list: Add agent to list in alphabetical order

        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            readme_path: README.md path (default: project_root/README.md)

        Returns:
            True if update successful
        """
        if readme_path is None:
            readme_path = self.project_root / "README.md"

        if not readme_path.exists():
            logger.warning(f"README.md not found: {readme_path}")
            return False

        # Create backup
        if self.create_backups:
            backup_path = self.create_backup(readme_path)
            if backup_path:
                logger.info(f"Created backup: {backup_path}")

        # Read content
        content = readme_path.read_text(encoding="utf-8")

        # Update agent count
        # Pattern: "- **Workflow Agents** (N):"
        count_pattern = r"- \*\*Workflow Agents\*\* \((\d+)\):"
        match = re.search(count_pattern, content)
        if match:
            current_count = int(match.group(1))
            new_count = current_count + 1
            content = re.sub(
                count_pattern,
                f"- **Workflow Agents** ({new_count}):",
                content,
                count=1,
            )
            logger.info(f"Updated agent count from {current_count} to {new_count}")

        # Add agent to list
        # Find agent list section and insert in alphabetical order
        # Pattern: "- `@{agent_name}` - {description}"
        agent_list_pattern = r"(- `@(\w+)` - .+?)(?=\n- `@|\n\n|$)"
        matches = list(re.finditer(agent_list_pattern, content, re.MULTILINE))

        if matches:
            # Find insertion point (alphabetical order)
            agent_entry = f"- `@{agent_name}` - {agent_info.purpose or agent_name.title()} Agent"
            insertion_index = None

            for i, match in enumerate(matches):
                existing_agent = match.group(2)
                if agent_name < existing_agent:
                    insertion_index = match.start()
                    break

            if insertion_index is not None:
                # Insert before the agent that comes after alphabetically
                content = (
                    content[:insertion_index]
                    + agent_entry
                    + "\n"
                    + content[insertion_index:]
                )
            else:
                # Insert at end of list
                last_match = matches[-1]
                insertion_point = last_match.end()
                content = (
                    content[:insertion_point]
                    + "\n"
                    + agent_entry
                    + content[insertion_point:]
                )
            logger.info(f"Added {agent_name} to agent list")
        else:
            logger.warning("Could not find agent list in README.md")

        # Write updated content
        readme_path.write_text(content, encoding="utf-8")
        return True

    def update_api_docs(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        api_path: Path | None = None,
    ) -> bool:
        """
        Update API.md with agent documentation.

        Updates:
        - Subcommands list: Add agent to subcommands
        - API section: Add agent API documentation section

        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            api_path: API.md path (default: project_root/docs/API.md)

        Returns:
            True if update successful
        """
        if api_path is None:
            api_path = self.project_root / "docs" / "API.md"

        if not api_path.exists():
            logger.warning(f"API.md not found: {api_path}")
            return False

        # Create backup
        if self.create_backups:
            backup_path = self.create_backup(api_path)
            if backup_path:
                logger.info(f"Created backup: {backup_path}")

        # Read content
        content = api_path.read_text(encoding="utf-8")

        # Add to subcommands list
        # Pattern: "## Agent subcommands:" or "### Agent subcommands:"
        subcommands_pattern = r"(## Agent subcommands:.*?\n)(- `\w+` - .+?)(?=\n\n|$)"
        match = re.search(subcommands_pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            subcommands_section = match.group(0)
            agent_entry = f"- `{agent_name}` - {agent_info.purpose or agent_name.title()} Agent"
            # Insert in alphabetical order
            if agent_entry not in subcommands_section:
                # Find insertion point
                agent_list_pattern = r"- `(\w+)` -"
                agent_matches = list(re.finditer(agent_list_pattern, subcommands_section))
                insertion_index = None

                for i, agent_match in enumerate(agent_matches):
                    existing_agent = agent_match.group(1)
                    if agent_name < existing_agent:
                        insertion_index = agent_match.start()
                        break

                if insertion_index is not None:
                    subcommands_section = (
                        subcommands_section[:insertion_index]
                        + agent_entry
                        + "\n"
                        + subcommands_section[insertion_index:]
                    )
                else:
                    # Insert at end
                    subcommands_section = subcommands_section.rstrip() + "\n" + agent_entry + "\n"

                content = content.replace(match.group(0), subcommands_section)
                logger.info(f"Added {agent_name} to subcommands list")

        # Add API section
        # Insert after last agent section
        # Convert snake_case to Title Case (e.g., "new_agent" -> "New Agent")
        agent_name_title = agent_name.replace("_", " ").title()
        api_section = f"\n## {agent_name_title} Agent\n\n"
        if agent_info.purpose:
            api_section += f"{agent_info.purpose}\n\n"

        if agent_info.commands:
            api_section += "### Commands\n\n"
            for command in agent_info.commands:
                api_section += f"- `{command}` - {agent_info.description or 'See agent documentation'}\n"
            api_section += "\n"

        # Find insertion point (after last agent section)
        # Look for last "## AgentName Agent" section
        agent_section_pattern = r"## \w+ Agent\n"
        agent_sections = list(re.finditer(agent_section_pattern, content))
        if agent_sections:
            last_section = agent_sections[-1]
            # Find end of that section (next ## or end of file)
            next_section = re.search(
                r"\n## [^#]", content[last_section.end() :], re.MULTILINE
            )
            if next_section:
                insertion_point = last_section.end() + next_section.start()
            else:
                insertion_point = len(content)
            content = content[:insertion_point] + api_section + content[insertion_point:]
            logger.info(f"Added {agent_name} API section")
        else:
            # Append at end
            content = content.rstrip() + "\n" + api_section
            logger.info(f"Appended {agent_name} API section")

        # Write updated content
        api_path.write_text(content, encoding="utf-8")
        return True

    def update_architecture_docs(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        arch_path: Path | None = None,
    ) -> bool:
        """
        Update ARCHITECTURE.md with agent details.

        Updates:
        - Agent list: Add agent to agent list
        - Agent details: Add agent purpose and relationships

        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            arch_path: ARCHITECTURE.md path (default: project_root/docs/ARCHITECTURE.md)

        Returns:
            True if update successful
        """
        if arch_path is None:
            arch_path = self.project_root / "docs" / "ARCHITECTURE.md"

        if not arch_path.exists():
            logger.warning(f"ARCHITECTURE.md not found: {arch_path}")
            return False

        # Create backup
        if self.create_backups:
            backup_path = self.create_backup(arch_path)
            if backup_path:
                logger.info(f"Created backup: {backup_path}")

        # Read content
        content = arch_path.read_text(encoding="utf-8")

        # Add to agent list
        # Pattern: "## Agents" or "### Agents"
        agents_section_pattern = r"(## Agents.*?\n)(- \*\*\w+ Agent\*\* - .+?)(?=\n\n|$)"
        match = re.search(agents_section_pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            agents_section = match.group(0)
            # Convert snake_case to Title Case
            agent_name_title = agent_name.replace("_", " ").title()
            agent_entry = f"- **{agent_name_title} Agent** - {agent_info.purpose or agent_name_title} Agent"
            # Insert in alphabetical order
            if agent_entry not in agents_section:
                # Find insertion point
                agent_list_pattern = r"- \*\*(\w+) Agent\*\* -"
                agent_matches = list(re.finditer(agent_list_pattern, agents_section))
                insertion_index = None

                for i, agent_match in enumerate(agent_matches):
                    existing_agent = agent_match.group(1).lower()
                    if agent_name.lower() < existing_agent:
                        insertion_index = agent_match.start()
                        break

                if insertion_index is not None:
                    agents_section = (
                        agents_section[:insertion_index]
                        + agent_entry
                        + "\n"
                        + agents_section[insertion_index:]
                    )
                else:
                    # Insert at end
                    agents_section = agents_section.rstrip() + "\n" + agent_entry + "\n"

                content = content.replace(match.group(0), agents_section)
                logger.info(f"Added {agent_name} to architecture agent list")

        # Write updated content
        arch_path.write_text(content, encoding="utf-8")
        return True

    def update_agent_capabilities(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        capabilities_path: Path | None = None,
    ) -> bool:
        """
        Update agent-capabilities.mdc with agent section.

        Updates:
        - Agent section: Add agent section with purpose and commands

        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            capabilities_path: agent-capabilities.mdc path (default: project_root/.cursor/rules/agent-capabilities.mdc)

        Returns:
            True if update successful
        """
        if capabilities_path is None:
            capabilities_path = (
                self.project_root / ".cursor" / "rules" / "agent-capabilities.mdc"
            )

        if not capabilities_path.exists():
            logger.warning(f"agent-capabilities.mdc not found: {capabilities_path}")
            return False

        # Create backup
        if self.create_backups:
            backup_path = self.create_backup(capabilities_path)
            if backup_path:
                logger.info(f"Created backup: {backup_path}")

        # Read content
        content = capabilities_path.read_text(encoding="utf-8")

        # Create agent section
        # Convert snake_case to Title Case
        agent_name_title = agent_name.replace("_", " ").title()
        agent_section = f"\n### {agent_name_title} Agent\n\n"
        if agent_info.purpose:
            agent_section += f"**Purpose**: {agent_info.purpose}\n\n"
        else:
            agent_section += f"**Purpose**: {agent_name_title} Agent\n\n"

        if agent_info.commands:
            agent_section += "**Commands**:\n"
            for command in agent_info.commands:
                agent_section += f"- `*{command}` - {agent_info.description or 'See agent documentation'}\n"
            agent_section += "\n"

        # Find insertion point (after last agent section)
        # Look for last "### AgentName Agent" section
        agent_section_pattern = r"### \w+ Agent\n"
        agent_sections = list(re.finditer(agent_section_pattern, content))
        if agent_sections:
            last_section = agent_sections[-1]
            # Find end of that section (next ### or end of file)
            next_section = re.search(
                r"\n### [^#]", content[last_section.end() :], re.MULTILINE
            )
            if next_section:
                insertion_point = last_section.end() + next_section.start()
            else:
                insertion_point = len(content)
            content = content[:insertion_point] + agent_section + content[insertion_point:]
            logger.info(f"Added {agent_name} to agent-capabilities.mdc")
        else:
            # Append at end
            content = content.rstrip() + "\n" + agent_section
            logger.info(f"Appended {agent_name} to agent-capabilities.mdc")

        # Write updated content
        capabilities_path.write_text(content, encoding="utf-8")
        return True

    def create_backup(self, file_path: Path) -> Path | None:
        """
        Create backup of file before update.

        Args:
            file_path: File to backup

        Returns:
            Backup file path, or None if backup failed
        """
        if not file_path.exists():
            return None

        try:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_filename

            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            return None
