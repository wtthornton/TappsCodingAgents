"""
Confidence Calculator for Expert Consultations

Implements improved confidence calculation algorithms that consider:
- Maximum expert confidence
- Agreement level between experts
- RAG knowledge base quality
- Domain relevance
- Agent-specific thresholds
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

from .builtin_registry import BuiltinExpertRegistry

if TYPE_CHECKING:
    from ..core.project_profile import ProjectProfile


# Agent-specific confidence thresholds
# These represent the minimum confidence level required for each agent type
AGENT_CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    "reviewer": 0.8,          # High threshold for code reviews
    "architect": 0.75,         # High for architecture decisions
    "implementer": 0.7,        # Medium-high for code generation
    "designer": 0.65,          # Medium for design decisions
    "tester": 0.7,             # Medium-high for test generation
    "ops": 0.75,               # High for operations
    "enhancer": 0.6,           # Medium for enhancements
    "analyst": 0.65,           # Medium for analysis
    "planner": 0.6,            # Medium for planning
    "debugger": 0.7,           # Medium-high for debugging
    "documenter": 0.5,         # Lower for documentation (less critical)
    "orchestrator": 0.6,       # Medium for orchestration
    "default": 0.7             # Default threshold
}


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
    - Maximum expert confidence (40%)
    - Agreement level between experts (30%)
    - RAG knowledge base quality (20%)
    - Domain relevance (10%)
    """
    
    # Weight factors for confidence calculation
    WEIGHT_MAX_CONFIDENCE = 0.35  # Reduced from 0.4
    WEIGHT_AGREEMENT = 0.25  # Reduced from 0.3
    WEIGHT_RAG_QUALITY = 0.2
    WEIGHT_DOMAIN_RELEVANCE = 0.1
    WEIGHT_PROJECT_CONTEXT = 0.1  # New: project context relevance
    
    @staticmethod
    def calculate(
        responses: List[Dict],
        domain: str,
        agent_id: Optional[str] = None,
        agreement_level: float = 0.0,
        rag_quality: Optional[float] = None,
        num_experts_consulted: Optional[int] = None,
        project_profile: Optional['ProjectProfile'] = None
    ) -> Tuple[float, float]:
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
        if not responses:
            threshold = AGENT_CONFIDENCE_THRESHOLDS.get(agent_id or "default", 0.7)
            return 0.0, threshold
        
        # Extract valid responses
        valid_responses = [r for r in responses if "error" not in r]
        if not valid_responses:
            threshold = AGENT_CONFIDENCE_THRESHOLDS.get(agent_id or "default", 0.7)
            return 0.0, threshold
        
        # Get maximum confidence from responses
        max_confidence = max(r.get("confidence", 0.0) for r in valid_responses)
        
        # Calculate RAG quality (default if not provided)
        if rag_quality is None:
            # Estimate RAG quality based on sources
            sources_count = sum(len(r.get("sources", [])) for r in valid_responses)
            num_responses = len(valid_responses)
            rag_quality = min(1.0, sources_count / (num_responses * 2))  # 2 sources per response = perfect
        
        # Calculate domain relevance
        is_technical_domain = domain in BuiltinExpertRegistry.TECHNICAL_DOMAINS
        domain_relevance = 1.0 if is_technical_domain else 0.9
        
        # Calculate project context relevance
        project_context_relevance = ConfidenceCalculator._calculate_project_context_relevance(
            responses, project_profile
        )
        
        # Normalize agreement level (ensure it's between 0 and 1)
        agreement_level = max(0.0, min(1.0, agreement_level))
        
        # Calculate weighted confidence
        confidence = (
            max_confidence * ConfidenceCalculator.WEIGHT_MAX_CONFIDENCE +
            agreement_level * ConfidenceCalculator.WEIGHT_AGREEMENT +
            rag_quality * ConfidenceCalculator.WEIGHT_RAG_QUALITY +
            domain_relevance * ConfidenceCalculator.WEIGHT_DOMAIN_RELEVANCE +
            project_context_relevance * ConfidenceCalculator.WEIGHT_PROJECT_CONTEXT
        )
        
        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        # Get agent-specific threshold
        threshold = AGENT_CONFIDENCE_THRESHOLDS.get(agent_id or "default", 0.7)
        
        return confidence, threshold
    
    @staticmethod
    def _calculate_project_context_relevance(
        responses: List[Dict],
        project_profile: Optional['ProjectProfile']
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
            if deployment == "cloud" and any(word in combined_answer for word in ["cloud", "aws", "azure", "gcp", "kubernetes", "docker", "container"]):
                score += 0.1
            elif deployment == "local" and any(word in combined_answer for word in ["local", "development", "dev environment"]):
                score += 0.1
            elif deployment == "enterprise" and any(word in combined_answer for word in ["enterprise", "scalable", "production", "infrastructure"]):
                score += 0.1
        
        # Check security level alignment
        if project_profile.security_level:
            security = project_profile.security_level.lower()
            if security in ["high", "critical"] and any(word in combined_answer for word in ["security", "secure", "encryption", "authentication", "authorization"]):
                score += 0.05
            elif security == "standard" and any(word in combined_answer for word in ["security", "best practice"]):
                score += 0.05
        
        # Check compliance alignment
        if project_profile.compliance_requirements:
            compliance_names = [req.name.lower() for req in project_profile.compliance_requirements]
            if any(compliance in combined_answer for compliance in compliance_names):
                score += 0.05
        
        # Check for conflicts (negative score)
        if project_profile.deployment_type == "local" and any(word in combined_answer for word in ["production", "scalable", "enterprise"]):
            score -= 0.05
        
        # Normalize to 0.0-1.0 range
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def calculate_with_metrics(
        metrics: ConfidenceMetrics,
        agent_id: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculate confidence using pre-computed metrics.
        
        Args:
            metrics: ConfidenceMetrics instance with all factors
            agent_id: Optional agent ID for agent-specific threshold
            
        Returns:
            Tuple of (calculated_confidence, threshold)
        """
        confidence = (
            metrics.max_confidence * ConfidenceCalculator.WEIGHT_MAX_CONFIDENCE +
            metrics.agreement_level * ConfidenceCalculator.WEIGHT_AGREEMENT +
            metrics.rag_quality * ConfidenceCalculator.WEIGHT_RAG_QUALITY +
            metrics.domain_relevance * ConfidenceCalculator.WEIGHT_DOMAIN_RELEVANCE +
            getattr(metrics, 'project_context_relevance', 0.0) * ConfidenceCalculator.WEIGHT_PROJECT_CONTEXT
        )
        
        confidence = max(0.0, min(1.0, confidence))
        threshold = AGENT_CONFIDENCE_THRESHOLDS.get(agent_id or "default", 0.7)
        
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
        return AGENT_CONFIDENCE_THRESHOLDS.get(agent_id, AGENT_CONFIDENCE_THRESHOLDS["default"])
    
    @staticmethod
    def meets_threshold(confidence: float, agent_id: Optional[str] = None) -> bool:
        """
        Check if confidence meets agent-specific threshold.
        
        Args:
            confidence: Calculated confidence score
            agent_id: Optional agent ID
            
        Returns:
            True if confidence meets threshold, False otherwise
        """
        threshold = AGENT_CONFIDENCE_THRESHOLDS.get(agent_id or "default", 0.7)
        return confidence >= threshold

