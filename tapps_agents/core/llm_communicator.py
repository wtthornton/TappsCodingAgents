"""
LLM Communication System

Communicates expert suggestions and improvements to LLM (Cursor/Claude).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..experts.expert_suggester import ExpertSuggestion


@dataclass
class LLMHint:
    """Hint to communicate to LLM."""

    type: str  # "expert_suggestion", "expert_performance", "voting_recommendation"
    message: str
    priority: str = "normal"  # "low", "normal", "high"
    actionable: bool = True  # Whether LLM can act on this hint
    metadata: dict[str, Any] | None = None


class LLMCommunicator:
    """
    Communicates expert suggestions and improvements to LLM.
    
    Generates hints that can be included in prompts, system messages,
    or Cursor Skills to guide LLM behavior.
    """

    def generate_expert_suggestion_hint(
        self, suggestion: ExpertSuggestion
    ) -> LLMHint:
        """
        Generate hint about new expert suggestion.

        Args:
            suggestion: ExpertSuggestion to communicate

        Returns:
            LLMHint for LLM
        """
        message = (
            f"💡 Expert Suggestion: A new '{suggestion.expert_name}' expert "
            f"has been auto-generated based on recent usage patterns. "
            f"Consider consulting this expert for {suggestion.primary_domain}-related code. "
            f"Use: @{suggestion.expert_id} *consult \"your question\""
        )

        return LLMHint(
            type="expert_suggestion",
            message=message,
            priority=suggestion.priority,
            actionable=True,
            metadata={
                "expert_id": suggestion.expert_id,
                "expert_name": suggestion.expert_name,
                "domain": suggestion.primary_domain,
                "confidence": suggestion.confidence,
            },
        )

    def generate_expert_performance_hint(
        self, expert_id: str, performance_data: dict[str, Any]
    ) -> LLMHint:
        """
        Generate hint about expert performance improvements.

        Args:
            expert_id: Expert identifier
            performance_data: Performance metrics

        Returns:
            LLMHint for LLM
        """
        success_rate = performance_data.get("first_pass_success_rate", 0.0)
        avg_confidence = performance_data.get("avg_confidence", 0.0)

        if success_rate > 0.8 and avg_confidence > 0.8:
            message = (
                f"✅ Expert Performance: {expert_id} is performing well "
                f"({success_rate:.0%} first-pass success, {avg_confidence:.0%} avg confidence). "
                f"Consider using this expert for related tasks."
            )
            priority = "normal"
        elif success_rate < 0.5 or avg_confidence < 0.6:
            message = (
                f"⚠️ Expert Performance: {expert_id} performance is below expectations "
                f"({success_rate:.0%} first-pass success, {avg_confidence:.0%} avg confidence). "
                f"Knowledge base may need updates."
            )
            priority = "high"
        else:
            message = (
                f"📊 Expert Performance: {expert_id} performance metrics: "
                f"{success_rate:.0%} first-pass success, {avg_confidence:.0%} avg confidence."
            )
            priority = "normal"

        return LLMHint(
            type="expert_performance",
            message=message,
            priority=priority,
            actionable=True,
            metadata={
                "expert_id": expert_id,
                "success_rate": success_rate,
                "avg_confidence": avg_confidence,
            },
        )

    def generate_voting_recommendation_hint(
        self, domain: str, recommended_experts: list[str]
    ) -> LLMHint:
        """
        Generate hint about expert voting recommendations.

        Args:
            domain: Domain context
            recommended_experts: List of recommended expert IDs

        Returns:
            LLMHint for LLM
        """
        if not recommended_experts:
            return LLMHint(
                type="voting_recommendation",
                message=f"No specific expert recommendations for domain '{domain}'",
                priority="low",
                actionable=False,
            )

        expert_list = ", ".join(recommended_experts[:3])  # Limit to 3
        message = (
            f"🎯 Expert Recommendation: For domain '{domain}', "
            f"consider consulting these experts: {expert_list}. "
            f"These experts have shown strong performance for this domain."
        )

        return LLMHint(
            type="voting_recommendation",
            message=message,
            priority="normal",
            actionable=True,
            metadata={"domain": domain, "recommended_experts": recommended_experts},
        )

    def format_hints_for_prompt(self, hints: list[LLMHint]) -> str:
        """
        Format hints for inclusion in prompts.

        Args:
            hints: List of LLMHints

        Returns:
            Formatted string for prompt
        """
        if not hints:
            return ""

        # Filter by priority (include normal and high)
        filtered_hints = [h for h in hints if h.priority in ("normal", "high")]

        if not filtered_hints:
            return ""

        lines = ["## Adaptive Learning Hints"]
        for hint in filtered_hints:
            lines.append(f"\n{hint.message}")

        return "\n".join(lines)

    def format_hints_for_system_message(self, hints: list[LLMHint]) -> str:
        """
        Format hints for system message.

        Args:
            hints: List of LLMHints

        Returns:
            Formatted string for system message
        """
        if not hints:
            return ""

        # Include all hints in system message
        lines = ["### Adaptive Learning Information"]
        for hint in hints:
            lines.append(f"- {hint.message}")

        return "\n".join(lines)
