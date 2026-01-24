"""
Expert Suggestion System

Suggests new experts based on detected domains and usage patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .adaptive_domain_detector import DomainSuggestion


@dataclass
class ExpertSuggestion:
    """Suggestion for creating a new expert."""

    expert_id: str
    expert_name: str
    primary_domain: str
    confidence: float  # 0.0-1.0
    usage_frequency: int
    suggested_knowledge: list[str] = field(default_factory=list)
    priority: str = "normal"  # "low", "normal", "high", "critical"
    estimated_value: float = 0.0  # Estimated value/impact score
    reasoning: str = ""


class ExpertSuggester:
    """
    Suggests new experts based on domain detection and usage patterns.
    
    Analyzes detected domains against existing experts and generates
    expert configuration suggestions with knowledge base structure.
    """

    # Knowledge templates for common domains
    KNOWLEDGE_TEMPLATES = {
        "oauth2-refresh-tokens": [
            "oauth2-refresh-token-flows.md",
            "token-expiry-handling.md",
            "custom-auth-headers.md",
            "token-refresh-strategies.md",
        ],
        "api-clients": [
            "api-client-patterns.md",
            "error-handling.md",
            "retry-strategies.md",
            "rate-limiting.md",
        ],
        "graphql": [
            "graphql-schema-design.md",
            "query-optimization.md",
            "resolver-patterns.md",
        ],
        "microservices": [
            "service-communication.md",
            "service-discovery.md",
            "circuit-breaker-patterns.md",
        ],
        "websocket": [
            "websocket-connection-management.md",
            "real-time-patterns.md",
            "message-routing.md",
        ],
        "mqtt": [
            "mqtt-topics-design.md",
            "qos-levels.md",
            "retained-messages.md",
        ],
    }

    # Expert name templates
    NAME_TEMPLATES = {
        "oauth2-refresh-tokens": "OAuth2 Refresh Token Expert",
        "api-clients": "API Client Integration Expert",
        "graphql": "GraphQL Expert",
        "microservices": "Microservices Architecture Expert",
        "websocket": "WebSocket Expert",
        "mqtt": "MQTT Protocol Expert",
    }

    def __init__(self, project_root: Path | None = None):
        """
        Initialize expert suggester.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()

    async def suggest_expert(
        self,
        domain: str,
        usage_context: dict[str, Any],
        confidence_threshold: float = 0.7,
    ) -> ExpertSuggestion | None:
        """
        Generate expert suggestion for a detected domain.

        Args:
            domain: Detected domain name
            usage_context: Context about domain usage (frequency, patterns, etc.)
            confidence_threshold: Minimum confidence to suggest

        Returns:
            ExpertSuggestion if domain meets criteria, None otherwise
        """
        # Check if expert already exists
        if self._expert_exists(domain):
            return None

        # Generate expert ID
        expert_id = self._generate_expert_id(domain)

        # Generate expert name
        expert_name = self._generate_expert_name(domain)

        # Get suggested knowledge areas
        suggested_knowledge = self._get_suggested_knowledge(domain)

        # Calculate confidence and priority
        confidence = usage_context.get("confidence", 0.5)
        usage_frequency = usage_context.get("frequency", 0)
        priority = self._calculate_priority(confidence, usage_frequency)

        # Estimate value
        estimated_value = self._estimate_value(confidence, usage_frequency, domain)

        # Generate reasoning
        reasoning = self._generate_reasoning(domain, usage_context, confidence)

        # Only suggest if confidence meets threshold
        if confidence < confidence_threshold:
            return None

        return ExpertSuggestion(
            expert_id=expert_id,
            expert_name=expert_name,
            primary_domain=domain,
            confidence=confidence,
            usage_frequency=usage_frequency,
            suggested_knowledge=suggested_knowledge,
            priority=priority,
            estimated_value=estimated_value,
            reasoning=reasoning,
        )

    async def suggest_from_domain_detection(
        self, domain_suggestion: DomainSuggestion
    ) -> ExpertSuggestion | None:
        """
        Suggest expert from domain detection result.

        Args:
            domain_suggestion: DomainSuggestion from domain detector

        Returns:
            ExpertSuggestion if valid, None otherwise
        """
        usage_context = {
            "confidence": domain_suggestion.confidence,
            "frequency": domain_suggestion.usage_frequency,
            "source": domain_suggestion.source,
            "evidence": domain_suggestion.evidence,
        }

        return await self.suggest_expert(
            domain_suggestion.domain,
            usage_context,
            confidence_threshold=0.6,  # Lower threshold for detected domains
        )

    def _expert_exists(self, domain: str) -> bool:
        """Check if expert already exists for domain."""
        # Check built-in experts
        from .builtin_registry import BuiltinExpertRegistry

        if domain in BuiltinExpertRegistry.TECHNICAL_DOMAINS:
            return True

        # Check project-defined experts
        experts_file = self.project_root / ".tapps-agents" / "experts.yaml"
        if experts_file.exists():
            try:
                import yaml

                with open(experts_file) as f:
                    experts_config = yaml.safe_load(f)
                    experts = experts_config.get("experts", [])
                    for expert in experts:
                        if expert.get("primary_domain") == domain:
                            return True
            except Exception:
                pass

        return False

    def _generate_expert_id(self, domain: str) -> str:
        """Generate expert ID from domain name."""
        # Convert domain to expert ID format: expert-{domain}
        domain_sanitized = domain.replace("_", "-").replace(" ", "-").lower()
        return f"expert-{domain_sanitized}"

    def _generate_expert_name(self, domain: str) -> str:
        """Generate human-readable expert name."""
        # Use template if available
        if domain in self.NAME_TEMPLATES:
            return self.NAME_TEMPLATES[domain]

        # Generate from domain name
        words = domain.replace("-", " ").replace("_", " ").split()
        capitalized = " ".join(word.capitalize() for word in words)
        return f"{capitalized} Expert"

    def _get_suggested_knowledge(self, domain: str) -> list[str]:
        """Get suggested knowledge base files for domain."""
        # Use template if available
        if domain in self.KNOWLEDGE_TEMPLATES:
            return self.KNOWLEDGE_TEMPLATES[domain]

        # Generate default knowledge files
        domain_sanitized = domain.replace("_", "-").replace(" ", "-")
        return [
            f"{domain_sanitized}-patterns.md",
            f"{domain_sanitized}-best-practices.md",
            f"{domain_sanitized}-common-issues.md",
        ]

    def _calculate_priority(
        self, confidence: float, usage_frequency: int
    ) -> str:
        """Calculate priority based on confidence and frequency."""
        if confidence >= 0.8 and usage_frequency >= 5:
            return "critical"
        elif confidence >= 0.7 or usage_frequency >= 3:
            return "high"
        elif confidence >= 0.6 or usage_frequency >= 1:
            return "normal"
        else:
            return "low"

    def _estimate_value(
        self, confidence: float, usage_frequency: int, domain: str
    ) -> float:
        """Estimate value/impact score for expert."""
        # Base value from confidence
        value = confidence * 0.5

        # Add value from frequency (log scale)
        if usage_frequency > 0:
            import math

            value += min(0.3, math.log(usage_frequency + 1) / 10)

        # Add value from domain importance (heuristic)
        high_value_domains = [
            "oauth2-refresh-tokens",
            "api-clients",
            "security",
            "authentication",
        ]
        if domain in high_value_domains:
            value += 0.2

        return min(1.0, value)

    def _generate_reasoning(
        self, domain: str, usage_context: dict[str, Any], confidence: float
    ) -> str:
        """Generate reasoning for expert suggestion."""
        source = usage_context.get("source", "unknown")
        frequency = usage_context.get("frequency", 0)
        evidence = usage_context.get("evidence", [])

        reasoning_parts = [
            f"Domain '{domain}' detected with {confidence:.0%} confidence",
            f"Source: {source}",
        ]

        if frequency > 0:
            reasoning_parts.append(f"Detected {frequency} times in recent usage")

        if evidence:
            reasoning_parts.append(f"Evidence: {evidence[0][:100]}")

        return ". ".join(reasoning_parts)
