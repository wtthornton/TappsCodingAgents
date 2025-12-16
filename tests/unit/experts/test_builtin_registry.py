"""
Tests for Built-in Expert Registry

Tests the built-in expert registry system that manages framework-controlled,
immutable experts.
"""

from pathlib import Path

from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.expert_config import ExpertConfigModel

import pytest

pytestmark = pytest.mark.unit


class TestBuiltinExpertRegistry:
    """Test built-in expert registry functionality."""

    def test_get_builtin_experts(self):
        """Test retrieving all built-in expert configurations."""
        experts = BuiltinExpertRegistry.get_builtin_experts()

        assert isinstance(experts, list)
        assert len(experts) > 0

        # All should be ExpertConfigModel instances
        for expert in experts:
            assert isinstance(expert, ExpertConfigModel)
            assert expert.expert_id
            assert expert.expert_name
            assert expert.primary_domain

    def test_get_builtin_expert_ids(self):
        """Test retrieving built-in expert IDs."""
        expert_ids = BuiltinExpertRegistry.get_builtin_expert_ids()

        assert isinstance(expert_ids, list)
        assert len(expert_ids) > 0

        # All should be strings
        for expert_id in expert_ids:
            assert isinstance(expert_id, str)
            assert expert_id.startswith("expert-")

    def test_is_builtin_expert(self):
        """Test checking if an expert is built-in."""
        expert_ids = BuiltinExpertRegistry.get_builtin_expert_ids()

        # All built-in experts should return True
        for expert_id in expert_ids:
            assert BuiltinExpertRegistry.is_builtin_expert(expert_id) is True

        # Non-built-in experts should return False
        assert BuiltinExpertRegistry.is_builtin_expert("expert-custom") is False
        assert BuiltinExpertRegistry.is_builtin_expert("not-an-expert") is False

    def test_security_expert_exists(self):
        """Test that Security expert is configured."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        security_expert = next(
            (e for e in experts if e.expert_id == "expert-security"), None
        )

        assert security_expert is not None
        assert security_expert.expert_name == "Security Expert"
        assert security_expert.primary_domain == "security"
        assert security_expert.rag_enabled is True

    def test_get_builtin_knowledge_path(self):
        """Test getting built-in knowledge base path."""
        knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()

        assert isinstance(knowledge_path, Path)
        # Path should exist or be a valid relative path
        assert knowledge_path is not None

    def test_is_technical_domain(self):
        """Test checking if a domain is a technical domain."""
        # Technical domains should return True
        assert BuiltinExpertRegistry.is_technical_domain("security") is True
        assert (
            BuiltinExpertRegistry.is_technical_domain("performance-optimization")
            is True
        )
        assert BuiltinExpertRegistry.is_technical_domain("testing-strategies") is True

        # Business domains should return False
        assert BuiltinExpertRegistry.is_technical_domain("healthcare") is False
        assert BuiltinExpertRegistry.is_technical_domain("finance") is False
        assert BuiltinExpertRegistry.is_technical_domain("e-commerce") is False

    def test_get_expert_for_domain(self):
        """Test getting expert configuration for a domain."""
        # Should find Security expert for security domain
        security_expert = BuiltinExpertRegistry.get_expert_for_domain("security")
        assert security_expert is not None
        assert security_expert.expert_id == "expert-security"

        # Should return None for non-technical domains
        business_expert = BuiltinExpertRegistry.get_expert_for_domain("healthcare")
        assert business_expert is None

    def test_all_builtin_experts_have_required_fields(self):
        """Test that all built-in experts have required configuration fields."""
        experts = BuiltinExpertRegistry.get_builtin_experts()

        for expert in experts:
            assert expert.expert_id, f"Expert missing expert_id: {expert}"
            assert expert.expert_name, f"Expert missing expert_name: {expert.expert_id}"
            assert (
                expert.primary_domain
            ), f"Expert missing primary_domain: {expert.expert_id}"
            assert isinstance(
                expert.rag_enabled, bool
            ), f"Expert rag_enabled not bool: {expert.expert_id}"
            assert isinstance(
                expert.fine_tuned, bool
            ), f"Expert fine_tuned not bool: {expert.expert_id}"

    def test_builtin_experts_unique_ids(self):
        """Test that all built-in expert IDs are unique."""
        experts = BuiltinExpertRegistry.get_builtin_experts()
        expert_ids = [e.expert_id for e in experts]

        assert len(expert_ids) == len(set(expert_ids)), "Duplicate expert IDs found"

    def test_builtin_experts_technical_domains(self):
        """Test that all built-in experts use technical domains."""
        experts = BuiltinExpertRegistry.get_builtin_experts()

        for expert in experts:
            assert BuiltinExpertRegistry.is_technical_domain(
                expert.primary_domain
            ), f"Expert {expert.expert_id} uses non-technical domain: {expert.primary_domain}"
