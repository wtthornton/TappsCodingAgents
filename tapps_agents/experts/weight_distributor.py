"""
Weight Distribution Algorithm for Industry Experts

Implements the 51% primary authority model:
- One expert has 51% authority per domain (PRIMARY)
- Other experts share remaining 49% equally
- N domains → N experts (1:1 primary mapping)
- Weights are fixed per domain
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class ExpertWeightMatrix:
    """
    Weight matrix for all experts across all domains.
    
    Structure:
    {
        "expert-1": {
            "domain-1": 0.51,  # Primary
            "domain-2": 0.245,
            "domain-3": 0.245
        },
        "expert-2": {
            "domain-1": 0.245,
            "domain-2": 0.51,  # Primary
            "domain-3": 0.245
        },
        ...
    }
    """
    weights: Dict[str, Dict[str, float]]
    domains: List[str]
    experts: List[str]
    
    def get_expert_weight(self, expert_id: str, domain: str) -> float:
        """Get weight for a specific expert-domain pair."""
        return self.weights.get(expert_id, {}).get(domain, 0.0)
    
    def get_primary_expert(self, domain: str) -> Optional[str]:
        """Get the primary expert (51%) for a domain."""
        for expert_id, domain_weights in self.weights.items():
            if domain_weights.get(domain, 0.0) >= 0.51:
                return expert_id
        return None
    
    def validate(self) -> List[str]:
        """
        Validate weight matrix against requirements.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check: Each domain has exactly one primary (51%)
        for domain in self.domains:
            primaries = []
            for expert_id, domain_weights in self.weights.items():
                weight = domain_weights.get(domain, 0.0)
                if weight >= 0.51:
                    primaries.append(expert_id)
            
            if len(primaries) == 0:
                errors.append(f"Domain '{domain}' has no primary expert (51%)")
            elif len(primaries) > 1:
                errors.append(f"Domain '{domain}' has multiple primary experts: {primaries}")
        
        # Check: Each domain column sums to 100%
        for domain in self.domains:
            total = sum(
                expert_weights.get(domain, 0.0)
                for expert_weights in self.weights.values()
            )
            if abs(total - 1.0) > 0.001:  # Allow small floating-point errors
                errors.append(f"Domain '{domain}' column sum is {total:.3f}, expected 1.000")
        
        # Check: Primary weight is exactly 51%
        for domain in self.domains:
            primary_expert = self.get_primary_expert(domain)
            if primary_expert:
                weight = self.weights[primary_expert][domain]
                if abs(weight - 0.51) > 0.001:
                    errors.append(
                        f"Domain '{domain}' primary expert '{primary_expert}' "
                        f"has weight {weight:.3f}, expected 0.510"
                    )
        
        # Check: Number of domains equals number of experts
        if len(self.domains) != len(self.experts):
            errors.append(
                f"Number of domains ({len(self.domains)}) "
                f"does not equal number of experts ({len(self.experts)})"
            )
        
        return errors


class WeightDistributor:
    """
    Calculates and manages expert weight distribution.
    
    Formula:
    - Primary Expert: 51%
    - Each Other Expert: 49% / (N-1)
    """
    
    PRIMARY_WEIGHT = 0.51
    OTHER_WEIGHT = 0.49
    
    @staticmethod
    def calculate_weights(
        domains: List[str],
        expert_primary_map: Dict[str, str]
    ) -> ExpertWeightMatrix:
        """
        Calculate weight matrix for experts and domains.
        
        Args:
            domains: List of domain names
            expert_primary_map: Mapping of expert_id -> primary_domain
        
        Returns:
            ExpertWeightMatrix with calculated weights
        
        Raises:
            ValueError: If validation fails
        """
        # Validate: Each domain has exactly one primary expert
        domain_primaries = {}
        for expert_id, primary_domain in expert_primary_map.items():
            if primary_domain in domain_primaries:
                raise ValueError(
                    f"Domain '{primary_domain}' has multiple primary experts: "
                    f"{domain_primaries[primary_domain]} and {expert_id}"
                )
            domain_primaries[primary_domain] = expert_id
        
        # Validate: All domains have a primary expert
        missing_domains = set(domains) - set(domain_primaries.keys())
        if missing_domains:
            raise ValueError(f"Domains without primary expert: {missing_domains}")
        
        # Validate: All experts are accounted for
        experts = list(expert_primary_map.keys())
        if len(experts) != len(domains):
            raise ValueError(
                f"Number of experts ({len(experts)}) does not equal "
                f"number of domains ({len(domains)})"
            )
        
        # Calculate weights
        num_experts = len(experts)
        other_weight = WeightDistributor.OTHER_WEIGHT / (num_experts - 1) if num_experts > 1 else 0.0
        
        # Round to avoid floating-point issues
        other_weight = float(Decimal(str(other_weight)).quantize(
            Decimal('0.001'), rounding=ROUND_HALF_UP
        ))
        
        weights: Dict[str, Dict[str, float]] = {}
        
        for expert_id in experts:
            expert_weights: Dict[str, float] = {}
            
            for domain in domains:
                if domain == expert_primary_map[expert_id]:
                    # Primary domain: 51%
                    expert_weights[domain] = WeightDistributor.PRIMARY_WEIGHT
                else:
                    # Other domains: equal share of 49%
                    expert_weights[domain] = other_weight
            
            weights[expert_id] = expert_weights
        
        matrix = ExpertWeightMatrix(
            weights=weights,
            domains=domains,
            experts=experts
        )
        
        # Validate the matrix
        errors = matrix.validate()
        if errors:
            raise ValueError(f"Weight matrix validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return matrix
    
    @staticmethod
    def recalculate_on_domain_add(
        current_matrix: ExpertWeightMatrix,
        new_domain: str,
        new_expert_id: str
    ) -> ExpertWeightMatrix:
        """
        Recalculate weights when a new domain/expert is added.
        
        When adding a new domain:
        1. Add new expert as primary for new domain (51%)
        2. Recalculate all existing weights:
           - Primary: Still 51%
           - Others: 49% / (new_total_experts - 1)
        
        Args:
            current_matrix: Current weight matrix
            new_domain: New domain to add
            new_expert_id: New expert to add (primary for new domain)
        
        Returns:
            Updated ExpertWeightMatrix
        """
        if new_domain in current_matrix.domains:
            raise ValueError(f"Domain '{new_domain}' already exists")
        
        if new_expert_id in current_matrix.experts:
            raise ValueError(f"Expert '{new_expert_id}' already exists")
        
        # Build new expert-primary mapping
        expert_primary_map = {}
        for expert_id in current_matrix.experts:
            primary_domain = current_matrix.get_primary_expert_domain(expert_id)
            if primary_domain:
                expert_primary_map[expert_id] = primary_domain
        
        # Add new expert-domain pair
        expert_primary_map[new_expert_id] = new_domain
        
        # Recalculate with all domains (including new one)
        new_domains = current_matrix.domains + [new_domain]
        
        return WeightDistributor.calculate_weights(new_domains, expert_primary_map)
    
    @staticmethod
    def format_matrix(matrix: ExpertWeightMatrix) -> str:
        """
        Format weight matrix as a readable table.
        
        Returns:
            Formatted string representation
        """
        lines = []
        
        # Header
        header = "Expert/Domain".ljust(25)
        for domain in matrix.domains:
            header += domain[:15].ljust(18)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Rows
        for expert_id in matrix.experts:
            row = expert_id[:24].ljust(25)
            for domain in matrix.domains:
                weight = matrix.get_expert_weight(expert_id, domain)
                marker = "▲" if weight >= 0.51 else " "
                row += f"{marker} {weight:.3f}".ljust(18)
            lines.append(row)
        
        # Column totals
        totals_row = "TOTAL".ljust(25)
        for domain in matrix.domains:
            total = sum(
                matrix.get_expert_weight(expert_id, domain)
                for expert_id in matrix.experts
            )
            totals_row += f"{total:.3f}".ljust(18)
        lines.append("-" * len(header))
        lines.append(totals_row)
        
        return "\n".join(lines)


# Add helper method to ExpertWeightMatrix
def _get_primary_expert_domain(self, expert_id: str) -> Optional[str]:
    """Get the primary domain for an expert."""
    expert_weights = self.weights.get(expert_id, {})
    for domain, weight in expert_weights.items():
        if weight >= 0.51:
            return domain
    return None


ExpertWeightMatrix.get_primary_expert_domain = _get_primary_expert_domain

