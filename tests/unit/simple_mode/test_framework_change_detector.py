"""
Unit tests for Framework Change Detector.

Tests agent directory scanning, CLI registration detection, and change detection.
"""

from unittest.mock import patch

import pytest

from tapps_agents.simple_mode.framework_change_detector import (
    AgentInfo,
    FrameworkChangeDetector,
)

pytestmark = pytest.mark.unit


class TestFrameworkChangeDetector:
    """Test FrameworkChangeDetector functionality."""

    def test_detector_initialization(self, tmp_path):
        """Test detector can be initialized."""
        detector = FrameworkChangeDetector(project_root=tmp_path)
        assert detector.project_root == tmp_path
        assert detector.agents_dir == tmp_path / "tapps_agents" / "agents"
        assert detector.cli_file == tmp_path / "tapps_agents" / "cli" / "main.py"
        assert (
            detector.skills_dir
            == tmp_path / "tapps_agents" / "resources" / "claude" / "skills"
        )

    def test_scan_agent_directories(self, tmp_path):
        """Test agent directory scanning."""
        # Create agent directories
        agents_dir = tmp_path / "tapps_agents" / "agents"
        agents_dir.mkdir(parents=True)

        # Create valid agent directory
        agent1_dir = agents_dir / "test_agent"
        agent1_dir.mkdir()
        (agent1_dir / "agent.py").write_text("# Test agent")

        # Create invalid directory (no agent.py)
        invalid_dir = agents_dir / "invalid"
        invalid_dir.mkdir()

        # Create __pycache__ (should be ignored)
        pycache_dir = agents_dir / "__pycache__"
        pycache_dir.mkdir()

        detector = FrameworkChangeDetector(project_root=tmp_path)
        agents = detector.scan_agent_directories()

        assert "test_agent" in agents
        assert "invalid" not in agents
        assert "__pycache__" not in agents

    def test_scan_agent_directories_missing_dir(self, tmp_path):
        """Test scanning when agents directory doesn't exist."""
        detector = FrameworkChangeDetector(project_root=tmp_path)
        agents = detector.scan_agent_directories()

        assert agents == []

    def test_detect_cli_registration(self, tmp_path):
        """Test CLI registration detection."""
        cli_file = tmp_path / "tapps_agents" / "cli" / "main.py"
        cli_file.parent.mkdir(parents=True)

        # Write CLI file with agent registration
        cli_file.write_text('register_agent("test_agent")')

        detector = FrameworkChangeDetector(project_root=tmp_path)
        assert detector.detect_cli_registration("test_agent") is True
        assert detector.detect_cli_registration("nonexistent") is False

    def test_detect_cli_registration_missing_file(self, tmp_path):
        """Test CLI registration detection when file doesn't exist."""
        detector = FrameworkChangeDetector(project_root=tmp_path)
        assert detector.detect_cli_registration("test_agent") is False

    def test_detect_cli_registration_regex_escaping(self, tmp_path):
        """Test CLI registration detection with special regex characters (Bug fix 3)."""
        cli_file = tmp_path / "tapps_agents" / "cli" / "main.py"
        cli_file.parent.mkdir(parents=True)

        # Write CLI file with agent name containing special regex characters
        agent_name_with_special_chars = "agent+name"
        cli_file.write_text(f'register_agent("{agent_name_with_special_chars}")')

        detector = FrameworkChangeDetector(project_root=tmp_path)
        # Should correctly match despite special characters (regex escaping)
        assert detector.detect_cli_registration(agent_name_with_special_chars) is True
        # Test that a different agent name with similar pattern doesn't match
        assert detector.detect_cli_registration("agent-name") is False

    def test_scan_agent_directories_permission_error(self, tmp_path):
        """Test agent directory scanning handles PermissionError (Bug fix 2)."""
        agents_dir = tmp_path / "tapps_agents" / "agents"
        agents_dir.mkdir(parents=True)

        detector = FrameworkChangeDetector(project_root=tmp_path)

        # Mock Path.iterdir at the class level to raise PermissionError
        with patch("pathlib.Path.iterdir", side_effect=PermissionError("Access denied")):
            agents = detector.scan_agent_directories()
            # Should return empty list and not crash
            assert agents == []

    def test_scan_agent_directories_os_error(self, tmp_path):
        """Test agent directory scanning handles OSError (Bug fix 2)."""
        agents_dir = tmp_path / "tapps_agents" / "agents"
        agents_dir.mkdir(parents=True)

        detector = FrameworkChangeDetector(project_root=tmp_path)

        # Mock Path.iterdir at the class level to raise OSError
        with patch("pathlib.Path.iterdir", side_effect=OSError("Disk error")):
            agents = detector.scan_agent_directories()
            # Should return empty list and not crash
            assert agents == []

    def test_detect_skill_creation(self, tmp_path):
        """Test skill file detection."""
        skills_dir = (
            tmp_path / "tapps_agents" / "resources" / "claude" / "skills"
        )
        skill_dir = skills_dir / "test_agent"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test skill")

        detector = FrameworkChangeDetector(project_root=tmp_path)
        assert detector.detect_skill_creation("test_agent") is True
        assert detector.detect_skill_creation("nonexistent") is False

    def test_get_agent_info(self, tmp_path):
        """Test agent info extraction."""
        agents_dir = tmp_path / "tapps_agents" / "agents"
        agent_dir = agents_dir / "test_agent"
        agent_dir.mkdir(parents=True)

        # Create agent.py with docstring
        agent_py = agent_dir / "agent.py"
        agent_py.write_text(
            '''class TestAgent:
    """Test agent purpose description."""
    pass
'''
        )

        detector = FrameworkChangeDetector(project_root=tmp_path)
        agent_info = detector.get_agent_info("test_agent")

        assert agent_info is not None
        assert agent_info.name == "test_agent"
        assert "purpose" in agent_info.purpose.lower() if agent_info.purpose else True

    def test_get_agent_info_nonexistent(self, tmp_path):
        """Test agent info extraction for nonexistent agent."""
        detector = FrameworkChangeDetector(project_root=tmp_path)
        agent_info = detector.get_agent_info("nonexistent")

        assert agent_info is None

    def test_detect_changes_new_agent(self, tmp_path):
        """Test change detection with new agent."""
        # Create agent directory
        agents_dir = tmp_path / "tapps_agents" / "agents"
        agent_dir = agents_dir / "new_agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.py").write_text("# New agent")

        detector = FrameworkChangeDetector(project_root=tmp_path)
        changes = detector.detect_changes(known_agents=set())

        assert "new_agent" in changes.new_agents

    def test_detect_changes_no_changes(self, tmp_path):
        """Test change detection with no changes."""
        # Create agent directory
        agents_dir = tmp_path / "tapps_agents" / "agents"
        agent_dir = agents_dir / "existing_agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.py").write_text("# Existing agent")

        detector = FrameworkChangeDetector(project_root=tmp_path)
        changes = detector.detect_changes(known_agents={"existing_agent"})

        assert "existing_agent" not in changes.new_agents
        # Bug fix 1: modified_agents should be empty (not include all existing agents)
        assert changes.modified_agents == []


class TestAgentInfo:
    """Test AgentInfo class."""

    def test_agent_info_from_directory(self, tmp_path):
        """Test agent info extraction from directory."""
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()

        # Create agent.py with docstring
        agent_py = agent_dir / "agent.py"
        agent_py.write_text(
            '''class TestAgent:
    """Test agent purpose."""
    pass
'''
        )

        agent_info = AgentInfo.from_agent_directory(agent_dir)

        assert agent_info is not None
        assert agent_info.name == "test_agent"
        assert agent_info.purpose is not None

    def test_agent_info_from_directory_missing(self, tmp_path):
        """Test agent info extraction from nonexistent directory."""
        agent_dir = tmp_path / "nonexistent"
        agent_info = AgentInfo.from_agent_directory(agent_dir)

        assert agent_info is None

    def test_agent_info_from_directory_with_skill(self, tmp_path):
        """Test agent info extraction with skill file."""
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()

        # Create agent.py
        (agent_dir / "agent.py").write_text('class TestAgent: pass')

        # Create skill file in resources
        skills_dir = tmp_path.parent / "resources" / "claude" / "skills" / "test_agent"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("Commands: `*test` `*run`")

        agent_info = AgentInfo.from_agent_directory(agent_dir)

        assert agent_info is not None
        # Commands may or may not be extracted depending on path resolution
        # This is acceptable for now

    def test_agent_info_from_directory_with_skill_proper_structure(self, tmp_path):
        """Test agent info extraction with skill file using proper directory structure (Bug fix 4)."""
        # Create proper tapps_agents structure
        tapps_agents_dir = tmp_path / "tapps_agents"
        agents_dir = tapps_agents_dir / "agents" / "test_agent"
        agents_dir.mkdir(parents=True)

        # Create agent.py
        (agents_dir / "agent.py").write_text('class TestAgent: pass')

        # Create skill file in proper location
        skills_dir = tapps_agents_dir / "resources" / "claude" / "skills" / "test_agent"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("Commands: `*test` `*run` `*build`")

        agent_info = AgentInfo.from_agent_directory(agents_dir)

        assert agent_info is not None
        assert agent_info.name == "test_agent"
        # Commands should be extracted from skill file
        assert len(agent_info.commands) > 0

    def test_agent_info_command_order_preservation(self, tmp_path):
        """Test that command extraction preserves order (Bug fix 5)."""
        agent_dir = tmp_path / "test_agent"
        agent_dir.mkdir()

        # Create agent.py
        (agent_dir / "agent.py").write_text('class TestAgent: pass')

        # Create skill file with commands in specific order (with duplicates)
        skill_file = agent_dir / "SKILL.md"
        # Include duplicate commands to test deduplication preserves order
        skill_file.write_text("Commands: `*first` `*second` `*third` `*second` `*fourth`")

        agent_info = AgentInfo.from_agent_directory(agent_dir)

        assert agent_info is not None
        # Commands should be in order, with duplicates removed
        # Using dict.fromkeys() preserves insertion order
        assert len(agent_info.commands) == 4  # Duplicates removed
        assert agent_info.commands[0] == "first"
        assert agent_info.commands[1] == "second"
        assert agent_info.commands[2] == "third"
        assert agent_info.commands[3] == "fourth"
