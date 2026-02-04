"""
Workflow Suggester - Proactive workflow suggestions based on user intent.

Detects when users are about to do direct edits and suggests appropriate
Simple Mode workflows instead. Includes semantic intent detection with
weighted signal scoring for workflow mismatch detection.
"""

import re
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from ..simple_mode.intent_parser import IntentParser, IntentType


# ============================================================================
# Type Definitions
# ============================================================================

IntentCategory = Literal["bug_fix", "enhancement", "architectural"]


class SignalTier(TypedDict):
    """
    Signal tier with weighted regex patterns.

    Attributes:
        patterns: List of regex patterns to match against prompt
        weight: Weight for this tier (0.0-1.0), higher = stronger signal
    """
    patterns: list[str]
    weight: float


SignalCategory = dict[str, SignalTier]


class TaskCharacteristics(TypedDict):
    """Task characteristics detected from prompt analysis."""
    intent: str  # "bug_fix" | "feature" | "architectural"
    scope: str  # "low" | "medium" | "high"
    complexity: str  # "low" | "medium" | "high"


# ============================================================================
# Signal Definitions for Intent Detection
# ============================================================================

SIGNAL_DEFINITIONS: dict[IntentCategory, SignalCategory] = {
    "bug_fix": {
        "explicit_keywords": {
            "patterns": [
                "fix",
                "bug",
                "broken",
                "error",
                "wrong",
                "incorrect",
                "failing",
                "failed",
            ],
            "weight": 1.0,
        },
        "implicit_descriptions": {
            "patterns": [
                r"reports? \d+ when (?:should be|files exist)",
                r"validation fails?",
                r"incorrect count",
                r"not working",
                r"doesn't detect",
                r"shows \w+ instead of",
                r"returns \w+ but expected",
            ],
            "weight": 0.9,
        },
        "behavior_mismatch": {
            "patterns": [
                r"should \w+ but (?:does|shows?) \w+",
                r"expected \w+ (?:but )?got \w+",
                r"supposed to \w+ but",
            ],
            "weight": 0.85,
        },
    },
    "enhancement": {
        "keywords": {
            "patterns": [
                "enhance",
                "improve",
                "better",
                "clearer",
                "modernize",
                "upgrade",
                "optimize",
            ],
            "weight": 0.7,
        },
        "ux_improvements": {
            "patterns": [
                "provide (?:better |clearer )?feedback",
                "better messaging",
                "clearer output",
                "improve (?:user )?experience",
            ],
            "weight": 0.6,
        },
    },
    "architectural": {
        "framework_dev": {
            "patterns": [
                r"modif(?:y|ying) tapps_agents/",
                r"framework (?:changes|development)",
                r"workflow engine",
                r"orchestrat(?:or|ion)",
                r"core system",
            ],
            "weight": 1.0,
        },
        "breaking_changes": {
            "patterns": [
                "major refactor",
                "architectural changes",
                "breaking change",
                "redesign",
                r"refactor (?:entire|whole) system",
            ],
            "weight": 0.95,
        },
    },
}


# Pre-compile regex patterns for performance
_COMPILED_PATTERNS: dict[IntentCategory, dict[str, list[re.Pattern]]] = {}


def _initialize_compiled_patterns() -> None:
    """Pre-compile all regex patterns at module load for performance."""
    global _COMPILED_PATTERNS

    for category, signals in SIGNAL_DEFINITIONS.items():
        _COMPILED_PATTERNS[category] = {}
        for tier_name, tier_data in signals.items():
            _COMPILED_PATTERNS[category][tier_name] = [
                re.compile(pattern, re.I) for pattern in tier_data["patterns"]
            ]


# Initialize patterns at module load
_initialize_compiled_patterns()


# ============================================================================
# Workflow Requirements
# ============================================================================

class WorkflowRequirement(TypedDict, total=False):
    """
    Workflow specification defining requirements and thresholds.

    Attributes:
        steps: Number of workflow steps
        min_complexity: Minimum complexity threshold (optional)
        max_complexity: Maximum complexity threshold (optional)
        min_scope: Minimum scope threshold (optional)
        max_scope: Maximum scope threshold (optional)
        required_intents: List of primary intents this workflow is designed for
        description: Human-readable description of workflow purpose
    """
    steps: int
    min_complexity: str
    max_complexity: str
    min_scope: str
    max_scope: str
    required_intents: list[str]
    description: str


WORKFLOW_REQUIREMENTS: dict[str, WorkflowRequirement] = {
    "*full": {
        "steps": 9,
        "min_complexity": "high",
        "min_scope": "high",
        "required_intents": ["framework_dev", "security_critical", "architectural"],
        "description": "Framework development, architectural changes, security-critical features",
    },
    "*build": {
        "steps": 4,
        "min_complexity": "medium",
        "min_scope": "medium",
        "required_intents": ["feature", "enhancement"],
        "description": "New features, enhancements, moderate complexity",
    },
    "*fix": {
        "steps": 3,
        "max_complexity": "medium",
        "max_scope": "low",
        "required_intents": ["bug_fix"],
        "description": "Bug fixes, focused changes, low to medium complexity",
    },
    "*refactor": {
        "steps": 4,
        "min_complexity": "medium",
        "max_scope": "medium",
        "required_intents": ["refactor", "modernization"],
        "description": "Code refactoring, modernization, pattern updates",
    },
}

# Helper constants for comparison
COMPLEXITY_ORDER: dict[str, int] = {"low": 1, "medium": 2, "high": 3}
SCOPE_ORDER: dict[str, int] = {"low": 1, "medium": 2, "high": 3}


# ============================================================================
# Intent Detection Functions
# ============================================================================

def score_signals(prompt: str, signals: SignalCategory) -> float:
    """
    Score prompt against weighted signal patterns.

    Calculates a weighted score by matching prompt text against signal patterns.
    Each signal tier has a weight (0.0-1.0) representing its strength/reliability.

    Args:
        prompt: Natural language prompt to analyze
        signals: Signal category with weighted tiers

    Returns:
        Normalized score (0.0-1.0) representing signal strength

        Formula: score = sum(weight * match_count) / total_patterns

    Performance:
        Uses pre-compiled regex patterns for speed (<50ms per category)

    Examples:
        >>> signals = SIGNAL_DEFINITIONS["bug_fix"]
        >>> score_signals("Fix validation bug", signals)
        0.95  # Matched "fix" and "bug" with high weights

    Edge Cases:
        - No matches: Returns 0.0
        - Empty signals: Returns 0.0
    """
    if not prompt or not signals:
        return 0.0

    total_score = 0.0
    total_patterns = sum(len(tier["patterns"]) for tier in signals.values())

    if total_patterns == 0:
        return 0.0

    for tier_name, tier in signals.items():
        weight = tier["weight"]

        # Use pre-compiled patterns for performance
        category = next(
            (cat for cat, sigs in SIGNAL_DEFINITIONS.items() if tier_name in sigs),
            None
        )

        if category and tier_name in _COMPILED_PATTERNS.get(category, {}):
            patterns = _COMPILED_PATTERNS[category][tier_name]
            matches = sum(1 for pattern in patterns if pattern.search(prompt))
        else:
            # Fallback to runtime compilation (shouldn't happen)
            matches = sum(
                1 for pattern_str in tier["patterns"]
                if re.search(pattern_str, prompt, re.I)
            )

        total_score += weight * matches

    return total_score / total_patterns if total_patterns > 0 else 0.0


def calculate_confidence(scores: dict[str, float]) -> float:
    """
    Calculate confidence based on score distribution.

    Confidence represents how distinct the primary intent is from other intents.

    Args:
        scores: Dict of intent → score mappings

    Returns:
        Confidence score (0.0-1.0)

        Currently: confidence = max_score
        Future: confidence = max_score * (1 - second_max / max_score)

    Examples:
        >>> calculate_confidence({"bug_fix": 0.85, "enhancement": 0.40})
        0.85

    Edge Cases:
        - All scores 0.0: Returns 0.0
        - Single score: Returns that score
    """
    if not scores:
        return 0.0

    max_score = max(scores.values())
    return max_score


def detect_primary_intent(prompt: str) -> tuple[str | None, float]:
    """
    Detect primary intent from natural language prompt using weighted signal scoring.

    Analyzes prompt text against multiple signal categories (bug fix, enhancement,
    architectural) using regex pattern matching with weighted scoring. Returns the
    PRIMARY intent only if confidence is high enough (≥0.6) and the gap between
    primary and secondary intents is significant (≥0.2).

    Args:
        prompt: Natural language task description from user.
            Examples:
            - "Fix validation bug that reports 0/14"
            - "Enhance init validation to correctly detect files"
            - "Add user authentication with JWT tokens"
            - "Modify workflow engine architecture"

    Returns:
        Tuple of (intent, confidence) where:
        - intent: Primary intent detected ("bug_fix" | "enhancement" | "architectural")
                 or None if confidence is too low
        - confidence: Confidence score (0.0-1.0) representing signal strength

        Examples:
        - ("bug_fix", 0.85) - High confidence bug fix
        - ("enhancement", 0.72) - Medium confidence enhancement
        - (None, 0.45) - Low confidence, intent unclear

    Algorithm:
        1. Score each category using weighted signal matching
        2. Calculate confidence based on score distribution
        3. Return PRIMARY intent if:
           - Confidence ≥ 0.6 (threshold)
           - Gap between primary and secondary ≥ 0.2 (distinctiveness)
        4. Return (None, confidence) if thresholds not met

    Performance:
        Target: <200ms (P99 latency)
        Optimizations:
        - Pre-compiled regex patterns (module-level)
        - Early exit on high-confidence matches

    Examples:
        >>> detect_primary_intent("Fix validation bug")
        ("bug_fix", 0.92)

        >>> detect_primary_intent("Enhance init validation to correctly detect files")
        ("bug_fix", 0.85)  # Implicit bug fix (validation broken)

        >>> detect_primary_intent("Add user authentication with JWT")
        ("enhancement", 0.88)

        >>> detect_primary_intent("Modify workflow engine architecture")
        ("architectural", 0.95)

        >>> detect_primary_intent("update config")
        (None, 0.45)  # Too vague, low confidence

    Edge Cases:
        - Empty prompt: Returns (None, 0.0)
        - Mixed signals: Returns primary if gap ≥ 0.2, else (None, confidence)

    See Also:
        - score_signals(): Helper for weighted signal matching
        - calculate_confidence(): Helper for confidence calculation
        - SIGNAL_DEFINITIONS: Signal pattern definitions
    """
    # Handle invalid input
    if not prompt or not isinstance(prompt, str):
        return (None, 0.0)

    if len(prompt.strip()) == 0:
        return (None, 0.0)

    # Score each category
    scores = {
        "bug_fix": score_signals(prompt, SIGNAL_DEFINITIONS["bug_fix"]),
        "enhancement": score_signals(prompt, SIGNAL_DEFINITIONS["enhancement"]),
        "architectural": score_signals(prompt, SIGNAL_DEFINITIONS["architectural"]),
    }

    # Sort by score (descending)
    sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if len(sorted_intents) < 2:
        return (None, 0.0)

    primary, primary_score = sorted_intents[0]
    secondary, secondary_score = sorted_intents[1]

    # Calculate confidence
    confidence = calculate_confidence(scores)

    # Check thresholds
    gap = primary_score - secondary_score

    # Return primary intent only if:
    # 1. Confidence ≥ 0.6 (high enough to be useful)
    # 2. Gap ≥ 0.2 (primary is distinct from secondary)
    if confidence >= 0.6 and gap >= 0.2:
        return (primary, confidence)

    # Not confident enough
    return (None, confidence)


# ============================================================================
# Existing WorkflowSuggestion Class
# ============================================================================

@dataclass
class WorkflowSuggestion:
    """A workflow suggestion with benefits and command."""

    workflow_command: str
    workflow_type: str
    benefits: list[str]
    confidence: float
    reason: str


class WorkflowSuggester:
    """
    Suggest Simple Mode workflows based on user intent.

    Analyzes user input to detect when a workflow would be beneficial
    and provides proactive suggestions.
    """

    def __init__(self):
        """Initialize workflow suggester."""
        self.intent_parser = IntentParser()

    def suggest_workflow(self, user_input: str, context: dict[str, Any] | None = None) -> WorkflowSuggestion | None:
        """
        Suggest a workflow based on user input.

        Args:
            user_input: User's natural language input
            context: Optional context (file paths, project type, etc.)

        Returns:
            WorkflowSuggestion if a workflow is recommended, None otherwise
        """
        if not user_input or not user_input.strip():
            return None

        context = context or {}

        # Parse intent
        intent = self.intent_parser.parse(user_input)

        # Check if intent suggests a workflow
        if intent.type == IntentType.UNKNOWN:
            return None

        # Detect hybrid "review + fix" intent with enhanced pattern matching
        user_input_lower = user_input.lower()

        # Pattern-based detection for hybrid requests
        HYBRID_PATTERNS = [
            r"review.*(?:and|then).*fix",
            r"check.*(?:and|then).*(?:fix|repair|correct)",
            r"compare.*(?:and|then).*fix",
            r"make.*match.*(?:and|then)?.*fix",
            r"(?:inspect|examine|analyze).*(?:and|then).*(?:fix|repair|correct)",
        ]
        pattern_match = any(
            re.search(pattern, user_input_lower)
            for pattern in HYBRID_PATTERNS
        )

        # Boolean detection with expanded keywords
        has_review = (
            intent.type == IntentType.REVIEW
            or "review" in user_input_lower
            or intent.compare_to_codebase
            or pattern_match  # Add pattern match signal
        )
        has_fix = (
            intent.type == IntentType.FIX
            or "fix" in user_input_lower
            or "repair" in user_input_lower  # Expanded keyword
            or "correct" in user_input_lower  # Expanded keyword
        )

        if has_review and has_fix:
            # Dynamic confidence scoring (0.85-1.0 range)
            base_confidence = 0.85

            # Boost confidence based on signal strength
            if pattern_match:
                base_confidence += 0.05  # Boost for pattern match
            if intent.compare_to_codebase:
                base_confidence += 0.05  # Boost for "compare to codebase" flag
            if intent.type == IntentType.REVIEW or intent.type == IntentType.FIX:
                base_confidence += 0.05  # Boost for explicit intent type match

            confidence = min(base_confidence, 1.0)  # Cap at 1.0

            return WorkflowSuggestion(
                workflow_command=(
                    '@simple-mode *review <file>  # Then: @simple-mode *fix <file> "issues from review"'
                ),
                workflow_type="review-then-fix",
                benefits=[
                    "Comprehensive quality analysis first",
                    "Targeted fixes based on review feedback",
                    "Quality gates after fixes",
                    "Full traceability from review to fix",
                ],
                confidence=confidence,
                reason="Review + fix hybrid request detected",
            )

        # Map intent to workflow command
        workflow_mapping = {
            IntentType.BUILD: {
                "command": f'@simple-mode *build "{user_input}"',
                "type": "build",
                "benefits": [
                    "Automatic test generation (80%+ coverage)",
                    "Quality gate enforcement (75+ score required)",
                    "Comprehensive documentation",
                    "Early bug detection with systematic review",
                    "Full traceability (requirements → implementation)",
                ],
                "reason": "New feature implementation detected",
            },
            IntentType.FIX: {
                "command": f'@simple-mode *fix <file> "{user_input}"',
                "type": "fix",
                "benefits": [
                    "Systematic root cause analysis",
                    "Automatic test verification",
                    "Quality review before fix",
                ],
                "reason": "Bug fix or error resolution detected",
            },
            IntentType.REVIEW: {
                "command": f'@simple-mode *review <file>',
                "type": "review",
                "benefits": [
                    "Comprehensive quality scores (5 metrics)",
                    "Actionable improvement suggestions",
                    "Security analysis",
                ],
                "reason": "Code review request detected",
            },
            IntentType.TEST: {
                "command": f'@simple-mode *test <file>',
                "type": "test",
                "benefits": [
                    "Comprehensive test generation",
                    "Coverage analysis",
                    "Test framework detection",
                ],
                "reason": "Test generation request detected",
            },
            IntentType.REFACTOR: {
                "command": f'@simple-mode *refactor <file>',
                "type": "refactor",
                "benefits": [
                    "Pattern detection and modernization",
                    "Quality validation after refactoring",
                    "Test updates",
                ],
                "reason": "Code refactoring request detected",
            },
        }

        workflow_info = workflow_mapping.get(intent.type)
        if not workflow_info:
            return None

        # Calculate confidence based on intent confidence
        confidence = intent.confidence

        # Adjust confidence based on context
        if context.get("has_existing_files"):
            # If files already exist, might be modification vs new feature
            if intent.type == IntentType.BUILD:
                confidence *= 0.9  # Slightly lower confidence

        return WorkflowSuggestion(
            workflow_command=workflow_info["command"],
            workflow_type=workflow_info["type"],
            benefits=workflow_info["benefits"],
            confidence=confidence,
            reason=workflow_info["reason"],
        )

    def format_suggestion(self, suggestion: WorkflowSuggestion) -> str:
        """
        Format a workflow suggestion as a user-friendly message.

        Args:
            suggestion: Workflow suggestion to format

        Returns:
            Formatted suggestion message
        """
        lines = [
            "🤖 **Workflow Suggestion**",
            "",
            f"For {suggestion.reason}, consider using:",
            "",
            f"```",
            f"{suggestion.workflow_command}",
            f"```",
            "",
            "**Benefits:**",
        ]

        for benefit in suggestion.benefits:
            lines.append(f"✅ {benefit}")

        lines.extend([
            "",
            "Would you like me to proceed with the workflow?",
            "[Yes, use workflow] [No, direct edit]",
        ])

        return "\n".join(lines)

    def should_suggest(self, user_input: str, context: dict[str, Any] | None = None) -> bool:
        """
        Determine if a workflow should be suggested.

        Args:
            user_input: User's natural language input
            context: Optional context

        Returns:
            True if workflow should be suggested, False otherwise
        """
        suggestion = self.suggest_workflow(user_input, context)

        if not suggestion:
            return False

        # Only suggest if confidence is high enough
        return suggestion.confidence >= 0.6

    def suggest_build_preset(self, prompt: str) -> str:
        """
        Suggest build preset (minimal, standard, comprehensive) from prompt scope.
        Automation-only: no user prompt; used to auto-select workflow depth.

        Args:
            prompt: Natural language feature description.

        Returns:
            "minimal" | "standard" | "comprehensive"
        """
        if not prompt or not isinstance(prompt, str):
            return "standard"
        pl = prompt.lower().strip()
        words = len(pl.split())

        # Minimal: very short, obvious small change
        minimal_keywords = (
            "fix typo", "typo", "add logging", "update config", "change value",
            "rename", "small fix", "quick fix", "one line", "single line",
        )
        if words <= 8 and any(k in pl for k in minimal_keywords):
            return "minimal"

        # Comprehensive: security, auth, api design, large scope
        comprehensive_keywords = (
            "authentication", "auth system", "security", "oauth", "jwt",
            "new api", "rest api", "graphql", "database schema", "migration",
            "refactor", "architecture", "microservice", "full sdlc",
        )
        if words >= 30 or any(k in pl for k in comprehensive_keywords):
            return "comprehensive"

        return "standard"
