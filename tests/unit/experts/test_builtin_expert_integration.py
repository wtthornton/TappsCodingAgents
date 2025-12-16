"""
Integration tests for built-in expert system.

Tests the integration of built-in experts with ExpertRegistry and BaseExpert.
"""

from pathlib import Path

import pytest

from tapps_agents.experts.base_expert import BaseExpert
from tapps_agents.experts.expert_registry import ExpertRegistry

pytestmark = pytest.mark.unit


class TestBuiltinExpertIntegration:
    """Test built-in expert integration with registry."""

    def test_expert_registry_loads_builtin_experts(self):
        """Test that ExpertRegistry automatically loads built-in experts."""
        registry = ExpertRegistry(load_builtin=True)

        # Should have built-in experts loaded
        assert len(registry.builtin_experts) > 0
        assert len(registry.experts) > 0

        # Security expert should be loaded
        security_expert = registry.get_expert("expert-security")
        assert security_expert is not None
        assert security_expert.expert_id == "expert-security"
        assert security_expert in registry.builtin_experts.values()

    def test_expert_registry_separates_builtin_and_customer(self):
        """Test that ExpertRegistry separates built-in and customer experts."""
        registry = ExpertRegistry(load_builtin=True)

        # Add a customer expert
        customer_expert = BaseExpert(
            expert_id="expert-custom",
            expert_name="Custom Expert",
            primary_domain="custom-domain",
            rag_enabled=False,
        )
        registry.register_expert(customer_expert, is_builtin=False)

        # Should be in customer experts
        assert "expert-custom" in registry.customer_experts
        assert "expert-custom" in registry.experts

        # Built-in experts should still be separate
        assert "expert-security" in registry.builtin_experts
        assert "expert-security" not in registry.customer_experts

    def test_builtin_expert_has_builtin_flags(self):
        """Test that built-in experts have proper flags set."""
        registry = ExpertRegistry(load_builtin=True)
        security_expert = registry.get_expert("expert-security")

        assert security_expert._is_builtin is True
        assert security_expert._builtin_knowledge_path is not None
        assert isinstance(security_expert._builtin_knowledge_path, Path)

    def test_customer_expert_not_builtin(self):
        """Test that customer experts don't have built-in flags."""
        registry = ExpertRegistry(load_builtin=True)

        customer_expert = BaseExpert(
            expert_id="expert-custom",
            expert_name="Custom Expert",
            primary_domain="custom-domain",
            rag_enabled=False,
        )
        registry.register_expert(customer_expert, is_builtin=False)

        assert customer_expert._is_builtin is False
        assert customer_expert._builtin_knowledge_path is None

    def test_from_config_file_skips_builtin_experts(self):
        """Test that from_config_file doesn't duplicate built-in experts."""
        # Create a temporary config file with a built-in expert
        import tempfile

        import yaml

        config_data = {
            "experts": [
                {
                    "expert_id": "expert-security",  # Built-in expert
                    "expert_name": "Security Expert",
                    "primary_domain": "security",
                    "rag_enabled": True,
                },
                {
                    "expert_id": "expert-custom",
                    "expert_name": "Custom Expert",
                    "primary_domain": "custom-domain",
                    "rag_enabled": False,
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            registry = ExpertRegistry.from_config_file(config_path)

            # Should have built-in expert (from auto-load)
            assert "expert-security" in registry.builtin_experts

            # Should have customer expert
            assert "expert-custom" in registry.customer_experts

            # Should not have duplicate security expert
            security_count = sum(
                1 for eid in registry.experts.keys() if eid == "expert-security"
            )
            assert security_count == 1, "Duplicate built-in expert found"
        finally:
            config_path.unlink()

    def test_builtin_expert_knowledge_path_resolution(self):
        """Test that built-in experts resolve knowledge paths correctly."""
        registry = ExpertRegistry(load_builtin=True)
        security_expert = registry.get_expert("expert-security")

        # Should have built-in knowledge path set
        assert security_expert._builtin_knowledge_path is not None

        # Knowledge path should point to security directory
        knowledge_path = security_expert._builtin_knowledge_path
        security_kb_path = knowledge_path / "security"

        # Path should exist or be a valid structure
        assert knowledge_path.exists() or security_kb_path.parent.exists()

    @pytest.mark.asyncio
    async def test_builtin_expert_rag_initialization(self):
        """Test that built-in experts initialize RAG with correct paths."""
        registry = ExpertRegistry(load_builtin=True)
        security_expert = registry.get_expert("expert-security")

        # Mock project root
        project_root = Path("/tmp/test-project")
        project_root.mkdir(exist_ok=True)

        try:
            # Activate expert
            await security_expert.activate(project_root=project_root)

            # If RAG is enabled, knowledge base should be initialized
            if security_expert.rag_enabled:
                # Knowledge base might be None if no knowledge files exist
                # but the initialization should have been attempted
                assert hasattr(security_expert, "knowledge_base")
        finally:
            # Cleanup
            if project_root.exists():
                import shutil

                shutil.rmtree(project_root, ignore_errors=True)

    def test_list_experts_includes_builtin(self):
        """Test that list_experts includes built-in experts."""
        registry = ExpertRegistry(load_builtin=True)
        expert_ids = registry.list_experts()

        # Should include built-in experts
        assert "expert-security" in expert_ids

        # Should include all registered experts
        assert len(expert_ids) >= len(registry.builtin_experts)
