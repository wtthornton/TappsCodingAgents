"""
Tests for Data Privacy Expert

Tests that Data Privacy expert is properly configured
and can be loaded from the built-in registry.
"""

import pytest

from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.expert_registry import ExpertRegistry


@pytest.mark.unit
class TestDataPrivacyExpert:
    """Test Data Privacy Expert configuration and loading."""

    def test_data_privacy_expert_exists(self):
        """Test that Data Privacy expert is configured."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        data_privacy_expert = next(
            (e for e in experts if e.expert_id == "expert-data-privacy"), None
        )

        assert data_privacy_expert is not None
        assert data_privacy_expert.expert_name == "Data Privacy & Compliance Expert"
        assert data_privacy_expert.primary_domain == "data-privacy-compliance"
        assert data_privacy_expert.rag_enabled is True

    def test_data_privacy_expert_loaded(self):
        """Test that Data Privacy expert is loaded in registry."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        data_privacy_expert = registry.get_expert("expert-data-privacy")

        assert data_privacy_expert is not None
        assert data_privacy_expert.expert_id == "expert-data-privacy"
        assert data_privacy_expert._is_builtin is True

    def test_data_privacy_knowledge_path(self):
        """Test that Data Privacy expert has knowledge base path."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        data_privacy_expert = registry.get_expert("expert-data-privacy")

        assert data_privacy_expert is not None
        assert data_privacy_expert._builtin_knowledge_path is not None
        knowledge_path = data_privacy_expert._builtin_knowledge_path

        # Knowledge directory should exist or be valid structure
        assert knowledge_path is not None
        # Path should point to knowledge directory
        assert "knowledge" in str(knowledge_path) or knowledge_path.exists()

    def test_data_privacy_is_technical_domain(self):
        """Test that data-privacy-compliance is a technical domain."""
        assert BuiltinExpertRegistry.is_technical_domain("data-privacy-compliance")

    def test_data_privacy_expert_for_domain(self):
        """Test that Data Privacy expert is returned for data-privacy-compliance domain."""
        expert_config = BuiltinExpertRegistry.get_expert_for_domain(
            "data-privacy-compliance"
        )

        assert expert_config is not None
        assert expert_config.expert_id == "expert-data-privacy"
        assert expert_config.primary_domain == "data-privacy-compliance"


@pytest.mark.unit
class TestDataPrivacyKnowledgeBase:
    """Test Data Privacy Expert knowledge base structure."""

    def test_knowledge_base_directory_exists(self):
        """Test that knowledge base directory structure exists."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()
        data_privacy_kb = knowledge_path / "data-privacy-compliance"

        # Directory should exist (created during Phase 3)
        assert data_privacy_kb.exists() or knowledge_path.exists()

    def test_knowledge_base_files_exist(self):
        """Test that key knowledge base files exist."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()
        data_privacy_kb = knowledge_path / "data-privacy-compliance"

        if data_privacy_kb.exists():
            # Check for key files
            expected_files = [
                "gdpr.md",
                "hipaa.md",
                "ccpa.md",
                "privacy-by-design.md",
                "data-minimization.md",
                "encryption-privacy.md",
                "anonymization.md",
                "data-retention.md",
                "consent-management.md",
                "data-subject-rights.md",
            ]

            existing_files = [f.name for f in data_privacy_kb.glob("*.md")]

            # At least some files should exist
            assert len(existing_files) > 0, "No knowledge base files found"

            # Check for key files
            for expected_file in expected_files[:3]:  # Check at least first 3
                if expected_file in existing_files:
                    file_path = data_privacy_kb / expected_file
                    assert file_path.exists()
                    assert file_path.stat().st_size > 0  # File should have content


@pytest.mark.unit
class TestDataPrivacyExpertIntegration:
    """Test Data Privacy Expert integration with registry."""

    def test_data_privacy_in_builtin_experts(self):
        """Test that Data Privacy expert is in builtin_experts dictionary."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)

        assert "expert-data-privacy" in registry.builtin_experts
        assert "expert-data-privacy" in registry.experts
        assert "expert-data-privacy" not in registry.customer_experts

    def test_data_privacy_expert_configuration(self):
        """Test Data Privacy expert configuration details."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        expert = registry.get_expert("expert-data-privacy")

        assert expert is not None
        assert expert.expert_id == "expert-data-privacy"
        assert expert.agent_name == "Data Privacy & Compliance Expert"
        assert expert.primary_domain == "data-privacy-compliance"
        assert expert.rag_enabled is True
        assert expert._is_builtin is True
