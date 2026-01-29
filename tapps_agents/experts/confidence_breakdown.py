"""
Confidence Score Breakdown and Transparency

Provides detailed breakdown of expert confidence scores for debugging and transparency.
Shows component weights and calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConfidenceBreakdown:
    """
    Detailed confidence score breakdown.

    Shows how each component contributes to final confidence score.
    """

    max_confidence: float  # Expert's maximum confidence (0-1)
    agreement: float  # Agreement with other experts (0-1)
    rag_quality: float  # Quality of RAG retrieval (0-1)
    domain_relevance: float  # Domain match quality (0-1)
    project_context: float  # Project-specific context (0-1)

    # Weights (from config)
    weight_max_confidence: float = 0.35
    weight_agreement: float = 0.25
    weight_rag_quality: float = 0.20
    weight_domain_relevance: float = 0.10
    weight_project_context: float = 0.10

    @property
    def total(self) -> float:
        """Calculate total weighted confidence score."""
        return (
            self.max_confidence * self.weight_max_confidence
            + self.agreement * self.weight_agreement
            + self.rag_quality * self.weight_rag_quality
            + self.domain_relevance * self.weight_domain_relevance
            + self.project_context * self.weight_project_context
        )

    def explain(self) -> str:
        """Generate human-readable explanation of confidence score."""
        lines = []

        # Determine overall confidence level
        if self.total >= 0.9:
            level = "Very High"
            emoji = "🟢"
        elif self.total >= 0.75:
            level = "High"
            emoji = "🟡"
        elif self.total >= 0.6:
            level = "Medium"
            emoji = "🟠"
        else:
            level = "Low"
            emoji = "🔴"

        lines.append(f"{emoji} Confidence Level: {level} ({self.total:.2f})")
        lines.append("")

        # Explain each component
        lines.append("Component Breakdown:")
        lines.append("")

        # Max Confidence
        lines.append(f"1. Expert Max Confidence: {self.max_confidence:.2f}")
        lines.append(f"   Weight: {self.weight_max_confidence:.2f}")
        lines.append(f"   Contribution: {self.max_confidence * self.weight_max_confidence:.4f}")
        lines.append("   → This expert's inherent confidence for this domain")
        lines.append("")

        # Agreement
        lines.append(f"2. Agreement with Other Experts: {self.agreement:.2f}")
        lines.append(f"   Weight: {self.weight_agreement:.2f}")
        lines.append(f"   Contribution: {self.agreement * self.weight_agreement:.4f}")
        lines.append("   → Consensus among consulted experts")
        lines.append("")

        # RAG Quality
        lines.append(f"3. RAG Retrieval Quality: {self.rag_quality:.2f}")
        lines.append(f"   Weight: {self.weight_rag_quality:.2f}")
        lines.append(f"   Contribution: {self.rag_quality * self.weight_rag_quality:.4f}")
        lines.append("   → Quality and relevance of knowledge base retrieval")
        lines.append("")

        # Domain Relevance
        lines.append(f"4. Domain Relevance: {self.domain_relevance:.2f}")
        lines.append(f"   Weight: {self.weight_domain_relevance:.2f}")
        lines.append(f"   Contribution: {self.domain_relevance * self.weight_domain_relevance:.4f}")
        lines.append("   → How well the domain matches the context")
        lines.append("")

        # Project Context
        lines.append(f"5. Project Context: {self.project_context:.2f}")
        lines.append(f"   Weight: {self.weight_project_context:.2f}")
        lines.append(f"   Contribution: {self.project_context * self.weight_project_context:.4f}")
        lines.append("   → Project-specific relevance and history")
        lines.append("")

        # Summary
        lines.append("=" * 60)
        lines.append(f"Total Confidence: {self.total:.4f}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert breakdown to dictionary."""
        return {
            "components": {
                "max_confidence": {
                    "value": self.max_confidence,
                    "weight": self.weight_max_confidence,
                    "contribution": self.max_confidence * self.weight_max_confidence,
                },
                "agreement": {
                    "value": self.agreement,
                    "weight": self.weight_agreement,
                    "contribution": self.agreement * self.weight_agreement,
                },
                "rag_quality": {
                    "value": self.rag_quality,
                    "weight": self.weight_rag_quality,
                    "contribution": self.rag_quality * self.weight_rag_quality,
                },
                "domain_relevance": {
                    "value": self.domain_relevance,
                    "weight": self.weight_domain_relevance,
                    "contribution": self.domain_relevance * self.weight_domain_relevance,
                },
                "project_context": {
                    "value": self.project_context,
                    "weight": self.weight_project_context,
                    "contribution": self.project_context * self.weight_project_context,
                },
            },
            "total": self.total,
        }


class ConfidenceExplainer:
    """
    Explain confidence scores for experts.

    Provides detailed breakdowns and debugging information.
    """

    def __init__(self, config: Any | None = None):
        """
        Initialize confidence explainer.

        Args:
            config: Project configuration (for custom weights)
        """
        self.config = config

        # Load weights from config if available
        self.weights = self._load_weights()

    def _load_weights(self) -> dict[str, float]:
        """Load weights from configuration."""
        # Default weights
        weights = {
            "max_confidence": 0.35,
            "agreement": 0.25,
            "rag_quality": 0.20,
            "domain_relevance": 0.10,
            "project_context": 0.10,
        }

        # Override from config if available
        if self.config and hasattr(self.config, "expert"):
            expert_config = self.config.expert
            weights["max_confidence"] = getattr(
                expert_config, "weight_max_confidence", weights["max_confidence"]
            )
            weights["agreement"] = getattr(
                expert_config, "weight_agreement", weights["agreement"]
            )
            weights["rag_quality"] = getattr(
                expert_config, "weight_rag_quality", weights["rag_quality"]
            )
            weights["domain_relevance"] = getattr(
                expert_config, "weight_domain_relevance", weights["domain_relevance"]
            )
            weights["project_context"] = getattr(
                expert_config, "weight_project_context", weights["project_context"]
            )

        return weights

    def create_breakdown(
        self,
        max_confidence: float,
        agreement: float,
        rag_quality: float,
        domain_relevance: float,
        project_context: float,
    ) -> ConfidenceBreakdown:
        """
        Create confidence breakdown.

        Args:
            max_confidence: Expert's maximum confidence (0-1)
            agreement: Agreement with other experts (0-1)
            rag_quality: Quality of RAG retrieval (0-1)
            domain_relevance: Domain match quality (0-1)
            project_context: Project-specific context (0-1)

        Returns:
            ConfidenceBreakdown with calculated total
        """
        return ConfidenceBreakdown(
            max_confidence=max_confidence,
            agreement=agreement,
            rag_quality=rag_quality,
            domain_relevance=domain_relevance,
            project_context=project_context,
            weight_max_confidence=self.weights["max_confidence"],
            weight_agreement=self.weights["agreement"],
            weight_rag_quality=self.weights["rag_quality"],
            weight_domain_relevance=self.weights["domain_relevance"],
            weight_project_context=self.weights["project_context"],
        )

    def explain_confidence(
        self,
        expert_id: str,
        breakdown: ConfidenceBreakdown,
        expert_name: str | None = None,
    ) -> str:
        """
        Generate detailed explanation for expert confidence.

        Args:
            expert_id: Expert ID
            breakdown: Confidence breakdown
            expert_name: Optional expert name

        Returns:
            Formatted explanation string
        """
        lines = ["=" * 70]
        lines.append("CONFIDENCE EXPLANATION")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Expert ID: {expert_id}")
        if expert_name:
            lines.append(f"Expert Name: {expert_name}")
        lines.append("")
        lines.append(breakdown.explain())
        lines.append("")

        # Add interpretation
        lines.append("Interpretation:")
        lines.append(self._get_interpretation(breakdown))

        lines.append("=" * 70)

        return "\n".join(lines)

    def _get_interpretation(self, breakdown: ConfidenceBreakdown) -> str:
        """Generate interpretation of confidence score."""
        lines = []

        # Overall assessment
        if breakdown.total >= 0.9:
            lines.append("✅ Very high confidence - Strong expert match with excellent knowledge")
        elif breakdown.total >= 0.75:
            lines.append("✓ High confidence - Good expert match with solid knowledge")
        elif breakdown.total >= 0.6:
            lines.append("⚠️  Medium confidence - Adequate match, but consider other experts")
        else:
            lines.append("❌ Low confidence - Consider consulting different experts")

        lines.append("")

        # Key drivers
        lines.append("Key Factors:")

        if breakdown.max_confidence >= 0.9:
            lines.append(f"  • High priority expert ({breakdown.max_confidence:.2f})")

        if breakdown.agreement >= 0.8:
            lines.append(f"  • Strong consensus with other experts ({breakdown.agreement:.2f})")

        if breakdown.rag_quality >= 0.8:
            lines.append(f"  • High-quality knowledge retrieval ({breakdown.rag_quality:.2f})")

        if breakdown.domain_relevance >= 0.8:
            lines.append(f"  • Excellent domain match ({breakdown.domain_relevance:.2f})")

        # Concerns
        if breakdown.max_confidence < 0.7:
            lines.append(f"  ⚠️  Lower priority expert ({breakdown.max_confidence:.2f})")

        if breakdown.rag_quality < 0.6:
            lines.append(f"  ⚠️  Limited knowledge available ({breakdown.rag_quality:.2f})")

        return "\n".join(lines)
