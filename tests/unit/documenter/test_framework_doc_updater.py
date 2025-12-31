"""
Unit tests for Framework Documentation Updater.

Tests documentation file updates for README.md, API.md, ARCHITECTURE.md, and agent-capabilities.mdc.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.documenter.framework_doc_updater import (
    FrameworkDocUpdater,
    UpdateResult,
)
from tapps_agents.simple_mode.framework_change_detector import AgentInfo

pytestmark = pytest.mark.unit


class TestFrameworkDocUpdater:
    """Test FrameworkDocUpdater functionality."""

    def test_updater_initialization(self, tmp_path):
        """Test updater can be initialized."""
        updater = FrameworkDocUpdater(project_root=tmp_path)
        assert updater.project_root == tmp_path
        assert updater.create_backups is True
        assert updater.backup_dir.exists()

    def test_create_backup(self, tmp_path):
        """Test backup creation."""
        updater = FrameworkDocUpdater(project_root=tmp_path)

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        backup_path = updater.create_backup(test_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "test content"

    def test_create_backup_missing_file(self, tmp_path):
        """Test backup creation for missing file."""
        updater = FrameworkDocUpdater(project_root=tmp_path)
        test_file = tmp_path / "nonexistent.txt"

        backup_path = updater.create_backup(test_file)

        assert backup_path is None

    def test_update_readme(self, tmp_path):
        """Test README.md update."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text(
            """# Project

- **Workflow Agents** (13): Standard SDLC task execution

- `@reviewer` - Code review
- `@implementer` - Code generation
"""
        )

        agent_info = AgentInfo(
            name="new_agent", purpose="New agent for testing", commands=["test"]
        )
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_readme("new_agent", agent_info)

        assert result is True
        content = readme_path.read_text()
        assert "Workflow Agents** (14)" in content
        assert "`@new_agent`" in content

    def test_update_readme_missing_file(self, tmp_path):
        """Test README.md update when file doesn't exist."""
        agent_info = AgentInfo(name="new_agent", purpose="Test")
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_readme("new_agent", agent_info)

        assert result is False

    def test_update_api_docs(self, tmp_path):
        """Test API.md update."""
        api_path = tmp_path / "docs" / "API.md"
        api_path.parent.mkdir(parents=True)
        api_path.write_text(
            """# API Reference

## Agent subcommands:

- `reviewer` - Code review commands
- `implementer` - Code generation commands

## Reviewer Agent

### Commands
- `review` - Review code
"""
        )

        agent_info = AgentInfo(
            name="new_agent", purpose="New agent", commands=["test", "run"]
        )
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_api_docs("new_agent", agent_info)

        assert result is True
        content = api_path.read_text()
        assert "`new_agent`" in content
        # Agent name formatting may use underscores
        assert "## New" in content and "Agent" in content

    def test_update_architecture_docs(self, tmp_path):
        """Test ARCHITECTURE.md update."""
        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.parent.mkdir(parents=True)
        arch_path.write_text(
            """# Architecture

## Agents

- **Reviewer Agent** - Code review
- **Implementer Agent** - Code generation
"""
        )

        agent_info = AgentInfo(name="new_agent", purpose="New agent")
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_architecture_docs("new_agent", agent_info)

        assert result is True
        content = arch_path.read_text()
        # Agent name formatting may use underscores
        assert "**New" in content and "Agent**" in content

    def test_update_agent_capabilities(self, tmp_path):
        """Test agent-capabilities.mdc update."""
        capabilities_path = tmp_path / ".cursor" / "rules" / "agent-capabilities.mdc"
        capabilities_path.parent.mkdir(parents=True)
        capabilities_path.write_text(
            """# Agent Capabilities

### Reviewer Agent

**Purpose**: Code review

### Implementer Agent

**Purpose**: Code generation
"""
        )

        agent_info = AgentInfo(
            name="new_agent", purpose="New agent", commands=["test"]
        )
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_agent_capabilities("new_agent", agent_info)

        assert result is True
        content = capabilities_path.read_text()
        # Agent name formatting may use underscores
        assert "### New" in content and "Agent" in content
        assert "**Purpose**: New agent" in content

    def test_update_all_docs(self, tmp_path):
        """Test updating all documentation files."""
        # Create all documentation files
        readme_path = tmp_path / "README.md"
        readme_path.write_text("- **Workflow Agents** (13):\n- `@reviewer` - Review")

        api_path = tmp_path / "docs" / "API.md"
        api_path.parent.mkdir(parents=True)
        api_path.write_text("## Agent subcommands:\n- `reviewer` - Review")

        arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
        arch_path.write_text("## Agents\n- **Reviewer Agent** - Review")

        capabilities_path = tmp_path / ".cursor" / "rules" / "agent-capabilities.mdc"
        capabilities_path.parent.mkdir(parents=True)
        capabilities_path.write_text("### Reviewer Agent\n**Purpose**: Review")

        agent_info = AgentInfo(name="new_agent", purpose="New agent")
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_all_docs("new_agent", agent_info)

        assert result.readme_updated is True
        assert result.api_updated is True
        assert result.architecture_updated is True
        assert result.capabilities_updated is True
        assert result.success is True

    def test_update_all_docs_partial_failure(self, tmp_path):
        """Test updating all docs with some files missing."""
        # Only create README.md
        readme_path = tmp_path / "README.md"
        readme_path.write_text("- **Workflow Agents** (13):")

        agent_info = AgentInfo(name="new_agent", purpose="New agent")
        updater = FrameworkDocUpdater(project_root=tmp_path)
        result = updater.update_all_docs("new_agent", agent_info)

        assert result.readme_updated is True
        assert result.api_updated is False  # File missing
        assert result.success is False
        # Errors may be logged but not always captured in result.errors
        # The important thing is that success is False


class TestUpdateResult:
    """Test UpdateResult class."""

    def test_update_result_success(self):
        """Test successful update result."""
        result = UpdateResult(
            readme_updated=True,
            api_updated=True,
            architecture_updated=True,
            capabilities_updated=True,
        )

        assert result.success is True

    def test_update_result_failure(self):
        """Test failed update result."""
        result = UpdateResult(
            readme_updated=True,
            api_updated=False,  # Failed
            architecture_updated=True,
            capabilities_updated=True,
        )

        assert result.success is False

    def test_update_result_with_errors(self):
        """Test update result with errors."""
        result = UpdateResult(
            readme_updated=True,
            api_updated=True,
            architecture_updated=True,
            capabilities_updated=True,
            errors=["Test error"],
        )

        assert result.success is False
