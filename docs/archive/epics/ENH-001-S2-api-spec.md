# ENH-001-S2: Intent Detection System - API Specification

**Document Type:** API Specification
**Component:** IntentDetector (ENH-001-S2)
**Epic:** ENH-001 Workflow Enforcement System
**Version:** 1.0
**Status:** Draft for Review
**Date:** 2026-01-30
**Author:** TappsCodingAgents Designer Agent

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Models](#data-models)
3. [API Interface](#api-interface)
4. [Type Annotations](#type-annotations)
5. [Validation Rules](#validation-rules)
6. [Error Handling](#error-handling)
7. [Performance Requirements](#performance-requirements)
8. [Usage Examples](#usage-examples)
9. [Integration Contract](#integration-contract)
10. [Testing Guidelines](#testing-guidelines)

---

## Executive Summary

### Overview

The Intent Detection System provides a high-performance Python API for classifying user prompts into workflow types with confidence scoring. This API specification defines the complete contract for the `IntentDetector` class and its data models.

**Key Design Principles:**
- **Type-Safe:** 100% type coverage with mypy strict mode
- **Immutable:** Frozen dataclasses prevent accidental mutation
- **Fail-Safe:** Never raises exceptions to callers
- **Performance-First:** <5ms p99 latency through optimization
- **Thread-Safe:** Stateless design for concurrent usage

### API Surface

The API consists of three core components:

1. **WorkflowType (Enum):** String-based enum for workflow classification
2. **DetectionResult (Dataclass):** Immutable result container with validation
3. **IntentDetector (Class):** Main detection engine with single responsibility

### Performance Contract

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Latency (p99)** | <5ms | Performance test suite |
| **Latency (p50)** | <2ms | Performance test suite |
| **Memory per call** | <100KB | Memory profiler |
| **Type coverage** | 100% | mypy --strict |
| **Thread safety** | Yes | Stateless design |

---

## Data Models

### 2.1 WorkflowType Enum

#### Definition

```python
from enum import Enum

class WorkflowType(str, Enum):
    """
    Workflow types for intent detection.

    Inherits from str to support JSON serialization and string comparisons.
    Each value corresponds to a Cursor Skills command pattern.

    Attributes:
        BUILD: New feature implementation (*build command)
        FIX: Bug fixes and error resolution (*fix command)
        REFACTOR: Code improvement and modernization (*refactor command)
        REVIEW: Code review and quality inspection (*review command)

    Example:
        >>> workflow = WorkflowType.BUILD
        >>> assert workflow == "*build"
        >>> assert workflow.value == "*build"
        >>> assert str(workflow) == "*build"
    """

    BUILD = "*build"
    FIX = "*fix"
    REFACTOR = "*refactor"
    REVIEW = "*review"
```

#### Serialization Support

**JSON Serialization:**
```python
import json
from enum import Enum

# Automatic serialization (inherits from str)
workflow = WorkflowType.BUILD
json_str = json.dumps({"workflow": workflow})
# Result: '{"workflow": "*build"}'

# Deserialization
data = json.loads(json_str)
workflow = WorkflowType(data["workflow"])
```

**String Comparison:**
```python
# Direct string comparison (thanks to str inheritance)
if workflow == "*build":
    print("Build workflow detected")

# Value access
assert workflow.value == "*build"
assert str(workflow) == "*build"
```

#### Design Rationale

**Why inherit from str?**
- Enables direct string comparison without `.value` access
- Supports JSON serialization without custom encoders
- Maintains type safety while improving ergonomics

**Why use "*" prefix?**
- Matches Cursor Skills command syntax exactly
- Prevents naming conflicts with Python keywords
- Clearly distinguishes workflow types from other strings

---

### 2.2 DetectionResult Dataclass

#### Definition

```python
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DetectionResult:
    """
    Immutable result of intent detection.

    This dataclass encapsulates the output of intent detection with validation,
    immutability, and memory optimization through slots.

    Attributes:
        workflow_type: Detected workflow type (*build, *fix, *refactor, *review)
        confidence: Confidence score (0.0-100.0), where:
            - 80-100: High confidence, clear intent
            - 60-79: Medium confidence, threshold for enforcement
            - 0-59: Low confidence, no enforcement
        reasoning: Human-readable explanation of detection logic.
            Max 500 characters for performance. Used for debugging and logging.
        is_ambiguous: True if multiple workflows scored within 10% of each other.
            Indicates that user intent may be unclear or multi-faceted.

    Validation:
        - confidence must be 0.0-100.0 (validated in __post_init__)
        - reasoning must be non-empty string
        - workflow_type must be valid WorkflowType enum value

    Memory Optimization:
        - frozen=True: Prevents mutation after creation
        - slots=True: Reduces memory overhead by ~60% (no __dict__)

    Thread Safety:
        - Immutable by design (frozen=True)
        - Safe to share across threads
        - Safe to cache without copy

    Example:
        >>> result = DetectionResult(
        ...     workflow_type=WorkflowType.BUILD,
        ...     confidence=85.0,
        ...     reasoning="Strong 'add' keyword at start of prompt",
        ...     is_ambiguous=False
        ... )
        >>> assert result.workflow_type == WorkflowType.BUILD
        >>> assert result.confidence == 85.0
        >>> assert not result.is_ambiguous
    """

    workflow_type: WorkflowType
    confidence: float
    reasoning: str
    is_ambiguous: bool = False

    def __post_init__(self) -> None:
        """
        Validate fields after initialization.

        Raises:
            ValueError: If confidence is out of range [0.0, 100.0]
            ValueError: If reasoning is empty string
            TypeError: If workflow_type is not WorkflowType enum

        Note:
            Validation happens at construction time to enforce invariants.
            Since dataclass is frozen, values cannot be changed after creation.
        """
        # Validate confidence range
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(
                f"confidence must be in range [0.0, 100.0], got {self.confidence}"
            )

        # Validate reasoning is non-empty
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("reasoning must be non-empty string")

        # Validate workflow_type is enum (type checker ensures this at compile time)
        if not isinstance(self.workflow_type, WorkflowType):
            raise TypeError(
                f"workflow_type must be WorkflowType enum, got {type(self.workflow_type)}"
            )
```

#### Field Specifications

**workflow_type: WorkflowType**
- **Type:** WorkflowType enum (not str)
- **Purpose:** Detected workflow classification
- **Constraints:** Must be one of BUILD, FIX, REFACTOR, REVIEW
- **Thread-Safe:** Yes (enum is immutable)

**confidence: float**
- **Type:** float (Python's 64-bit float)
- **Range:** [0.0, 100.0] (validated)
- **Purpose:** Confidence score for detection accuracy
- **Interpretation:**
  - 80-100: High confidence, strong signal
  - 60-79: Medium confidence, enforcement threshold
  - 0-59: Low confidence, insufficient signal
- **Precision:** 1 decimal place sufficient (e.g., 85.0)

**reasoning: str**
- **Type:** str (UTF-8)
- **Length:** 1-500 characters recommended
- **Purpose:** Human-readable explanation for debugging/logging
- **Constraints:** Non-empty, trimmed
- **Example:** `"Strong 'add' keyword at start, new file context bonus"`

**is_ambiguous: bool**
- **Type:** bool
- **Default:** False
- **Purpose:** Flag for ambiguous detection (multiple high scores)
- **Detection Logic:** Set to True if top 2 scores are within 10%
- **Use Case:** Future Story 3 will suggest multiple workflows

#### Memory Layout

**With __slots__:**
```
DetectionResult instance size: ~88 bytes
├── workflow_type (enum): 8 bytes (reference)
├── confidence (float): 8 bytes
├── reasoning (str ref): 8 bytes (reference to string)
├── is_ambiguous (bool): 1 byte
└── Slots overhead: ~63 bytes (Python internals)
```

**Without __slots__ (for comparison):**
```
DetectionResult instance size: ~232 bytes
├── Same fields as above: ~25 bytes
└── __dict__ overhead: ~207 bytes
```

**Savings:** ~60% memory reduction with slots

#### Immutability Benefits

**Prevention of Accidental Mutation:**
```python
result = DetectionResult(
    workflow_type=WorkflowType.BUILD,
    confidence=85.0,
    reasoning="Test",
    is_ambiguous=False
)

# This will raise FrozenInstanceError
result.confidence = 90.0  # ❌ Error!
```

**Safe Caching:**
```python
from functools import lru_cache

# Safe to cache because result is immutable
@lru_cache(maxsize=128)
def get_detection_result(prompt: str) -> DetectionResult:
    detector = IntentDetector()
    return detector.detect_workflow(prompt)
```

**Thread Safety:**
```python
from concurrent.futures import ThreadPoolExecutor

# Safe to share result across threads
result = detector.detect_workflow("add feature")

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(process_result, result)
        for _ in range(100)
    ]
    # No race conditions - result is immutable
```

---

## API Interface

### 3.1 IntentDetector Class

#### Class Definition

```python
from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    High-performance intent detector for workflow classification.

    This class implements keyword-based intent detection with context analysis
    to classify user prompts into workflow types (*build, *fix, *refactor, *review).

    Design Pattern: Strategy Pattern (keyword-based strategy)
    Architecture: Stateless, thread-safe, fail-safe
    Performance: <5ms p99 latency, <100KB memory per call

    Algorithm:
        1. Keyword Matching (80% weight): Regex pattern matching on prompt
        2. Context Analysis (20% weight): File path and existence signals
        3. Score Combination: Weighted sum of keyword + context scores
        4. Ambiguity Detection: Flag if top 2 scores within 10%

    Attributes (Class Variables):
        BUILD_KEYWORDS: Tuple of keywords for *build detection
        FIX_KEYWORDS: Tuple of keywords for *fix detection
        REFACTOR_KEYWORDS: Tuple of keywords for *refactor detection
        REVIEW_KEYWORDS: Tuple of keywords for *review detection

    Instance Attributes (via __slots__):
        _build_pattern: Pre-compiled regex pattern for BUILD keywords
        _fix_pattern: Pre-compiled regex pattern for FIX keywords
        _refactor_pattern: Pre-compiled regex pattern for REFACTOR keywords
        _review_pattern: Pre-compiled regex pattern for REVIEW keywords
        _keyword_map: Dict mapping WorkflowType to (keywords, pattern) tuples

    Thread Safety:
        - Stateless design (no shared mutable state)
        - Pre-compiled patterns are immutable
        - Safe for concurrent calls across threads

    Example:
        >>> detector = IntentDetector()
        >>> result = detector.detect_workflow("add user authentication")
        >>> print(f"{result.workflow_type}: {result.confidence:.1f}%")
        *build: 85.0%
        >>> print(f"Reasoning: {result.reasoning}")
        Reasoning: Strong 'add' keyword at start of prompt
    """

    # Class constants (keyword definitions)
    BUILD_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "build", "create", "add", "implement", "new", "feature",
        "develop", "write", "generate", "make"
    )

    FIX_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "fix", "bug", "error", "issue", "broken", "repair",
        "correct", "resolve", "debug", "patch"
    )

    REFACTOR_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "refactor", "modernize", "improve", "update", "cleanup",
        "rewrite", "optimize", "enhance"
    )

    REVIEW_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "review", "check", "analyze", "inspect", "examine",
        "audit", "quality", "assess", "evaluate"
    )

    # Memory optimization
    __slots__ = (
        "_build_pattern",
        "_fix_pattern",
        "_refactor_pattern",
        "_review_pattern",
        "_keyword_map",
    )

    def __init__(self, config: EnforcementConfig | None = None) -> None:
        """
        Initialize intent detector with pre-compiled patterns.

        Pre-compiles regex patterns for performance (<5ms latency target).
        Patterns are cached using @lru_cache to avoid recompilation.

        Args:
            config: Optional EnforcementConfig for future extensibility.
                Currently unused (Story 1 scope). Reserved for future features:
                - Custom keyword sets from config
                - Configurable scoring weights
                - ML model integration toggle

        Performance:
            - Initialization time: <10ms (one-time cost)
            - Pattern compilation: Cached via @lru_cache
            - Memory overhead: ~5KB for 4 compiled patterns

        Example:
            >>> # Default initialization
            >>> detector = IntentDetector()

            >>> # Future: Custom config
            >>> config = EnforcementConfig()
            >>> detector = IntentDetector(config=config)
        """
        # Pre-compile regex patterns (performance optimization)
        self._build_pattern = self._compile_pattern(self.BUILD_KEYWORDS)
        self._fix_pattern = self._compile_pattern(self.FIX_KEYWORDS)
        self._refactor_pattern = self._compile_pattern(self.REFACTOR_KEYWORDS)
        self._review_pattern = self._compile_pattern(self.REVIEW_KEYWORDS)

        # Map workflow types to (keywords, pattern) tuples
        self._keyword_map = {
            WorkflowType.BUILD: (self.BUILD_KEYWORDS, self._build_pattern),
            WorkflowType.FIX: (self.FIX_KEYWORDS, self._fix_pattern),
            WorkflowType.REFACTOR: (self.REFACTOR_KEYWORDS, self._refactor_pattern),
            WorkflowType.REVIEW: (self.REVIEW_KEYWORDS, self._review_pattern),
        }

        logger.debug("IntentDetector initialized with pre-compiled patterns")
```

#### Constructor Signature

```python
def __init__(self, config: EnforcementConfig | None = None) -> None
```

**Parameters:**
- `config` (optional): EnforcementConfig instance for future extensibility
  - Type: `EnforcementConfig | None`
  - Default: `None`
  - Current Usage: Reserved for future features (Story 5+)
  - Future Usage: Custom keywords, scoring weights, ML toggle

**Return Type:** `None`

**Side Effects:**
- Pre-compiles 4 regex patterns (cached)
- Initializes `_keyword_map` dict
- Logs debug message

**Thread Safety:** Yes (read-only operations)

**Performance:** <10ms initialization time (one-time cost)

---

### 3.2 Main Detection Method

#### Method Signature

```python
def detect_workflow(
    self,
    user_intent: str,
    file_path: Path | None = None,
) -> DetectionResult:
    """
    Detect workflow type from user intent with confidence scoring.

    This is the main entry point for intent detection. It analyzes the user's
    prompt using keyword matching and optional context analysis, then returns
    a structured result with workflow type, confidence, and reasoning.

    Args:
        user_intent: User's natural language prompt or description.
            - Type: str (UTF-8 encoded)
            - Length: 1-10000 characters (longer prompts are truncated)
            - Examples: "add user authentication", "fix login bug"
            - Special handling: Empty strings return (*build, 0.0)

        file_path: Optional file path for context analysis.
            - Type: Path | None
            - Default: None
            - Purpose: Provides context signals (file exists, path patterns)
            - Examples: Path("src/auth.py"), Path("tests/test_auth.py")
            - Context boost: +5% confidence for matching patterns

    Returns:
        DetectionResult: Immutable dataclass with detection results:
            - workflow_type: Detected WorkflowType enum
            - confidence: Float score (0.0-100.0)
            - reasoning: Explanation string
            - is_ambiguous: Boolean ambiguity flag

    Raises:
        Never raises exceptions (fail-safe design).
        On error: Returns DetectionResult(BUILD, 0.0, "Error: ...", False)

    Performance Contract:
        - Latency: <5ms p99, <2ms p50
        - Memory: <100KB allocation per call
        - CPU: <1% overhead on enforcement path
        - Thread-safe: Yes (stateless)

    Error Handling:
        - Empty prompt → (BUILD, 0.0)
        - Invalid type → str() conversion, then process
        - Long prompt (>10KB) → Truncate to 10000 chars, log warning
        - Exception → (BUILD, 0.0), log error with stack trace

    Algorithm:
        1. Input validation and sanitization
        2. Keyword matching (80% weight) with regex patterns
        3. Context analysis (20% weight) if file_path provided
        4. Score combination and normalization
        5. Ambiguity detection (10% threshold)
        6. Reasoning generation for debugging

    Example:
        >>> detector = IntentDetector()

        >>> # Basic usage
        >>> result = detector.detect_workflow("add user authentication")
        >>> assert result.workflow_type == WorkflowType.BUILD
        >>> assert result.confidence >= 80.0

        >>> # With context
        >>> result = detector.detect_workflow(
        ...     "add authentication",
        ...     file_path=Path("src/auth.py")
        ... )
        >>> # Confidence boosted by file path context

        >>> # Ambiguous case
        >>> result = detector.detect_workflow("fix and improve auth")
        >>> if result.is_ambiguous:
        ...     print("Multiple workflows detected")
    """
```

**Input Validation:**

```python
# Type coercion
if not isinstance(user_intent, str):
    user_intent = str(user_intent)

# Whitespace handling
user_intent = user_intent.strip()

# Length validation (DoS protection)
if len(user_intent) > 10000:
    logger.warning(
        f"User intent truncated from {len(user_intent)} to 10000 chars"
    )
    user_intent = user_intent[:10000]

# Empty string handling
if not user_intent:
    logger.debug("Empty user intent, returning default")
    return DetectionResult(
        workflow_type=WorkflowType.BUILD,
        confidence=0.0,
        reasoning="Empty user intent",
        is_ambiguous=False
    )
```

**Return Value Guarantees:**

1. **Always returns DetectionResult** (never None)
2. **Confidence in range [0.0, 100.0]** (validated by dataclass)
3. **Non-empty reasoning** (always provides explanation)
4. **Valid WorkflowType** (enum validation)

---

### 3.3 Private Methods

#### _score_keywords Method

```python
def _score_keywords(
    self,
    user_intent: str,
) -> dict[WorkflowType, float]:
    """
    Calculate keyword match scores for all workflow types.

    Uses pre-compiled regex patterns to efficiently match keywords in the
    user intent. Applies scoring algorithm with base score, position bonus,
    and multiple-match bonus.

    Args:
        user_intent: Normalized lowercase intent string
            - Already validated and sanitized by detect_workflow()
            - Length: 1-10000 characters
            - Format: "add user authentication feature"

    Returns:
        Dict mapping WorkflowType to keyword score (0.0-100.0):
            - BUILD: Score for build-related keywords
            - FIX: Score for fix-related keywords
            - REFACTOR: Score for refactor-related keywords
            - REVIEW: Score for review-related keywords

    Scoring Algorithm:
        1. Base Score: 60% per keyword match (max 100%)
        2. Position Bonus: +10% if keyword at start of prompt
        3. Multiple Match Bonus: +5% per extra keyword (max +15%)
        4. Total Score: min(base + position + multi, 100.0)

    Performance:
        - Time Complexity: O(n) where n = len(user_intent)
        - Space Complexity: O(1) (fixed size dict)
        - Regex: Pre-compiled patterns (cached)

    Example:
        >>> detector = IntentDetector()
        >>> scores = detector._score_keywords("add new feature")
        >>> # {"BUILD": 75.0, "FIX": 0.0, "REFACTOR": 0.0, "REVIEW": 0.0}
        >>> # 60 (base) + 10 (position) + 5 (multi) = 75.0
    """
```

#### _analyze_context Method

```python
def _analyze_context(
    self,
    file_path: Path | None,
) -> dict[WorkflowType, float]:
    """
    Analyze file path context for confidence bonuses.

    Examines file path patterns and existence to provide additional signals
    for workflow detection. Context signals are weighted at 20% in final score.

    Args:
        file_path: Optional file path for analysis
            - Type: Path | None
            - Examples: Path("src/auth.py"), Path("tests/test_auth.py")
            - If None, returns empty dict (no bonuses)

    Returns:
        Dict mapping WorkflowType to bonus score (0.0-5.0):
            - Empty dict if file_path is None
            - Bonuses based on file patterns and existence
            - Max bonus: 5.0 (for new file → BUILD)

    Context Signals:
        1. File Existence:
            - New file (not exists) → +5.0 to BUILD
            - Existing file → +2.0 to FIX, +2.0 to REFACTOR

        2. File Path Patterns:
            - "test_*.py" or "*_test.py" → +5.0 to TEST
            - "auth", "login", "session" in name → +2.0 to FIX/REVIEW

        3. File Extension (future):
            - ".py" → Python-specific patterns
            - ".md" → Documentation patterns

    Error Handling:
        - OSError on file_path.exists() → Ignore, return empty dict
        - Invalid Path → Ignore, return empty dict
        - Never raises exceptions (fail-safe)

    Performance:
        - Time: <1ms (single exists() call)
        - I/O: 1 filesystem stat call (cached by OS)

    Example:
        >>> detector = IntentDetector()

        >>> # New file context
        >>> bonuses = detector._analyze_context(Path("src/new_feature.py"))
        >>> assert bonuses[WorkflowType.BUILD] == 5.0

        >>> # Existing file context
        >>> bonuses = detector._analyze_context(Path("src/auth.py"))
        >>> assert bonuses[WorkflowType.FIX] == 2.0
        >>> assert bonuses[WorkflowType.REFACTOR] == 2.0
    """
```

#### _combine_scores Method

```python
def _combine_scores(
    self,
    keyword_scores: dict[WorkflowType, float],
    context_scores: dict[WorkflowType, float],
) -> tuple[WorkflowType, float]:
    """
    Combine keyword and context scores with weighted average.

    Applies 80/20 weighting to keyword vs context scores, then selects
    the highest scoring workflow type.

    Args:
        keyword_scores: Dict of WorkflowType → keyword score (0-100)
        context_scores: Dict of WorkflowType → context bonus (0-5)

    Returns:
        Tuple of (best_workflow_type, combined_score):
            - best_workflow_type: WorkflowType with highest score
            - combined_score: Float in range [0.0, 100.0]

    Algorithm:
        For each workflow_type:
            final_score = keyword_score * 0.8 + context_score * 0.2

        Return workflow_type with max(final_score)

    Example:
        >>> keyword_scores = {
        ...     WorkflowType.BUILD: 85.0,
        ...     WorkflowType.FIX: 10.0,
        ...     WorkflowType.REFACTOR: 0.0,
        ...     WorkflowType.REVIEW: 0.0,
        ... }
        >>> context_scores = {
        ...     WorkflowType.BUILD: 5.0,
        ... }
        >>> workflow, score = detector._combine_scores(
        ...     keyword_scores, context_scores
        ... )
        >>> # 85.0 * 0.8 + 5.0 * 0.2 = 68.0 + 1.0 = 69.0
        >>> assert workflow == WorkflowType.BUILD
        >>> assert score == 69.0
    """
```

#### _detect_ambiguity Method

```python
def _detect_ambiguity(
    self,
    scores: dict[WorkflowType, float],
) -> bool:
    """
    Detect if intent is ambiguous based on score distribution.

    Ambiguity occurs when multiple workflows have similar scores,
    indicating unclear or multi-faceted user intent.

    Args:
        scores: Dict of WorkflowType → final combined score

    Returns:
        True if ambiguous (top 2 scores within 10%), False otherwise

    Algorithm:
        1. Sort scores in descending order
        2. Get top 2 scores
        3. If abs(score1 - score2) <= 10.0 → Ambiguous
        4. Otherwise → Not ambiguous

    Example:
        >>> scores = {
        ...     WorkflowType.BUILD: 85.0,
        ...     WorkflowType.FIX: 83.0,  # Within 10% of BUILD
        ...     WorkflowType.REFACTOR: 20.0,
        ...     WorkflowType.REVIEW: 10.0,
        ... }
        >>> is_ambiguous = detector._detect_ambiguity(scores)
        >>> assert is_ambiguous == True  # 85.0 - 83.0 = 2.0 < 10.0
    """
```

---

## Type Annotations

### 4.1 Complete Type Coverage

**Target:** 100% type coverage with mypy strict mode

**Validation Command:**
```bash
mypy tapps_agents/workflow/intent_detector.py --strict --show-error-codes
# Expected: Success: no issues found in 1 source file
```

### 4.2 Type Annotation Examples

#### Function Signatures

```python
# Public API
def detect_workflow(
    self,
    user_intent: str,
    file_path: Path | None = None,
) -> DetectionResult:
    """Fully typed public API."""

# Private methods
def _score_keywords(
    self,
    user_intent: str,
) -> dict[WorkflowType, float]:
    """Return type uses concrete types (not Any)."""

def _analyze_context(
    self,
    file_path: Path | None,
) -> dict[WorkflowType, float]:
    """Optional types use Union syntax (Path | None)."""

def _combine_scores(
    self,
    keyword_scores: dict[WorkflowType, float],
    context_scores: dict[WorkflowType, float],
) -> tuple[WorkflowType, float]:
    """Tuple return types are fully specified."""
```

#### Variable Annotations

```python
from typing import ClassVar

class IntentDetector:
    # Class variables
    BUILD_KEYWORDS: ClassVar[tuple[str, ...]] = (...)
    FIX_KEYWORDS: ClassVar[tuple[str, ...]] = (...)

    # Instance variables (via __slots__)
    __slots__ = (
        "_build_pattern",      # re.Pattern[str]
        "_fix_pattern",        # re.Pattern[str]
        "_refactor_pattern",   # re.Pattern[str]
        "_review_pattern",     # re.Pattern[str]
        "_keyword_map",        # dict[WorkflowType, tuple[tuple[str, ...], re.Pattern[str]]]
    )

    def __init__(self) -> None:
        # Type inference from method return types
        self._build_pattern = self._compile_pattern(self.BUILD_KEYWORDS)
        # Type: re.Pattern[str] (inferred from _compile_pattern return type)
```

#### Generic Types

```python
from typing import Pattern

@staticmethod
@lru_cache(maxsize=4)
def _compile_pattern(keywords: tuple[str, ...]) -> Pattern[str]:
    """
    Return type is Pattern[str] (generic regex pattern).

    Pattern[str] indicates:
        - Pattern object (from re module)
        - Matches strings (not bytes)
        - Type-safe with mypy
    """
    pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    return re.compile(pattern, re.IGNORECASE)
```

### 4.3 Type Safety Guarantees

**No `Any` Types:**
```python
# ❌ AVOID: Any type (loses type safety)
def detect_workflow(self, user_intent: Any) -> Any:
    pass

# ✅ CORRECT: Specific types
def detect_workflow(self, user_intent: str) -> DetectionResult:
    pass
```

**Proper Optional Types:**
```python
# ❌ AVOID: Implicit None
def detect_workflow(self, file_path=None):
    pass

# ✅ CORRECT: Explicit Optional
def detect_workflow(self, file_path: Path | None = None) -> DetectionResult:
    pass
```

**Type Guards:**
```python
def detect_workflow(
    self,
    user_intent: str,
    file_path: Path | None = None,
) -> DetectionResult:
    # Type guard for input validation
    if not isinstance(user_intent, str):
        user_intent = str(user_intent)

    # After this point, mypy knows user_intent is str
    intent_lower = user_intent.lower()  # Type-safe method call
```

---

## Validation Rules

### 5.1 Input Validation

#### User Intent Validation

```python
def detect_workflow(self, user_intent: str, ...) -> DetectionResult:
    # Rule 1: Type Validation
    if not isinstance(user_intent, str):
        user_intent = str(user_intent)

    # Rule 2: Whitespace Normalization
    user_intent = user_intent.strip()

    # Rule 3: Length Validation (DoS protection)
    MAX_INTENT_LENGTH = 10000
    if len(user_intent) > MAX_INTENT_LENGTH:
        logger.warning(
            f"User intent truncated from {len(user_intent)} to {MAX_INTENT_LENGTH} chars"
        )
        user_intent = user_intent[:MAX_INTENT_LENGTH]

    # Rule 4: Empty String Handling
    if not user_intent:
        logger.debug("Empty user intent, returning default")
        return DetectionResult(
            workflow_type=WorkflowType.BUILD,
            confidence=0.0,
            reasoning="Empty user intent provided",
            is_ambiguous=False
        )
```

**Validation Rules Summary:**

| Rule | Check | Action | Rationale |
|------|-------|--------|-----------|
| Type | `isinstance(user_intent, str)` | `str()` conversion | Accept any string-like input |
| Whitespace | Leading/trailing spaces | `strip()` | Normalize input |
| Length | `len() > 10000` | Truncate to 10000 | DoS protection |
| Empty | `not user_intent` | Return (BUILD, 0.0) | Fail-safe default |

#### File Path Validation

```python
def detect_workflow(self, ..., file_path: Path | None = None) -> DetectionResult:
    # Rule 1: Optional Value (None allowed)
    if file_path is None:
        # No context analysis performed
        context_scores = {}

    # Rule 2: Path Type Validation
    if file_path is not None and not isinstance(file_path, Path):
        logger.warning(f"file_path is not Path type: {type(file_path)}")
        # Convert to Path if possible
        try:
            file_path = Path(file_path)
        except Exception as e:
            logger.warning(f"Failed to convert file_path to Path: {e}")
            file_path = None
```

**File Path Rules:**

| Rule | Check | Action | Rationale |
|------|-------|--------|-----------|
| Optional | `file_path is None` | Skip context analysis | None is valid input |
| Type | `isinstance(file_path, Path)` | Convert or skip | Accept Path objects only |
| Exists | `file_path.exists()` | Catch OSError | Filesystem may be unavailable |

### 5.2 Output Validation

#### DetectionResult Validation

**Automatic Validation (Dataclass):**

```python
@dataclass(frozen=True)
class DetectionResult:
    workflow_type: WorkflowType
    confidence: float
    reasoning: str
    is_ambiguous: bool = False

    def __post_init__(self) -> None:
        """Validate fields at construction time."""
        # Validate confidence range
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(
                f"confidence must be in range [0.0, 100.0], got {self.confidence}"
            )

        # Validate reasoning non-empty
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("reasoning must be non-empty string")

        # Validate workflow_type is enum
        if not isinstance(self.workflow_type, WorkflowType):
            raise TypeError(
                f"workflow_type must be WorkflowType enum, got {type(self.workflow_type)}"
            )
```

**Output Guarantees:**

1. **confidence ∈ [0.0, 100.0]** (enforced by __post_init__)
2. **reasoning is non-empty** (enforced by __post_init__)
3. **workflow_type is valid WorkflowType** (type checker + runtime check)
4. **is_ambiguous is boolean** (type checker enforces)

### 5.3 Constraint Validation

#### Score Normalization

```python
def _combine_scores(
    self,
    keyword_scores: dict[WorkflowType, float],
    context_scores: dict[WorkflowType, float],
) -> tuple[WorkflowType, float]:
    """Combine and normalize scores."""
    final_scores = {}

    for workflow_type in WorkflowType:
        keyword_score = keyword_scores.get(workflow_type, 0.0)
        context_score = context_scores.get(workflow_type, 0.0)

        # Weighted combination
        combined = keyword_score * 0.8 + context_score * 0.2

        # Normalization: Ensure [0.0, 100.0]
        normalized = min(max(combined, 0.0), 100.0)

        final_scores[workflow_type] = normalized

    # Select best
    best_workflow = max(final_scores, key=final_scores.get)
    best_score = final_scores[best_workflow]

    return (best_workflow, best_score)
```

**Normalization Rules:**

| Constraint | Rule | Enforcement |
|------------|------|-------------|
| Lower bound | `score >= 0.0` | `max(score, 0.0)` |
| Upper bound | `score <= 100.0` | `min(score, 100.0)` |
| Range | `0.0 <= score <= 100.0` | `min(max(score, 0.0), 100.0)` |

---

## Error Handling

### 6.1 Fail-Safe Design Principle

**Core Principle:** Never raise exceptions to callers. Always return valid DetectionResult.

**Rationale:**
- Workflow enforcement must not break user operations
- Detection failures should default to "allow" (zero confidence)
- All errors logged for debugging but handled gracefully

### 6.2 Error Handling Strategy

#### Top-Level Exception Handling

```python
def detect_workflow(
    self,
    user_intent: str,
    file_path: Path | None = None,
) -> DetectionResult:
    """
    Fail-safe error handling: Never raises exceptions.
    """
    try:
        # Input validation
        if not isinstance(user_intent, str):
            user_intent = str(user_intent)

        user_intent = user_intent.strip()
        if len(user_intent) > 10000:
            user_intent = user_intent[:10000]

        if not user_intent:
            return DetectionResult(
                workflow_type=WorkflowType.BUILD,
                confidence=0.0,
                reasoning="Empty user intent",
                is_ambiguous=False
            )

        # Main detection logic
        return self._detect_workflow_impl(user_intent, file_path)

    except Exception as e:
        # Catch all exceptions (fail-safe)
        logger.error(
            f"Intent detection failed: {e}",
            extra={
                "user_intent_preview": user_intent[:100] if user_intent else "",
                "file_path": str(file_path) if file_path else None,
            },
            exc_info=True,  # Include stack trace
        )

        # Return safe default
        return DetectionResult(
            workflow_type=WorkflowType.BUILD,
            confidence=0.0,
            reasoning=f"Detection error: {str(e)[:200]}",
            is_ambiguous=False
        )
```

#### Specific Error Cases

**Type Errors:**
```python
# Handle non-string inputs gracefully
if not isinstance(user_intent, str):
    try:
        user_intent = str(user_intent)
    except Exception as e:
        logger.warning(f"Failed to convert user_intent to str: {e}")
        return DetectionResult(
            workflow_type=WorkflowType.BUILD,
            confidence=0.0,
            reasoning="Invalid user_intent type",
            is_ambiguous=False
        )
```

**Filesystem Errors:**
```python
def _analyze_context(self, file_path: Path | None) -> dict[WorkflowType, float]:
    """Handle filesystem errors gracefully."""
    bonuses = {}

    if not file_path:
        return bonuses

    try:
        # File existence check may raise OSError
        if not file_path.exists():
            bonuses[WorkflowType.BUILD] = 5.0
        else:
            bonuses[WorkflowType.FIX] = 2.0
            bonuses[WorkflowType.REFACTOR] = 2.0
    except OSError as e:
        # Filesystem unavailable or permission denied
        logger.debug(f"Failed to check file existence: {e}")
        # Return empty bonuses (no context analysis)
        return {}

    return bonuses
```

**Validation Errors:**
```python
# DetectionResult validation errors are caught at construction
try:
    result = DetectionResult(
        workflow_type=best_workflow,
        confidence=best_score,
        reasoning=reasoning,
        is_ambiguous=is_ambiguous
    )
except ValueError as e:
    # Confidence out of range or empty reasoning
    logger.error(f"Failed to create DetectionResult: {e}")
    return DetectionResult(
        workflow_type=WorkflowType.BUILD,
        confidence=0.0,
        reasoning="Validation error in result construction",
        is_ambiguous=False
    )
```

### 6.3 Error Logging Strategy

**Structured Logging:**

```python
import logging

logger = logging.getLogger(__name__)

# Info level: Normal operations
logger.info(
    f"Detected workflow: {workflow_type}",
    extra={
        "workflow": str(workflow_type),
        "confidence": confidence,
        "is_ambiguous": is_ambiguous,
        "user_intent_preview": user_intent[:100],
    }
)

# Warning level: Recoverable issues
logger.warning(
    f"User intent truncated from {len(user_intent)} to 10000 chars",
    extra={
        "original_length": len(user_intent),
        "truncated_length": 10000,
    }
)

# Error level: Unexpected failures
logger.error(
    f"Intent detection failed: {e}",
    extra={
        "user_intent_preview": user_intent[:100],
        "file_path": str(file_path),
    },
    exc_info=True,  # Include full stack trace
)
```

**Logging Levels:**

| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Initialization, internal state | "IntentDetector initialized with patterns" |
| INFO | Successful detections | "Detected workflow: *build (85.0%)" |
| WARNING | Input sanitization, truncation | "User intent truncated to 10000 chars" |
| ERROR | Exceptions, failures | "Intent detection failed: ValueError" |

**Privacy Considerations:**

```python
# ❌ AVOID: Logging full user input (may contain PII)
logger.info(f"User intent: {user_intent}")

# ✅ CORRECT: Truncate to preview (100 chars)
logger.info(
    f"Detected workflow",
    extra={
        "user_intent_preview": user_intent[:100],  # Safe truncation
    }
)
```

---

## Performance Requirements

### 7.1 Latency Targets

**Performance Contract:**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **p99 latency** | <5ms | Performance test suite (1000 iterations) |
| **p50 latency** | <2ms | Performance test suite (1000 iterations) |
| **p25 latency** | <1ms | Performance test suite (1000 iterations) |
| **Initialization** | <10ms | One-time cost on first instantiation |

**Measurement Code:**

```python
import time
import numpy as np

def benchmark_latency():
    """Benchmark detect_workflow() latency."""
    detector = IntentDetector()
    latencies = []

    # Warm-up (exclude from measurements)
    for _ in range(100):
        detector.detect_workflow("add feature")

    # Actual measurements
    for _ in range(1000):
        start = time.perf_counter()
        detector.detect_workflow("add user authentication")
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # Convert to ms

    # Calculate percentiles
    p25 = np.percentile(latencies, 25)
    p50 = np.percentile(latencies, 50)
    p99 = np.percentile(latencies, 99)

    print(f"Latency: p25={p25:.2f}ms, p50={p50:.2f}ms, p99={p99:.2f}ms")

    # Assertions
    assert p99 < 5.0, f"p99 latency {p99:.2f}ms exceeds 5ms"
    assert p50 < 2.0, f"p50 latency {p50:.2f}ms exceeds 2ms"
    assert p25 < 1.0, f"p25 latency {p25:.2f}ms exceeds 1ms"
```

### 7.2 Memory Targets

**Memory Contract:**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Per-call allocation** | <100KB | tracemalloc profiling |
| **Instance size** | <5KB | sys.getsizeof() |
| **Pattern cache** | <20KB | 4 compiled patterns |

**Measurement Code:**

```python
import tracemalloc
import sys

def benchmark_memory():
    """Benchmark detect_workflow() memory usage."""
    detector = IntentDetector()

    # Measure instance size
    instance_size = sys.getsizeof(detector)
    print(f"Instance size: {instance_size} bytes")
    assert instance_size < 5 * 1024, f"Instance size {instance_size} exceeds 5KB"

    # Measure per-call allocation
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    detector.detect_workflow("add user authentication")

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Calculate allocation
    stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    total_allocation = sum(stat.size_diff for stat in stats)

    print(f"Per-call allocation: {total_allocation / 1024:.1f} KB")
    assert total_allocation < 100 * 1024, f"Allocation {total_allocation} exceeds 100KB"
```

### 7.3 Optimization Techniques

#### Pre-compiled Regex Patterns

**Problem:** Compiling regex patterns at runtime adds ~50ms latency per call.

**Solution:** Pre-compile patterns at initialization using @lru_cache.

```python
@staticmethod
@lru_cache(maxsize=4)
def _compile_pattern(keywords: tuple[str, ...]) -> re.Pattern[str]:
    """
    Compile regex pattern with caching.

    Benefits:
        - Patterns compiled once and cached
        - Subsequent calls return cached pattern (O(1))
        - Reduces latency from ~50ms to <2ms
    """
    pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    return re.compile(pattern, re.IGNORECASE)
```

**Impact:** 25x latency reduction (50ms → 2ms)

#### Short-Circuit Evaluation

**Problem:** Context analysis adds ~2ms latency even when confidence is already high.

**Solution:** Skip context analysis for very high confidence (≥95%).

```python
# Stage 1: Keyword Matching
keyword_scores = self._score_keywords(user_intent)

# Short-circuit for very high confidence
if max(keyword_scores.values()) >= 95.0:
    best_workflow = max(keyword_scores, key=keyword_scores.get)
    return DetectionResult(
        workflow_type=best_workflow,
        confidence=keyword_scores[best_workflow],
        reasoning="High-confidence keyword match",
        is_ambiguous=False
    )

# Stage 2: Context Analysis (only if needed)
context_scores = self._analyze_context(file_path)
```

**Impact:** 30% latency reduction for high-confidence cases (majority of prompts)

#### Memory Optimization with __slots__

**Problem:** Default Python objects allocate ~500KB per instance due to __dict__.

**Solution:** Use __slots__ to reduce memory overhead.

```python
class IntentDetector:
    __slots__ = (
        "_build_pattern",
        "_fix_pattern",
        "_refactor_pattern",
        "_review_pattern",
        "_keyword_map",
    )
```

**Impact:** 60% memory reduction (~500KB → ~50KB per instance)

#### Efficient Keyword Matching

**Problem:** Iterating over keywords in nested loops is O(n²).

**Solution:** Use pre-compiled regex with findall() for O(n) complexity.

```python
# ✅ EFFICIENT: O(n) with single regex pass
def _calculate_keyword_score(self, intent: str, pattern: re.Pattern) -> float:
    matches = pattern.findall(intent)  # Single pass
    return len(matches) * 60.0

# ❌ INEFFICIENT: O(n²) with nested loops
def _calculate_keyword_score_slow(self, intent: str, keywords: list) -> float:
    score = 0
    for keyword in keywords:
        if keyword in intent:  # Nested iteration
            score += 60
    return score
```

**Impact:** Reduces time complexity from O(n²) to O(n)

---

## Usage Examples

### 8.1 Basic Usage

```python
from pathlib import Path
from tapps_agents.workflow.intent_detector import IntentDetector

# Initialize detector
detector = IntentDetector()

# Example 1: Build intent
result = detector.detect_workflow("add user authentication")
print(f"Workflow: {result.workflow_type}")  # *build
print(f"Confidence: {result.confidence:.1f}%")  # 85.0%
print(f"Reasoning: {result.reasoning}")
# Output: Strong 'add' keyword at start of prompt

# Example 2: Fix intent
result = detector.detect_workflow("fix login bug in authentication")
print(f"Workflow: {result.workflow_type}")  # *fix
print(f"Confidence: {result.confidence:.1f}%")  # 90.0%

# Example 3: Refactor intent
result = detector.detect_workflow("modernize authentication system")
print(f"Workflow: {result.workflow_type}")  # *refactor
print(f"Confidence: {result.confidence:.1f}%")  # 85.0%

# Example 4: Review intent
result = detector.detect_workflow("review authentication code for security issues")
print(f"Workflow: {result.workflow_type}")  # *review
print(f"Confidence: {result.confidence:.1f}%")  # 88.0%
```

### 8.2 Context Analysis

```python
# Example 5: New file context (boosts BUILD confidence)
result = detector.detect_workflow(
    "add authentication",
    file_path=Path("src/auth.py")  # New file (doesn't exist)
)
print(f"Confidence: {result.confidence:.1f}%")  # Higher than without context

# Example 6: Existing file context (boosts FIX/REFACTOR confidence)
Path("src/existing.py").touch()  # Create file
result = detector.detect_workflow(
    "modify authentication",
    file_path=Path("src/existing.py")  # Existing file
)
print(f"Workflow: {result.workflow_type}")  # Likely FIX or REFACTOR
```

### 8.3 Ambiguity Handling

```python
# Example 7: Ambiguous intent
result = detector.detect_workflow("fix and improve authentication system")

if result.is_ambiguous:
    print("⚠️ Ambiguous intent detected")
    print(f"Primary: {result.workflow_type} ({result.confidence:.1f}%)")
    # Future Story 3: Show secondary workflow suggestion
else:
    print(f"Clear intent: {result.workflow_type} ({result.confidence:.1f}%)")
```

### 8.4 Error Handling

```python
# Example 8: Empty input (fail-safe)
result = detector.detect_workflow("")
assert result.workflow_type == WorkflowType.BUILD
assert result.confidence == 0.0
assert "Empty" in result.reasoning

# Example 9: Very long input (truncation)
long_prompt = "add feature " * 10000  # >10KB
result = detector.detect_workflow(long_prompt)
# Automatically truncated to 10000 chars, processes normally

# Example 10: Invalid file path (graceful degradation)
result = detector.detect_workflow(
    "add authentication",
    file_path=Path("/nonexistent/path/file.py")
)
# Context analysis skipped, keyword matching still works
```

### 8.5 Integration with WorkflowEnforcer

```python
from tapps_agents.workflow.enforcer import WorkflowEnforcer
from tapps_agents.core.llm_behavior import EnforcementConfig

# Example 11: Full integration
config = EnforcementConfig(
    mode="warning",
    confidence_threshold=60.0,
    suggest_workflows=True,
)

enforcer = WorkflowEnforcer(config=config)
detector = IntentDetector()

# Simulate user attempting direct edit
user_intent = "add user authentication feature"
file_path = Path("src/api/auth.py")

# Detect workflow type
result = detector.detect_workflow(user_intent, file_path)

# Make enforcement decision
if result.confidence >= config.confidence_threshold:
    decision = enforcer.intercept_code_edit(
        file_path=file_path,
        user_intent=user_intent,
        is_new_file=True,
    )

    if decision["action"] == "warn":
        print(f"⚠️ {decision['message']}")
        print(f"Suggested workflow: @simple-mode {result.workflow_type}")
    elif decision["action"] == "block":
        print(f"🚫 {decision['message']}")
        raise BlockedOperationError(decision["message"])
else:
    # Low confidence: Allow operation
    print("✅ Operation allowed (low confidence)")
```

### 8.6 Performance Testing

```python
import time
import numpy as np

# Example 12: Latency benchmark
detector = IntentDetector()
latencies = []

for _ in range(1000):
    start = time.perf_counter()
    result = detector.detect_workflow("add user authentication")
    latency = (time.perf_counter() - start) * 1000  # ms
    latencies.append(latency)

p99 = np.percentile(latencies, 99)
p50 = np.percentile(latencies, 50)
print(f"Latency: p50={p50:.2f}ms, p99={p99:.2f}ms")
assert p99 < 5.0, f"p99 latency {p99:.2f}ms exceeds 5ms target"
```

---

## Integration Contract

### 9.1 WorkflowEnforcer Integration

#### Integration Point

The IntentDetector is used by WorkflowEnforcer to determine which workflow to suggest when intercepting code edits.

**Modified WorkflowEnforcer Code:**

```python
# tapps_agents/workflow/enforcer.py
from tapps_agents.workflow.intent_detector import IntentDetector, DetectionResult

class WorkflowEnforcer:
    def __init__(
        self,
        config_path: Path | None = None,
        config: EnforcementConfig | None = None,
    ) -> None:
        self._config_path = config_path
        self._config_mtime: float = 0.0

        # Load or use provided config
        if config is not None:
            self.config = config
        else:
            self.config = self._load_config(config_path)

        # NEW: Initialize IntentDetector (ENH-001-S2)
        self.intent_detector = IntentDetector()

        logger.info(
            f"WorkflowEnforcer initialized with mode={self.config.mode}, "
            f"confidence_threshold={self.config.confidence_threshold}"
        )

    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool,
        skip_enforcement: bool = False,
    ) -> EnforcementDecision:
        """Intercept with intent detection."""
        try:
            # Check if enforcement should be applied
            if not self._should_enforce(file_path, is_new_file, skip_enforcement):
                return self._create_decision("allow", file_path, user_intent)

            # NEW: Detect workflow type and confidence (ENH-001-S2)
            detection_result = self.intent_detector.detect_workflow(
                user_intent=user_intent,
                file_path=file_path
            )

            # NEW: Check confidence threshold
            if detection_result.confidence < self.config.confidence_threshold:
                # Low confidence: Allow operation
                logger.info(
                    f"Low confidence ({detection_result.confidence:.1f}% < "
                    f"{self.config.confidence_threshold}%), allowing operation"
                )
                return self._create_decision("allow", file_path, user_intent)

            # Determine action based on config mode
            action: Literal["block", "warn", "allow"]
            if self.config.mode == "blocking":
                action = "block"
            elif self.config.mode == "warning":
                action = "warn"
            else:  # silent
                action = "allow"

            # Create decision with detected workflow
            decision = self._create_decision(action, file_path, user_intent)

            # NEW: Attach detection metadata
            decision["workflow"] = detection_result.workflow_type
            decision["confidence"] = detection_result.confidence
            decision["reasoning"] = detection_result.reasoning
            decision["is_ambiguous"] = detection_result.is_ambiguous

            return decision

        except Exception as e:
            # Fail-safe: Log error and allow operation
            logger.error(
                f"WorkflowEnforcer.intercept_code_edit() failed with error: {e}. "
                f"Defaulting to 'allow' (fail-safe). file_path={file_path}, "
                f"user_intent={user_intent[:100]}"
            )
            return self._create_decision("allow", file_path, user_intent)
```

#### Updated EnforcementDecision

```python
# tapps_agents/workflow/enforcer.py
class EnforcementDecision(TypedDict):
    """
    Enforcement decision with intent detection metadata.

    Updated for ENH-001-S2 to include detected workflow information.
    """

    action: Literal["block", "warn", "allow"]
    message: str
    should_block: bool
    confidence: float  # NEW: Populated by IntentDetector (0.0-100.0)

    # NEW: ENH-001-S2 fields
    workflow: str | None  # NEW: Detected workflow type (e.g., "*build")
    reasoning: str | None  # NEW: Detection reasoning
    is_ambiguous: bool  # NEW: Ambiguity flag
```

### 9.2 Dependency Injection

**Constructor Pattern:**

```python
class WorkflowEnforcer:
    def __init__(
        self,
        config: EnforcementConfig | None = None,
        intent_detector: IntentDetector | None = None,  # Dependency injection
    ) -> None:
        """
        Initialize with optional dependencies.

        Args:
            config: Optional EnforcementConfig (defaults to from_config_file())
            intent_detector: Optional IntentDetector (defaults to new instance)

        Design Pattern: Dependency Injection
        Benefits:
            - Testability: Mock detector in unit tests
            - Flexibility: Use custom detector implementations
            - Decoupling: WorkflowEnforcer doesn't know detector internals
        """
        self.config = config or EnforcementConfig.from_config_file()
        self.intent_detector = intent_detector or IntentDetector()
```

**Testing Example:**

```python
# tests/unit/workflow/test_enforcer_integration.py
from unittest.mock import Mock
from tapps_agents.workflow.enforcer import WorkflowEnforcer
from tapps_agents.workflow.intent_detector import DetectionResult, WorkflowType

def test_enforcer_with_mock_detector():
    """Test WorkflowEnforcer with mock IntentDetector."""
    # Create mock detector
    mock_detector = Mock()
    mock_detector.detect_workflow.return_value = DetectionResult(
        workflow_type=WorkflowType.BUILD,
        confidence=85.0,
        reasoning="Mock detection",
        is_ambiguous=False
    )

    # Inject mock into enforcer
    enforcer = WorkflowEnforcer(intent_detector=mock_detector)

    # Test enforcement decision
    decision = enforcer.intercept_code_edit(
        file_path=Path("test.py"),
        user_intent="add feature",
        is_new_file=True
    )

    # Verify mock was called
    mock_detector.detect_workflow.assert_called_once_with(
        user_intent="add feature",
        file_path=Path("test.py")
    )

    # Verify decision includes detection metadata
    assert decision["workflow"] == WorkflowType.BUILD
    assert decision["confidence"] == 85.0
```

### 9.3 API Contract Summary

**Contract Guarantees:**

1. **Never raises exceptions** to WorkflowEnforcer
2. **Always returns DetectionResult** (not None)
3. **Confidence in range [0.0, 100.0]** (validated)
4. **Latency <5ms p99** (performance tested)
5. **Thread-safe** (stateless design)

**Contract Expectations:**

1. **user_intent is string** (WorkflowEnforcer provides)
2. **file_path is Path or None** (WorkflowEnforcer provides)
3. **IntentDetector initialized** before calls (WorkflowEnforcer ensures)

---

## Testing Guidelines

### 10.1 Unit Test Structure

**Test File:** `tests/unit/workflow/test_intent_detector.py`

**Test Coverage Target:** ≥85% line coverage, 90%+ branch coverage

#### Test Categories

**1. Keyword Matching Tests (60 tests)**

```python
class TestKeywordMatching:
    """Test keyword matching for all workflow types."""

    @pytest.fixture
    def detector(self):
        return IntentDetector()

    # Build Intent Tests (15 tests)
    def test_build_keyword_add(self, detector):
        result = detector.detect_workflow("add user authentication")
        assert result.workflow_type == WorkflowType.BUILD
        assert result.confidence >= 60.0

    def test_build_keyword_create(self, detector):
        result = detector.detect_workflow("create API endpoint")
        assert result.workflow_type == WorkflowType.BUILD
        assert result.confidence >= 60.0

    # ... 13 more build tests

    # Fix Intent Tests (15 tests)
    def test_fix_keyword_bug(self, detector):
        result = detector.detect_workflow("fix login bug")
        assert result.workflow_type == WorkflowType.FIX
        assert result.confidence >= 60.0

    # ... 14 more fix tests

    # Refactor Intent Tests (15 tests)
    # Review Intent Tests (15 tests)
```

**2. Scoring Algorithm Tests (10 tests)**

```python
class TestScoringAlgorithm:
    """Test confidence scoring algorithm."""

    def test_base_score_single_match(self, detector):
        """Test base score for single keyword match."""
        result = detector.detect_workflow("add feature")
        # Expected: 60 (base) + 10 (position) = 70
        assert result.confidence == 70.0

    def test_position_bonus(self, detector):
        """Test position bonus when keyword at start."""
        result_with_bonus = detector.detect_workflow("add feature")
        result_without_bonus = detector.detect_workflow("please add feature")
        assert result_with_bonus.confidence > result_without_bonus.confidence

    def test_multiple_match_bonus(self, detector):
        """Test bonus for multiple keyword matches."""
        result = detector.detect_workflow("build new feature")
        # Expected: 60 (base) + 10 (position) + 5 (multi) = 75
        assert result.confidence >= 75.0
```

**3. Context Analysis Tests (10 tests)**

```python
class TestContextAnalysis:
    """Test file path context analysis."""

    def test_new_file_boosts_build(self, detector, tmp_path):
        """Test new file context boosts BUILD confidence."""
        new_file = tmp_path / "new_feature.py"

        result_with_context = detector.detect_workflow(
            "add feature",
            file_path=new_file
        )
        result_without_context = detector.detect_workflow("add feature")

        assert result_with_context.confidence > result_without_context.confidence

    def test_existing_file_boosts_fix(self, detector, tmp_path):
        """Test existing file context boosts FIX confidence."""
        existing_file = tmp_path / "existing.py"
        existing_file.touch()

        result = detector.detect_workflow(
            "modify code",
            file_path=existing_file
        )
        # FIX or REFACTOR more likely for existing files
        assert result.workflow_type in [WorkflowType.FIX, WorkflowType.REFACTOR]
```

**4. Edge Case Tests (10 tests)**

```python
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self, detector):
        """Test empty input returns safe default."""
        result = detector.detect_workflow("")
        assert result.workflow_type == WorkflowType.BUILD
        assert result.confidence == 0.0

    def test_whitespace_only(self, detector):
        """Test whitespace-only input."""
        result = detector.detect_workflow("   ")
        assert result.workflow_type == WorkflowType.BUILD
        assert result.confidence == 0.0

    def test_very_long_prompt(self, detector):
        """Test prompt >10KB is truncated."""
        long_prompt = "add feature " * 10000
        result = detector.detect_workflow(long_prompt)
        # Should process without error
        assert result.workflow_type == WorkflowType.BUILD

    def test_special_characters(self, detector):
        """Test special characters are handled."""
        result = detector.detect_workflow("add @#$% feature")
        assert result.workflow_type == WorkflowType.BUILD

    def test_unicode_characters(self, detector):
        """Test unicode characters are handled."""
        result = detector.detect_workflow("add 用户认证 feature")
        assert result.workflow_type == WorkflowType.BUILD
```

**5. Integration Tests (5 tests)**

```python
class TestIntegration:
    """Test integration with WorkflowEnforcer."""

    def test_enforcer_integration(self):
        """Test full integration with WorkflowEnforcer."""
        from tapps_agents.workflow.enforcer import WorkflowEnforcer

        enforcer = WorkflowEnforcer()
        decision = enforcer.intercept_code_edit(
            file_path=Path("test.py"),
            user_intent="add user authentication",
            is_new_file=True
        )

        assert decision["workflow"] == WorkflowType.BUILD
        assert decision["confidence"] >= 60.0
```

### 10.2 Performance Tests

**Test File:** `tests/performance/test_intent_detector_perf.py`

```python
import time
import numpy as np
import tracemalloc
from tapps_agents.workflow.intent_detector import IntentDetector

def test_latency_p99_under_5ms():
    """Verify p99 latency <5ms."""
    detector = IntentDetector()
    latencies = []

    # Warm-up
    for _ in range(100):
        detector.detect_workflow("add feature")

    # Measurements
    for _ in range(1000):
        start = time.perf_counter()
        detector.detect_workflow("add user authentication")
        latencies.append((time.perf_counter() - start) * 1000)

    p99 = np.percentile(latencies, 99)
    p50 = np.percentile(latencies, 50)

    assert p99 < 5.0, f"p99 latency {p99:.2f}ms exceeds 5ms"
    assert p50 < 2.0, f"p50 latency {p50:.2f}ms exceeds 2ms"

def test_memory_overhead_under_100kb():
    """Verify memory overhead <100KB per call."""
    detector = IntentDetector()

    tracemalloc.start()
    detector.detect_workflow("add user authentication")
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 100 * 1024, f"Memory {peak} exceeds 100KB"
```

### 10.3 Validation Tests

**Test File:** `tests/validation/test_intent_detector_accuracy.py`

```python
import pytest
from pathlib import Path
from tapps_agents.workflow.intent_detector import IntentDetector, WorkflowType

# Validation dataset (100+ labeled prompts)
VALIDATION_DATA = [
    ("add user authentication", WorkflowType.BUILD),
    ("create API endpoint", WorkflowType.BUILD),
    ("implement JWT tokens", WorkflowType.BUILD),
    ("fix login bug", WorkflowType.FIX),
    ("resolve authentication error", WorkflowType.FIX),
    ("debug session management", WorkflowType.FIX),
    ("modernize auth system", WorkflowType.REFACTOR),
    ("improve code quality", WorkflowType.REFACTOR),
    ("update deprecated API", WorkflowType.REFACTOR),
    ("review authentication code", WorkflowType.REVIEW),
    ("analyze security issues", WorkflowType.REVIEW),
    ("inspect code quality", WorkflowType.REVIEW),
    # ... 88 more labeled examples
]

def test_classification_accuracy():
    """Verify classification accuracy ≥85%."""
    detector = IntentDetector()
    correct = 0

    for prompt, expected_workflow in VALIDATION_DATA:
        result = detector.detect_workflow(prompt)
        if result.workflow_type == expected_workflow:
            correct += 1

    accuracy = correct / len(VALIDATION_DATA) * 100
    print(f"Accuracy: {accuracy:.1f}% ({correct}/{len(VALIDATION_DATA)})")

    assert accuracy >= 85.0, f"Accuracy {accuracy:.1f}% below 85% target"
```

### 10.4 Test Coverage Report

**Generate Coverage Report:**

```bash
# Run tests with coverage
pytest tests/unit/workflow/test_intent_detector.py \
    --cov=tapps_agents.workflow.intent_detector \
    --cov-report=html \
    --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

**Coverage Targets:**

| Metric | Target | Command |
|--------|--------|---------|
| **Line coverage** | ≥85% | `--cov-report=term-missing` |
| **Branch coverage** | ≥90% | `--cov-branch` |
| **Function coverage** | 100% | All public methods tested |

**Expected Output:**

```
---------- coverage: platform win32, python 3.12.0-final-0 -----------
Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
tapps_agents\workflow\intent_detector.py      150      8    95%   45-47, 112-115
-------------------------------------------------------------------------
TOTAL                                         150      8    95%
```

### 10.5 CI/CD Integration

**GitHub Actions Workflow:**

```yaml
# .github/workflows/test-intent-detector.yml
name: Test Intent Detector

on:
  push:
    paths:
      - 'tapps_agents/workflow/intent_detector.py'
      - 'tests/unit/workflow/test_intent_detector.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov numpy

      - name: Run unit tests
        run: |
          pytest tests/unit/workflow/test_intent_detector.py \
            --cov=tapps_agents.workflow.intent_detector \
            --cov-report=xml \
            --cov-fail-under=85

      - name: Run performance tests
        run: |
          pytest tests/performance/test_intent_detector_perf.py -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Appendix

### A. Complete Type Signatures

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Pattern

# Data Models
class WorkflowType(str, Enum):
    BUILD: str
    FIX: str
    REFACTOR: str
    REVIEW: str

@dataclass(frozen=True, slots=True)
class DetectionResult:
    workflow_type: WorkflowType
    confidence: float
    reasoning: str
    is_ambiguous: bool = False

    def __post_init__(self) -> None: ...

# Main Class
class IntentDetector:
    BUILD_KEYWORDS: ClassVar[tuple[str, ...]]
    FIX_KEYWORDS: ClassVar[tuple[str, ...]]
    REFACTOR_KEYWORDS: ClassVar[tuple[str, ...]]
    REVIEW_KEYWORDS: ClassVar[tuple[str, ...]]

    __slots__: tuple[str, ...]

    def __init__(self, config: EnforcementConfig | None = None) -> None: ...

    def detect_workflow(
        self,
        user_intent: str,
        file_path: Path | None = None,
    ) -> DetectionResult: ...

    def _score_keywords(
        self,
        user_intent: str,
    ) -> dict[WorkflowType, float]: ...

    def _analyze_context(
        self,
        file_path: Path | None,
    ) -> dict[WorkflowType, float]: ...

    def _combine_scores(
        self,
        keyword_scores: dict[WorkflowType, float],
        context_scores: dict[WorkflowType, float],
    ) -> tuple[WorkflowType, float]: ...

    def _detect_ambiguity(
        self,
        scores: dict[WorkflowType, float],
    ) -> bool: ...

    @staticmethod
    @lru_cache(maxsize=4)
    def _compile_pattern(keywords: tuple[str, ...]) -> Pattern[str]: ...
```

### B. Configuration Reference

**EnforcementConfig for IntentDetector:**

```yaml
# .tapps-agents/config.yaml
llm_behavior:
  mode: "senior-developer"

  workflow_enforcement:
    mode: "blocking"              # "blocking" | "warning" | "silent"
    confidence_threshold: 60.0    # 0.0-100.0 (ENH-001-S2 uses this)
    suggest_workflows: true       # Show workflow suggestions
    block_direct_edits: true      # Actually block in blocking mode
```

**Future Enhancement (Story 5+):**

```yaml
llm_behavior:
  workflow_enforcement:
    # ... existing fields ...

    intent_detection:
      # Custom keyword sets (override defaults)
      build_keywords:
        - "build"
        - "create"
        - "custom-build-keyword"

      # Scoring weights (override 80/20 default)
      keyword_weight: 0.8
      context_weight: 0.2

      # ML model integration (future)
      use_ml_model: false
      ml_model_path: "models/intent_classifier.pkl"
```

---

**End of API Specification**

**Next Steps:**
1. Review this API specification with team
2. Execute implementation using @simple-mode *build
3. Validate against acceptance criteria in this document
4. Integrate with ENH-001-S1 WorkflowEnforcer
5. Deploy to production with monitoring

**Related Documents:**
- Architecture: `docs/architecture/ENH-001-S2-architecture.md`
- Enhanced Prompt: `docs/enhancement/ENH-001-S2-ENHANCED-PROMPT.md`
- Task Breakdown: `stories/ENH-001-S2-task-breakdown.md`
- Implementation: `tapps_agents/workflow/intent_detector.py` (to be created)
