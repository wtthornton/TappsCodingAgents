"""
Expert Registry

Manages expert instances and provides consultation services with weighted decision-making.
"""

# @ai-prime-directive: This file implements the Expert Registry system for weighted expert consultation.
# The registry manages both built-in framework experts and project-defined industry experts, providing
# weighted decision aggregation and confidence calculation. This is a core component of the expert system design.

# @ai-constraints:
# - Must maintain separation between built-in experts (framework-controlled) and customer experts (project-defined)
# - Weight distribution must follow 51% primary authority model for technical domains
# - Confidence calculation must consider agreement level, expert weights, and domain expertise
# - Built-in experts have primary authority in TECHNICAL_DOMAINS (see BuiltinExpertRegistry)
# - Performance: Consultation should complete in <5s for typical queries

# @note[2025-01-15]: Expert system design per ADR-003.
# The registry implements weighted consultation with built-in and project-defined experts.
# See docs/architecture/decisions/ADR-003-expert-system-design.md

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..core.config import get_expert_config
from ..core.project_profile import ProjectProfile, load_project_profile
from .base_expert import BaseExpert
from .builtin_registry import BuiltinExpertRegistry
from .confidence_calculator import ConfidenceCalculator
from .confidence_metrics import get_tracker
from .domain_config import DomainConfig, DomainConfigParser
from .expert_config import load_expert_configs
from .weight_distributor import ExpertWeightMatrix

logger = logging.getLogger(__name__)

# Technical domains where built-in experts have primary authority
# These domains are framework-controlled and built-in experts should be prioritized
TECHNICAL_DOMAINS = BuiltinExpertRegistry.TECHNICAL_DOMAINS


@dataclass
class ConsultationResult:
    """Result from consulting multiple experts."""

    domain: str
    query: str
    responses: list[dict[str, Any]]  # Individual expert responses
    weighted_answer: str  # Combined weighted answer
    agreement_level: float  # 0.0-1.0
    confidence: float  # Overall confidence
    confidence_threshold: float  # Agent-specific confidence threshold
    primary_expert: str
    all_experts_agreed: bool


class ExpertRegistry:
    """
    Registry for managing Industry Expert agents.

    Provides:
    - Expert instance management
    - Weighted consultation services
    - Decision aggregation
    """

    def __init__(
        self,
        domain_config: DomainConfig | None = None,
        load_builtin: bool = True,
        project_root: Path | None = None,
    ):
        """
        Initialize expert registry.

        Args:
            domain_config: Optional domain configuration (can be loaded later)
            load_builtin: Whether to auto-load built-in framework experts (default: True)
            project_root: Optional project root for profile loading
        """
        self.domain_config = domain_config
        self.experts: dict[str, BaseExpert] = {}
        self.builtin_experts: dict[str, BaseExpert] = {}  # Built-in framework experts
        self.customer_experts: dict[str, BaseExpert] = {}  # Customer-configured experts
        self.weight_matrix: ExpertWeightMatrix | None = (
            domain_config.weight_matrix if domain_config else None
        )
        self.project_root = project_root or Path.cwd()
        self._cached_profile: ProjectProfile | None = None
        self._tech_stack_priorities: dict[str, float] | None = None

        # Auto-load built-in experts if enabled
        if load_builtin:
            self._load_builtin_experts()

        # Load tech stack priorities if available
        self._load_tech_stack_priorities()

    def _get_project_profile(self) -> ProjectProfile | None:
        """
        Get project profile (cached).

        Returns:
            ProjectProfile if available, None otherwise
        """
        if self._cached_profile is None:
            self._cached_profile = load_project_profile(project_root=self.project_root)
        return self._cached_profile

    def _load_tech_stack_priorities(self) -> None:
        """
        Load expert priorities from tech-stack.yaml config file.

        Priorities are loaded from `.tapps-agents/tech-stack.yaml` if it exists.
        Priorities from `expert_priorities` section are merged with `overrides` section
        (overrides take precedence).
        """
        tech_stack_config = self.project_root / ".tapps-agents" / "tech-stack.yaml"
        if not tech_stack_config.exists():
            return

        try:
            content = tech_stack_config.read_text(encoding="utf-8")
            config = yaml.safe_load(content) or {}

            # Get expert priorities (defaults)
            expert_priorities = config.get("expert_priorities", {}).copy()

            # Apply overrides (overrides take precedence)
            overrides = config.get("overrides", {})
            expert_priorities.update(overrides)

            if expert_priorities:
                self._tech_stack_priorities = expert_priorities
        except Exception:
            # Silently fail if config file can't be loaded
            # Registry will work without priorities (backward compatible)
            pass

    @classmethod
    def from_domains_file(cls, domains_file: Path) -> ExpertRegistry:
        """
        Create registry from domains.md file.

        Args:
            domains_file: Path to domains.md

        Returns:
            ExpertRegistry instance
        """
        domain_config = DomainConfigParser.parse(domains_file)
        return cls(domain_config=domain_config)

    @classmethod
    def from_config_file(
        cls, config_file: Path, domain_config: DomainConfig | None = None
    ) -> ExpertRegistry:
        """
        Create registry from experts.yaml configuration file.

        This is the preferred method for creating experts - define them
        in YAML configuration rather than code classes.

        Args:
            config_file: Path to experts.yaml file
            domain_config: Optional domain configuration for weight matrix

        Returns:
            ExpertRegistry instance with experts loaded from config

        Example:
            ```python
            registry = ExpertRegistry.from_config_file(
                Path(".tapps-agents/experts.yaml"),
                domain_config=domain_config
            )
            ```
        """
        expert_configs = load_expert_configs(config_file)
        registry = cls(domain_config=domain_config)

        # Create and register experts from config
        for expert_config in expert_configs:
            expert = BaseExpert(
                expert_id=expert_config.expert_id,
                expert_name=expert_config.expert_name,
                primary_domain=expert_config.primary_domain,
                confidence_matrix=expert_config.confidence_matrix,
                rag_enabled=expert_config.rag_enabled,
                fine_tuned=expert_config.fine_tuned,
            )
            registry.register_expert(expert)

        registry = cls(domain_config=domain_config, load_builtin=True)

        # Create and register customer experts from config
        for expert_config in expert_configs:
            # Skip if this is a built-in expert (already loaded)
            if BuiltinExpertRegistry.is_builtin_expert(expert_config.expert_id):
                continue

            expert = BaseExpert(
                expert_id=expert_config.expert_id,
                expert_name=expert_config.expert_name,
                primary_domain=expert_config.primary_domain,
                confidence_matrix=expert_config.confidence_matrix,
                rag_enabled=expert_config.rag_enabled,
                fine_tuned=expert_config.fine_tuned,
            )
            registry.register_expert(expert, is_builtin=False)

        return registry

    def _load_builtin_experts(self):
        """
        Load all built-in framework experts automatically.

        Built-in experts are immutable and provide technical domain knowledge.
        They are loaded from the BuiltinExpertRegistry.
        """
        builtin_configs = BuiltinExpertRegistry.get_builtin_experts()
        builtin_knowledge_path = BuiltinExpertRegistry.get_builtin_knowledge_path()

        for config in builtin_configs:
            expert = BaseExpert(
                expert_id=config.expert_id,
                expert_name=config.expert_name,
                primary_domain=config.primary_domain,
                confidence_matrix=config.confidence_matrix,
                rag_enabled=config.rag_enabled,
                fine_tuned=config.fine_tuned,
            )
            # Mark as built-in for knowledge base path resolution
            expert._is_builtin = True
            expert._builtin_knowledge_path = builtin_knowledge_path

            self.register_expert(expert, is_builtin=True)

    def register_expert(self, expert: BaseExpert, is_builtin: bool = False) -> None:
        """
        Register an expert agent.

        Args:
            expert: BaseExpert instance to register
            is_builtin: Whether this is a built-in expert (default: False)

        Raises:
            ValueError: If expert not found in weight matrix (unless it's a built-in expert)
        """
        # Built-in experts don't need to be in weight matrix
        if (
            self.weight_matrix
            and expert.expert_id not in self.weight_matrix.experts
            and not is_builtin
        ):
            raise ValueError(
                f"Expert '{expert.expert_id}' not found in weight matrix. "
                f"Registered experts: {list(self.weight_matrix.experts)}"
            )

        # Update confidence matrix from weight matrix if available
        if self.weight_matrix:
            expert.confidence_matrix = self.weight_matrix.weights.get(
                expert.expert_id, {}
            )

        # Register in appropriate dictionary
        self.experts[expert.expert_id] = expert
        if is_builtin:
            self.builtin_experts[expert.expert_id] = expert
        else:
            self.customer_experts[expert.expert_id] = expert

    def get_expert(self, expert_id: str) -> BaseExpert | None:
        """Get an expert by ID."""
        return self.experts.get(expert_id)

    def list_experts(self) -> list[str]:
        """List all registered expert IDs."""
        return list(self.experts.keys())

    async def consult(
        self,
        query: str,
        domain: str,
        include_all: bool = True,
        prioritize_builtin: bool = False,
        agent_id: str | None = None,
    ) -> ConsultationResult:
        """
        Consult multiple experts on a domain question and aggregate weighted responses.

        Args:
            query: The question to ask
            domain: Domain context
            include_all: Whether to consult all experts or just primary
            prioritize_builtin: If True, built-in experts get higher weight for technical domains.
                               If False (default), uses weight matrix configuration.
                               For technical domains, built-in experts should be prioritized.
                               For business domains, customer experts should be prioritized.
            agent_id: Optional agent ID for agent-specific confidence threshold

        Returns:
            ConsultationResult with weighted answer and agreement metrics
        """
        # Determine expert priority based on domain type
        is_technical_domain = domain in TECHNICAL_DOMAINS

        # Collect expert IDs to consult
        expert_ids_to_consult = []

        # If weight matrix is available and not prioritizing built-in explicitly, use it
        if self.weight_matrix and not prioritize_builtin:
            primary_expert_id = self.weight_matrix.get_primary_expert(domain)
            if primary_expert_id:
                if include_all:
                    # Consult all experts in weight matrix
                    expert_ids_to_consult = list(self.weight_matrix.experts)
                else:
                    # Only consult primary
                    expert_ids_to_consult = [primary_expert_id]

        # If no experts from weight matrix, get experts for domain
        if not expert_ids_to_consult:
            if prioritize_builtin and is_technical_domain:
                # Technical domain: built-in experts have authority
                expert_ids_to_consult = self._get_experts_for_domain(
                    domain, prioritize_builtin=True
                )
            elif not is_technical_domain:
                # Business domain: customer experts have authority
                expert_ids_to_consult = self._get_experts_for_domain(
                    domain, prioritize_builtin=False
                )
            else:
                # Technical domain without prioritize_builtin: use built-in experts
                expert_ids_to_consult = self._get_experts_for_domain(
                    domain, prioritize_builtin=True
                )

        # If still no experts found, try fallback
        if not expert_ids_to_consult:
            # Fallback: get any available experts
            if is_technical_domain:
                expert_ids_to_consult = list(self.builtin_experts.keys())
            else:
                expert_ids_to_consult = list(self.customer_experts.keys()) + list(
                    self.builtin_experts.keys()
                )

        if not expert_ids_to_consult:
            raise ValueError(f"No experts found for domain '{domain}'")

        # Get project profile if available
        project_profile = self._get_project_profile()

        # Consult each expert
        responses = []
        for expert_id in expert_ids_to_consult:
            expert = self.experts.get(expert_id)
            if not expert:
                continue  # Skip if expert not registered

            try:
                # Pass project profile to expert consultation
                response = await expert.run(
                    "consult",
                    query=query,
                    domain=domain,
                    project_profile=project_profile,
                )
                if "error" not in response:
                    confidence = response.get("confidence", 0.0)
                    responses.append(
                        {
                            "expert_id": expert_id,
                            "expert_name": expert.agent_name,
                            "answer": response.get("answer", ""),
                            "confidence": confidence,
                            "sources": response.get("sources", []),
                        }
                    )
                    
                    # Track expert consultation for adaptive learning
                    try:
                        from ..experts.performance_tracker import (
                            ExpertPerformanceTracker,
                        )
                        perf_tracker = ExpertPerformanceTracker(project_root=self.project_root)
                        perf_tracker.track_consultation(
                            expert_id=expert_id,
                            domain=domain,
                            confidence=confidence,
                            query=query,
                        )
                    except Exception as e:
                        # Don't fail consultation if tracking fails
                        logger.debug(f"Failed to track expert consultation: {e}")
            except Exception as e:
                # Log error but continue with other experts
                responses.append({"expert_id": expert_id, "error": str(e)})

        if not responses:
            raise ValueError(f"No expert responses received for domain '{domain}'")

        # Determine primary expert ID for aggregation
        primary_expert_id = None
        if self.weight_matrix:
            primary_expert_id = self.weight_matrix.get_primary_expert(domain)

        # If no primary from weight matrix, use first expert or built-in expert for technical domains
        if not primary_expert_id:
            is_technical_domain = domain in TECHNICAL_DOMAINS
            if is_technical_domain:
                # For technical domains, prefer built-in expert
                for expert_id in expert_ids_to_consult:
                    if expert_id in self.builtin_experts:
                        primary_expert_id = expert_id
                        break

            # Fallback to first available expert
            if not primary_expert_id and responses:
                primary_expert_id = responses[0].get("expert_id")

        # Ensure a stable non-None primary expert id for downstream logic and dataclass typing.
        if not primary_expert_id:
            primary_expert_id = "unknown"

        # Aggregate weighted responses
        weighted_answer = self._aggregate_responses(
            responses, domain, primary_expert_id
        )

        # Calculate agreement level
        agreement_level = self._calculate_agreement(
            responses, domain, primary_expert_id
        )

        # Calculate confidence using improved algorithm
        valid_responses = [r for r in responses if "error" not in r]

        # Calculate RAG quality from sources
        rag_quality = None
        if valid_responses:
            sources_count = sum(len(r.get("sources", [])) for r in valid_responses)
            num_responses = len(valid_responses)
            rag_quality = min(
                1.0, sources_count / max(num_responses * 2, 1)
            )  # 2 sources per response = perfect

        # Use improved confidence calculator
        confidence, threshold = ConfidenceCalculator.calculate(
            responses=valid_responses,
            domain=domain,
            agent_id=agent_id,
            agreement_level=agreement_level,
            rag_quality=rag_quality,
            num_experts_consulted=len(expert_ids_to_consult),
            project_profile=project_profile,
        )

        # Get expert config for thresholds
        expert_config = get_expert_config()
        all_agreed = agreement_level >= expert_config.high_agreement_threshold

        # Track confidence metrics
        if agent_id:
            try:
                tracker = get_tracker()
                tracker.record(
                    agent_id=agent_id,
                    domain=domain,
                    confidence=confidence,
                    threshold=threshold,
                    agreement_level=agreement_level,
                    num_experts=len(expert_ids_to_consult),
                    primary_expert=primary_expert_id or "unknown",
                    query=query,
                )
            except Exception as e:
                # Silently fail if tracking fails (non-critical)
                # Log at debug level if logging is available
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(f"Failed to track confidence metrics: {e}")

        return ConsultationResult(
            domain=domain,
            query=query,
            responses=responses,
            weighted_answer=weighted_answer,
            agreement_level=agreement_level,
            confidence=confidence,
            confidence_threshold=threshold,
            primary_expert=primary_expert_id,
            all_experts_agreed=all_agreed,
        )

    def _aggregate_responses(
        self,
        responses: list[dict[str, Any]],
        domain: str,
        primary_expert_id: str | None = None,
    ) -> str:
        """
        Aggregate expert responses using weighted decision-making.

        Primary expert (51%) has primary influence; others augment.
        """
        if not primary_expert_id:
            # Fallback: use first available response
            primary = next(
                (r for r in responses if r.get("expert_id") and "error" not in r), None
            )
            return primary.get("answer", "") if primary else ""

        # Try to get primary expert from weight matrix if not provided
        if self.weight_matrix and not primary_expert_id:
            primary_expert_id = self.weight_matrix.get_primary_expert(domain)

        # Find primary expert response
        primary_response = next(
            (
                r
                for r in responses
                if r.get("expert_id") == primary_expert_id and "error" not in r
            ),
            None,
        )

        if not primary_response:
            # Fallback to first available response
            primary_response = next((r for r in responses if "error" not in r), None)
            if not primary_response:
                return "No expert responses available."
            return primary_response.get("answer", "")

        # Start with primary expert answer (51% weight)
        primary_answer = primary_response.get("answer", "")
        aggregated_parts = [
            f"[Primary - {primary_response.get('expert_name', 'Expert')}] {primary_answer}"
        ]

        # Add influences from other experts
        other_responses = [
            r
            for r in responses
            if r.get("expert_id") != primary_expert_id and "error" not in r
        ]

        if other_responses:
            influences = []
            for response in other_responses:
                expert_id = response.get("expert_id", "")
                # Get weight from weight matrix if available, otherwise use default
                if self.weight_matrix:
                    weight = self.weight_matrix.get_expert_weight(expert_id, domain)
                else:
                    # Default weight for non-primary experts (from config)
                    expert_config = get_expert_config()
                    weight = expert_config.supporting_expert_weight
                answer = response.get("answer", "")
                expert_name = response.get("expert_name", expert_id)

                influences.append(
                    f"[Influence ({weight:.1%}) - {expert_name}] {answer}"
                )

            if influences:
                aggregated_parts.append("\n\nAdditional Expert Input:")
                aggregated_parts.extend(influences)

        return "\n".join(aggregated_parts)

    def _calculate_agreement(
        self, responses: list[dict[str, Any]], domain: str, primary_expert_id: str
    ) -> float:
        """
        Calculate agreement level between experts.

        Agreement Level = Sum of weights for experts who agree with Primary

        Returns:
            Agreement level (0.0-1.0)
        """
        if not self.weight_matrix:
            return 1.0  # Assume agreement if no matrix

        primary_response = next(
            (
                r
                for r in responses
                if r.get("expert_id") == primary_expert_id and "error" not in r
            ),
            None,
        )

        if not primary_response:
            return 0.51  # Minimum (primary alone)

        primary_answer = primary_response.get("answer", "")

        # For now, simple check: count experts with similar answers
        # In a real implementation, this would use semantic similarity
        agreement_weight = 0.51  # Primary always agrees with itself

        for response in responses:
            expert_id = response.get("expert_id", "")
            if expert_id == primary_expert_id or "error" in response:
                continue

            # Simple similarity check (in practice, use semantic similarity)
            answer = response.get("answer", "")
            if answer and primary_answer:
                # Very basic: if answers share significant content, consider agreeing
                # This is a placeholder - real implementation would use embeddings
                similarity = self._simple_similarity(primary_answer, answer)
                expert_config = get_expert_config()
                if similarity > expert_config.similarity_threshold:
                    weight = self.weight_matrix.get_expert_weight(expert_id, domain)
                    agreement_weight += weight

        return min(agreement_weight, 1.0)

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """
        Simple text similarity metric (placeholder).

        In production, use proper semantic similarity (embeddings, cosine similarity).
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _get_experts_for_domain(
        self, domain: str, prioritize_builtin: bool = False
    ) -> list[str]:
        """
        Get expert IDs for a domain, prioritizing built-in or customer experts.

        Args:
            domain: Domain name
            prioritize_builtin: If True, prioritize built-in experts for technical domains.
                              If False, prioritize customer experts for business domains.

        Returns:
            List of expert IDs to consult, ordered by priority
        """
        expert_ids = []
        is_technical_domain = domain in TECHNICAL_DOMAINS

        # Find experts that match the domain
        builtin_matches = []
        customer_matches = []

        for expert_id, expert in self.builtin_experts.items():
            if expert.primary_domain == domain:
                builtin_matches.append(expert_id)

        for expert_id, expert in self.customer_experts.items():
            if expert.primary_domain == domain:
                customer_matches.append(expert_id)

        # Determine priority order
        if is_technical_domain and prioritize_builtin:
            # Technical domain: built-in experts first
            expert_ids.extend(builtin_matches)
            expert_ids.extend(customer_matches)
        elif not is_technical_domain and not prioritize_builtin:
            # Business domain: customer experts first
            expert_ids.extend(customer_matches)
            expert_ids.extend(builtin_matches)
        else:
            # Default: built-in first for technical, customer first for business
            if is_technical_domain:
                expert_ids.extend(builtin_matches)
                expert_ids.extend(customer_matches)
            else:
                expert_ids.extend(customer_matches)
                expert_ids.extend(builtin_matches)

        # If no domain matches, try to find experts with related domains
        if not expert_ids:
            # Fallback: get any expert that might be relevant
            if is_technical_domain:
                expert_ids.extend(list(self.builtin_experts.keys()))
            else:
                expert_ids.extend(list(self.customer_experts.keys()))
                expert_ids.extend(list(self.builtin_experts.keys()))

        # Apply tech stack priorities if available
        if self._tech_stack_priorities and expert_ids:
            expert_ids = self._apply_priorities(expert_ids)

        return expert_ids

    def _apply_priorities(self, expert_ids: list[str]) -> list[str]:
        """
        Apply tech stack priorities to expert ID list.

        Experts are sorted by priority (higher first), with experts not in
        priority mapping appearing at the end.

        Args:
            expert_ids: List of expert IDs to prioritize

        Returns:
            List of expert IDs sorted by priority (higher first)
        """
        if not self._tech_stack_priorities:
            return expert_ids

        # Separate experts into prioritized and unprioritized
        prioritized: list[tuple[str, float]] = []
        unprioritized: list[str] = []

        for expert_id in expert_ids:
            priority = self._tech_stack_priorities.get(expert_id)
            if priority is not None:
                prioritized.append((expert_id, priority))
            else:
                unprioritized.append(expert_id)

        # Sort prioritized experts by priority (higher first)
        prioritized.sort(key=lambda x: x[1], reverse=True)

        # Combine: prioritized experts first (sorted), then unprioritized
        result = [expert_id for expert_id, _ in prioritized]
        result.extend(unprioritized)

        return result
