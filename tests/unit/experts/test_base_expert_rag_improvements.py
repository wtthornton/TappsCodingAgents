"""
Tests for Base Expert RAG improvements (defaults, metrics, freshness).
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.experts.base_expert import BaseExpert

pytestmark = pytest.mark.unit


class TestBaseExpertRAGDefaults:
    """Test improved RAG defaults in BaseExpert."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        import shutil
        import tempfile

        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge" / "security"
        knowledge_dir.mkdir(parents=True)

        test_file = knowledge_dir / "test.md"
        test_file.write_text("# Security Guide\nContent", encoding="utf-8")

        yield knowledge_dir.parent

        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_vector_rag_defaults(self, temp_knowledge_dir):
        """Test that VectorKnowledgeBase uses improved defaults."""
        expert = BaseExpert(
            expert_id="expert-security",
            expert_name="Security Expert",
            primary_domain="security",
            rag_enabled=True,
        )

        expert._is_builtin = True
        expert._builtin_knowledge_path = temp_knowledge_dir

        # Mock VectorKnowledgeBase to avoid actual initialization
        with patch("tapps_agents.experts.base_expert.VectorKnowledgeBase") as mock_vector:
            mock_instance = MagicMock()
            mock_instance.get_backend_type.return_value = "vector"
            mock_vector.return_value = mock_instance

            await expert._initialize_rag()

            # Verify VectorKnowledgeBase was called with improved defaults
            mock_vector.assert_called_once()
            call_kwargs = mock_vector.call_args[1]

            assert call_kwargs["chunk_size"] == 768  # Increased from 512
            assert call_kwargs["overlap"] == 100  # Increased from 50
            assert call_kwargs["similarity_threshold"] == 0.65  # Lowered from 0.7

    @pytest.mark.asyncio
    async def test_freshness_tracking_initialization(self, temp_knowledge_dir):
        """Test that freshness tracking is initialized."""
        expert = BaseExpert(
            expert_id="expert-security",
            expert_name="Security Expert",
            primary_domain="security",
            rag_enabled=True,
        )

        expert._is_builtin = True
        expert._builtin_knowledge_path = temp_knowledge_dir

        with patch("tapps_agents.experts.knowledge_freshness.get_freshness_tracker") as mock_freshness:
            mock_tracker = MagicMock()
            mock_tracker.scan_and_update.return_value = {"scanned": 1, "updated": 0, "new_files": 1}
            mock_freshness.return_value = mock_tracker

            with patch("tapps_agents.experts.base_expert.VectorKnowledgeBase"):
                await expert._initialize_rag()

            # Verify freshness tracker was used
            mock_freshness.assert_called_once()
            mock_tracker.scan_and_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_metrics_tracking_in_context_building(self, temp_knowledge_dir):
        """Test that metrics are tracked during context building."""
        expert = BaseExpert(
            expert_id="expert-security",
            expert_name="Security Expert",
            primary_domain="security",
            rag_enabled=True,
        )

        expert._is_builtin = True
        expert._builtin_knowledge_path = temp_knowledge_dir

        # Mock knowledge base
        mock_kb = MagicMock()
        mock_kb.get_backend_type.return_value = "vector"
        mock_kb.search.return_value = [
            MagicMock(score=0.8),
            MagicMock(score=0.7),
        ]
        mock_kb.get_context.return_value = "[From: test.md]\nContext content"
        expert.knowledge_base = mock_kb

        # Mock metrics tracking
        mock_timer = MagicMock()
        mock_timer.__enter__ = MagicMock(return_value=mock_timer)
        mock_timer.__exit__ = MagicMock(return_value=None)
        mock_timer.set_params = MagicMock()

        with patch("tapps_agents.experts.rag_metrics.get_rag_metrics_tracker") as mock_get_tracker:
            with patch("tapps_agents.experts.rag_metrics.RAGQueryTimer", return_value=mock_timer):
                mock_metrics_tracker = MagicMock()
                mock_get_tracker.return_value = mock_metrics_tracker

                context = await expert._build_domain_context("test query", "security")

                # Verify context was built
                assert context is not None
                assert "[From:" in context

                # Verify metrics tracking was attempted
                # Note: If metrics tracking fails, code continues (non-critical feature)
                mock_get_tracker.assert_called()
