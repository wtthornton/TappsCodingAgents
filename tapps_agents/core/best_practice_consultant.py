"""
Best Practice Consultant

Consults expert system for best practices guidance with intelligent caching.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CachedAdvice:
    """Cached best practice advice."""

    advice: Any  # ConsultationResult
    cached_at: datetime
    expires_at: datetime
    cache_key: str


@dataclass
class BestPracticeAdvice:
    """Best practice advice result."""

    advice: str
    confidence: float
    source: str  # "expert" or "cache"
    cached: bool = False
    consultation_result: Any | None = None  # ConsultationResult if from expert


class BestPracticeConsultant:
    """
    Consults expert system for best practices with caching.

    Provides context-aware query generation and intelligent caching
    to minimize expert consultation overhead.
    """

    # Query templates for different decision types
    QUERY_TEMPLATES: dict[str, str] = {
        "quality_threshold": (
            "What quality threshold should I use for pattern extraction? "
            "Context: quality_score={quality_score}, usage_count={usage_count}, "
            "success_rate={success_rate:.2%}, hardware={hardware_profile}"
        ),
        "pattern_extraction": (
            "What patterns should I extract from code? "
            "Context: quality_score={quality_score}, task_type={task_type}, "
            "hardware={hardware_profile}"
        ),
        "prompt_optimization": (
            "How should I optimize prompts for {hardware_profile}? "
            "Context: current_quality={current_quality:.2f}, "
            "test_count={test_count}, learning_intensity={learning_intensity}"
        ),
        "learning_intensity": (
            "What learning intensity should I use? "
            "Context: hardware={hardware_profile}, current_intensity={current_intensity}, "
            "capability_usage={capability_usage}"
        ),
        "capability_refinement": (
            "When should I refine a capability? "
            "Context: quality_score={quality_score:.2f}, usage_count={usage_count}, "
            "success_rate={success_rate:.2%}, hardware={hardware_profile}"
        ),
        "pattern_selection": (
            "Which patterns should I use for this context? "
            "Context: task_type={task_type}, quality_requirement={quality_requirement}, "
            "hardware={hardware_profile}"
        ),
    }

    # Cache TTL settings
    CACHE_TTL_DYNAMIC = timedelta(hours=1)  # For dynamic decisions
    CACHE_TTL_STATIC = timedelta(hours=24)  # For static decisions

    # Decision types that are more static (longer cache)
    STATIC_DECISION_TYPES = {"learning_intensity", "prompt_optimization"}

    def __init__(self, expert_registry: Any, max_cache_size: int = 1000):
        """
        Initialize best practice consultant.

        Args:
            expert_registry: ExpertRegistry instance
            max_cache_size: Maximum cache size (default: 1000)
        """
        self.expert_registry = expert_registry
        self.cache: dict[str, CachedAdvice] = {}
        self.max_cache_size = max_cache_size
        self._cache_hits = 0
        self._cache_misses = 0

    async def consult_best_practices(
        self,
        decision_type: str,
        context: dict[str, Any],
        domain: str = "agent-learning",
    ) -> BestPracticeAdvice | None:
        """
        Consult best practices for a decision type.

        Args:
            decision_type: Type of decision (e.g., "quality_threshold")
            context: Context dictionary with relevant information
            domain: Expert domain to consult (default: "agent-learning")

        Returns:
            BestPracticeAdvice if consultation successful, None otherwise
        """
        # Check cache first
        cache_key = self._generate_cache_key(decision_type, context)
        cached_advice = self._get_cached_advice(cache_key)

        if cached_advice:
            self._cache_hits += 1
            logger.debug(f"Cache hit for decision type: {decision_type}")
            return BestPracticeAdvice(
                advice=cached_advice.advice.weighted_answer,
                confidence=cached_advice.advice.confidence,
                source="expert",
                cached=True,
                consultation_result=cached_advice.advice,
            )

        # Cache miss - consult expert
        self._cache_misses += 1
        logger.debug(
            f"Cache miss for decision type: {decision_type}, consulting expert"
        )

        try:
            # Generate query
            query = self._generate_query(decision_type, context)

            # Consult expert
            consultation_result = await self.expert_registry.consult(
                query=query,
                domain=domain,
                include_all=True,
                prioritize_builtin=True,  # Prioritize built-in experts for agent-learning
                agent_id="agent-learner",
            )

            # Cache the result
            ttl = (
                self.CACHE_TTL_STATIC
                if decision_type in self.STATIC_DECISION_TYPES
                else self.CACHE_TTL_DYNAMIC
            )
            self._cache_advice(cache_key, consultation_result, ttl)

            return BestPracticeAdvice(
                advice=consultation_result.weighted_answer,
                confidence=consultation_result.confidence,
                source="expert",
                cached=False,
                consultation_result=consultation_result,
            )

        except Exception as e:
            logger.warning(f"Failed to consult best practices: {e}")
            return None

    def _generate_query(self, decision_type: str, context: dict[str, Any]) -> str:
        """
        Generate context-aware query for expert consultation.

        Args:
            decision_type: Type of decision
            context: Context dictionary

        Returns:
            Query string
        """
        template = self.QUERY_TEMPLATES.get(decision_type)
        if not template:
            # Fallback template
            template = (
                "What are the best practices for {decision_type}? " "Context: {context}"
            )
            return template.format(
                decision_type=decision_type, context=json.dumps(context, default=str)
            )

        # Format template with context
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(
                f"Missing context key {e} for decision type {decision_type}, using fallback"
            )
            return template.format(
                decision_type=decision_type,
                **{k: v for k, v in context.items() if k in template},
            )

    def _generate_cache_key(self, decision_type: str, context: dict[str, Any]) -> str:
        """
        Generate cache key from decision type and context.

        Args:
            decision_type: Type of decision
            context: Context dictionary

        Returns:
            Cache key string
        """
        # Create a stable hash of the context
        context_str = json.dumps(context, sort_keys=True, default=str)
        # Use a modern hash even for non-security identifiers.
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()[:8]

        return f"{decision_type}_{context_hash}"

    def _get_cached_advice(self, cache_key: str) -> CachedAdvice | None:
        """
        Get cached advice if available and not expired.

        Args:
            cache_key: Cache key

        Returns:
            CachedAdvice if available and valid, None otherwise
        """
        cached = self.cache.get(cache_key)
        if not cached:
            return None

        # Check if expired
        if datetime.now() > cached.expires_at:
            # Remove expired entry
            del self.cache[cache_key]
            return None

        return cached

    def _cache_advice(
        self, cache_key: str, advice: Any, ttl: timedelta  # ConsultationResult
    ) -> None:
        """
        Cache advice with TTL.

        Args:
            cache_key: Cache key
            advice: ConsultationResult to cache
            ttl: Time to live
        """
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._evict_cache()

        now = datetime.now()
        self.cache[cache_key] = CachedAdvice(
            advice=advice, cached_at=now, expires_at=now + ttl, cache_key=cache_key
        )

    def _evict_cache(self) -> None:
        """Evict oldest cache entries."""
        if not self.cache:
            return

        # Sort by expiration time and remove oldest 10%
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].expires_at)

        evict_count = max(1, len(sorted_entries) // 10)
        for cache_key, _ in sorted_entries[:evict_count]:
            del self.cache[cache_key]

    def get_cache_statistics(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0

        return {
            "cache_size": len(self.cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "max_cache_size": self.max_cache_size,
        }

    def clear_cache(self) -> None:
        """Clear all cached advice."""
        self.cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
