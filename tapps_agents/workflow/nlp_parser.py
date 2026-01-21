"""
Natural Language Parser for Workflow Triggers

Parses natural language input to extract workflow intent and match workflows.
Epic 9 / Story 9.1: Natural Language Parser Foundation
Epic 9 / Story 9.2: Workflow Intent Detection
"""

import difflib
import re
from dataclasses import dataclass, field
from typing import Any

from .preset_loader import PRESET_ALIASES, PresetLoader


@dataclass
class WorkflowIntent:
    """Parsed workflow intent result."""

    intent_type: str  # "workflow_trigger", "workflow_query", "unknown"
    workflow_name: str | None  # Matched workflow name (canonical)
    confidence: float  # 0.0 to 1.0
    aliases_matched: list[str]  # Aliases that matched
    raw_input: str  # Original input
    match_type: str | None = None  # "exact", "partial", "fuzzy", "alias", "synonym"
    alternative_matches: list[tuple[str, float]] | None = None  # (workflow_name, confidence)


@dataclass
class WorkflowIntentResult:
    """Complete intent detection result with action verb and parameters."""

    action_verb: str | None  # "run", "execute", "start", "trigger", etc.
    workflow_type: str | None  # Detected workflow type/category
    workflow_name: str | None  # Matched workflow name
    parameters: dict[str, Any] = field(default_factory=dict)  # Extracted parameters
    ambiguity_flag: bool = False  # True if multiple workflows match
    suggestions: list[str] = field(default_factory=list)  # Alternative workflows
    confidence: float = 0.0  # Overall confidence score
    intent_confidence: float = 0.0  # Confidence in intent detection
    workflow_confidence: float = 0.0  # Confidence in workflow matching


# Workflow synonyms for natural language matching
WORKFLOW_SYNONYMS: dict[str, list[str]] = {
    "full-sdlc": [
        "full sdlc",
        "full software development lifecycle",
        "complete sdlc",
        "enterprise workflow",
        "full pipeline",
        "complete workflow",
    ],
    "rapid-dev": [
        "rapid development",
        "rapid dev",
        "quick development",
        "fast development",
        "feature development",
        "sprint workflow",
    ],
    "fix": [
        "fix workflow",
        "maintenance workflow",
        "bug fix",
        "bug fixing",
        "refactoring",
        "technical debt",
        "code improvement",
        "quick fix",
        "hotfix",
        "urgent fix",
        "emergency fix",
        "critical fix",
        "patch",
    ],
    "quality": [
        "quality improvement",
        "code quality",
        "quality workflow",
        "code review",
        "quality check",
    ],
    "brownfield-analysis": [
        "brownfield",
        "brownfield analysis",
        "existing codebase",
        "legacy analysis",
    ],
}


class NaturalLanguageParser:
    """Parses natural language input to extract workflow intent."""

    def __init__(self, preset_loader: PresetLoader | None = None):
        """
        Initialize natural language parser.

        Args:
            preset_loader: PresetLoader instance (creates new one if None)
        """
        self.preset_loader = preset_loader or PresetLoader()
        self._workflow_names_cache: list[str] | None = None

    def _get_workflow_names(self) -> list[str]:
        """Get list of available workflow names (cached)."""
        if self._workflow_names_cache is None:
            presets = self.preset_loader.list_presets()
            self._workflow_names_cache = list(presets.keys())
        return self._workflow_names_cache

    def parse(self, input_text: str) -> WorkflowIntent:
        """
        Parse natural language input to extract workflow intent.

        Args:
            input_text: Natural language input from user

        Returns:
            WorkflowIntent with parsed results
        """
        if not input_text or not input_text.strip():
            return WorkflowIntent(
                intent_type="unknown",
                workflow_name=None,
                confidence=0.0,
                aliases_matched=[],
                raw_input=input_text,
            )

        normalized = input_text.lower().strip()

        # Try exact match first
        result = self._try_exact_match(normalized)
        if result and result.confidence >= 0.9:
            return result

        # Try alias match
        result = self._try_alias_match(normalized)
        if result and result.confidence >= 0.8:
            return result

        # Try synonym match
        result = self._try_synonym_match(normalized)
        if result and result.confidence >= 0.7:
            return result

        # Try partial match
        result = self._try_partial_match(normalized)
        if result and result.confidence >= 0.6:
            return result

        # Try fuzzy match
        result = self._try_fuzzy_match(normalized)
        if result:
            return result

        # No match found
        return WorkflowIntent(
            intent_type="unknown",
            workflow_name=None,
            confidence=0.0,
            aliases_matched=[],
            raw_input=input_text,
        )

    def _try_exact_match(self, normalized: str) -> WorkflowIntent | None:
        """Try exact match against workflow names and aliases."""
        workflow_names = self._get_workflow_names()

        # Check exact match against workflow names
        for workflow_name in workflow_names:
            if normalized == workflow_name.lower():
                return WorkflowIntent(
                    intent_type="workflow_trigger",
                    workflow_name=workflow_name,
                    confidence=1.0,
                    aliases_matched=[workflow_name],
                    raw_input=normalized,
                    match_type="exact",
                )

        # Check exact match against aliases
        for alias, workflow_name in PRESET_ALIASES.items():
            if normalized == alias.lower():
                return WorkflowIntent(
                    intent_type="workflow_trigger",
                    workflow_name=workflow_name,
                    confidence=0.95,
                    aliases_matched=[alias],
                    raw_input=normalized,
                    match_type="exact",
                )

        return None

    def _try_alias_match(self, normalized: str) -> WorkflowIntent | None:
        """Try matching against aliases (substring)."""
        best_match: tuple[str, str, float] | None = None

        for alias, workflow_name in PRESET_ALIASES.items():
            alias_lower = alias.lower()
            if alias_lower in normalized or normalized in alias_lower:
                # Calculate confidence based on match quality
                if normalized == alias_lower:
                    confidence = 0.95
                elif normalized.startswith(alias_lower) or alias_lower.startswith(normalized):
                    confidence = 0.85
                else:
                    confidence = 0.75

                if best_match is None or confidence > best_match[2]:
                    best_match = (alias, workflow_name, confidence)

        if best_match:
            alias, workflow_name, confidence = best_match
            return WorkflowIntent(
                intent_type="workflow_trigger",
                workflow_name=workflow_name,
                confidence=confidence,
                aliases_matched=[alias],
                raw_input=normalized,
                match_type="alias",
            )

        return None

    def _try_synonym_match(self, normalized: str) -> WorkflowIntent | None:
        """Try matching against synonyms."""
        best_match: tuple[str, float] | None = None

        for workflow_name, synonyms in WORKFLOW_SYNONYMS.items():
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                if synonym_lower in normalized or normalized in synonym_lower:
                    # Calculate confidence based on match quality
                    if normalized == synonym_lower:
                        confidence = 0.9
                    elif normalized.startswith(synonym_lower) or synonym_lower.startswith(normalized):
                        confidence = 0.8
                    else:
                        confidence = 0.7

                    if best_match is None or confidence > best_match[1]:
                        best_match = (workflow_name, confidence)

        if best_match:
            workflow_name, confidence = best_match
            return WorkflowIntent(
                intent_type="workflow_trigger",
                workflow_name=workflow_name,
                confidence=confidence,
                aliases_matched=[],
                raw_input=normalized,
                match_type="synonym",
            )

        return None

    def _try_partial_match(self, normalized: str) -> WorkflowIntent | None:
        """Try partial/substring matching."""
        workflow_names = self._get_workflow_names()
        best_match: tuple[str, float] | None = None

        for workflow_name in workflow_names:
            workflow_lower = workflow_name.lower()
            # Check if normalized contains workflow name or vice versa
            if workflow_lower in normalized:
                # Calculate confidence based on how much of the workflow name matches
                match_ratio = len(workflow_lower) / len(normalized) if normalized else 0
                confidence = min(0.8, 0.5 + match_ratio * 0.3)

                if best_match is None or confidence > best_match[1]:
                    best_match = (workflow_name, confidence)
            elif normalized in workflow_lower:
                # Normalized is substring of workflow name
                match_ratio = len(normalized) / len(workflow_lower) if workflow_lower else 0
                confidence = min(0.75, 0.4 + match_ratio * 0.35)

                if best_match is None or confidence > best_match[1]:
                    best_match = (workflow_name, confidence)

        if best_match:
            workflow_name, confidence = best_match
            return WorkflowIntent(
                intent_type="workflow_trigger",
                workflow_name=workflow_name,
                confidence=confidence,
                aliases_matched=[],
                raw_input=normalized,
                match_type="partial",
            )

        return None

    def _try_fuzzy_match(self, normalized: str) -> WorkflowIntent | None:
        """Try fuzzy matching using string similarity."""
        workflow_names = self._get_workflow_names()
        best_matches: list[tuple[str, float]] = []

        for workflow_name in workflow_names:
            # Calculate similarity using SequenceMatcher
            similarity = difflib.SequenceMatcher(None, normalized, workflow_name.lower()).ratio()

            if similarity >= 0.5:  # Minimum threshold for fuzzy match
                best_matches.append((workflow_name, similarity))

        # Also check aliases
        for alias, workflow_name in PRESET_ALIASES.items():
            similarity = difflib.SequenceMatcher(None, normalized, alias.lower()).ratio()

            if similarity >= 0.5:
                best_matches.append((workflow_name, similarity))

        if not best_matches:
            return None

        # Sort by similarity (descending)
        best_matches.sort(key=lambda x: x[1], reverse=True)

        # Get best match
        best_workflow, best_confidence = best_matches[0]

        # Get alternative matches (top 3)
        alternatives = best_matches[1:4] if len(best_matches) > 1 else None

        return WorkflowIntent(
            intent_type="workflow_trigger",
            workflow_name=best_workflow,
            confidence=min(0.7, best_confidence * 0.9),  # Cap fuzzy match confidence
            aliases_matched=[],
            raw_input=normalized,
            match_type="fuzzy",
            alternative_matches=alternatives,
        )

    # Story 9.2: Intent Detection Methods

    # Action verbs that indicate workflow execution intent
    ACTION_VERBS = [
        "run",
        "execute",
        "start",
        "trigger",
        "launch",
        "begin",
        "perform",
        "do",
        "create",
        "build",
    ]

    # Action verb variations and phrases
    ACTION_PHRASES = [
        r"i want to (\w+)",
        r"please (\w+)",
        r"can you (\w+)",
        r"could you (\w+)",
        r"let's (\w+)",
        r"let me (\w+)",
    ]

    # Workflow type keywords
    WORKFLOW_TYPE_KEYWORDS = {
        "rapid": ["rapid", "quick", "fast", "feature", "sprint", "dev"],
        "full": ["full", "enterprise", "complete", "sdlc", "lifecycle", "all"],
        "fix": ["fix", "maintenance", "bug", "repair", "patch"],
        "quality": ["quality", "improve", "review", "refactor", "clean"],
        "hotfix": ["hotfix", "urgent", "emergency", "critical", "patch"],
        "enterprise": ["enterprise", "full", "complete", "sdlc"],
        "feature": ["feature", "rapid", "quick", "new"],
    }

    def detect_intent(self, input_text: str) -> WorkflowIntentResult:
        """
        Detect complete workflow intent including action verb and parameters.

        Args:
            input_text: Natural language input from user

        Returns:
            WorkflowIntentResult with complete intent information
        """
        if not input_text or not input_text.strip():
            return WorkflowIntentResult(
                action_verb=None,
                workflow_type=None,
                workflow_name=None,
                confidence=0.0,
            )

        normalized = input_text.lower().strip()

        # Detect action verb
        action_verb = self._detect_action_verb(normalized)
        intent_confidence = 0.9 if action_verb else 0.5

        # Detect workflow type
        workflow_type = self._detect_workflow_type(normalized)

        # Parse workflow name using base parser
        workflow_intent = self.parse(input_text)
        workflow_confidence = workflow_intent.confidence

        # Extract parameters
        parameters = self._extract_parameters(normalized, input_text)

        # Detect ambiguity
        ambiguity_flag = self._detect_ambiguity(workflow_intent)

        # Generate suggestions
        suggestions = self._generate_suggestions(workflow_intent)

        # Calculate overall confidence
        overall_confidence = (intent_confidence * 0.3 + workflow_confidence * 0.7) if workflow_intent.workflow_name else intent_confidence * 0.5

        return WorkflowIntentResult(
            action_verb=action_verb,
            workflow_type=workflow_type,
            workflow_name=workflow_intent.workflow_name,
            parameters=parameters,
            ambiguity_flag=ambiguity_flag,
            suggestions=suggestions,
            confidence=overall_confidence,
            intent_confidence=intent_confidence,
            workflow_confidence=workflow_confidence,
        )

    def _detect_action_verb(self, normalized: str) -> str | None:
        """Detect action verb in input."""
        # Check for direct verb matches
        for verb in self.ACTION_VERBS:
            # Match verb as whole word
            pattern = r"\b" + re.escape(verb) + r"\b"
            if re.search(pattern, normalized):
                return verb

        # Check for action phrases
        for phrase_pattern in self.ACTION_PHRASES:
            match = re.search(phrase_pattern, normalized)
            if match:
                verb = match.group(1)
                if verb in self.ACTION_VERBS:
                    return verb

        return None

    def _detect_workflow_type(self, normalized: str) -> str | None:
        """Detect workflow type from keywords."""
        best_match: tuple[str, int] | None = None

        for workflow_type, keywords in self.WORKFLOW_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in normalized)
            if score > 0:
                if best_match is None or score > best_match[1]:
                    best_match = (workflow_type, score)

        return best_match[0] if best_match else None

    def _extract_parameters(self, normalized: str, original: str) -> dict[str, Any]:
        """Extract parameters from input (target file, options)."""
        parameters: dict[str, Any] = {}

        # Extract target file
        # Patterns: "on file.py", "for example.py", "targeting bug.py", "file: example.py"
        file_patterns = [
            r"(?:on|for|targeting|file:?)\s+([^\s]+\.(?:py|js|ts|java|go|rs|cpp|c|h|md|yaml|yml|json|txt))",
            r"([^\s]+\.(?:py|js|ts|java|go|rs|cpp|c|h|md|yaml|yml|json|txt))",
        ]

        for pattern in file_patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                file_path = match.group(1)
                parameters["target_file"] = file_path
                break

        # Extract options/flags
        if "auto" in normalized or "automatic" in normalized:
            parameters["auto"] = True

        if "skip" in normalized and "test" in normalized:
            parameters["skip_tests"] = True

        if "prompt" in normalized:
            # Try to extract prompt text
            prompt_match = re.search(r'prompt[:\s]+["\']?([^"\']+)["\']?', normalized)
            if prompt_match:
                parameters["prompt"] = prompt_match.group(1)

        return parameters

    def _detect_ambiguity(self, workflow_intent: WorkflowIntent) -> bool:
        """Detect if request is ambiguous (multiple matches with similar confidence)."""
        if not workflow_intent.workflow_name:
            return False

        # Check if there are alternative matches with similar confidence
        if workflow_intent.alternative_matches:
            best_confidence = workflow_intent.confidence
            for _, alt_confidence in workflow_intent.alternative_matches:
                # If alternative is within 20% of best match, consider ambiguous
                if abs(best_confidence - alt_confidence) < 0.2:
                    return True

        # Low confidence itself indicates potential ambiguity
        if workflow_intent.confidence < 0.7:
            return True

        return False

    def _generate_suggestions(self, workflow_intent: WorkflowIntent) -> list[str]:
        """Generate workflow suggestions based on intent."""
        suggestions: list[str] = []

        if workflow_intent.alternative_matches:
            for workflow_name, _ in workflow_intent.alternative_matches[:3]:
                suggestions.append(workflow_name)

        # If no match, suggest all available workflows
        if not workflow_intent.workflow_name:
            workflow_names = self._get_workflow_names()
            suggestions.extend(workflow_names[:5])

        return suggestions

