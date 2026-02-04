"""
Unit tests for Context7 Cross-Reference Resolver.

Tests cross-reference resolution, link detection, and cache integration.
"""

from unittest.mock import MagicMock

import pytest

from tapps_agents.context7.cross_reference_resolver import CrossReferenceResolver

pytestmark = pytest.mark.unit


class TestCrossReferenceResolver:
    """Tests for CrossReferenceResolver class."""

    def test_cross_reference_resolver_init(self, tmp_path):
        """Test CrossReferenceResolver initialization."""
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_kb_cache = MagicMock()
        
        resolver = CrossReferenceResolver(
            cache_structure=mock_cache_structure,
            kb_cache=mock_kb_cache
        )
        
        assert resolver.cache_structure == mock_cache_structure
        assert resolver.kb_cache == mock_kb_cache
        assert resolver.cross_ref_manager is not None

    def test_cross_reference_resolver_init_with_manager(self, tmp_path):
        """Test CrossReferenceResolver initialization with provided manager."""
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_kb_cache = MagicMock()
        mock_manager = MagicMock()
        
        resolver = CrossReferenceResolver(
            cache_structure=mock_cache_structure,
            kb_cache=mock_kb_cache,
            cross_ref_manager=mock_manager
        )
        
        assert resolver.cross_ref_manager == mock_manager

    def test_resolve_cross_references_with_topic(self, tmp_path):
        """Test resolve_cross_references with library and topic."""
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_kb_cache = MagicMock()
        mock_manager = MagicMock()
        
        # Mock cross-reference
        mock_ref = MagicMock()
        mock_ref.target_library = "related_lib"
        mock_ref.target_topic = "related_topic"
        mock_ref.relationship_type = "depends_on"
        mock_ref.confidence = 0.9
        
        mock_manager.get_cross_references.return_value = [mock_ref]
        mock_kb_cache.get.return_value = {"content": "test"}
        
        resolver = CrossReferenceResolver(
            cache_structure=mock_cache_structure,
            kb_cache=mock_kb_cache,
            cross_ref_manager=mock_manager
        )
        
        result = resolver.resolve_cross_references("test_lib", topic="test_topic")
        
        assert result["library"] == "test_lib"
        assert result["topic"] == "test_topic"
        assert len(result["cross_references"]) > 0
        assert "related_lib" in result["related_libraries"]

    def test_resolve_cross_references_without_topic(self, tmp_path):
        """Test resolve_cross_references with library only."""
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_kb_cache = MagicMock()
        mock_manager = MagicMock()
        
        mock_manager.get_cross_references.return_value = []
        
        resolver = CrossReferenceResolver(
            cache_structure=mock_cache_structure,
            kb_cache=mock_kb_cache,
            cross_ref_manager=mock_manager
        )
        
        result = resolver.resolve_cross_references("test_lib")
        
        assert result["library"] == "test_lib"
        assert result["topic"] is None

    def test_resolve_cross_references_checks_cache_availability(self, tmp_path):
        """Test resolve_cross_references checks if referenced entries exist in cache."""
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_kb_cache = MagicMock()
        mock_manager = MagicMock()
        
        # Mock cross-reference
        mock_ref = MagicMock()
        mock_ref.target_library = "related_lib"
        mock_ref.target_topic = "related_topic"
        mock_ref.relationship_type = "depends_on"
        mock_ref.confidence = 0.9
        
        mock_manager.get_cross_references.return_value = [mock_ref]
        mock_kb_cache.get.return_value = {"content": "test"}  # Entry exists
        
        resolver = CrossReferenceResolver(
            cache_structure=mock_cache_structure,
            kb_cache=mock_kb_cache,
            cross_ref_manager=mock_manager
        )
        
        result = resolver.resolve_cross_references("test_lib", topic="test_topic")
        
        assert len(result["available_references"]) > 0
        assert result["available_references"][0]["available"] is True

    def test_resolve_cross_references_missing_cache_entry(self, tmp_path):
        """Test resolve_cross_references when referenced entry not in cache."""
        mock_cache_structure = MagicMock()
        mock_cache_structure.cache_root = tmp_path / "cache"
        mock_kb_cache = MagicMock()
        mock_manager = MagicMock()
        
        # Mock cross-reference
        mock_ref = MagicMock()
        mock_ref.target_library = "missing_lib"
        mock_ref.target_topic = "missing_topic"
        mock_ref.relationship_type = "depends_on"
        mock_ref.confidence = 0.9
        
        mock_manager.get_cross_references.return_value = [mock_ref]
        mock_kb_cache.get.return_value = None  # Entry doesn't exist
        
        resolver = CrossReferenceResolver(
            cache_structure=mock_cache_structure,
            kb_cache=mock_kb_cache,
            cross_ref_manager=mock_manager
        )
        
        result = resolver.resolve_cross_references("test_lib", topic="test_topic")
        
        # Should still have cross_references but available_references may be empty
        assert len(result["cross_references"]) > 0

