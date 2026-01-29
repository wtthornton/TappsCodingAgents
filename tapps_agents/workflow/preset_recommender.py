"""Workflow preset recommendation system.

Analyzes task complexity and recommends appropriate workflow presets to optimize
planning time and token usage.

@ai-prime-directive: Recommendations must be:
- Accurate (80%+ precision)
- Fast (<50ms recommendation time)
- Explainable (clear reasoning provided)
- Overridable (user can ignore)
"""

from dataclasses import dataclass
from typing import Literal, Optional
from pathlib import Path
import re

PresetType = Literal["minimal", "standard", "comprehensive", "full-sdlc"]


@dataclass
class PresetRecommendation:
    """Recommendation for workflow preset.

    Attributes:
        preset: Recommended preset type
        confidence: Confidence level (0-1)
        reasoning: List of reasons for recommendation
        complexity_score: Task complexity (1-10)
        risk_score: Task risk level (1-10)
    """
    preset: PresetType
    confidence: float
    reasoning: list[str]
    complexity_score: float
    risk_score: float

    def format(self) -> str:
        """Format recommendation for display."""
        emoji = {"minimal": "⚡", "standard": "⚙️", "comprehensive": "🎯", "full-sdlc": "🏗️"}
        return f"""
{emoji[self.preset]} Recommended Preset: **{self.preset}**
Confidence: {self.confidence:.0%}
Complexity: {self.complexity_score:.1f}/10 | Risk: {self.risk_score:.1f}/10

Reasoning:
{chr(10).join(f'  - {reason}' for reason in self.reasoning)}

To use: @simple-mode *build "description" --preset {self.preset}
To override: Use any other preset or proceed without flag
"""


class PresetRecommender:
    """Recommend workflow preset based on task analysis."""

    # Complexity indicators
    HIGH_COMPLEXITY_KEYWORDS = [
        "architecture", "design", "refactor", "rewrite", "migrate",
        "multiple", "several", "integrate", "coordinate", "system"
    ]

    MEDIUM_COMPLEXITY_KEYWORDS = [
        "new", "create", "build", "implement", "add", "feature"
    ]

    LOW_COMPLEXITY_KEYWORDS = [
        "typo", "fix comment", "update doc", "add log", "simple",
        "quick", "small", "minor"
    ]

    # Risk indicators
    HIGH_RISK_KEYWORDS = [
        "security", "auth", "authentication", "authorization", "crypto",
        "password", "token", "validation", "sanitization"
    ]

    MEDIUM_RISK_KEYWORDS = [
        "breaking", "migration", "deprecate", "database", "api",
        "production", "deploy", "release"
    ]

    LOW_RISK_KEYWORDS = [
        "test", "doc", "comment", "log", "debug",
        "internal", "dev", "local"
    ]

    def recommend(
        self,
        prompt: str,
        file_context: Optional[dict] = None
    ) -> PresetRecommendation:
        """Analyze task and recommend preset.

        Args:
            prompt: User's task description
            file_context: Optional file/project context

        Returns:
            Preset recommendation with reasoning
        """
        # Check for framework changes first (mandatory full-sdlc)
        if self._is_framework_change(file_context or {}):
            return PresetRecommendation(
                preset="full-sdlc",
                confidence=1.0,
                reasoning=[
                    "Framework change detected (tapps_agents/ package)",
                    "Full SDLC mandatory for framework development",
                    "Required: comprehensive testing, documentation, security scan"
                ],
                complexity_score=10.0,
                risk_score=10.0
            )

        # Analyze complexity and risk
        complexity = self._analyze_complexity(prompt, file_context)
        risk = self._analyze_risk(prompt, file_context)

        # Decision logic
        if complexity >= 8 or risk >= 8:
            return PresetRecommendation(
                preset="comprehensive",
                confidence=0.9,
                reasoning=[
                    f"High complexity ({complexity:.1f}/10)" if complexity >= 8 else None,
                    f"High risk ({risk:.1f}/10)" if risk >= 8 else None,
                    "Design phase recommended for complex/risky changes",
                    "Full architecture and security review needed"
                ],
                complexity_score=complexity,
                risk_score=risk
            )

        if complexity <= 3 and risk <= 3:
            return PresetRecommendation(
                preset="minimal",
                confidence=0.85,
                reasoning=[
                    f"Low complexity ({complexity:.1f}/10)",
                    f"Low risk ({risk:.1f}/10)",
                    "Simple change requiring minimal overhead",
                    "Direct implementation with basic testing sufficient"
                ],
                complexity_score=complexity,
                risk_score=risk
            )

        # Default: standard
        return PresetRecommendation(
            preset="standard",
            confidence=0.8,
            reasoning=[
                f"Moderate complexity ({complexity:.1f}/10)",
                f"Moderate risk ({risk:.1f}/10)",
                "Standard workflow provides good balance",
                "Planning + implementation + review + testing"
            ],
            complexity_score=complexity,
            risk_score=risk
        )

    def _analyze_complexity(
        self,
        prompt: str,
        context: Optional[dict]
    ) -> float:
        """Score task complexity 1-10."""
        score = 5.0  # Baseline
        prompt_lower = prompt.lower()

        # High complexity indicators
        for keyword in self.HIGH_COMPLEXITY_KEYWORDS:
            if keyword in prompt_lower:
                score += 1.5
                break  # Only count once per category

        # Medium complexity indicators
        if any(kw in prompt_lower for kw in self.MEDIUM_COMPLEXITY_KEYWORDS):
            score += 0.5

        # Low complexity indicators (decrease score)
        for keyword in self.LOW_COMPLEXITY_KEYWORDS:
            if keyword in prompt_lower:
                score -= 2.0
                break

        # File context adjustments
        if context:
            files_affected = context.get("files_affected", 1)
            if files_affected > 5:
                score += 2.0
            elif files_affected == 1:
                score -= 0.5

            # Test files are typically simpler
            if context.get("is_test_file"):
                score -= 1.0

        return max(1.0, min(10.0, score))

    def _analyze_risk(
        self,
        prompt: str,
        context: Optional[dict]
    ) -> float:
        """Score task risk 1-10."""
        score = 5.0  # Baseline
        prompt_lower = prompt.lower()

        # High risk indicators
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in prompt_lower:
                score += 2.0
                break

        # Medium risk indicators
        if any(kw in prompt_lower for kw in self.MEDIUM_RISK_KEYWORDS):
            score += 1.0

        # Low risk indicators (decrease score)
        for keyword in self.LOW_RISK_KEYWORDS:
            if keyword in prompt_lower:
                score -= 1.5
                break

        # File context adjustments
        if context:
            # Test files are lower risk
            if context.get("is_test_file"):
                score -= 2.0

            # Production code is higher risk
            if context.get("is_production"):
                score += 1.0

        return max(1.0, min(10.0, score))

    def _is_framework_change(self, context: dict) -> bool:
        """Check if change affects framework (tapps_agents/)."""
        file_path = context.get("file_path", "")

        # Check if modifying framework package
        if "tapps_agents/" in file_path and "/tests/" not in file_path:
            return True

        # Check multiple files
        files = context.get("files", [])
        for f in files:
            if "tapps_agents/" in f and "/tests/" not in f:
                return True

        return False


def recommend_preset(
    prompt: str,
    file_context: Optional[dict] = None
) -> PresetRecommendation:
    """Convenience function to recommend preset.

    Args:
        prompt: Task description
        file_context: Optional context

    Returns:
        Preset recommendation
    """
    recommender = PresetRecommender()
    return recommender.recommend(prompt, file_context)
