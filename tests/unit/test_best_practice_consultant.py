"""
Unit tests for Best Practice Consultant.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.core.best_practice_consultant import (
    BestPracticeConsultant,
)


class TestBestPracticeConsultant:
    """Test BestPracticeConsultant."""

    @pytest.fixture
    def mock_expert_registry(self):
        """Create mock expert registry."""
        registry = MagicMock()
        return registry

    @pytest.fixture
    def consultant(self, mock_expert_registry):
        """Create BestPracticeConsultant instance."""
        return BestPracticeConsultant(mock_expert_registry, max_cache_size=100)

    @pytest.mark.asyncio
    async def test_consult_best_practices_cache_hit(self, consultant):
        """Test that cached advice is returned."""
        # Create mock consultation result
        mock_result = MagicMock()
        mock_result.weighted_answer = "Use threshold 0.7"
        mock_result.confidence = 0.85

        # Pre-populate cache
        cache_key = consultant._generate_cache_key(
            "quality_threshold", {"quality_score": 0.8}
        )
        consultant._cache_advice(cache_key, mock_result, timedelta(hours=1))

        # Consult (should hit cache)
        advice = await consultant.consult_best_practices(
            decision_type="quality_threshold", context={"quality_score": 0.8}
        )

        assert advice is not None
        assert advice.cached is True
        assert advice.confidence == 0.85
        assert "threshold 0.7" in advice.advice

    @pytest.mark.asyncio
    async def test_consult_best_practices_cache_miss(
        self, consultant, mock_expert_registry
    ):
        """Test that expert is consulted on cache miss."""
        # Create mock consultation result
        mock_result = MagicMock()
        mock_result.weighted_answer = "Use threshold 0.75"
        mock_result.confidence = 0.9

        # Mock expert registry consult
        mock_expert_registry.consult = AsyncMock(return_value=mock_result)

        # Consult (should miss cache and consult expert)
        advice = await consultant.consult_best_practices(
            decision_type="quality_threshold",
            context={"quality_score": 0.8, "usage_count": 10},
        )

        assert advice is not None
        assert advice.cached is False
        assert advice.confidence == 0.9
        assert "threshold 0.75" in advice.advice

        # Verify expert was consulted
        mock_expert_registry.consult.assert_called_once()
        call_args = mock_expert_registry.consult.call_args
        assert call_args.kwargs["domain"] == "agent-learning"
        assert call_args.kwargs["prioritize_builtin"] is True

    @pytest.mark.asyncio
    async def test_consult_best_practices_expert_failure(
        self, consultant, mock_expert_registry
    ):
        """Test handling of expert consultation failure."""
        # Mock expert registry to raise exception
        mock_expert_registry.consult = AsyncMock(side_effect=Exception("Expert error"))

        # Consult (should handle error gracefully)
        advice = await consultant.consult_best_practices(
            decision_type="quality_threshold", context={"quality_score": 0.8}
        )

        assert advice is None

    def test_generate_query(self, consultant):
        """Test query generation."""
        query = consultant._generate_query(
            "quality_threshold",
            {
                "quality_score": 0.8,
                "usage_count": 10,
                "success_rate": 0.85,
                "hardware_profile": "nuc",
            },
        )

        assert "quality threshold" in query.lower()
        assert "0.8" in query
        assert "nuc" in query

    def test_generate_query_unknown_type(self, consultant):
        """Test query generation for unknown decision type."""
        query = consultant._generate_query("unknown_type", {"context": "test"})

        assert "unknown_type" in query.lower()
        assert "test" in query

    def test_generate_cache_key(self, consultant):
        """Test cache key generation."""
        key1 = consultant._generate_cache_key(
            "quality_threshold", {"quality_score": 0.8, "usage_count": 10}
        )
        key2 = consultant._generate_cache_key(
            "quality_threshold", {"quality_score": 0.8, "usage_count": 10}
        )

        # Same context should generate same key
        assert key1 == key2

        # Different context should generate different key
        key3 = consultant._generate_cache_key(
            "quality_threshold", {"quality_score": 0.9, "usage_count": 10}
        )
        assert key1 != key3

    def test_cache_expiration(self, consultant):
        """Test that expired cache entries are not returned."""
        # Create mock result
        mock_result = MagicMock()
        mock_result.weighted_answer = "Test advice"
        mock_result.confidence = 0.8

        # Cache with short TTL
        cache_key = consultant._generate_cache_key("test", {})
        consultant._cache_advice(
            cache_key,
            mock_result,
            timedelta(seconds=-1),  # Already expired
        )

        # Should not return expired entry
        cached = consultant._get_cached_advice(cache_key)
        assert cached is None

    def test_cache_eviction(self, consultant):
        """Test cache eviction when full."""
        # Fill cache beyond max size
        for i in range(110):  # More than max_cache_size (100)
            mock_result = MagicMock()
            mock_result.weighted_answer = f"Advice {i}"
            mock_result.confidence = 0.8

            cache_key = consultant._generate_cache_key("test", {"index": i})
            consultant._cache_advice(cache_key, mock_result, timedelta(hours=1))

        # Cache should not exceed max size
        assert len(consultant.cache) <= consultant.max_cache_size

    def test_get_cache_statistics(self, consultant):
        """Test cache statistics."""
        # Create some cache entries
        for i in range(5):
            mock_result = MagicMock()
            mock_result.weighted_answer = f"Advice {i}"
            mock_result.confidence = 0.8

            cache_key = consultant._generate_cache_key("test", {"index": i})
            consultant._cache_advice(cache_key, mock_result, timedelta(hours=1))

        # Get statistics
        stats = consultant.get_cache_statistics()

        assert stats["cache_size"] == 5
        assert stats["max_cache_size"] == 100
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats

    def test_clear_cache(self, consultant):
        """Test cache clearing."""
        # Add some entries
        for i in range(5):
            mock_result = MagicMock()
            mock_result.weighted_answer = f"Advice {i}"
            mock_result.confidence = 0.8

            cache_key = consultant._generate_cache_key("test", {"index": i})
            consultant._cache_advice(cache_key, mock_result, timedelta(hours=1))

        assert len(consultant.cache) == 5

        # Clear cache
        consultant.clear_cache()

        assert len(consultant.cache) == 0
        assert consultant._cache_hits == 0
        assert consultant._cache_misses == 0
