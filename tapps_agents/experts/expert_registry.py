"""
Expert Registry

Manages expert instances and provides consultation services with weighted decision-making.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_expert import BaseExpert
from .domain_config import DomainConfig, DomainConfigParser
from .weight_distributor import ExpertWeightMatrix
from .expert_config import load_expert_configs, ExpertConfigModel


@dataclass
class ConsultationResult:
    """Result from consulting multiple experts."""
    domain: str
    query: str
    responses: List[Dict[str, Any]]  # Individual expert responses
    weighted_answer: str  # Combined weighted answer
    agreement_level: float  # 0.0-1.0
    confidence: float  # Overall confidence
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
    
    def __init__(self, domain_config: Optional[DomainConfig] = None):
        """
        Initialize expert registry.
        
        Args:
            domain_config: Optional domain configuration (can be loaded later)
        """
        self.domain_config = domain_config
        self.experts: Dict[str, BaseExpert] = {}
        self.weight_matrix: Optional[ExpertWeightMatrix] = (
            domain_config.weight_matrix if domain_config else None
        )
    
    @classmethod
    def from_domains_file(cls, domains_file: Path) -> 'ExpertRegistry':
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
        cls,
        config_file: Path,
        domain_config: Optional[DomainConfig] = None
    ) -> 'ExpertRegistry':
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
                fine_tuned=expert_config.fine_tuned
            )
            registry.register_expert(expert)
        
        return registry
    
    def register_expert(self, expert: BaseExpert) -> None:
        """
        Register an expert agent.
        
        Args:
            expert: BaseExpert instance to register
        
        Raises:
            ValueError: If expert not found in weight matrix
        """
        if self.weight_matrix and expert.expert_id not in self.weight_matrix.experts:
            raise ValueError(
                f"Expert '{expert.expert_id}' not found in weight matrix. "
                f"Registered experts: {list(self.weight_matrix.experts)}"
            )
        
        # Update confidence matrix from weight matrix if available
        if self.weight_matrix:
            expert.confidence_matrix = self.weight_matrix.weights.get(
                expert.expert_id, {}
            )
        
        self.experts[expert.expert_id] = expert
    
    def get_expert(self, expert_id: str) -> Optional[BaseExpert]:
        """Get an expert by ID."""
        return self.experts.get(expert_id)
    
    def list_experts(self) -> List[str]:
        """List all registered expert IDs."""
        return list(self.experts.keys())
    
    async def consult(
        self,
        query: str,
        domain: str,
        include_all: bool = True
    ) -> ConsultationResult:
        """
        Consult multiple experts on a domain question and aggregate weighted responses.
        
        Args:
            query: The question to ask
            domain: Domain context
            include_all: Whether to consult all experts or just primary
        
        Returns:
            ConsultationResult with weighted answer and agreement metrics
        """
        if not self.weight_matrix:
            raise ValueError("Weight matrix not initialized. Load domain config first.")
        
        primary_expert_id = self.weight_matrix.get_primary_expert(domain)
        if not primary_expert_id:
            raise ValueError(f"No primary expert found for domain '{domain}'")
        
        # Collect expert IDs to consult
        expert_ids_to_consult = []
        if include_all:
            # Consult all experts
            expert_ids_to_consult = list(self.weight_matrix.experts)
        else:
            # Only consult primary
            expert_ids_to_consult = [primary_expert_id]
        
        # Consult each expert
        responses = []
        for expert_id in expert_ids_to_consult:
            expert = self.experts.get(expert_id)
            if not expert:
                continue  # Skip if expert not registered
            
            try:
                response = await expert.run("consult", query=query, domain=domain)
                if "error" not in response:
                    responses.append({
                        "expert_id": expert_id,
                        "expert_name": expert.agent_name,
                        "answer": response.get("answer", ""),
                        "confidence": response.get("confidence", 0.0),
                        "sources": response.get("sources", [])
                    })
            except Exception as e:
                # Log error but continue with other experts
                responses.append({
                    "expert_id": expert_id,
                    "error": str(e)
                })
        
        if not responses:
            raise ValueError(f"No expert responses received for domain '{domain}'")
        
        # Aggregate weighted responses
        weighted_answer = self._aggregate_responses(responses, domain)
        
        # Calculate agreement level
        agreement_level = self._calculate_agreement(responses, domain, primary_expert_id)
        
        # Get overall confidence
        confidence = max(r.get("confidence", 0.0) for r in responses if "error" not in r)
        
        # Check if all experts agreed
        primary_response = next(
            (r for r in responses if r.get("expert_id") == primary_expert_id and "error" not in r),
            None
        )
        all_agreed = agreement_level >= 0.75  # High agreement threshold
        
        return ConsultationResult(
            domain=domain,
            query=query,
            responses=responses,
            weighted_answer=weighted_answer,
            agreement_level=agreement_level,
            confidence=confidence,
            primary_expert=primary_expert_id,
            all_experts_agreed=all_agreed
        )
    
    def _aggregate_responses(
        self,
        responses: List[Dict[str, Any]],
        domain: str
    ) -> str:
        """
        Aggregate expert responses using weighted decision-making.
        
        Primary expert (51%) has primary influence; others augment.
        """
        if not self.weight_matrix:
            # Fallback: just use primary expert
            primary = next((r for r in responses if r.get("expert_id") and "error" not in r), None)
            return primary.get("answer", "") if primary else ""
        
        primary_expert_id = self.weight_matrix.get_primary_expert(domain)
        
        # Find primary expert response
        primary_response = next(
            (r for r in responses if r.get("expert_id") == primary_expert_id and "error" not in r),
            None
        )
        
        if not primary_response:
            # Fallback to first available response
            primary_response = next((r for r in responses if "error" not in r), None)
            if not primary_response:
                return "No expert responses available."
            return primary_response.get("answer", "")
        
        # Start with primary expert answer (51% weight)
        primary_answer = primary_response.get("answer", "")
        aggregated_parts = [f"[Primary - {primary_response.get('expert_name', 'Expert')}] {primary_answer}"]
        
        # Add influences from other experts
        other_responses = [
            r for r in responses
            if r.get("expert_id") != primary_expert_id and "error" not in r
        ]
        
        if other_responses:
            influences = []
            for response in other_responses:
                expert_id = response.get("expert_id", "")
                weight = self.weight_matrix.get_expert_weight(expert_id, domain)
                answer = response.get("answer", "")
                expert_name = response.get("expert_name", expert_id)
                
                influences.append(f"[Influence ({weight:.1%}) - {expert_name}] {answer}")
            
            if influences:
                aggregated_parts.append("\n\nAdditional Expert Input:")
                aggregated_parts.extend(influences)
        
        return "\n".join(aggregated_parts)
    
    def _calculate_agreement(
        self,
        responses: List[Dict[str, Any]],
        domain: str,
        primary_expert_id: str
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
            (r for r in responses if r.get("expert_id") == primary_expert_id and "error" not in r),
            None
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
                if similarity > 0.6:  # 60% similarity threshold
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

