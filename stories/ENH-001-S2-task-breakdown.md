# ENH-001-S2: Intent Detection System - Task Breakdown

**Story ID:** ENH-001-S2
**Epic:** ENH-001 Workflow Enforcement System
**Created:** 2026-01-30
**Status:** Ready for Implementation
**Story Points:** 2 (8 hours)
**Priority:** High

---

## Executive Summary

This document provides a detailed task breakdown for implementing the Intent Detection System as part of the Workflow Enforcement epic. The system will intelligently classify user prompts into workflow types (*build, *fix, *refactor, *review) with confidence scoring, enabling proactive workflow suggestions.

**Key Objectives:**
- Implement IntentDetector class with keyword matching (80% weight) and context analysis (20% weight)
- Achieve <5ms p99 latency, <100KB memory overhead
- Deliver ≥85% test coverage with 85%+ classification accuracy
- Integrate seamlessly with ENH-001-S1 WorkflowEnforcer

---

## Story Context

### User Story

> As a developer, I want the system to detect my intent (build, fix, refactor, review) from my prompt, so that it can suggest the most appropriate workflow.

### Dependencies

- **ENH-001-S1** (Core Workflow Enforcer) - COMPLETE
  - `tapps_agents/workflow/enforcer.py` exists
  - Provides WorkflowEnforcer class
  - Integration point: `intercept_code_edit()` method

### Integration Points

**WorkflowEnforcer Integration:**
```python
# tapps_agents/workflow/enforcer.py (existing)
class WorkflowEnforcer:
    def __init__(self, config: EnforcementConfig):
        self.intent_detector = IntentDetector()  # NEW

    def intercept_code_edit(self, file_path, user_intent, is_new_file):
        # NEW: Detect workflow and confidence
        workflow, confidence = self.intent_detector.detect_workflow(
            user_intent=user_intent,
            file_path=file_path
        )
        # Use workflow and confidence in enforcement decision
```

**Existing Intent Parser:**
- Current implementation: `tapps_agents/simple_mode/intent_parser.py`
- Provides: IntentType enum, Intent dataclass, keyword matching
- **Note:** New IntentDetector will be separate, focused on workflow enforcement
- Consider convergence in future refactoring (not in scope for this story)

---

## Task Breakdown

### Task 2.1: Create IntentDetector Class (3 hours)

**Objective:** Implement core IntentDetector class with keyword matching algorithm.

#### Subtask 2.1.1: Create Module Structure (30 minutes)

**Actions:**
1. Create `tapps_agents/workflow/intent_detector.py` file
2. Add module docstring with purpose and usage examples
3. Import required dependencies:
   - `re` (regex for keyword matching)
   - `logging` (structured logging)
   - `dataclasses` (DetectionResult)
   - `functools.lru_cache` (performance optimization)
   - `pathlib.Path` (file path handling)
   - `typing` (type hints)
4. Create logger instance: `logger = logging.getLogger(__name__)`

**Deliverables:**
- File created: `tapps_agents/workflow/intent_detector.py`
- Module docstring complete
- All imports added

**Acceptance Criteria:**
- [ ] File created in correct location
- [ ] Module docstring explains purpose
- [ ] All required imports present
- [ ] No syntax errors

---

#### Subtask 2.1.2: Define DetectionResult Dataclass (30 minutes)

**Actions:**
1. Create `DetectionResult` dataclass with attributes:
   - `workflow: WorkflowType` (detected workflow)
   - `confidence: float` (0.0-100.0)
   - `ambiguous: bool = False` (multiple high scores)
   - `secondary_workflow: WorkflowType | None = None` (second best)
2. Add `__post_init__()` validation:
   - Check confidence is 0-100
   - Raise ValueError if invalid
3. Add comprehensive docstring with examples
4. Make dataclass frozen (immutable)

**Implementation:**
```python
@dataclass(frozen=True)
class DetectionResult:
    """
    Result of intent detection.

    Attributes:
        workflow: Detected workflow type (*build, *fix, *refactor, *review)
        confidence: Confidence score (0.0-100.0)
        ambiguous: True if multiple workflows scored within 10%
        secondary_workflow: Second-highest scoring workflow (if ambiguous)
    """
    workflow: WorkflowType
    confidence: float
    ambiguous: bool = False
    secondary_workflow: WorkflowType | None = None

    def __post_init__(self) -> None:
        """Validate confidence range."""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")
```

**Acceptance Criteria:**
- [ ] DetectionResult dataclass created
- [ ] All attributes defined with correct types
- [ ] Validation logic in `__post_init__`
- [ ] Frozen (immutable) dataclass
- [ ] Comprehensive docstring

---

#### Subtask 2.1.3: Define IntentDetector Class Structure (30 minutes)

**Actions:**
1. Create `IntentDetector` class with:
   - Class docstring explaining algorithm and performance
   - Class constants for keyword sets (BUILD_KEYWORDS, FIX_KEYWORDS, etc.)
   - `__slots__` for memory optimization
   - `__init__()` method for initialization
2. Define keyword constants as tuples (immutable):
   - `BUILD_KEYWORDS`: build, create, add, implement, new, feature, develop, write, generate, make
   - `FIX_KEYWORDS`: fix, bug, error, issue, broken, repair, correct, resolve, debug, patch
   - `REFACTOR_KEYWORDS`: refactor, modernize, improve, update, cleanup, rewrite, optimize, enhance
   - `REVIEW_KEYWORDS`: review, check, analyze, inspect, examine, audit, quality, assess, evaluate

**Implementation:**
```python
class IntentDetector:
    """
    Detect workflow type from user intent using keyword matching.

    Algorithm:
        1. Keyword Matching (80% weight)
        2. Context Analysis (20% weight)
        3. Score Combination
        4. Ambiguity Detection

    Performance:
        - Latency: <5ms p99, <2ms p50
        - Memory: <100KB per call
        - Accuracy: 85%+ on validation dataset
    """

    BUILD_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "build", "create", "add", "implement", "new", "feature",
        "develop", "write", "generate", "make"
    )
    # ... other keywords

    __slots__ = (
        "_build_pattern", "_fix_pattern",
        "_refactor_pattern", "_review_pattern",
        "_keyword_map"
    )

    def __init__(self) -> None:
        """Initialize intent detector with pre-compiled patterns."""
        # Will implement in next subtask
        pass
```

**Acceptance Criteria:**
- [ ] IntentDetector class created
- [ ] Class docstring complete
- [ ] All keyword constants defined
- [ ] `__slots__` defined for memory optimization
- [ ] Empty `__init__()` method

---

#### Subtask 2.1.4: Implement Pattern Pre-compilation (45 minutes)

**Actions:**
1. Create `_compile_pattern()` static method:
   - Use `@lru_cache(maxsize=4)` for caching
   - Build regex pattern with word boundaries
   - Use `re.IGNORECASE` flag
2. Implement `__init__()` method:
   - Pre-compile patterns for all keyword sets
   - Store patterns in slots
   - Create keyword map dictionary
   - Log initialization

**Implementation:**
```python
@staticmethod
@lru_cache(maxsize=4)
def _compile_pattern(keywords: tuple[str, ...]) -> re.Pattern[str]:
    """
    Compile regex pattern for keyword matching.

    Uses word boundaries to avoid partial matches.
    Cached to avoid recompilation (performance optimization).
    """
    pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    return re.compile(pattern, re.IGNORECASE)

def __init__(self) -> None:
    """Initialize intent detector."""
    self._build_pattern = self._compile_pattern(self.BUILD_KEYWORDS)
    self._fix_pattern = self._compile_pattern(self.FIX_KEYWORDS)
    self._refactor_pattern = self._compile_pattern(self.REFACTOR_KEYWORDS)
    self._review_pattern = self._compile_pattern(self.REVIEW_KEYWORDS)

    self._keyword_map = {
        "*build": (self.BUILD_KEYWORDS, self._build_pattern),
        "*fix": (self.FIX_KEYWORDS, self._fix_pattern),
        "*refactor": (self.REFACTOR_KEYWORDS, self._refactor_pattern),
        "*review": (self.REVIEW_KEYWORDS, self._review_pattern),
    }

    logger.debug("IntentDetector initialized with keyword patterns")
```

**Acceptance Criteria:**
- [ ] `_compile_pattern()` method implemented
- [ ] Patterns pre-compiled in `__init__()`
- [ ] Keyword map created
- [ ] Logging added
- [ ] Performance: <5ms p99 latency maintained

---

#### Subtask 2.1.5: Implement detect_workflow() Main Method (45 minutes)

**Actions:**
1. Create `detect_workflow()` public method:
   - Accept `user_intent: str` and `file_path: Path | None`
   - Return `DetectionResult`
   - Add input validation and sanitization
   - Handle edge cases (empty, too long, special chars)
   - Fail-safe error handling (never raise exceptions)
2. Implement input validation:
   - Convert non-strings to string
   - Strip whitespace
   - Truncate if >10KB
   - Log warnings for invalid input
3. Add fail-safe wrapper:
   - Try-except block around implementation
   - Return `(*build, 0.0)` on error
   - Log errors with context

**Implementation:**
```python
def detect_workflow(
    self,
    user_intent: str,
    file_path: Path | None = None,
) -> DetectionResult:
    """
    Detect workflow type from user intent.

    Args:
        user_intent: User's prompt/description (1-10000 chars)
        file_path: Optional file path for context analysis

    Returns:
        DetectionResult with workflow type, confidence, and flags

    Performance:
        - Latency: <5ms p99, <2ms p50
        - Memory: <100KB per call
    """
    # Input validation
    if not isinstance(user_intent, str):
        user_intent = str(user_intent)

    user_intent = user_intent.strip()
    if len(user_intent) > 10000:
        logger.warning(f"Intent truncated from {len(user_intent)} to 10000 chars")
        user_intent = user_intent[:10000]

    # Handle empty input
    if not user_intent:
        logger.debug("Empty user intent, returning default")
        return DetectionResult(workflow="*build", confidence=0.0)

    # Fail-safe error handling
    try:
        return self._detect_workflow_impl(user_intent, file_path)
    except Exception as e:
        logger.error(f"Intent detection failed: {e}", exc_info=True)
        return DetectionResult(workflow="*build", confidence=0.0)
```

**Acceptance Criteria:**
- [ ] `detect_workflow()` method implemented
- [ ] Input validation complete
- [ ] Edge cases handled
- [ ] Fail-safe error handling
- [ ] Comprehensive docstring
- [ ] Type hints on all parameters

---

#### Subtask 2.1.6: Implement Keyword Scoring Algorithm (30 minutes)

**Actions:**
1. Create `_calculate_keyword_score()` method:
   - Accept intent string, keywords tuple, and pattern
   - Return float score (0.0-100.0)
   - Implement scoring algorithm:
     - Base score: 60% per keyword match (max 100%)
     - Position bonus: +10% if keyword at start
     - Multiple match bonus: +5% per extra keyword (max +15%)
2. Use regex `findall()` for efficient matching
3. Cap total score at 100%

**Implementation:**
```python
def _calculate_keyword_score(
    self,
    intent: str,
    keywords: tuple[str, ...],
    pattern: re.Pattern[str],
) -> float:
    """
    Calculate keyword match score (0-100%).

    Algorithm:
        1. Count matches using regex
        2. Base score: 60% per match (max 100%)
        3. Position bonus: +10% if keyword at start
        4. Multiple match bonus: +5% per extra (max +15%)
    """
    # Count matches
    matches = pattern.findall(intent)
    match_count = len(matches)

    if match_count == 0:
        return 0.0

    # Base score
    base_score = min(match_count * 60, 100)

    # Position bonus
    position_bonus = 10 if any(intent.startswith(kw) for kw in keywords) else 0

    # Multiple match bonus
    multi_bonus = min((match_count - 1) * 5, 15) if match_count > 1 else 0

    # Total score (capped at 100%)
    return min(base_score + position_bonus + multi_bonus, 100.0)
```

**Acceptance Criteria:**
- [ ] `_calculate_keyword_score()` method implemented
- [ ] Scoring algorithm correct
- [ ] All bonuses applied correctly
- [ ] Score capped at 100%
- [ ] Docstring with algorithm description

---

### Task 2.2: Add Context Analysis (2 hours)

**Objective:** Implement lightweight context analysis for file path signals (20% weight).

#### Subtask 2.2.1: Implement Context Analysis Method (1 hour)

**Actions:**
1. Create `_analyze_context()` method:
   - Accept `file_path: Path | None`
   - Return `dict[str, float]` (workflow → bonus score)
   - Implement file path pattern detection
   - Implement file existence checks
2. File path patterns to detect:
   - "test" in filename → test intent (5.0 bonus)
   - "auth"/"login"/"session" → fix/review (2.0 bonus)
3. File existence signals:
   - New file (not exists) → build (5.0 bonus)
   - Existing file → fix/refactor (2.0 bonus)
4. Handle file system errors gracefully (fail-safe)

**Implementation:**
```python
def _analyze_context(self, file_path: Path | None) -> dict[str, float]:
    """
    Analyze context for confidence bonuses (20% weight).

    Context signals:
        - File path patterns (test files, auth files, etc.)
        - File existence (new vs existing)

    Returns:
        Dict mapping workflow_type → bonus_score (0-5%)
    """
    bonuses: dict[str, float] = {}

    if not file_path:
        return bonuses

    file_name = file_path.name.lower()

    # File path pattern analysis
    if "test" in file_name or file_name.startswith("test_"):
        bonuses["*test"] = 5.0

    if any(kw in file_name for kw in ["auth", "login", "session"]):
        bonuses["*fix"] = 2.0
        bonuses["*review"] = 2.0

    # File existence analysis
    try:
        if not file_path.exists():
            bonuses["*build"] = 5.0
        else:
            bonuses["*fix"] = 2.0
            bonuses["*refactor"] = 2.0
    except OSError:
        # Ignore file system errors (fail-safe)
        pass

    return bonuses
```

**Acceptance Criteria:**
- [ ] `_analyze_context()` method implemented
- [ ] File path patterns detected
- [ ] File existence checks implemented
- [ ] Fail-safe error handling for file system errors
- [ ] Returns correct bonus structure

---

#### Subtask 2.2.2: Implement Score Combination Logic (1 hour)

**Actions:**
1. Create `_detect_workflow_impl()` internal method:
   - Normalize input (lowercase)
   - Calculate keyword scores for all workflow types
   - Call context analysis
   - Combine scores with 80/20 weighting
   - Select best match
   - Detect ambiguity (scores within 10%)
   - Return DetectionResult
2. Implement short-circuit optimization:
   - If keyword score ≥95%, return immediately (skip context)
3. Add structured logging at each stage
4. Implement ambiguity detection:
   - Check if second-best score within 10% of best
   - Set ambiguous flag and secondary_workflow

**Implementation:**
```python
def _detect_workflow_impl(
    self,
    user_intent: str,
    file_path: Path | None,
) -> DetectionResult:
    """Internal implementation of intent detection."""
    intent_lower = user_intent.lower()

    logger.debug("Detecting workflow intent", extra={
        "user_intent_length": len(user_intent),
        "has_file_path": file_path is not None,
    })

    # Stage 1: Keyword Matching (80% weight)
    keyword_scores = {}
    for workflow_type, (keywords, pattern) in self._keyword_map.items():
        score = self._calculate_keyword_score(intent_lower, keywords, pattern)
        keyword_scores[workflow_type] = score

        # Short-circuit for very high confidence
        if score >= 95.0:
            logger.info(f"High-confidence match: {workflow_type} ({score:.1f}%)")
            return DetectionResult(workflow=workflow_type, confidence=score)

    # Stage 2: Context Analysis (20% weight)
    context_bonuses = self._analyze_context(file_path)

    # Stage 3: Combine Scores (80/20 weighted)
    final_scores = {}
    for workflow_type in self._keyword_map:
        keyword_score = keyword_scores[workflow_type]
        context_bonus = context_bonuses.get(workflow_type, 0.0)
        final_scores[workflow_type] = keyword_score * 0.8 + context_bonus * 0.2

    # Stage 4: Select Best Match
    sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    best_workflow, best_confidence = sorted_scores[0]
    second_workflow, second_confidence = sorted_scores[1] if len(sorted_scores) > 1 else (None, 0.0)

    # Stage 5: Ambiguity Detection
    ambiguous = False
    if second_workflow and abs(best_confidence - second_confidence) <= 10.0:
        ambiguous = True
        logger.info(f"Ambiguous intent: {best_workflow} vs {second_workflow}")

    logger.info(f"Detected workflow: {best_workflow} ({best_confidence:.1f}%)")

    return DetectionResult(
        workflow=best_workflow,
        confidence=min(best_confidence, 100.0),
        ambiguous=ambiguous,
        secondary_workflow=second_workflow if ambiguous else None,
    )
```

**Acceptance Criteria:**
- [ ] `_detect_workflow_impl()` method implemented
- [ ] Keyword scores calculated for all types
- [ ] Context analysis integrated
- [ ] 80/20 weighted combination
- [ ] Short-circuit optimization
- [ ] Ambiguity detection
- [ ] Structured logging at each stage

---

### Task 2.3: Write Unit Tests (3 hours)

**Objective:** Achieve ≥85% test coverage with comprehensive test suite.

#### Subtask 2.3.1: Create Test Module Structure (30 minutes)

**Actions:**
1. Create `tests/unit/workflow/test_intent_detector.py`
2. Add module docstring
3. Import dependencies:
   - `pytest`
   - `pathlib.Path`
   - `IntentDetector`, `DetectionResult`
   - `WorkflowType`
4. Create test class `TestIntentDetector`
5. Add fixture for detector instance

**Implementation:**
```python
"""
Unit tests for IntentDetector.

Part of ENH-001-S2: Intent Detection System.
Coverage target: ≥85% line coverage, 90%+ branch coverage.
"""

import pytest
from pathlib import Path

from tapps_agents.workflow.intent_detector import IntentDetector, DetectionResult
from tapps_agents.workflow.models import WorkflowType


class TestIntentDetector:
    """Test suite for IntentDetector class."""

    @pytest.fixture
    def detector(self):
        """Create IntentDetector instance for tests."""
        return IntentDetector()
```

**Acceptance Criteria:**
- [ ] Test file created in correct location
- [ ] Module docstring complete
- [ ] All imports present
- [ ] Test class created
- [ ] Detector fixture defined

---

#### Subtask 2.3.2: Write Keyword Matching Tests (1 hour)

**Actions:**
1. Write tests for each workflow type (4 × 10 = 40 tests):
   - Build intent: test each BUILD_KEYWORD
   - Fix intent: test each FIX_KEYWORD
   - Refactor intent: test each REFACTOR_KEYWORD
   - Review intent: test each REVIEW_KEYWORD
2. Test position bonus:
   - Keyword at start vs middle
3. Test multiple keyword bonus:
   - Single keyword vs multiple keywords
4. Test confidence thresholds:
   - Verify confidence ≥60% for single match
   - Verify confidence ≥70% for position bonus
   - Verify confidence ≥75% for multiple matches

**Test Examples:**
```python
# Build Intent Tests
def test_detect_build_add(self, detector):
    """Test build intent: 'add' keyword."""
    result = detector.detect_workflow("add user authentication")
    assert result.workflow == "*build"
    assert result.confidence >= 60.0

def test_detect_build_create(self, detector):
    """Test build intent: 'create' keyword."""
    result = detector.detect_workflow("create API endpoint")
    assert result.workflow == "*build"
    assert result.confidence >= 60.0

def test_detect_build_position_bonus(self, detector):
    """Test build intent: position bonus."""
    result = detector.detect_workflow("build authentication system")
    assert result.workflow == "*build"
    assert result.confidence >= 70.0  # 60 base + 10 position

# Fix Intent Tests
def test_detect_fix_bug(self, detector):
    """Test fix intent: 'bug' keyword."""
    result = detector.detect_workflow("fix login bug")
    assert result.workflow == "*fix"
    assert result.confidence >= 60.0

# ... 36 more keyword tests
```

**Acceptance Criteria:**
- [ ] 40+ keyword matching tests written
- [ ] All workflow types covered
- [ ] Position bonus tested
- [ ] Multiple keyword bonus tested
- [ ] Confidence thresholds validated

---

#### Subtask 2.3.3: Write Edge Case Tests (30 minutes)

**Actions:**
1. Test empty string
2. Test whitespace only
3. Test special characters
4. Test very long prompts (>10KB)
5. Test unicode characters
6. Test numeric input
7. Test mixed case
8. Test partial keyword matches (should not match)
9. Test multiple workflow keywords (ambiguity)
10. Test non-string input (should convert)

**Test Examples:**
```python
def test_empty_string(self, detector):
    """Test edge case: empty string."""
    result = detector.detect_workflow("")
    assert result.workflow == "*build"
    assert result.confidence == 0.0

def test_whitespace_only(self, detector):
    """Test edge case: whitespace only."""
    result = detector.detect_workflow("   ")
    assert result.workflow == "*build"
    assert result.confidence == 0.0

def test_special_characters(self, detector):
    """Test edge case: special characters."""
    result = detector.detect_workflow("add @#$% feature")
    assert result.workflow == "*build"
    assert result.confidence >= 60.0

def test_very_long_prompt(self, detector):
    """Test edge case: very long prompt (>10KB)."""
    long_prompt = "add feature " * 10000
    result = detector.detect_workflow(long_prompt)
    assert result.workflow == "*build"

# ... 6 more edge case tests
```

**Acceptance Criteria:**
- [ ] 10 edge case tests written
- [ ] All edge cases handled gracefully
- [ ] No exceptions raised
- [ ] Fail-safe behavior verified

---

#### Subtask 2.3.4: Write Context Analysis Tests (30 minutes)

**Actions:**
1. Test file path patterns:
   - Test files boost test intent
   - Auth files boost fix/review
2. Test file existence:
   - New files boost build intent
   - Existing files boost fix/refactor
3. Test combined keyword + context:
   - Verify 80/20 weighting
   - Verify context increases confidence
4. Test missing file path (None)
5. Test file system errors (OSError)

**Test Examples:**
```python
def test_context_new_file(self, detector, tmp_path):
    """Test context: new file boosts build confidence."""
    new_file = tmp_path / "auth.py"
    result_with_context = detector.detect_workflow(
        "add authentication", file_path=new_file
    )
    result_without_context = detector.detect_workflow("add authentication")
    assert result_with_context.confidence > result_without_context.confidence

def test_context_existing_file(self, detector, tmp_path):
    """Test context: existing file boosts fix/refactor."""
    existing_file = tmp_path / "auth.py"
    existing_file.touch()
    result = detector.detect_workflow("modify authentication", file_path=existing_file)
    assert result.confidence >= 60.0

# ... 8 more context tests
```

**Acceptance Criteria:**
- [ ] 10 context analysis tests written
- [ ] File path patterns tested
- [ ] File existence tested
- [ ] Combined scoring tested
- [ ] Edge cases handled

---

#### Subtask 2.3.5: Write Integration Tests (30 minutes)

**Actions:**
1. Test WorkflowEnforcer integration:
   - Mock WorkflowEnforcer
   - Verify IntentDetector called correctly
   - Verify results used in enforcement decision
2. Test end-to-end workflow:
   - User prompt → Intent detection → Enforcement
3. Test configuration integration:
   - Verify confidence threshold usage
4. Test logging integration:
   - Verify logs generated
5. Test performance integration:
   - Verify latency within bounds

**Test Examples:**
```python
def test_integration_with_enforcer(self, detector):
    """Test integration with WorkflowEnforcer."""
    from tapps_agents.workflow.enforcer import WorkflowEnforcer
    from tapps_agents.core.llm_behavior import EnforcementConfig

    config = EnforcementConfig(confidence_threshold=60.0)
    enforcer = WorkflowEnforcer(config)

    decision = enforcer.intercept_code_edit(
        file_path=Path("src/auth.py"),
        user_intent="add user authentication",
        is_new_file=True
    )

    assert decision["workflow"] == "*build"
    assert decision["confidence"] >= 60.0

# ... 4 more integration tests
```

**Acceptance Criteria:**
- [ ] 5 integration tests written
- [ ] WorkflowEnforcer integration tested
- [ ] End-to-end flow tested
- [ ] Configuration integration tested
- [ ] All tests passing

---

#### Subtask 2.3.6: Write Performance Tests (30 minutes)

**Actions:**
1. Create performance test module: `tests/performance/test_intent_detector_perf.py`
2. Write latency benchmark:
   - Run 1000 detections
   - Measure p99, p50, p25 latency
   - Assert p99 <5ms, p50 <2ms
3. Write memory benchmark:
   - Use `tracemalloc`
   - Assert peak memory <100KB
4. Write load test:
   - 10,000 consecutive calls
   - Verify no performance degradation

**Test Implementation:**
```python
"""Performance tests for IntentDetector."""

import time
import tracemalloc
import numpy as np
import pytest

from tapps_agents.workflow.intent_detector import IntentDetector


class TestIntentDetectorPerformance:
    """Performance test suite."""

    def test_latency_p99_under_5ms(self):
        """Verify p99 latency <5ms."""
        detector = IntentDetector()
        latencies = []

        for _ in range(1000):
            start = time.perf_counter()
            detector.detect_workflow("add user authentication")
            latency = (time.perf_counter() - start) * 1000  # ms
            latencies.append(latency)

        p99 = np.percentile(latencies, 99)
        p50 = np.percentile(latencies, 50)

        assert p99 < 5.0, f"p99 latency {p99:.2f}ms exceeds 5ms"
        assert p50 < 2.0, f"p50 latency {p50:.2f}ms exceeds 2ms"

    def test_memory_overhead_under_100kb(self):
        """Verify memory overhead <100KB per call."""
        detector = IntentDetector()

        tracemalloc.start()
        detector.detect_workflow("add user authentication")
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert peak < 100 * 1024, f"Memory {peak} exceeds 100KB"
```

**Acceptance Criteria:**
- [ ] Performance tests written
- [ ] Latency benchmarks pass (<5ms p99)
- [ ] Memory benchmarks pass (<100KB)
- [ ] Load tests pass (no degradation)

---

## Acceptance Criteria Checklist

### Functional Requirements

- [ ] **FR-1:** Detects *build intent (keywords: build, create, add, implement, new, feature)
- [ ] **FR-2:** Detects *fix intent (keywords: fix, bug, error, issue, broken, repair)
- [ ] **FR-3:** Detects *refactor intent (keywords: refactor, modernize, improve, update)
- [ ] **FR-4:** Detects *review intent (keywords: review, check, analyze, inspect, quality)
- [ ] **FR-5:** Returns confidence score (0-100%)
- [ ] **FR-6:** Triggers suggestion when confidence ≥60%
- [ ] **FR-7:** Handles ambiguous cases (multiple high scores)

### Non-Functional Requirements

- [ ] **NFR-1:** Latency <5ms (p99), <2ms (p50)
- [ ] **NFR-2:** Memory overhead <100KB per call
- [ ] **NFR-3:** Test coverage ≥85% line, 90%+ branch
- [ ] **NFR-4:** Classification accuracy ≥85%
- [ ] **NFR-5:** Type hints on all public APIs (mypy strict)
- [ ] **NFR-6:** Comprehensive docstrings (Google style)
- [ ] **NFR-7:** Ruff compliance (0 violations)

### Integration Requirements

- [ ] **INT-1:** Integrates with WorkflowEnforcer (ENH-001-S1)
- [ ] **INT-2:** Returns DetectionResult dataclass
- [ ] **INT-3:** Fail-safe error handling (never raises exceptions)
- [ ] **INT-4:** Structured logging at all stages

---

## Testing Strategy

### Test Coverage Targets

**Unit Tests:** ≥85% line coverage, 90%+ branch coverage

**Test Distribution:**
- Keyword matching tests: 40 tests
- Edge case tests: 10 tests
- Context analysis tests: 10 tests
- Integration tests: 5 tests
- Performance tests: 3 tests

**Total Tests:** 68+ tests

### Test Execution

```bash
# Run all tests
pytest tests/unit/workflow/test_intent_detector.py -v

# Run with coverage
pytest tests/unit/workflow/test_intent_detector.py \
  --cov=tapps_agents.workflow.intent_detector \
  --cov-report=html \
  --cov-report=term-missing

# Run performance tests
pytest tests/performance/test_intent_detector_perf.py -v

# Target: ≥85% coverage, all tests passing
```

---

## Implementation Order

### Day 1 Morning (3 hours) - Task 2.1: Core Implementation

1. **Hour 1:** Create module structure, DetectionResult dataclass
2. **Hour 2:** IntentDetector class structure, pattern pre-compilation
3. **Hour 3:** detect_workflow() main method, keyword scoring

**Checkpoint:** Core detection working, manual smoke tests pass

### Day 1 Afternoon (2 hours) - Task 2.2: Context Analysis

4. **Hour 4:** Implement context analysis, score combination
5. **Hour 5:** Integration with WorkflowEnforcer, end-to-end testing

**Checkpoint:** Full detection pipeline working, integration tests pass

### Day 2 (3 hours) - Task 2.3: Unit Tests

6. **Hour 6:** Keyword matching tests, edge case tests
7. **Hour 7:** Context analysis tests, integration tests
8. **Hour 8:** Performance tests, coverage verification

**Checkpoint:** ≥85% coverage, all tests passing

---

## Risk Management

### Risk #1: Performance Degradation

**Probability:** Medium
**Impact:** High (blocks story)

**Mitigation:**
- Pre-compile regex patterns at initialization
- Use `__slots__` for memory optimization
- Implement short-circuit evaluation for high confidence
- Add performance benchmarks in CI/CD

**Contingency:**
- If latency >5ms p99, optimize regex patterns
- If memory >100KB, reduce pattern complexity
- If still failing, increase thresholds to 10ms/200KB

---

### Risk #2: False Positive Rate >20%

**Probability:** Medium
**Impact:** Medium (user frustration)

**Mitigation:**
- Validate against 100+ real user prompts
- Adjust confidence threshold (60% → 70%)
- Add more context signals
- Improve keyword selection

**Contingency:**
- If false positive rate >20%, increase threshold to 70%
- Add user feedback mechanism for corrections
- Consider ML-based classification (future story)

---

### Risk #3: Integration Issues with WorkflowEnforcer

**Probability:** Low
**Impact:** High (blocks story)

**Mitigation:**
- Review ENH-001-S1 implementation early
- Write integration tests before implementation
- Mock WorkflowEnforcer for unit tests
- Coordinate with ENH-001-S1 owner

**Contingency:**
- If API incompatible, add adapter pattern
- If timing issues, add async support
- If config issues, add default values

---

## Definition of Done

- [ ] All code implemented and committed
- [ ] All acceptance criteria met
- [ ] Test coverage ≥85% (line), 90%+ (branch)
- [ ] All tests passing (unit, integration, performance)
- [ ] Performance benchmarks pass (<5ms p99, <100KB)
- [ ] Type checking passes (mypy strict mode)
- [ ] Code style passes (ruff check)
- [ ] Documentation complete (docstrings, comments)
- [ ] Integration with WorkflowEnforcer verified
- [ ] Code reviewed and approved
- [ ] Merged to main branch

---

## Dependencies and References

### Dependencies

- **ENH-001-S1:** Core Workflow Enforcer (COMPLETE)
  - File: `tapps_agents/workflow/enforcer.py`
  - Class: `WorkflowEnforcer`
  - Method: `intercept_code_edit()`

### References

- **Story Document:** `stories/enh-001-workflow-enforcement.md` (lines 104-167)
- **Enhanced Prompt:** `docs/enhancement/ENH-001-S2-ENHANCED-PROMPT.md`
- **Existing Intent Parser:** `tapps_agents/simple_mode/intent_parser.py`
- **Epic Document:** `stories/enh-001-workflow-enforcement.md`

### Related Files

- `tapps_agents/workflow/models.py` - WorkflowType enum
- `tapps_agents/core/llm_behavior.py` - EnforcementConfig
- `tests/unit/workflow/` - Test directory

---

## Next Steps

1. **Review this task breakdown** with team (15 minutes)
2. **Set up development environment** (15 minutes)
3. **Start Task 2.1** - Create IntentDetector class (3 hours)
4. **Checkpoint:** Core detection working
5. **Continue to Task 2.2** - Add context analysis (2 hours)
6. **Continue to Task 2.3** - Write unit tests (3 hours)
7. **Final review** and integration (30 minutes)

**Total Time:** 8 hours (2 story points)

---

**Created By:** TappsCodingAgents Planner Agent
**Created Date:** 2026-01-30
**Story:** ENH-001-S2 Intent Detection System
**Epic:** ENH-001 Workflow Enforcement System
**Status:** Ready for Implementation
