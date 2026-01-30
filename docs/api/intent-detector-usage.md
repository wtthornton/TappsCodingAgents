# IntentDetector Usage Guide

**Component:** ENH-001-S2 Intent Detection System
**Module:** `tapps_agents.workflow.intent_detector`
**Status:** Production Ready

---

## Quick Start

```python
from tapps_agents.workflow.intent_detector import IntentDetector, WorkflowType

# Initialize detector
detector = IntentDetector()

# Detect workflow from user prompt
result = detector.detect_workflow("add user authentication")

# Access results
print(f"Workflow: {result.workflow_type}")      # WorkflowType.BUILD
print(f"Confidence: {result.confidence:.1f}%")  # 26.7%
print(f"Reasoning: {result.reasoning}")         # Detection explanation
print(f"Ambiguous: {result.is_ambiguous}")      # False
```

---

## Basic Usage

### Simple Detection

```python
from tapps_agents.workflow.intent_detector import IntentDetector

detector = IntentDetector()

# BUILD intent
result = detector.detect_workflow("create new feature")
assert result.workflow_type == WorkflowType.BUILD

# FIX intent
result = detector.detect_workflow("fix authentication bug")
assert result.workflow_type == WorkflowType.FIX

# REFACTOR intent
result = detector.detect_workflow("improve code quality")
assert result.workflow_type == WorkflowType.REFACTOR

# REVIEW intent
result = detector.detect_workflow("review security issues")
assert result.workflow_type == WorkflowType.REVIEW
```

### Detection with Context

```python
from pathlib import Path

# New file context boosts BUILD confidence
result = detector.detect_workflow(
    "add authentication",
    file_path=Path("src/new_feature.py")  # File doesn't exist
)
# Confidence is higher due to context signal

# Existing file context boosts FIX/REFACTOR confidence
result = detector.detect_workflow(
    "modify authentication",
    file_path=Path("src/auth.py")  # File exists
)
```

---

## Data Models

### WorkflowType Enum

```python
class WorkflowType(str, Enum):
    BUILD = "*build"      # New feature implementation
    FIX = "*fix"          # Bug fixes and error resolution
    REFACTOR = "*refactor"  # Code improvement and modernization
    REVIEW = "*review"    # Code review and quality inspection

# String-based enum supports direct comparison
if result.workflow_type == "*build":
    print("Build workflow detected")

# Access enum value
print(result.workflow_type.value)  # "*build"
```

### DetectionResult Dataclass

```python
@dataclass(frozen=True, slots=True)
class DetectionResult:
    workflow_type: WorkflowType  # Detected workflow type
    confidence: float            # Confidence score (0.0-100.0)
    reasoning: str               # Human-readable explanation
    is_ambiguous: bool = False   # True if multiple workflows scored similarly

# Immutable - cannot be modified after creation
result.confidence = 90.0  # Raises FrozenInstanceError

# Thread-safe - can be shared across threads
```

---

## Advanced Usage

### Handling Ambiguous Results

```python
result = detector.detect_workflow("fix and refactor authentication")

if result.is_ambiguous:
    print(f"⚠️ Ambiguous intent detected")
    print(f"Primary workflow: {result.workflow_type}")
    print(f"Confidence: {result.confidence:.1f}%")
    # Future enhancement: Show secondary workflow options
else:
    print(f"Clear intent: {result.workflow_type}")
```

### Confidence Thresholding

```python
CONFIDENCE_THRESHOLD = 60.0

result = detector.detect_workflow(user_input)

if result.confidence >= CONFIDENCE_THRESHOLD:
    # High confidence - enforce workflow
    print(f"Suggest using {result.workflow_type}")
else:
    # Low confidence - allow direct edit
    print("Confidence too low, allowing direct edit")
```

### Error Handling (Fail-Safe)

```python
# IntentDetector NEVER raises exceptions
result = detector.detect_workflow("")
assert result.workflow_type == WorkflowType.BUILD
assert result.confidence == 0.0
assert "Empty" in result.reasoning

# Long input is automatically truncated
long_input = "add feature " * 10000  # >10KB
result = detector.detect_workflow(long_input)
# Processes without error (truncated to 10000 chars)
```

---

## Integration Patterns

### With WorkflowEnforcer

```python
from tapps_agents.workflow.enforcer import WorkflowEnforcer
from tapps_agents.core.llm_behavior import EnforcementConfig

class WorkflowEnforcer:
    def __init__(self, config: EnforcementConfig):
        self.config = config
        self.intent_detector = IntentDetector()

    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool
    ) -> EnforcementDecision:
        # Detect workflow
        result = self.intent_detector.detect_workflow(
            user_intent=user_intent,
            file_path=file_path
        )

        # Check confidence threshold
        if result.confidence < self.config.confidence_threshold:
            return {"action": "allow", "message": "", ...}

        # Enforce workflow
        return {
            "action": "warn",
            "message": f"Consider using {result.workflow_type}",
            "workflow": result.workflow_type,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            ...
        }
```

### With Dependency Injection (Testing)

```python
from unittest.mock import Mock

# Create mock detector for testing
mock_detector = Mock()
mock_detector.detect_workflow.return_value = DetectionResult(
    workflow_type=WorkflowType.BUILD,
    confidence=85.0,
    reasoning="Mock detection",
    is_ambiguous=False
)

# Inject into enforcer
enforcer = WorkflowEnforcer(
    config=config,
    intent_detector=mock_detector  # Use mock instead of real detector
)
```

---

## Performance Characteristics

### Latency

```python
import time

detector = IntentDetector()

# Measure latency
start = time.perf_counter()
result = detector.detect_workflow("add user authentication")
latency = (time.perf_counter() - start) * 1000  # Convert to ms

print(f"Latency: {latency:.2f}ms")
# Expected: <5ms p99, <2ms p50
```

### Thread Safety

```python
from concurrent.futures import ThreadPoolExecutor

detector = IntentDetector()

def detect_intent(prompt):
    return detector.detect_workflow(prompt)

# Safe to use across threads (stateless design)
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(detect_intent, "add feature")
        for _ in range(100)
    ]
    results = [f.result() for f in futures]

# All results are valid DetectionResult instances
```

---

## Keyword Reference

### BUILD Keywords

`build`, `create`, `add`, `implement`, `new`, `feature`, `develop`, `write`, `generate`, `make`

**Example Prompts:**
- "add user authentication"
- "create new API endpoint"
- "implement JWT tokens"
- "build feature for exporting data"

### FIX Keywords

`fix`, `bug`, `error`, `issue`, `broken`, `repair`, `resolve`, `debug`, `problem`, `correct`

**Example Prompts:**
- "fix login bug"
- "resolve authentication error"
- "debug session management issue"
- "repair broken API endpoint"

### REFACTOR Keywords

`refactor`, `modernize`, `improve`, `update`, `clean`, `restructure`, `optimize`, `rewrite`

**Example Prompts:**
- "refactor authentication module"
- "modernize legacy code"
- "improve code quality"
- "update deprecated API"

### REVIEW Keywords

`review`, `check`, `analyze`, `inspect`, `examine`, `quality`, `audit`, `assess`, `evaluate`

**Example Prompts:**
- "review authentication code"
- "analyze security issues"
- "inspect code quality"
- "audit error handling"

---

## Best Practices

### 1. Provide Clear User Intent

```python
# ✅ GOOD: Clear, specific intent
result = detector.detect_workflow("add user authentication with JWT")

# ❌ AVOID: Vague or generic intent
result = detector.detect_workflow("do something")
```

### 2. Use File Path Context When Available

```python
# ✅ GOOD: Provide file path for context
result = detector.detect_workflow(
    "add authentication",
    file_path=Path("src/auth.py")
)

# ⚠️ OK: Without context (lower confidence)
result = detector.detect_workflow("add authentication")
```

### 3. Check Confidence Before Enforcement

```python
# ✅ GOOD: Respect confidence threshold
if result.confidence >= 60.0:
    # Enforce workflow
    suggest_workflow(result.workflow_type)
else:
    # Allow direct edit
    allow_operation()
```

### 4. Handle Ambiguous Cases

```python
# ✅ GOOD: Handle ambiguity explicitly
if result.is_ambiguous:
    # Show multiple options or ask for clarification
    present_workflow_options(result)
else:
    # Proceed with single workflow
    execute_workflow(result.workflow_type)
```

---

## Common Patterns

### Pattern 1: Basic Enforcement

```python
result = detector.detect_workflow(user_input)
if result.confidence >= threshold:
    print(f"Use {result.workflow_type} instead of direct edit")
```

### Pattern 2: Confidence-Based Actions

```python
result = detector.detect_workflow(user_input, file_path)

if result.confidence >= 80:
    # High confidence - enforce strongly
    block_operation()
elif result.confidence >= 60:
    # Medium confidence - suggest workflow
    show_warning()
else:
    # Low confidence - allow operation
    allow_operation()
```

### Pattern 3: Logging and Debugging

```python
result = detector.detect_workflow(user_input, file_path)

logger.info(
    f"Intent detection: {result.workflow_type}",
    extra={
        "workflow": str(result.workflow_type),
        "confidence": result.confidence,
        "is_ambiguous": result.is_ambiguous,
        "reasoning": result.reasoning,
    }
)
```

---

## Troubleshooting

### Low Confidence Scores

**Problem:** Detection returns low confidence (<60%)

**Solutions:**
1. **Add more keywords** to user prompt
   - Instead of: "modify auth"
   - Use: "fix authentication bug in login"

2. **Provide file path context**
   ```python
   result = detector.detect_workflow(
       "modify auth",
       file_path=Path("src/auth.py")  # Adds context
   )
   ```

### Incorrect Workflow Detection

**Problem:** Detects wrong workflow type

**Solutions:**
1. **Use specific keywords**
   - Instead of: "change login"
   - Use: "fix login bug" (FIX) or "refactor login" (REFACTOR)

2. **Check for keyword conflicts**
   - "fix and refactor" triggers ambiguity
   - Use single intent: "fix login" or "refactor login"

### Ambiguous Detection

**Problem:** `is_ambiguous=True` flag set

**Solutions:**
1. **Clarify user intent**
   - Ask user to choose primary workflow
   - Rephrase prompt to focus on single action

2. **Handle ambiguity programmatically**
   ```python
   if result.is_ambiguous:
       # Show multiple workflow options
       # Let user choose
       pass
   ```

---

## API Reference

### IntentDetector Class

```python
class IntentDetector:
    """High-performance intent detector for workflow classification."""

    def __init__(self) -> None:
        """Initialize with pre-compiled patterns."""

    def detect_workflow(
        self,
        user_intent: str,
        file_path: Path | None = None,
    ) -> DetectionResult:
        """
        Detect workflow type from user intent.

        Args:
            user_intent: User's prompt (1-10000 chars)
            file_path: Optional file path for context

        Returns:
            DetectionResult with workflow, confidence, reasoning

        Raises:
            Never (fail-safe design)

        Performance:
            - Latency: <5ms p99, <2ms p50
            - Memory: <100KB per call
            - Thread-safe: Yes
        """
```

### DetectionResult Dataclass

```python
@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Immutable result of intent detection."""

    workflow_type: WorkflowType  # Detected workflow
    confidence: float            # Score 0.0-100.0
    reasoning: str               # Explanation
    is_ambiguous: bool = False   # Ambiguity flag
```

---

## Related Documentation

- **API Specification:** `docs/api/ENH-001-S2-api-spec.md`
- **Architecture Design:** `docs/architecture/ENH-001-S2-architecture.md`
- **Implementation Summary:** `docs/implementation/ENH-001-S2-implementation-summary.md`
- **WorkflowEnforcer Integration:** `tapps_agents/workflow/enforcer.py`
- **Configuration Reference:** `docs/CONFIGURATION.md`

---

**Last Updated:** 2026-01-30
**Version:** 1.0
**Status:** Production Ready
