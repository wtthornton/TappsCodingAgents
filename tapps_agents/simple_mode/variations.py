"""
Command Variation Handling - Synonym mapping for common variations.

Maps different ways users might express the same intent to standard intents.
"""

from .intent_parser import IntentType

# Synonym mappings for each intent type
BUILD_SYNONYMS = [
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
    "scaffold",
    "setup",
    "initialize",
    "start",
]

REVIEW_SYNONYMS = [
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
    "look at",
    "go over",
    "verify",
]

FIX_SYNONYMS = [
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
    "solve",
    "troubleshoot",
    "patch",
]

TEST_SYNONYMS = [
    "test",
    "verify",
    "validate",
    "coverage",
    "testing",
    "tests",
    "unit test",
    "integration test",
    "e2e test",
    "end-to-end test",
]


def normalize_command(command: str) -> str:
    """
    Normalize a command by expanding synonyms.

    Args:
        command: User's command text

    Returns:
        Normalized command with synonyms expanded
    """
    command_lower = command.lower()

    # Replace synonyms with primary keywords
    for synonym in BUILD_SYNONYMS:
        if synonym in command_lower and "build" not in command_lower:
            command_lower = command_lower.replace(synonym, "build", 1)
            break

    for synonym in REVIEW_SYNONYMS:
        if synonym in command_lower and "review" not in command_lower:
            command_lower = command_lower.replace(synonym, "review", 1)
            break

    for synonym in FIX_SYNONYMS:
        if synonym in command_lower and "fix" not in command_lower:
            command_lower = command_lower.replace(synonym, "fix", 1)
            break

    for synonym in TEST_SYNONYMS:
        if synonym in command_lower and "test" not in command_lower:
            command_lower = command_lower.replace(synonym, "test", 1)
            break

    return command_lower


def get_intent_synonyms(intent_type: IntentType) -> list[str]:
    """
    Get synonyms for an intent type.

    Args:
        intent_type: Intent type

    Returns:
        List of synonym keywords
    """
    if intent_type == IntentType.BUILD:
        return BUILD_SYNONYMS
    elif intent_type == IntentType.REVIEW:
        return REVIEW_SYNONYMS
    elif intent_type == IntentType.FIX:
        return FIX_SYNONYMS
    elif intent_type == IntentType.TEST:
        return TEST_SYNONYMS
    else:
        return []

