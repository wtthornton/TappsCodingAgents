"""
Intent Parser - Parse natural language input into structured intents.

Maps user commands to agent sequences using keyword matching and
simple NLP patterns.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class IntentType(Enum):
    """Types of user intents."""

    BUILD = "build"
    VALIDATE = "validate"  # Validation workflow for comparing implementations
    REVIEW = "review"
    FIX = "fix"
    TEST = "test"
    EPIC = "epic"
    EXPLORE = "explore"
    REFACTOR = "refactor"
    PLAN_ANALYSIS = "plan-analysis"
    PR = "pr"
    REQUIREMENTS = "requirements"
    BROWNFIELD = "brownfield"
    ENHANCE = "enhance"  # §3.4: first-class *enhance
    BREAKDOWN = "breakdown"  # §3.4: first-class *breakdown
    TODO = "todo"  # §3.5: *todo (Beads-backed)
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Structured intent parsed from user input."""

    type: IntentType
    confidence: float
    parameters: dict[str, Any]
    original_input: str
    compare_to_codebase: bool = False  # Flag for "compare to codebase" intent

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for this intent."""
        if self.type == IntentType.BUILD:
            return ["planner", "architect", "designer", "implementer"]
        elif self.type == IntentType.REVIEW:
            return ["reviewer", "improver"]
        elif self.type == IntentType.FIX:
            return ["debugger", "implementer", "tester"]
        elif self.type == IntentType.TEST:
            return ["tester"]
        elif self.type == IntentType.EPIC:
            return ["epic-orchestrator"]
        elif self.type == IntentType.EXPLORE:
            return ["analyst", "reviewer"]
        elif self.type == IntentType.REFACTOR:
            return ["reviewer", "architect", "implementer", "tester"]
        elif self.type == IntentType.PLAN_ANALYSIS:
            return ["analyst", "architect", "reviewer"]
        elif self.type == IntentType.PR:
            return ["reviewer", "documenter"]
        elif self.type == IntentType.REQUIREMENTS:
            return ["analyst", "planner", "documenter"]
        elif self.type == IntentType.BROWNFIELD:
            return ["brownfield-review"]
        elif self.type == IntentType.ENHANCE:
            return ["enhancer"]
        elif self.type == IntentType.BREAKDOWN:
            return ["planner"]
        elif self.type == IntentType.TODO:
            return ["beads"]
        else:
            return []


class IntentParser:
    """Parse natural language input into structured intents."""

    def __init__(self):
        """Initialize the intent parser with keyword mappings."""
        # Build intent keywords
        self.build_keywords = [
            "build",
            "create",
            "make",
            "generate",
            "add",
            "implement",
            "develop",
            "write",
            "new",
            "feature",
        ]

        # Review intent keywords
        self.review_keywords = [
            "review",
            "check",
            "analyze",
            "inspect",
            "examine",
            "score",
            "quality",
            "audit",
            "assess",
            "evaluate",
            "compare",
            "compare to",
            "match",
            "align with",
            "follow patterns",
        ]

        # Fix intent keywords
        self.fix_keywords = [
            "fix",
            "repair",
            "resolve",
            "debug",
            "error",
            "bug",
            "issue",
            "problem",
            "broken",
            "correct",
        ]

        # Test intent keywords
        self.test_keywords = [
            "test",
            "verify",
            "validate",
            "coverage",
            "testing",
            "tests",
            "unit test",
            "integration test",
        ]

        # Epic intent keywords
        self.epic_keywords = [
            "epic",
            "implement epic",
            "execute epic",
            "run epic",
            "story",
            "stories",
        ]

        # Explore intent keywords
        self.explore_keywords = [
            "explore",
            "understand",
            "navigate",
            "find",
            "discover",
            "overview",
            "codebase",
            "trace",
            "search",
            "locate",
        ]

        # Refactor intent keywords
        self.refactor_keywords = [
            "refactor",
            "modernize",
            "update",
            "improve code",
            "modernize code",
            "legacy",
            "deprecated",
            "upgrade code",
        ]

        # Plan Analysis intent keywords
        self.plan_analysis_keywords = [
            "plan",
            "planning",
            "analyze",
            "analysis",
            "design",
            "proposal",
            "strategy",
            "roadmap",
        ]

        # PR intent keywords
        self.pr_keywords = [
            "pr",
            "pull request",
            "create pr",
            "open pr",
            "merge request",
            "mr",
        ]

        # Requirements intent keywords
        self.requirements_keywords = [
            "requirements",
            "gather requirements",
            "extract requirements",
            "document requirements",
            "analyze requirements",
            "requirements document",
            "requirements gathering",
            "requirements analysis",
        ]

        # Brownfield intent keywords
        self.brownfield_keywords = [
            "brownfield",
            "brownfield review",
            "review brownfield",
            "analyze brownfield",
            "brownfield system",
            "review system",
            "analyze project",
            "create experts",
            "auto experts",
            "expert creation",
            "populate rag",
            "fill rag",
        ]

        # Simple Mode intent keywords
        self.simple_mode_keywords = [
            "@simple-mode",
            "simple mode",
            "use simple mode",
            "simple-mode",
            "@simple_mode",
            "simple_mode",
        ]

    def detect_simple_mode_intent(self, text: str) -> bool:
        """
        Detect if user wants Simple Mode.

        Args:
            text: User input text

        Returns:
            True if Simple Mode intent detected, False otherwise

        Examples:
            >>> parser = IntentParser()
            >>> parser.detect_simple_mode_intent("@simple-mode build feature")
            True
            >>> parser.detect_simple_mode_intent("use simple mode to create api")
            True
            >>> parser.detect_simple_mode_intent("build feature")
            False
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.simple_mode_keywords)

    def parse(self, input_text: str) -> Intent:
        """
        Parse natural language input into a structured intent.

        Args:
            input_text: User's natural language command

        Returns:
            Intent object with type, confidence, and parameters
        """
        input_lower = input_text.lower().strip()

        # Extract parameters
        parameters = self._extract_parameters(input_text)

        # Check for Simple Mode intent first
        if self.detect_simple_mode_intent(input_text):
            # Force Simple Mode workflow
            parameters["force_simple_mode"] = True

        # Check for explicit command patterns
        if input_text.strip().startswith("*epic") or input_text.strip().startswith("@simple-mode *epic"):
            # Extract epic path
            epic_path = input_text.replace("*epic", "").replace("@simple-mode", "").strip()
            if epic_path:
                parameters["epic_path"] = epic_path
            return Intent(
                type=IntentType.EPIC,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        if input_text.strip().startswith("*explore") or input_text.strip().startswith("@simple-mode *explore"):
            return Intent(
                type=IntentType.EXPLORE,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        if input_text.strip().startswith("*validate") or input_text.strip().startswith("@simple-mode *validate"):
            return Intent(
                type=IntentType.VALIDATE,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        if input_text.strip().startswith("*refactor") or input_text.strip().startswith("@simple-mode *refactor"):
            return Intent(
                type=IntentType.REFACTOR,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        if input_text.strip().startswith("*plan") or input_text.strip().startswith("@simple-mode *plan") or "plan-analysis" in input_lower:
            return Intent(
                type=IntentType.PLAN_ANALYSIS,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        if input_text.strip().startswith("*pr") or input_text.strip().startswith("@simple-mode *pr") or "pull request" in input_lower:
            return Intent(
                type=IntentType.PR,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        if input_text.strip().startswith("*brownfield") or input_text.strip().startswith("*brownfield-review") or input_text.strip().startswith("@simple-mode *brownfield"):
            return Intent(
                type=IntentType.BROWNFIELD,
                confidence=1.0,
                parameters=parameters,
                original_input=input_text,
            )

        # *enhance and *breakdown (§3.4)
        if input_text.strip().startswith("*enhance") or input_text.strip().startswith("@simple-mode *enhance"):
            prompt = (parameters.get("description") or re.sub(r"^(@simple-mode\s*)?\*enhance\s*", "", input_text, flags=re.I).strip() or input_text)
            parameters["prompt"] = prompt
            return Intent(type=IntentType.ENHANCE, confidence=1.0, parameters=parameters, original_input=input_text)
        if input_text.strip().startswith("*breakdown") or input_text.strip().startswith("@simple-mode *breakdown"):
            prompt = (parameters.get("description") or re.sub(r"^(@simple-mode\s*)?\*breakdown\s*", "", input_text, flags=re.I).strip() or input_text)
            parameters["prompt"] = prompt
            return Intent(type=IntentType.BREAKDOWN, confidence=1.0, parameters=parameters, original_input=input_text)

        # *todo (§3.5) – remainder forwarded to bd
        if input_text.strip().startswith("*todo") or input_text.strip().startswith("@simple-mode *todo"):
            rest = re.sub(r"^(@simple-mode\s*)?\*todo\s*", "", input_text.strip(), flags=re.I).strip()
            parameters["todo_rest"] = rest
            return Intent(type=IntentType.TODO, confidence=1.0, parameters=parameters, original_input=input_text)

        # Score each intent type
        scores = {
            IntentType.BUILD: self._score_intent(input_lower, self.build_keywords),
            IntentType.REVIEW: self._score_intent(input_lower, self.review_keywords),
            IntentType.FIX: self._score_intent(input_lower, self.fix_keywords),
            IntentType.TEST: self._score_intent(input_lower, self.test_keywords),
            IntentType.EPIC: self._score_intent(input_lower, self.epic_keywords),
            IntentType.EXPLORE: self._score_intent(input_lower, self.explore_keywords),
            IntentType.REFACTOR: self._score_intent(input_lower, self.refactor_keywords),
            IntentType.PLAN_ANALYSIS: self._score_intent(input_lower, self.plan_analysis_keywords),
            IntentType.PR: self._score_intent(input_lower, self.pr_keywords),
            IntentType.REQUIREMENTS: self._score_intent(input_lower, self.requirements_keywords),
            IntentType.BROWNFIELD: self._score_intent(input_lower, self.brownfield_keywords),
        }

        # Find best match
        best_intent = max(scores.items(), key=lambda x: x[1])
        intent_type, confidence = best_intent

        # If confidence is too low, mark as unknown
        if confidence < 0.3:
            intent_type = IntentType.UNKNOWN
            confidence = 0.0

        # Detect "compare to codebase" intent
        compare_to_codebase = False
        compare_phrases = [
            "compare to",
            "compare with",
            "match our",
            "align with",
            "follow patterns",
            "match patterns",
            "compare to codebase",
            "compare to our",
        ]
        if any(phrase in input_lower for phrase in compare_phrases):
            compare_to_codebase = True

        return Intent(
            type=intent_type,
            confidence=confidence,
            parameters=parameters,
            original_input=input_text,
            compare_to_codebase=compare_to_codebase,
        )

    def _score_intent(self, text: str, keywords: list[str]) -> float:
        """
        Score how well text matches an intent based on keywords.

        Args:
            text: Lowercase input text
            keywords: List of keywords for this intent

        Returns:
            Confidence score between 0.0 and 1.0
        """
        matches = sum(1 for keyword in keywords if keyword in text)
        if not matches:
            return 0.0

        # Normalize by number of keywords (max score is 1.0)
        score = min(matches / len(keywords) * 2.0, 1.0)

        # Boost score if keyword appears at start of sentence
        for keyword in keywords:
            if text.startswith(keyword):
                score = min(score + 0.2, 1.0)
                break

        return score

    def _extract_parameters(self, text: str) -> dict[str, Any]:
        """
        Extract parameters from user input.

        Args:
            text: User input text

        Returns:
            Dictionary of extracted parameters
        """
        parameters: dict[str, Any] = {}

        # Extract file paths (quoted strings or common file extensions)
        file_pattern = r'["\']?([^\s"\']+\.(py|ts|js|tsx|jsx|java|go|rs|rb|php|cs|sql|yaml|yml|json|md|txt))["\']?'
        file_matches = re.findall(file_pattern, text, re.IGNORECASE)
        if file_matches:
            parameters["files"] = [match[0] for match in file_matches]

        # Extract quoted descriptions
        quoted_pattern = r'["\']([^"\']+)["\']'
        quoted_matches = re.findall(quoted_pattern, text)
        if quoted_matches:
            parameters["description"] = quoted_matches[0]

        # Extract Epic document paths (epic-*.md or docs/prd/epic-*.md)
        epic_pattern = r'(?:epic-[\w-]+\.md|docs/prd/epic-[\w-]+\.md|[\w/]+epic[\w-]*\.md)'
        epic_matches = re.findall(epic_pattern, text, re.IGNORECASE)
        if epic_matches:
            parameters["epic_path"] = epic_matches[0]

        # Extract feature/functionality mentions
        feature_patterns = [
            r"(?:add|create|build|implement)\s+(?:a\s+)?([a-z\s]+?)(?:\s+for|\s+in|\s+with|$)",
            r"feature[:\s]+([a-z\s]+?)(?:\s+for|\s+in|\s+with|$)",
        ]
        for pattern in feature_patterns:
            match = re.search(pattern, text.lower())
            if match:
                parameters["feature"] = match.group(1).strip()
                break

        return parameters

    def get_agent_sequence(self, intent: Intent) -> list[str]:
        """
        Get the sequence of agents for an intent.

        Args:
            intent: Parsed intent

        Returns:
            List of agent names in execution order
        """
        return intent.get_agent_sequence()

