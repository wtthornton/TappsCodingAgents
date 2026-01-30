"""Prompt analysis engine for Simple Mode intelligence.

This module provides intelligent prompt analysis to detect:
- Task intent (build, validate, fix, etc.)
- Prompt complexity
- Existing code references
- Optimal workflow selection
"""

import re
from dataclasses import dataclass, field
from enum import Enum


class TaskIntent(Enum):
    """Task intent types."""
    BUILD = "build"              # New feature/component
    VALIDATE = "validate"        # Compare/validate existing code
    FIX = "fix"                  # Bug fix
    REVIEW = "review"            # Code review
    TEST = "test"                # Test generation
    REFACTOR = "refactor"        # Refactoring
    OPTIMIZE = "optimize"        # Performance optimization
    EXPLORE = "explore"          # Codebase exploration


class PromptComplexity(Enum):
    """Prompt complexity levels."""
    MINIMAL = "minimal"          # < 50 words, simple task
    STANDARD = "standard"        # 50-150 words, typical task
    DETAILED = "detailed"        # 150-300 words, comprehensive
    COMPREHENSIVE = "comprehensive"  # > 300 words, very detailed


@dataclass
class ExistingCodeReference:
    """Reference to existing code in prompt."""
    file_path: str | None = None
    line_range: str | None = None
    description: str | None = None
    quality_hint: str | None = None  # "excellent", "needs work", etc.


@dataclass
class PromptAnalysis:
    """Result of prompt analysis."""
    # Intent detection
    primary_intent: TaskIntent
    secondary_intents: list[TaskIntent] = field(default_factory=list)
    intent_confidence: float = 0.0  # 0.0-1.0

    # Complexity analysis
    complexity: PromptComplexity = PromptComplexity.STANDARD
    word_count: int = 0
    estimated_lines_of_code: int = 0

    # Existing code detection
    has_existing_code: bool = False
    existing_code_refs: list[ExistingCodeReference] = field(default_factory=list)

    # Keywords and patterns
    keywords: list[str] = field(default_factory=list)
    mentions_compare: bool = False
    mentions_validate: bool = False
    mentions_existing: bool = False

    # Recommendations
    recommended_workflow: str = "build"  # "build", "validate", "quick-wins"
    recommended_enhancement: str = "full"  # "full", "quick", "none"
    recommended_preset: str = "standard"  # "minimal", "standard", "comprehensive"

    # Rationale
    analysis_rationale: str = ""


class PromptAnalyzer:
    """Analyze prompts for intent, complexity, and existing code references."""

    # Intent keywords
    INTENT_KEYWORDS = {
        TaskIntent.BUILD: [
            "create", "build", "implement", "add", "generate",
            "make", "develop", "new", "feature"
        ],
        TaskIntent.VALIDATE: [
            "compare", "validate", "verify", "check against",
            "existing implementation", "manual implementation"
        ],
        TaskIntent.FIX: [
            "fix", "repair", "resolve", "debug", "error",
            "bug", "issue", "broken"
        ],
        TaskIntent.REVIEW: [
            "review", "analyze", "inspect", "examine",
            "audit", "assess"
        ],
        TaskIntent.TEST: [
            "test", "testing", "tests", "coverage",
            "verify", "validate"
        ],
        TaskIntent.REFACTOR: [
            "refactor", "improve", "modernize", "update",
            "restructure", "reorganize"
        ],
        TaskIntent.OPTIMIZE: [
            "optimize", "faster", "performance", "speed up",
            "improve performance", "quick wins"
        ],
        TaskIntent.EXPLORE: [
            "explore", "understand", "navigate", "find",
            "discover", "trace"
        ],
    }

    # Existing code patterns
    EXISTING_CODE_PATTERNS = [
        r"existing implementation",
        r"manual implementation",
        r"current code",
        r"lines?\s+\d+-\d+",  # "lines 751-878"
        r"at lines?\s+\d+",
        r"starting at line\s+\d+",
        r"compare with existing",
        r"already exists",
    ]

    # Comparison keywords
    COMPARISON_KEYWORDS = [
        "compare", "comparison", "validate", "verify against",
        "check against", "vs", "versus", "instead of"
    ]

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze(self, prompt: str, command: str | None = None) -> PromptAnalysis:
        """
        Analyze prompt for intent, complexity, and existing code.

        Args:
            prompt: User's prompt text
            command: Optional explicit command (*build, *validate, etc.)

        Returns:
            PromptAnalysis with all detected characteristics
        """
        # 1. Detect intent
        intent, intent_confidence, secondary_intents = self._detect_intent(prompt, command)

        # 2. Analyze complexity
        complexity, word_count, estimated_loc = self._analyze_complexity(prompt)

        # 3. Detect existing code references
        has_existing, existing_refs = self._detect_existing_code(prompt)

        # 4. Extract keywords
        keywords = self._extract_keywords(prompt)

        # 5. Check for comparison/validation keywords
        mentions_compare = any(kw in prompt.lower() for kw in self.COMPARISON_KEYWORDS)
        mentions_validate = "validate" in prompt.lower() or "validation" in prompt.lower()
        mentions_existing = has_existing

        # 6. Generate recommendations
        workflow, enhancement, preset, rationale = self._generate_recommendations(
            intent=intent,
            complexity=complexity,
            has_existing=has_existing,
            word_count=word_count,
            mentions_compare=mentions_compare,
            command=command
        )

        return PromptAnalysis(
            primary_intent=intent,
            secondary_intents=secondary_intents,
            intent_confidence=intent_confidence,
            complexity=complexity,
            word_count=word_count,
            estimated_lines_of_code=estimated_loc,
            has_existing_code=has_existing,
            existing_code_refs=existing_refs,
            keywords=keywords,
            mentions_compare=mentions_compare,
            mentions_validate=mentions_validate,
            mentions_existing=mentions_existing,
            recommended_workflow=workflow,
            recommended_enhancement=enhancement,
            recommended_preset=preset,
            analysis_rationale=rationale
        )

    def _detect_intent(
        self,
        prompt: str,
        command: str | None
    ) -> tuple[TaskIntent, float, list[TaskIntent]]:
        """Detect primary and secondary intents."""
        prompt_lower = prompt.lower()

        # Score each intent
        intent_scores: dict[TaskIntent, int] = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            if score > 0:
                intent_scores[intent] = score

        # Check for explicit command override
        if command:
            command_lower = command.lower()
            if "build" in command_lower:
                # But check if it's really validation
                if any(kw in prompt_lower for kw in ["compare", "existing", "validate"]):
                    primary = TaskIntent.VALIDATE
                    confidence = 0.85
                else:
                    primary = TaskIntent.BUILD
                    confidence = 0.95
            elif "validate" in command_lower:
                primary = TaskIntent.VALIDATE
                confidence = 0.95
            elif "fix" in command_lower:
                primary = TaskIntent.FIX
                confidence = 0.95
            elif "review" in command_lower:
                primary = TaskIntent.REVIEW
                confidence = 0.95
            elif "test" in command_lower:
                primary = TaskIntent.TEST
                confidence = 0.95
            else:
                # Use scored intent
                primary = max(intent_scores, key=intent_scores.get) if intent_scores else TaskIntent.BUILD
                confidence = 0.7
        else:
            # No command - use highest scoring intent
            primary = max(intent_scores, key=intent_scores.get) if intent_scores else TaskIntent.BUILD
            confidence = 0.7 if intent_scores else 0.5

        # Secondary intents (score >= 2)
        secondary = [
            intent for intent, score in intent_scores.items()
            if score >= 2 and intent != primary
        ]

        return primary, confidence, secondary

    def _analyze_complexity(self, prompt: str) -> tuple[PromptComplexity, int, int]:
        """Analyze prompt complexity."""
        words = prompt.split()
        word_count = len(words)

        # Estimate lines of code based on requirements mentioned
        # Heuristic: ~5 words per requirement, ~20 lines per requirement
        estimated_requirements = word_count / 50  # Rough estimate
        estimated_loc = int(estimated_requirements * 20)

        # Determine complexity
        if word_count < 50:
            complexity = PromptComplexity.MINIMAL
        elif word_count < 150:
            complexity = PromptComplexity.STANDARD
        elif word_count < 300:
            complexity = PromptComplexity.DETAILED
        else:
            complexity = PromptComplexity.COMPREHENSIVE

        return complexity, word_count, estimated_loc

    def _detect_existing_code(self, prompt: str) -> tuple[bool, list[ExistingCodeReference]]:
        """Detect references to existing code."""
        refs: list[ExistingCodeReference] = []

        for pattern in self.EXISTING_CODE_PATTERNS:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(prompt), match.end() + 50)
                context = prompt[start:end]

                # Try to extract file path
                file_match = re.search(r'[\w/\\]+\.(py|js|ts|java|cpp)', context)
                file_path = file_match.group(0) if file_match else None

                # Try to extract line range
                line_match = re.search(r'lines?\s+(\d+)-(\d+)', context, re.IGNORECASE)
                line_range = line_match.group(0) if line_match else None

                # Check for quality hints
                quality_hint = None
                if "excellent" in context.lower():
                    quality_hint = "excellent"
                elif "good" in context.lower():
                    quality_hint = "good"
                elif "needs work" in context.lower() or "broken" in context.lower():
                    quality_hint = "needs_work"

                refs.append(ExistingCodeReference(
                    file_path=file_path,
                    line_range=line_range,
                    description=context.strip(),
                    quality_hint=quality_hint
                ))

        return len(refs) > 0, refs

    def _extract_keywords(self, prompt: str) -> list[str]:
        """Extract important keywords."""
        # Simple keyword extraction (can be improved)
        words = prompt.lower().split()

        # Filter out common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        # Get unique keywords
        return list(set(keywords))

    def _generate_recommendations(
        self,
        intent: TaskIntent,
        complexity: PromptComplexity,
        has_existing: bool,
        word_count: int,
        mentions_compare: bool,
        command: str | None
    ) -> tuple[str, str, str, str]:
        """Generate workflow, enhancement, and preset recommendations."""

        rationale_parts: list[str] = []

        # 1. Workflow recommendation
        if has_existing and (mentions_compare or intent == TaskIntent.VALIDATE):
            workflow = "validate"
            rationale_parts.append("Existing code detected + comparison mentioned → validation workflow")
        elif intent == TaskIntent.BUILD and not has_existing:
            workflow = "build"
            rationale_parts.append("New feature → build workflow")
        elif intent == TaskIntent.OPTIMIZE:
            workflow = "quick-wins"
            rationale_parts.append("Optimization task → quick wins workflow")
        else:
            workflow = intent.value
            rationale_parts.append(f"Intent: {intent.value} → {intent.value} workflow")

        # 2. Enhancement recommendation
        if word_count > 150:
            # Detailed prompt - use quick enhancement
            enhancement = "quick"
            rationale_parts.append(f"Detailed prompt ({word_count} words) → concise enhancement")
        elif word_count < 50:
            # Very short prompt - full enhancement needed
            enhancement = "full"
            rationale_parts.append(f"Brief prompt ({word_count} words) → full enhancement")
        else:
            # Standard prompt - full enhancement
            enhancement = "full"
            rationale_parts.append(f"Standard prompt ({word_count} words) → full enhancement")

        # 3. Preset recommendation
        if workflow == "validate":
            preset = "validation"  # Custom preset for validation
            rationale_parts.append("Validation workflow → validation preset (4 steps)")
        elif workflow == "quick-wins":
            preset = "minimal"
            rationale_parts.append("Quick wins → minimal preset (3 steps)")
        elif complexity == PromptComplexity.MINIMAL:
            preset = "minimal"
            rationale_parts.append("Low complexity → minimal preset (2 steps)")
        elif complexity == PromptComplexity.COMPREHENSIVE:
            preset = "comprehensive"
            rationale_parts.append("High complexity → comprehensive preset (7 steps)")
        else:
            preset = "standard"
            rationale_parts.append("Medium complexity → standard preset (4 steps)")

        rationale = " | ".join(rationale_parts)

        return workflow, enhancement, preset, rationale
