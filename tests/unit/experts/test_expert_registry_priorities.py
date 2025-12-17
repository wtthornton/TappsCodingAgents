"""
Tests for expert registry priority integration.

Tests that expert registry loads and applies tech stack priorities.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from tapps_agents.experts.expert_registry import ExpertRegistry

pytestmark = pytest.mark.unit


class TestExpertRegistryPriorityLoading:
    """Tests for loading priorities from tech-stack.yaml."""

    def test_loads_priorities_from_config(self, tmp_path: Path):
        """Test that priorities are loaded from tech-stack.yaml."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir()
        tech_stack_file = config_dir / "tech-stack.yaml"
        tech_stack_file.write_text(
            yaml.safe_dump(
                {
                    "expert_priorities": {
                        "expert-api-design": 1.0,
                        "expert-performance": 0.8,
                    }
                }
            )
        )

        registry = ExpertRegistry(project_root=tmp_path)

        assert registry._tech_stack_priorities is not None
        assert registry._tech_stack_priorities["expert-api-design"] == 1.0
        assert registry._tech_stack_priorities["expert-performance"] == 0.8

    def test_applies_overrides_to_priorities(self, tmp_path: Path):
        """Test that overrides take precedence over default priorities."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir()
        tech_stack_file = config_dir / "tech-stack.yaml"
        tech_stack_file.write_text(
            yaml.safe_dump(
                {
                    "expert_priorities": {"expert-api-design": 1.0},
                    "overrides": {"expert-api-design": 0.7},
                }
            )
        )

        registry = ExpertRegistry(project_root=tmp_path)

        assert registry._tech_stack_priorities is not None
        # Override should take precedence
        assert registry._tech_stack_priorities["expert-api-design"] == 0.7

    def test_works_without_config_file(self, tmp_path: Path):
        """Test that registry works without tech-stack.yaml (backward compatible)."""
        registry = ExpertRegistry(project_root=tmp_path)

        assert registry._tech_stack_priorities is None
        # Should still work - no priorities applied
        assert registry is not None

    def test_handles_invalid_config_gracefully(self, tmp_path: Path):
        """Test that invalid config file doesn't break registry."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir()
        tech_stack_file = config_dir / "tech-stack.yaml"
        tech_stack_file.write_text("invalid yaml: [\n\n")

        # Should not raise exception
        registry = ExpertRegistry(project_root=tmp_path)

        # Priorities should be None if config is invalid
        assert registry._tech_stack_priorities is None


class TestExpertRegistryPriorityApplication:
    """Tests for applying priorities to expert ordering."""

    def test_apply_priorities_sorts_by_priority(self):
        """Test that _apply_priorities sorts experts by priority (higher first)."""
        registry = ExpertRegistry(project_root=Path.cwd())
        registry._tech_stack_priorities = {
            "expert-api-design": 1.0,
            "expert-performance": 0.8,
            "expert-security": 0.9,
        }

        expert_ids = ["expert-performance", "expert-api-design", "expert-security"]
        result = registry._apply_priorities(expert_ids)

        # Should be sorted by priority: api-design (1.0) > security (0.9) > performance (0.8)
        assert result[0] == "expert-api-design"
        assert result[1] == "expert-security"
        assert result[2] == "expert-performance"

    def test_apply_priorities_handles_unprioritized_experts(self):
        """Test that experts without priorities appear at the end."""
        registry = ExpertRegistry(project_root=Path.cwd())
        registry._tech_stack_priorities = {"expert-api-design": 1.0}

        expert_ids = ["expert-unknown", "expert-api-design", "expert-another-unknown"]
        result = registry._apply_priorities(expert_ids)

        # Prioritized expert should come first
        assert result[0] == "expert-api-design"
        # Unprioritized experts should come after
        assert "expert-unknown" in result[1:]
        assert "expert-another-unknown" in result[1:]

    def test_apply_priorities_no_priorities_returns_unchanged(self):
        """Test that _apply_priorities returns unchanged list if no priorities loaded."""
        registry = ExpertRegistry(project_root=Path.cwd())
        registry._tech_stack_priorities = None

        expert_ids = ["expert-api-design", "expert-performance"]
        result = registry._apply_priorities(expert_ids)

        assert result == expert_ids

    def test_get_experts_for_domain_applies_priorities(self, tmp_path: Path):
        """Test that _get_experts_for_domain applies priorities when available."""
        # Create config with priorities
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir()
        tech_stack_file = config_dir / "tech-stack.yaml"
        tech_stack_file.write_text(
            yaml.safe_dump(
                {
                    "expert_priorities": {
                        "expert-performance": 1.0,
                        "expert-security": 0.9,
                    }
                }
            )
        )

        registry = ExpertRegistry(project_root=tmp_path)

        # Get experts for a domain (assuming we have built-in experts registered)
        # Note: This test depends on actual built-in experts being loaded
        expert_ids = registry._get_experts_for_domain("performance-optimization")

        # If priorities are applied, expert-performance should come before expert-security
        # (if both are in the list)
        if "expert-performance" in expert_ids and "expert-security" in expert_ids:
            perf_index = expert_ids.index("expert-performance")
            sec_index = expert_ids.index("expert-security")
            # expert-performance (1.0) should come before expert-security (0.9)
            assert perf_index < sec_index

    def test_get_experts_for_domain_works_without_priorities(self, tmp_path: Path):
        """Test that _get_experts_for_domain works without priorities (backward compatible)."""
        registry = ExpertRegistry(project_root=tmp_path)

        # Should work without priorities
        expert_ids = registry._get_experts_for_domain("security")

        # Should return list of expert IDs (may be empty if no experts match)
        assert isinstance(expert_ids, list)

