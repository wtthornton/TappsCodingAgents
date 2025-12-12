"""
Tests for Performance and Testing Experts

Tests that Performance and Testing experts are properly configured
and can be loaded from the built-in registry.
"""


import pytest

from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.expert_registry import ExpertRegistry


@pytest.mark.unit
class TestPerformanceExpert:
    """Test Performance Expert configuration and loading."""

    def test_performance_expert_exists(self):
        """Test that Performance expert is configured."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        performance_expert = next(
            (e for e in experts if e.expert_id == "expert-performance"), None
        )

        assert performance_expert is not None
        assert performance_expert.expert_name == "Performance Expert"
        assert performance_expert.primary_domain == "performance-optimization"
        assert performance_expert.rag_enabled is True

    def test_performance_expert_loaded(self):
        """Test that Performance expert is loaded in registry."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        performance_expert = registry.get_expert("expert-performance")

        assert performance_expert is not None
        assert performance_expert.expert_id == "expert-performance"
        assert performance_expert._is_builtin is True

    def test_performance_knowledge_path(self):
        """Test that Performance expert has knowledge base path."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        performance_expert = registry.get_expert("expert-performance")

        assert performance_expert is not None
        assert performance_expert._builtin_knowledge_path is not None
        knowledge_path = performance_expert._builtin_knowledge_path

        # Knowledge directory should exist or be valid structure
        assert knowledge_path is not None
        # Path should point to knowledge directory
        assert "knowledge" in str(knowledge_path) or knowledge_path.exists()


@pytest.mark.unit
class TestTestingExpert:
    """Test Testing Expert configuration and loading."""

    def test_testing_expert_exists(self):
        """Test that Testing expert is configured."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        testing_expert = next(
            (e for e in experts if e.expert_id == "expert-testing"), None
        )

        assert testing_expert is not None
        assert testing_expert.expert_name == "Testing Expert"
        assert testing_expert.primary_domain == "testing-strategies"
        assert testing_expert.rag_enabled is True

    def test_testing_expert_loaded(self):
        """Test that Testing expert is loaded in registry."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        testing_expert = registry.get_expert("expert-testing")

        assert testing_expert is not None
        assert testing_expert.expert_id == "expert-testing"
        assert testing_expert._is_builtin is True

    def test_testing_knowledge_path(self):
        """Test that Testing expert has knowledge base path."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        testing_expert = registry.get_expert("expert-testing")

        assert testing_expert is not None
        assert testing_expert._builtin_knowledge_path is not None
        knowledge_path = testing_expert._builtin_knowledge_path

        # Knowledge directory should exist or be valid structure
        assert knowledge_path is not None
        # Path should point to knowledge directory
        assert "knowledge" in str(knowledge_path) or knowledge_path.exists()


@pytest.mark.unit
class TestPerformanceTestingExpertIntegration:
    """Integration tests for Performance and Testing experts."""

    def test_both_experts_available(self):
        """Test that both experts are available in registry."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)

        performance_expert = registry.get_expert("expert-performance")
        testing_expert = registry.get_expert("expert-testing")

        assert performance_expert is not None
        assert testing_expert is not None
        assert performance_expert in registry.builtin_experts.values()
        assert testing_expert in registry.builtin_experts.values()

    def test_experts_have_different_domains(self):
        """Test that experts have different primary domains."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)

        performance_expert = registry.get_expert("expert-performance")
        testing_expert = registry.get_expert("expert-testing")

        assert performance_expert is not None
        assert testing_expert is not None
        assert performance_expert.primary_domain != testing_expert.primary_domain
        assert performance_expert.primary_domain == "performance-optimization"
        assert testing_expert.primary_domain == "testing-strategies"

    def test_experts_are_technical_domains(self):
        """Test that both experts use technical domains."""
        performance_domain = "performance-optimization"
        testing_domain = "testing-strategies"

        assert BuiltinExpertRegistry.is_technical_domain(performance_domain) is True
        assert BuiltinExpertRegistry.is_technical_domain(testing_domain) is True
