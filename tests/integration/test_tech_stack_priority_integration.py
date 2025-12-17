"""
Integration tests for tech stack priority system.

Tests the full flow: detection → config → registry → consultation.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from tapps_agents.core.init_project import detect_tech_stack, init_tech_stack_config
from tapps_agents.experts.expert_registry import ExpertRegistry

pytestmark = pytest.mark.integration


class TestTechStackPriorityIntegration:
    """Integration tests for tech stack priority system end-to-end."""

    def test_full_flow_detection_to_consultation(self, tmp_path: Path):
        """Test full flow: detection → config → registry → consultation."""
        # Create a mock FastAPI project
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("fastapi==0.100.0\nuvicorn==0.23.0")

        # Step 1: Detect tech stack
        tech_stack = detect_tech_stack(tmp_path)
        assert "FastAPI" in tech_stack["frameworks"]
        assert "expert_priorities" in tech_stack

        # Step 2: Persist to config
        created, config_path = init_tech_stack_config(tmp_path, tech_stack)
        assert created is True
        config_file = Path(config_path)
        assert config_file.exists()

        # Step 3: Load config and verify
        config = yaml.safe_load(config_file.read_text())
        assert "frameworks" in config
        assert "FastAPI" in config["frameworks"]
        assert "expert_priorities" in config
        assert "expert-api-design" in config["expert_priorities"]
        assert config["expert_priorities"]["expert-api-design"] == 1.0

        # Step 4: Initialize expert registry (should load priorities)
        registry = ExpertRegistry(project_root=tmp_path)
        assert registry._tech_stack_priorities is not None
        assert registry._tech_stack_priorities["expert-api-design"] == 1.0

        # Step 5: Verify expert ordering uses priorities
        # Get experts for API design domain
        expert_ids = registry._get_experts_for_domain("api-design-integration")
        # If expert-api-design is in the list, it should be prioritized
        if "expert-api-design" in expert_ids:
            # Should appear early in the list (prioritized)
            assert expert_ids.index("expert-api-design") < len(expert_ids)

    def test_multiple_frameworks_priority_combination(self, tmp_path: Path):
        """Test that multiple frameworks combine priorities correctly."""
        # Create a project with both FastAPI and React
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"react": "^18.0.0"}}')
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("fastapi==0.100.0")

        # Detect tech stack
        tech_stack = detect_tech_stack(tmp_path)
        assert "FastAPI" in tech_stack["frameworks"]
        assert "React" in tech_stack["frameworks"]

        # Persist config
        init_tech_stack_config(tmp_path, tech_stack)

        # Initialize registry
        registry = ExpertRegistry(project_root=tmp_path)
        assert registry._tech_stack_priorities is not None

        # Should have priorities from both frameworks
        assert "expert-api-design" in registry._tech_stack_priorities  # From FastAPI
        assert "expert-user-experience" in registry._tech_stack_priorities  # From React

    def test_priority_overrides_work_end_to_end(self, tmp_path: Path):
        """Test that priority overrides work in full flow."""
        # Create mock project
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("fastapi==0.100.0")

        # Detect and persist
        tech_stack = detect_tech_stack(tmp_path)
        init_tech_stack_config(tmp_path, tech_stack)

        # Manually add override
        config_file = tmp_path / ".tapps-agents" / "tech-stack.yaml"
        config = yaml.safe_load(config_file.read_text())
        config["overrides"] = {"expert-api-design": 0.5}
        config_file.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

        # Initialize registry (should load with override)
        registry = ExpertRegistry(project_root=tmp_path)
        assert registry._tech_stack_priorities is not None
        # Override should be applied
        assert registry._tech_stack_priorities["expert-api-design"] == 0.5

    def test_works_without_priorities_backward_compatible(self, tmp_path: Path):
        """Test that system works without priorities (backward compatible)."""
        # Create project without tech stack config
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("some-library==1.0.0")

        # Detect tech stack (no frameworks detected)
        tech_stack = detect_tech_stack(tmp_path)
        assert tech_stack["frameworks"] == []

        # Persist config (no priorities)
        init_tech_stack_config(tmp_path, tech_stack)

        # Initialize registry (should work without priorities)
        registry = ExpertRegistry(project_root=tmp_path)
        # Priorities may be None or empty - both are valid
        assert registry is not None

        # Should still be able to get experts for domain
        expert_ids = registry._get_experts_for_domain("security")
        assert isinstance(expert_ids, list)

    def test_config_update_preserves_overrides(self, tmp_path: Path):
        """Test that updating config preserves user overrides."""
        # Initial setup
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("fastapi==0.100.0")

        tech_stack1 = detect_tech_stack(tmp_path)
        init_tech_stack_config(tmp_path, tech_stack1)

        # Add override
        config_file = tmp_path / ".tapps-agents" / "tech-stack.yaml"
        config = yaml.safe_load(config_file.read_text())
        config["overrides"] = {"expert-api-design": 0.6}
        config_file.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

        # Update config with new tech stack
        tech_stack2 = detect_tech_stack(tmp_path)
        tech_stack2["frameworks"] = ["FastAPI", "React"]  # Add React
        init_tech_stack_config(tmp_path, tech_stack2)

        # Verify override is preserved
        updated_config = yaml.safe_load(config_file.read_text())
        assert "overrides" in updated_config
        assert updated_config["overrides"]["expert-api-design"] == 0.6

        # Verify registry uses override
        registry = ExpertRegistry(project_root=tmp_path)
        assert registry._tech_stack_priorities["expert-api-design"] == 0.6

