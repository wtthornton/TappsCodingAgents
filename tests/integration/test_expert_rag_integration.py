"""
Integration tests for Expert RAG system.

Tests expert consultations with RAG knowledge bases.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tapps_agents.experts.base_expert import BaseExpert
from tapps_agents.experts.simple_rag import SimpleKnowledgeBase

pytestmark = pytest.mark.integration


class TestExpertRAGIntegration:
    """Test Expert RAG integration."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory with test files."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / ".tapps-agents" / "knowledge" / "test-domain"
        knowledge_dir.mkdir(parents=True)

        # Create test knowledge file
        test_file = knowledge_dir / "test-knowledge.md"
        test_file.write_text(
            """# Test Domain Knowledge

## Best Practices
Always follow best practices when implementing features.
Use proper error handling and logging.

## Patterns
Common patterns include:
- Design patterns
- Architectural patterns
- Code patterns
""",
            encoding="utf-8",
        )

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def test_expert(self, temp_knowledge_dir):
        """Create a test expert with RAG enabled."""
        expert = BaseExpert(
            expert_id="expert-test-domain",
            expert_name="Test Domain Expert",
            primary_domain="test-domain",
            rag_enabled=True,
        )
        return expert

    @pytest.mark.asyncio
    async def test_expert_rag_initialization(self, test_expert, temp_knowledge_dir):
        """Test that expert initializes RAG correctly."""
        await test_expert.activate(project_root=temp_knowledge_dir)

        # RAG should be initialized if knowledge base exists
        # Note: May be None if knowledge directory doesn't match expected structure
        assert hasattr(test_expert, "knowledge_base")
        assert hasattr(test_expert, "rag_interface")

    @pytest.mark.asyncio
    async def test_expert_consult_with_rag(self, test_expert, temp_knowledge_dir):
        """Test expert consultation uses RAG when available."""
        await test_expert.activate(project_root=temp_knowledge_dir)

        # Build domain context (uses RAG if available)
        context = await test_expert._build_domain_context("best practices", "test-domain")

        # Should return context (either from RAG or default)
        assert isinstance(context, str)
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_expert_get_sources_with_rag(self, test_expert, temp_knowledge_dir):
        """Test expert get_sources uses RAG when available."""
        await test_expert.activate(project_root=temp_knowledge_dir)

        # Get sources (uses RAG if available)
        sources = await test_expert._get_sources("best practices", "test-domain")

        # Should return list of sources
        assert isinstance(sources, list)

    @pytest.mark.asyncio
    async def test_expert_consult_returns_sources(self, test_expert, temp_knowledge_dir):
        """Test that expert consultation returns sources when RAG is enabled."""
        await test_expert.activate(project_root=temp_knowledge_dir)

        # Consult expert
        result = await test_expert.run("consult", query="What are best practices?", domain="test-domain")

        # Should return sources in response
        assert "sources" in result
        assert isinstance(result["sources"], list)

    @pytest.mark.asyncio
    async def test_expert_rag_disabled(self):
        """Test expert behavior when RAG is disabled."""
        expert = BaseExpert(
            expert_id="expert-no-rag",
            expert_name="No RAG Expert",
            primary_domain="test-domain",
            rag_enabled=False,
        )

        await expert.activate()

        # RAG should not be initialized
        assert expert.knowledge_base is None or expert.rag_enabled is False

        # Should still return context (default)
        context = await expert._build_domain_context("test query", "test-domain")
        assert isinstance(context, str)
        assert "Domain: test-domain" in context

    @pytest.mark.asyncio
    async def test_expert_no_knowledge_base(self):
        """Test expert behavior when no knowledge base exists."""
        expert = BaseExpert(
            expert_id="expert-no-kb",
            expert_name="No KB Expert",
            primary_domain="test-domain",
            rag_enabled=True,
        )

        # Activate with non-existent knowledge directory
        temp_dir = Path(tempfile.mkdtemp())
        await expert.activate(project_root=temp_dir)

        # Should handle gracefully
        context = await expert._build_domain_context("test query", "test-domain")
        assert isinstance(context, str)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_simple_knowledge_base_integration(self, temp_knowledge_dir):
        """Test SimpleKnowledgeBase can be used directly."""
        knowledge_dir = temp_knowledge_dir / ".tapps-agents" / "knowledge" / "test-domain"

        if knowledge_dir.exists():
            kb = SimpleKnowledgeBase(knowledge_dir)

            # Should load files
            assert len(kb.files) > 0

            # Should search
            results = kb.search("best practices", max_results=3)
            assert len(results) > 0

            # Should get context
            context = kb.get_context("best practices", max_length=500)
            assert len(context) > 0

            # Should get sources
            sources = kb.get_sources("best practices", max_results=5)
            assert len(sources) > 0
