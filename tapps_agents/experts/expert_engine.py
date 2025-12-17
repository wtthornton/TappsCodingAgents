"""
Expert Engine Runtime Component

Orchestrates expert consultation and knowledge retrieval automatically.
Provides intelligent routing, knowledge need detection, and metrics collection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.project_profile import ProjectProfile
from ..core.unified_cache import CacheType, UnifiedCache
from .expert_registry import ExpertRegistry, ConsultationResult


@dataclass
class KnowledgeNeed:
    """Represents a detected knowledge need."""

    domain: str
    query: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, critical
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExpertRoutingPlan:
    """Plan for which experts to consult for a given knowledge need."""

    knowledge_need: KnowledgeNeed
    expert_ids: list[str]
    domains: list[str]
    priority_order: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class KnowledgeRetrievalPlan:
    """Plan for knowledge retrieval from different sources."""

    knowledge_need: KnowledgeNeed
    context7_sources: list[dict[str, str]] = field(default_factory=list)  # [{library, topic}]
    local_kb_sources: list[str] = field(default_factory=list)  # [domain paths]
    retrieval_strategy: str = "hybrid"  # context7_only, local_only, hybrid
    reasoning: str = ""


@dataclass
class KnowledgeWriteRequest:
    """Request to write knowledge to the KB."""

    domain: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # Where this knowledge came from
    validated: bool = False


@dataclass
class ExpertEngineMetrics:
    """Metrics collected by the Expert Engine."""

    cache_hit_rate: float = 0.0
    context7_hit_rate: float = 0.0
    local_kb_hit_rate: float = 0.0
    retrieval_quality_scores: list[float] = field(default_factory=list)
    confidence_trends: list[float] = field(default_factory=list)
    knowledge_needs_detected: int = 0
    expert_consultations: int = 0
    knowledge_writes: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class ExpertEngine:
    """
    Expert Engine runtime component that orchestrates expert consultation and knowledge retrieval.

    Provides:
    - Automatic knowledge need detection
    - Expert routing plan generation
    - Knowledge retrieval plan generation
    - Controlled knowledge writes
    - Metrics collection
    """

    def __init__(
        self,
        expert_registry: ExpertRegistry,
        unified_cache: UnifiedCache | None = None,
        project_root: Path | None = None,
        enable_metrics: bool = True,
    ):
        """
        Initialize Expert Engine.

        Args:
            expert_registry: Expert registry for consultation
            unified_cache: Unified cache for knowledge retrieval (optional)
            project_root: Project root directory (optional)
            enable_metrics: Whether to collect metrics (default: True)
        """
        self.expert_registry = expert_registry
        self.unified_cache = unified_cache
        self.project_root = project_root or Path.cwd()
        self.enable_metrics = enable_metrics

        # Metrics tracking
        self.metrics = ExpertEngineMetrics()
        self._cache_hits = 0
        self._cache_misses = 0
        self._context7_hits = 0
        self._context7_misses = 0
        self._local_kb_hits = 0
        self._local_kb_misses = 0

    def detect_knowledge_need(
        self,
        query: str | None = None,
        domain: str | None = None,
        context: dict[str, Any] | None = None,
        step_context: dict[str, Any] | None = None,
    ) -> KnowledgeNeed | None:
        """
        Detect knowledge need from context.

        Args:
            query: Optional explicit query
            domain: Optional domain hint
            context: Optional context dictionary
            step_context: Optional workflow step context

        Returns:
            KnowledgeNeed if detected, None otherwise
        """
        if not query and not step_context:
            return None

        # Extract query from step context if not provided
        if not query and step_context:
            agent = step_context.get("agent", "")
            action = step_context.get("action", "")
            notes = step_context.get("notes", "")
            metadata = step_context.get("metadata", {})

            query_parts = []
            if agent:
                query_parts.append(f"Agent: {agent}")
            if action:
                query_parts.append(f"Action: {action}")
            if notes:
                query_parts.append(f"Context: {notes}")
            if metadata:
                context_info = metadata.get("context") or metadata.get("description")
                if context_info:
                    query_parts.append(f"Additional context: {context_info}")

            query = " | ".join(query_parts) if query_parts else None

        if not query:
            return None

        # Infer domain from context if not provided
        if not domain:
            if step_context:
                # Try to infer from expert IDs in step
                expert_ids = step_context.get("consults", [])
                if expert_ids:
                    first_expert = expert_ids[0]
                    if first_expert.startswith("expert-"):
                        domain = first_expert.replace("expert-", "")
                    else:
                        domain = first_expert.split("-")[-1] if "-" in first_expert else "general"
                else:
                    # Infer from agent/action
                    agent = step_context.get("agent", "")
                    if agent:
                        domain = agent.replace("agent-", "") if agent.startswith("agent-") else agent
                    else:
                        domain = "general"
            else:
                domain = "general"

        # Determine priority
        priority = "normal"
        if context:
            if context.get("critical") or context.get("urgent"):
                priority = "critical"
            elif context.get("high_priority"):
                priority = "high"
            elif context.get("low_priority"):
                priority = "low"

        knowledge_need = KnowledgeNeed(
            domain=domain,
            query=query,
            context=context or {},
            priority=priority,
        )

        if self.enable_metrics:
            self.metrics.knowledge_needs_detected += 1

        return knowledge_need

    def generate_routing_plan(
        self, knowledge_need: KnowledgeNeed, available_experts: list[str] | None = None
    ) -> ExpertRoutingPlan:
        """
        Generate expert routing plan for a knowledge need.

        Args:
            knowledge_need: The detected knowledge need
            available_experts: Optional list of available expert IDs (if None, uses registry)

        Returns:
            ExpertRoutingPlan with expert IDs and domains to consult
        """
        # Get available experts from registry if not provided
        if available_experts is None:
            available_experts = list(self.expert_registry.experts.keys())

        # Determine which experts to consult based on domain
        expert_ids = []
        domains = [knowledge_need.domain]

        # Check if domain-specific experts exist
        domain_expert_id = f"expert-{knowledge_need.domain}"
        if domain_expert_id in available_experts:
            expert_ids.append(domain_expert_id)

        # Check for related domains/experts
        # For now, use the primary domain expert
        # Future: could use domain config to find related domains

        # If no domain-specific expert, use general expert
        if not expert_ids:
            general_expert_id = "expert-general"
            if general_expert_id in available_experts:
                expert_ids.append(general_expert_id)
            elif available_experts:
                # Use first available expert as fallback
                expert_ids.append(available_experts[0])

        # Priority order: domain-specific first, then general
        priority_order = expert_ids.copy()

        reasoning = f"Routing to {len(expert_ids)} expert(s) for domain '{knowledge_need.domain}'"

        return ExpertRoutingPlan(
            knowledge_need=knowledge_need,
            expert_ids=expert_ids,
            domains=domains,
            priority_order=priority_order,
            reasoning=reasoning,
        )

    def generate_retrieval_plan(
        self,
        knowledge_need: KnowledgeNeed,
        project_profile: ProjectProfile | None = None,
    ) -> KnowledgeRetrievalPlan:
        """
        Generate knowledge retrieval plan.

        Args:
            knowledge_need: The detected knowledge need
            project_profile: Optional project profile for context

        Returns:
            KnowledgeRetrievalPlan with sources to retrieve from
        """
        context7_sources = []
        local_kb_sources = []
        retrieval_strategy = "hybrid"

        # For now, use hybrid strategy
        # Future: could analyze query to determine if Context7 or local KB is more appropriate

        # Check if query mentions specific libraries (Context7 candidates)
        query_lower = knowledge_need.query.lower()
        # Simple heuristic: if query mentions common library patterns, consider Context7
        library_keywords = ["library", "framework", "package", "dependency", "api"]
        if any(keyword in query_lower for keyword in library_keywords):
            # Would need library detection from project profile or query analysis
            # For now, leave empty - will be populated by domain detector (Story 28.2)
            pass

        # Local KB sources: use domain
        if knowledge_need.domain:
            local_kb_sources.append(knowledge_need.domain)

        reasoning = f"Hybrid retrieval: Context7 for library docs, local KB for domain '{knowledge_need.domain}'"

        return KnowledgeRetrievalPlan(
            knowledge_need=knowledge_need,
            context7_sources=context7_sources,
            local_kb_sources=local_kb_sources,
            retrieval_strategy=retrieval_strategy,
            reasoning=reasoning,
        )

    async def consult_with_plan(
        self, routing_plan: ExpertRoutingPlan
    ) -> ConsultationResult:
        """
        Consult experts using a routing plan.

        Args:
            routing_plan: The expert routing plan

        Returns:
            ConsultationResult from expert registry
        """
        knowledge_need = routing_plan.knowledge_need

        # Consult experts via registry
        consultation_result = await self.expert_registry.consult(
            query=knowledge_need.query,
            domain=knowledge_need.domain,
            include_all=True,
        )

        if self.enable_metrics:
            self.metrics.expert_consultations += 1
            self.metrics.confidence_trends.append(consultation_result.confidence)

        return consultation_result

    async def retrieve_knowledge(
        self, retrieval_plan: KnowledgeRetrievalPlan
    ) -> dict[str, Any]:
        """
        Retrieve knowledge according to retrieval plan.

        Args:
            retrieval_plan: The knowledge retrieval plan

        Returns:
            Dictionary with retrieved knowledge from various sources
        """
        if not self.unified_cache:
            return {"error": "Unified cache not available"}

        knowledge_need = retrieval_plan.knowledge_need
        results = {
            "context7": {},
            "local_kb": {},
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Retrieve from Context7 KB cache
        for source in retrieval_plan.context7_sources:
            library = source.get("library", "")
            topic = source.get("topic", "")
            if library and topic:
                cached = self.unified_cache.get(
                    CacheType.CONTEXT7_KB,
                    key=f"{library}/{topic}",
                    library=library,
                    topic=topic,
                )
                if cached:
                    results["context7"][f"{library}/{topic}"] = cached.content
                    self._context7_hits += 1
                    results["cache_hits"] += 1
                else:
                    self._context7_misses += 1
                    results["cache_misses"] += 1

        # Retrieve from local KB (RAG)
        for domain in retrieval_plan.local_kb_sources:
            if domain:
                cached = self.unified_cache.get(
                    CacheType.RAG_KNOWLEDGE,
                    key=domain,
                    domain=domain,
                    query=knowledge_need.query,
                )
                if cached:
                    results["local_kb"][domain] = cached.content
                    self._local_kb_hits += 1
                    results["cache_hits"] += 1
                else:
                    self._local_kb_misses += 1
                    results["cache_misses"] += 1

        # Update metrics
        if self.enable_metrics:
            total_requests = results["cache_hits"] + results["cache_misses"]
            if total_requests > 0:
                self._cache_hits += results["cache_hits"]
                self._cache_misses += results["cache_misses"]
                self._update_cache_metrics()

        return results

    def write_knowledge(
        self, write_request: KnowledgeWriteRequest, validate: bool = True
    ) -> dict[str, Any]:
        """
        Write knowledge to the KB (controlled write).

        Args:
            write_request: The knowledge write request
            validate: Whether to validate before writing (default: True)

        Returns:
            Dictionary with write result
        """
        if validate and not write_request.validated:
            # Basic validation: check for secrets/PII (will be enhanced in Story 28.5)
            content_lower = write_request.content.lower()
            secret_indicators = ["password", "secret", "api_key", "token", "credential"]
            if any(indicator in content_lower for indicator in secret_indicators):
                return {
                    "success": False,
                    "error": "Potential secret detected in content. Validation failed.",
                }

        # For now, return success but don't actually write
        # Actual write implementation will be in Story 28.4 (Knowledge Ingestion Pipeline)
        # This is a controlled interface that will be used by the ingestion pipeline

        if self.enable_metrics:
            self.metrics.knowledge_writes += 1

        return {
            "success": True,
            "domain": write_request.domain,
            "validated": write_request.validated,
            "note": "Write interface ready - actual write will be implemented in Story 28.4",
        }

    def get_metrics(self) -> ExpertEngineMetrics:
        """
        Get current metrics.

        Returns:
            ExpertEngineMetrics with current statistics
        """
        if self.enable_metrics:
            self._update_cache_metrics()
            self.metrics.last_updated = datetime.now()
        return self.metrics

    def _update_cache_metrics(self):
        """Update cache hit rate metrics."""
        total_cache_requests = self._cache_hits + self._cache_misses
        if total_cache_requests > 0:
            self.metrics.cache_hit_rate = self._cache_hits / total_cache_requests

        total_context7_requests = self._context7_hits + self._context7_misses
        if total_context7_requests > 0:
            self.metrics.context7_hit_rate = self._context7_hits / total_context7_requests

        total_local_kb_requests = self._local_kb_hits + self._local_kb_misses
        if total_local_kb_requests > 0:
            self.metrics.local_kb_hit_rate = self._local_kb_hits / total_local_kb_requests

