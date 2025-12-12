"""
Confidence Calculator for Expert Consultations

Implements improved confidence calculation algorithms that consider:
- Maximum expert confidence
- Agreement level between experts
- RAG knowledge base quality
- Domain relevance
- Agent-specific thresholds
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .builtin_registry import BuiltinExpertRegistry

if TYPE_CHECKING:
    from ..core.config import ExpertConfig
    from ..core.project_profile import ProjectProfile

# Legacy constant for backward compatibility (deprecated, use config instead)
AGENT_CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "reviewer": 0.8,
    "architect": 0.75,
    "implementer": 0.7,
    "designer": 0.65,
    "tester": 0.7,
    "ops": 0.75,
    "enhancer": 0.6,
    "analyst": 0.65,
    "planner": 0.6,
    "debugger": 0.7,
    "documenter": 0.5,
    "orchestrator": 0.6,
    "default": 0.7,
}


def _get_expert_config() -> ExpertConfig:
    """Get expert configuration (lazy load)."""
    from ..core.config import get_expert_config

    return get_expert_config()


@dataclass
class ConfidenceMetrics:
    """Metrics used in confidence calculation."""

    max_confidence: float
    agreement_level: float
    rag_quality: float = 0.8  # Default RAG quality if not provided
    domain_relevance: float = 1.0  # Domain relevance score
    num_experts: int = 1
    num_responses: int = 1


class ConfidenceCalculator:
    """
    Calculates confidence scores for expert consultations.

    Uses a weighted algorithm that considers multiple factors:
    - Maximum expert confidence (configurable, default 35%)
    - Agreement level between experts (configurable, default 25%)
    - RAG knowledge base quality (configurable, default 20%)
    - Domain relevance (configurable, default 10%)
    - Project context relevance (configurable, default 10%)
    """

    # Legacy class constants for backward compatibility (deprecated, use config instead)
    WEIGHT_MAX_CONFIDENCE = 0.35
    WEIGHT_AGREEMENT = 0.25
    WEIGHT_RAG_QUALITY = 0.2
    WEIGHT_DOMAIN_RELEVANCE = 0.1
    WEIGHT_PROJECT_CONTEXT = 0.1

    @staticmethod
    def calculate(
        responses: list[dict],
        domain: str,
        agent_id: str | None = None,
        agreement_level: float = 0.0,
        rag_quality: float | None = None,
        num_experts_consulted: int | None = None,
        project_profile: ProjectProfile | None = None,
    ) -> tuple[float, float]:
        """
        Calculate confidence score with multiple factors.

        Args:
            responses: List of expert response dictionaries
            domain: Domain name for the consultation
            agent_id: Optional agent ID for agent-specific threshold
            agreement_level: Agreement level between experts (0.0-1.0)
            rag_quality: Optional RAG quality score (0.0-1.0)
            num_experts_consulted: Optional number of experts consulted

        Returns:
            Tuple of (calculated_confidence, threshold) where:
            - calculated_confidence: Confidence score (0.0-1.0)
            - threshold: Agent-specific minimum threshold (0.0-1.0)
        """
        # Get expert config
        expert_config = _get_expert_config()

        if not responses:
            threshold = expert_config.agent_confidence_thresholds.get(
                agent_id or "default",
                expert_config.agent_confidence_thresholds["default"],
            )
            return 0.0, threshold

        # Extract valid responses
        valid_responses = [r for r in responses if "error" not in r]
        if not valid_responses:
            threshold = expert_config.agent_confidence_thresholds.get(
                agent_id or "default",
                expert_config.agent_confidence_thresholds["default"],
            )
            return 0.0, threshold

        # Get maximum confidence from responses
        max_confidence = max(r.get("confidence", 0.0) for r in valid_responses)

        # Calculate RAG quality (default if not provided)
        if rag_quality is None:
            # Estimate RAG quality based on sources
            sources_count = sum(len(r.get("sources", [])) for r in valid_responses)
            num_responses = len(valid_responses)
            rag_quality = min(
                1.0, sources_count / (num_responses * 2)
            )  # 2 sources per response = perfect

        # Calculate domain relevance
        is_technical_domain = domain in BuiltinExpertRegistry.TECHNICAL_DOMAINS
        domain_relevance = 1.0 if is_technical_domain else 0.9

        # Calculate project context relevance
        project_context_relevance = (
            ConfidenceCalculator._calculate_project_context_relevance(
                responses, project_profile
            )
        )

        # Normalize agreement level (ensure it's between 0 and 1)
        agreement_level = max(0.0, min(1.0, agreement_level))

        # Calculate weighted confidence using config
        confidence = (
            max_confidence * expert_config.weight_max_confidence
            + agreement_level * expert_config.weight_agreement
            + rag_quality * expert_config.weight_rag_quality
            + domain_relevance * expert_config.weight_domain_relevance
            + project_context_relevance * expert_config.weight_project_context
        )

        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        # Get agent-specific threshold from config
        threshold = expert_config.agent_confidence_thresholds.get(
            agent_id or "default", expert_config.agent_confidence_thresholds["default"]
        )

        return confidence, threshold

    @staticmethod
    def _calculate_project_context_relevance(
        responses: list[dict], project_profile: ProjectProfile | None
    ) -> float:
        """
        Calculate how well expert advice matches project profile.

        Simple keyword matching to detect alignment between advice and profile.

        Args:
            responses: List of expert responses
            project_profile: Optional project profile

        Returns:
            Relevance score (0.0-1.0)
        """
        if not project_profile or not responses:
            return 0.0  # Neutral if no profile or responses

        # Extract answers from responses
        answers = [r.get("answer", "") for r in responses if "error" not in r]
        if not answers:
            return 0.0

        combined_answer = " ".join(answers).lower()
        score = 0.0

        # Check deployment type alignment
        if project_profile.deployment_type:
            deployment = project_profile.deployment_type.lower()
            if deployment == "cloud" and any(
                word in combined_answer
                for word in [
                    "cloud",
                    "aws",
                    "azure",
                    "gcp",
                    "kubernetes",
                    "docker",
                    "container",
                ]
            ):
                score += 0.1
            elif deployment == "local" and any(
                word in combined_answer
                for word in ["local", "development", "dev environment"]
            ):
                score += 0.1
            elif deployment == "enterprise" and any(
                word in combined_answer
                for word in ["enterprise", "scalable", "production", "infrastructure"]
            ):
                score += 0.1

        # Check security level alignment
        if project_profile.security_level:
            security = project_profile.security_level.lower()
            if security in ["high", "critical"] and any(
                word in combined_answer
                for word in [
                    "security",
                    "secure",
                    "encryption",
                    "authentication",
                    "authorization",
                ]
            ):
                score += 0.05
            elif security == "standard" and any(
                word in combined_answer for word in ["security", "best practice"]
            ):
                score += 0.05

        # Check compliance alignment
        if project_profile.compliance_requirements:
            compliance_names = [
                req.name.lower() for req in project_profile.compliance_requirements
            ]
            if any(compliance in combined_answer for compliance in compliance_names):
                score += 0.05

        # Check for conflicts (negative score)
        if project_profile.deployment_type == "local" and any(
            word in combined_answer for word in ["production", "scalable", "enterprise"]
        ):
            score -= 0.05

        # Normalize to 0.0-1.0 range
        return max(0.0, min(1.0, score))

    @staticmethod
    def calculate_with_metrics(
        metrics: ConfidenceMetrics, agent_id: str | None = None
    ) -> tuple[float, float]:
        """
        Calculate confidence using pre-computed metrics.

        Args:
            metrics: ConfidenceMetrics instance with all factors
            agent_id: Optional agent ID for agent-specific threshold

        Returns:
            Tuple of (calculated_confidence, threshold)
        """
        # Get expert config
        expert_config = _get_expert_config()

        confidence = (
            metrics.max_confidence * expert_config.weight_max_confidence
            + metrics.agreement_level * expert_config.weight_agreement
            + metrics.rag_quality * expert_config.weight_rag_quality
            + metrics.domain_relevance * expert_config.weight_domain_relevance
            + getattr(metrics, "project_context_relevance", 0.0)
            * expert_config.weight_project_context
        )

        confidence = max(0.0, min(1.0, confidence))
        threshold = expert_config.agent_confidence_thresholds.get(
            agent_id or "default", expert_config.agent_confidence_thresholds["default"]
        )

        return confidence, threshold

    @staticmethod
    def get_threshold(agent_id: str) -> float:
        """
        Get confidence threshold for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Confidence threshold (0.0-1.0)
        """
        expert_config = _get_expert_config()
        return expert_config.agent_confidence_thresholds.get(
            agent_id, expert_config.agent_confidence_thresholds["default"]
        )

    @staticmethod
    def meets_threshold(confidence: float, agent_id: str | None = None) -> bool:
        """
        Check if confidence meets agent-specific threshold.

        Args:
            confidence: Calculated confidence score
            agent_id: Optional agent ID

        Returns:
            True if confidence meets threshold, False otherwise
        """
        expert_config = _get_expert_config()
        threshold = expert_config.agent_confidence_thresholds.get(
            agent_id or "default", expert_config.agent_confidence_thresholds["default"]
        )
        return confidence >= threshold
