"""
Tests for tech stack config persistence.

Tests the init_tech_stack_config function and tech stack detection with priorities.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from tapps_agents.core.init_project import (
    detect_tech_stack,
    init_tech_stack_config,
)
from tapps_agents.core.tech_stack_priorities import get_priorities_for_frameworks

pytestmark = pytest.mark.unit


class TestInitTechStackConfig:
    """Tests for init_tech_stack_config function."""

    def test_creates_config_file(self, tmp_path: Path):
        """Test that config file is created in .tapps-agents directory."""
        tech_stack = {"frameworks": ["FastAPI"]}
        tech_stack["expert_priorities"] = get_priorities_for_frameworks(
            tech_stack["frameworks"]
        )

        created, path = init_tech_stack_config(tmp_path, tech_stack)

        assert created is True
        assert path is not None
        config_file = Path(path)
        assert config_file.exists()
        assert config_file.name == "tech-stack.yaml"
        assert config_file.parent.name == ".tapps-agents"

    def test_config_includes_frameworks(self, tmp_path: Path):
        """Test that config file includes detected frameworks."""
        tech_stack = {"frameworks": ["FastAPI", "React"]}
        tech_stack["expert_priorities"] = get_priorities_for_frameworks(
            tech_stack["frameworks"]
        )

        created, path = init_tech_stack_config(tmp_path, tech_stack)

        config_file = Path(path)
        config = yaml.safe_load(config_file.read_text())

        assert "frameworks" in config
        assert "FastAPI" in config["frameworks"]
        assert "React" in config["frameworks"]

    def test_config_includes_expert_priorities(self, tmp_path: Path):
        """Test that config file includes expert priorities."""
        tech_stack = {"frameworks": ["FastAPI"]}
        tech_stack["expert_priorities"] = get_priorities_for_frameworks(
            tech_stack["frameworks"]
        )

        created, path = init_tech_stack_config(tmp_path, tech_stack)

        config_file = Path(path)
        config = yaml.safe_load(config_file.read_text())

        assert "expert_priorities" in config
        assert "expert-api-design" in config["expert_priorities"]
        assert config["expert_priorities"]["expert-api-design"] == 1.0

    def test_updates_existing_config_preserves_overrides(self, tmp_path: Path):
        """Test that updating existing config preserves user overrides."""
        # Create initial config
        tech_stack1 = {"frameworks": ["FastAPI"]}
        tech_stack1["expert_priorities"] = get_priorities_for_frameworks(
            tech_stack1["frameworks"]
        )
        created1, path1 = init_tech_stack_config(tmp_path, tech_stack1)

        # Manually add overrides
        config_file = Path(path1)
        config = yaml.safe_load(config_file.read_text())
        config["overrides"] = {"expert-api-design": 0.8}
        config_file.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

        # Update with new tech stack
        tech_stack2 = {"frameworks": ["FastAPI", "React"]}
        tech_stack2["expert_priorities"] = get_priorities_for_frameworks(
            tech_stack2["frameworks"]
        )
        created2, path2 = init_tech_stack_config(tmp_path, tech_stack2)

        # Check that overrides are preserved
        updated_config = yaml.safe_load(config_file.read_text())
        assert "overrides" in updated_config
        assert updated_config["overrides"]["expert-api-design"] == 0.8

    def test_empty_frameworks_creates_empty_config(self, tmp_path: Path):
        """Test that empty frameworks list creates valid config."""
        tech_stack = {"frameworks": []}

        created, path = init_tech_stack_config(tmp_path, tech_stack)

        config_file = Path(path)
        config = yaml.safe_load(config_file.read_text())

        assert "frameworks" in config
        assert config["frameworks"] == []

    def test_no_priorities_no_expert_priorities_section(self, tmp_path: Path):
        """Test that if no priorities, expert_priorities section is not added."""
        tech_stack = {"frameworks": []}

        created, path = init_tech_stack_config(tmp_path, tech_stack)

        config_file = Path(path)
        config = yaml.safe_load(config_file.read_text())

        assert "expert_priorities" not in config

    def test_detect_tech_stack_includes_priorities(self, tmp_path: Path):
        """Test that detect_tech_stack includes expert priorities when frameworks detected."""
        # Create a mock FastAPI project
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("fastapi==0.100.0\nuvicorn==0.23.0")

        tech_stack = detect_tech_stack(tmp_path)

        assert "frameworks" in tech_stack
        assert "FastAPI" in tech_stack["frameworks"]
        assert "expert_priorities" in tech_stack
        assert "expert-api-design" in tech_stack["expert_priorities"]
        assert tech_stack["expert_priorities"]["expert-api-design"] == 1.0

    def test_detect_tech_stack_no_frameworks_no_priorities(self, tmp_path: Path):
        """Test that detect_tech_stack doesn't include priorities when no frameworks."""
        tech_stack = detect_tech_stack(tmp_path)

        assert "frameworks" in tech_stack
        assert tech_stack["frameworks"] == []
        # Should not include expert_priorities if no frameworks
        assert "expert_priorities" not in tech_stack

    def test_config_uses_provided_tech_stack(self, tmp_path: Path):
        """Test that function uses provided tech_stack parameter."""
        provided_stack = {"frameworks": ["Django"], "expert_priorities": {"expert-database": 0.9}}

        created, path = init_tech_stack_config(tmp_path, provided_stack)

        config_file = Path(path)
        config = yaml.safe_load(config_file.read_text())

        assert config["frameworks"] == ["Django"]
        assert config["expert_priorities"]["expert-database"] == 0.9

    def test_config_detects_tech_stack_if_not_provided(self, tmp_path: Path):
        """Test that function detects tech stack if not provided."""
        # Create a mock React project
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"react": "^18.0.0"}}')

        created, path = init_tech_stack_config(tmp_path, tech_stack=None)

        config_file = Path(path)
        config = yaml.safe_load(config_file.read_text())

        assert "frameworks" in config
        # Should detect React from package.json
        assert "React" in config["frameworks"]

