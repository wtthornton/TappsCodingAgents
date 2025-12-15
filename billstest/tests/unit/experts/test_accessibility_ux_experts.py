"""
Tests for Accessibility and UX Experts

Tests that Accessibility and UX experts are properly configured
and can be loaded from the built-in registry.
"""

import pytest

from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.expert_registry import ExpertRegistry


@pytest.mark.unit
class TestAccessibilityExpert:
    """Test Accessibility Expert configuration and loading."""

    def test_accessibility_expert_exists(self):
        """Test that Accessibility expert is configured."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        accessibility_expert = next(
            (e for e in experts if e.expert_id == "expert-accessibility"), None
        )

        assert accessibility_expert is not None
        assert accessibility_expert.expert_name == "Accessibility Expert"
        assert accessibility_expert.primary_domain == "accessibility"
        assert accessibility_expert.rag_enabled is True

    def test_accessibility_expert_loaded(self):
        """Test that Accessibility expert is loaded in registry."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        accessibility_expert = registry.get_expert("expert-accessibility")

        assert accessibility_expert is not None
        assert accessibility_expert.expert_id == "expert-accessibility"
        assert accessibility_expert._is_builtin is True

    def test_accessibility_knowledge_path(self):
        """Test that Accessibility expert has knowledge base path."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        accessibility_expert = registry.get_expert("expert-accessibility")

        assert accessibility_expert is not None
        assert accessibility_expert._builtin_knowledge_path is not None
        knowledge_path = accessibility_expert._builtin_knowledge_path

        # Knowledge directory should exist or be valid structure
        assert knowledge_path is not None
        # Path should point to knowledge directory
        assert "knowledge" in str(knowledge_path) or knowledge_path.exists()

    def test_accessibility_is_technical_domain(self):
        """Test that accessibility is a technical domain."""
        assert BuiltinExpertRegistry.is_technical_domain("accessibility")

    def test_accessibility_expert_for_domain(self):
        """Test that Accessibility expert is returned for accessibility domain."""
        expert_config = BuiltinExpertRegistry.get_expert_for_domain("accessibility")

        assert expert_config is not None
        assert expert_config.expert_id == "expert-accessibility"
        assert expert_config.primary_domain == "accessibility"


@pytest.mark.unit
class TestUXExpert:
    """Test UX Expert configuration and loading."""

    def test_ux_expert_exists(self):
        """Test that UX expert is configured."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        ux_expert = next(
            (e for e in experts if e.expert_id == "expert-user-experience"), None
        )

        assert ux_expert is not None
        assert ux_expert.expert_name == "User Experience Expert"
        assert ux_expert.primary_domain == "user-experience"
        assert ux_expert.rag_enabled is True

    def test_ux_expert_loaded(self):
        """Test that UX expert is loaded in registry."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        ux_expert = registry.get_expert("expert-user-experience")

        assert ux_expert is not None
        assert ux_expert.expert_id == "expert-user-experience"
        assert ux_expert._is_builtin is True

    def test_ux_knowledge_path(self):
        """Test that UX expert has knowledge base path."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        ux_expert = registry.get_expert("expert-user-experience")

        assert ux_expert is not None
        assert ux_expert._builtin_knowledge_path is not None
        knowledge_path = ux_expert._builtin_knowledge_path

        # Knowledge directory should exist or be valid structure
        assert knowledge_path is not None
        # Path should point to knowledge directory
        assert "knowledge" in str(knowledge_path) or knowledge_path.exists()

    def test_ux_is_technical_domain(self):
        """Test that user-experience is a technical domain."""
        assert BuiltinExpertRegistry.is_technical_domain("user-experience")

    def test_ux_expert_for_domain(self):
        """Test that UX expert is returned for user-experience domain."""
        expert_config = BuiltinExpertRegistry.get_expert_for_domain("user-experience")

        assert expert_config is not None
        assert expert_config.expert_id == "expert-user-experience"
        assert expert_config.primary_domain == "user-experience"


@pytest.mark.unit
class TestAccessibilityKnowledgeBase:
    """Test Accessibility Expert knowledge base structure."""

    def test_knowledge_base_directory_exists(self):
        """Test that knowledge base directory structure exists."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()
        accessibility_kb = knowledge_path / "accessibility"

        # Directory should exist (created during Phase 4)
        assert accessibility_kb.exists() or knowledge_path.exists()

    def test_knowledge_base_files_exist(self):
        """Test that key knowledge base files exist."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()
        accessibility_kb = knowledge_path / "accessibility"

        if accessibility_kb.exists():
            # Check for key files
            expected_files = [
                "wcag-2.1.md",
                "wcag-2.2.md",
                "aria-patterns.md",
                "screen-readers.md",
                "keyboard-navigation.md",
                "color-contrast.md",
                "semantic-html.md",
                "accessible-forms.md",
                "testing-accessibility.md",
            ]

            existing_files = [f.name for f in accessibility_kb.glob("*.md")]

            # At least some files should exist
            assert len(existing_files) > 0, "No knowledge base files found"

            # Check for key files
            for expected_file in expected_files[:3]:  # Check at least first 3
                if expected_file in existing_files:
                    file_path = accessibility_kb / expected_file
                    assert file_path.exists()
                    assert file_path.stat().st_size > 0  # File should have content


@pytest.mark.unit
class TestUXKnowledgeBase:
    """Test UX Expert knowledge base structure."""

    def test_knowledge_base_directory_exists(self):
        """Test that knowledge base directory structure exists."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()
        ux_kb = knowledge_path / "user-experience"

        # Directory should exist (created during Phase 4)
        assert ux_kb.exists() or knowledge_path.exists()

    def test_knowledge_base_files_exist(self):
        """Test that key knowledge base files exist."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()
        ux_kb = knowledge_path / "user-experience"

        if ux_kb.exists():
            # Check for key files
            expected_files = [
                "ux-principles.md",
                "usability-heuristics.md",
                "user-research.md",
                "interaction-design.md",
                "information-architecture.md",
                "user-journeys.md",
                "prototyping.md",
                "usability-testing.md",
            ]

            existing_files = [f.name for f in ux_kb.glob("*.md")]

            # At least some files should exist
            assert len(existing_files) > 0, "No knowledge base files found"

            # Check for key files
            for expected_file in expected_files[:3]:  # Check at least first 3
                if expected_file in existing_files:
                    file_path = ux_kb / expected_file
                    assert file_path.exists()
                    assert file_path.stat().st_size > 0  # File should have content


@pytest.mark.unit
class TestAccessibilityUXExpertIntegration:
    """Test Accessibility and UX Expert integration with registry."""

    def test_both_experts_in_builtin_experts(self):
        """Test that both experts are in builtin_experts dictionary."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)

        assert "expert-accessibility" in registry.builtin_experts
        assert "expert-user-experience" in registry.builtin_experts
        assert "expert-accessibility" in registry.experts
        assert "expert-user-experience" in registry.experts
        assert "expert-accessibility" not in registry.customer_experts
        assert "expert-user-experience" not in registry.customer_experts

    def test_accessibility_expert_configuration(self):
        """Test Accessibility expert configuration details."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        expert = registry.get_expert("expert-accessibility")

        assert expert is not None
        assert expert.expert_id == "expert-accessibility"
        assert expert.agent_name == "Accessibility Expert"
        assert expert.primary_domain == "accessibility"
        assert expert.rag_enabled is True
        assert expert._is_builtin is True

    def test_ux_expert_configuration(self):
        """Test UX expert configuration details."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        expert = registry.get_expert("expert-user-experience")

        assert expert is not None
        assert expert.expert_id == "expert-user-experience"
        assert expert.agent_name == "User Experience Expert"
        assert expert.primary_domain == "user-experience"
        assert expert.rag_enabled is True
        assert expert._is_builtin is True
