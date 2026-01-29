# ENH-001: Workflow Enforcement System - Architecture Design

**Date:** 2026-01-29
**Version:** 1.0.0
**Status:** Design Complete
**Architect:** TappsCodingAgents Architect Agent

---

## Executive Summary

### System Purpose

Implement a workflow enforcement system that intercepts direct code edits and proactively suggests @simple-mode workflows, ensuring LLMs act as "Senior Developers" by default with automatic validation, testing, and quality gates.

### Architecture Pattern

**Interceptor Pattern** with modular components for intent detection, policy enforcement, and user messaging.

### Key Components

1. **WorkflowEnforcer** - Core enforcement engine
2. **IntentDetector** - Intent classification with confidence scoring
3. **MessageFormatter** - User-facing message generation
4. **EnforcementConfig** - Configuration management

### Performance Characteristics

- **Latency:** <50ms (p95) for interception check
- **Memory:** <10MB overhead
- **CPU:** <5% impact on file operations
- **Throughput:** 1000+ interceptions/second

---

## System Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────┐
│              Application Layer                          │
│  (ImplementerAgent, CLI, Cursor Skills)                │
└─────────────────────┬──────────────────────────────────┘
                      │
                      ↓ File Operation Request
┌────────────────────────────────────────────────────────┐
│          File Operation Interceptor                     │
│  (Write tool, Edit tool, File creation hooks)          │
└─────────────────────┬──────────────────────────────────┘
                      │
                      ↓ intercept_code_edit()
┌────────────────────────────────────────────────────────┐
│         WorkflowEnforcer (Core Engine)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Capture context (file_path, user_intent)    │  │
│  │  2. Detect workflow type and confidence         │  │
│  │  3. Load enforcement policy from config         │  │
│  │  4. Make enforcement decision                   │  │
│  │  5. Format user message                         │  │
│  │  6. Log enforcement event                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────┬──────────────────────────────────┘
                      │
         ┌────────────┼────────────┬──────────────┐
         ↓            ↓            ↓              ↓
┌────────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐
│ Intent     │  │ Config   │  │ Message │  │ Analytics│
│ Detector   │  │ Loader   │  │Formatter│  │ Logger   │
│            │  │          │  │         │  │          │
│ - Keyword  │  │ - YAML   │  │ - CLI   │  │ - JSONL  │
│ - Context  │  │ - Schema │  │ - IDE   │  │ - Metrics│
│ - ML(opt)  │  │ - Valid  │  │ - Emoji │  │ - Events │
└────────────┘  └──────────┘  └─────────┘  └──────────┘
```

### Data Flow

```
1. User Attempts Code Edit
    ↓
2. File Operation Interceptor catches request
    file_path="src/api/auth.py"
    user_intent="add JWT authentication"
    ↓
3. WorkflowEnforcer.intercept_code_edit()
    ↓
4. IntentDetector.detect_workflow(user_intent)
    → Analyzes keywords: ["add", "authentication"]
    → Confidence: 85% (*build workflow)
    ↓
5. EnforcementConfig.get_policy()
    → Mode: "blocking"
    → Threshold: 60%
    → Confidence 85% > Threshold 60% ✓
    ↓
6. Enforcement Decision: BLOCK
    ↓
7. MessageFormatter.format_blocking_message()
    → Shows workflow suggestion
    → Lists benefits
    → Provides override instructions
    ↓
8. Return to Application Layer
    action="block"
    message="⚠️  Use @simple-mode *build instead..."
    ↓
9. User sees message and chooses:
    Option A: Use @simple-mode *build (recommended)
    Option B: Add --skip-enforcement flag (override)
```

---

## Component Specifications

### 1. WorkflowEnforcer (Core Engine)

**Purpose:** Coordinate enforcement workflow from interception to decision.

**Location:** `tapps_agents/workflow/enforcer.py` (250 lines)

**Responsibilities:**
- Intercept file operations before execution
- Coordinate intent detection, policy enforcement, and messaging
- Provide override mechanisms
- Log enforcement events

**Public Interface:**
```python
class WorkflowEnforcer:
    """Core workflow enforcement engine."""

    def __init__(
        self,
        config: EnforcementConfig,
        intent_detector: IntentDetector,
        message_formatter: MessageFormatter,
        analytics_logger: Optional[AnalyticsLogger] = None
    ):
        """Initialize enforcer with dependencies."""

    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool = False,
        skip_enforcement: bool = False
    ) -> EnforcementResult:
        """
        Intercept code edit and enforce workflow policy.

        Args:
            file_path: Target file path
            user_intent: User's intent/description
            is_new_file: True if creating new file
            skip_enforcement: True to bypass enforcement

        Returns:
            EnforcementResult with action, workflow, message, confidence

        Performance:
            - Latency: <50ms (p95)
            - Memory: <1MB per call
        """

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "WorkflowEnforcer":
        """Factory method to create enforcer from config file."""
```

**Data Structures:**
```python
@dataclass
class EnforcementResult:
    """Result of enforcement check."""
    action: Literal["block", "warn", "allow"]
    workflow: Optional[WorkflowType]  # "*build", "*fix", "*refactor", "*review"
    message: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
```

**Algorithm:**
```python
def intercept_code_edit(...) -> EnforcementResult:
    # 1. Check skip flag
    if skip_enforcement:
        return EnforcementResult(action="allow", ...)

    # 2. Detect workflow type and confidence
    workflow, confidence = self.intent_detector.detect_workflow(user_intent)

    # 3. Check confidence threshold
    if confidence < self.config.confidence_threshold:
        return EnforcementResult(action="allow", ...)

    # 4. Apply enforcement policy
    if self.config.mode == "blocking":
        message = self.message_formatter.format_blocking_message(...)
        action = "block"
    elif self.config.mode == "warning":
        message = self.message_formatter.format_warning_message(...)
        action = "warn"
    else:  # silent
        action = "allow"
        message = ""

    # 5. Log event
    if self.analytics_logger:
        self.analytics_logger.log_enforcement(...)

    # 6. Return result
    return EnforcementResult(action, workflow, message, confidence)
```

**Performance Optimizations:**
- Cache configuration (loaded once)
- Lazy initialize components
- No blocking I/O in hot path
- Pre-compile keyword patterns

---

### 2. IntentDetector

**Purpose:** Classify user intent into workflow types with confidence scoring.

**Location:** `tapps_agents/workflow/intent_detector.py` (150 lines)

**Responsibilities:**
- Analyze user intent string
- Classify into workflow types (*build, *fix, *refactor, *review)
- Calculate confidence score (0-100%)
- Handle ambiguous cases

**Public Interface:**
```python
class IntentDetector:
    """Detect workflow type from user intent."""

    # Keyword definitions
    BUILD_KEYWORDS = ["build", "create", "add", "implement", "new", "feature", "develop", "write"]
    FIX_KEYWORDS = ["fix", "bug", "error", "issue", "broken", "repair", "correct", "resolve"]
    REFACTOR_KEYWORDS = ["refactor", "modernize", "improve", "update", "cleanup", "rewrite"]
    REVIEW_KEYWORDS = ["review", "check", "analyze", "inspect", "examine", "audit", "quality"]

    def detect_workflow(self, user_intent: str) -> tuple[WorkflowType, float]:
        """
        Detect workflow type from user intent.

        Args:
            user_intent: User's intent/description

        Returns:
            (workflow_type, confidence_score)
            confidence_score: 0.0-100.0

        Examples:
            >>> detect_workflow("add user authentication")
            ("*build", 85.0)

            >>> detect_workflow("fix login bug")
            ("*fix", 90.0)

        Performance:
            - Latency: <5ms
            - Memory: <100KB
        """

    def _calculate_score(self, intent: str, keywords: list[str]) -> float:
        """Calculate match score for keyword set (0-100%)."""

    def _analyze_context(self, file_path: Optional[Path] = None) -> dict[str, float]:
        """Optional: Analyze file context for additional signals."""
```

**Detection Algorithm:**
```python
def detect_workflow(user_intent: str) -> tuple[WorkflowType, float]:
    # 1. Normalize input
    intent_lower = user_intent.lower()
    intent_words = set(intent_lower.split())

    # 2. Calculate keyword scores
    build_score = _calculate_score(intent_lower, BUILD_KEYWORDS)
    fix_score = _calculate_score(intent_lower, FIX_KEYWORDS)
    refactor_score = _calculate_score(intent_lower, REFACTOR_KEYWORDS)
    review_score = _calculate_score(intent_lower, REVIEW_KEYWORDS)

    # 3. Select highest score
    scores = {
        "*build": build_score,
        "*fix": fix_score,
        "*refactor": refactor_score,
        "*review": review_score
    }

    workflow = max(scores, key=scores.get)
    confidence = scores[workflow]

    # 4. Apply confidence boosters
    # - Multiple keyword matches: +10%
    # - File path context: +5%

    return workflow, min(confidence, 100.0)

def _calculate_score(intent: str, keywords: list[str]) -> float:
    # Count keyword matches
    matches = sum(1 for kw in keywords if kw in intent)

    # Base score: 60% per match (max 100%)
    base_score = min(matches * 60, 100)

    # Position bonus: +10% if keyword at start
    if any(intent.startswith(kw) for kw in keywords):
        base_score += 10

    return min(base_score, 100.0)
```

**Confidence Levels:**
- **High (80-100%):** Clear intent, strong keyword match
- **Medium (60-79%):** Moderate confidence, some ambiguity
- **Low (<60%):** Unclear intent, no enforcement triggered

---

### 3. MessageFormatter

**Purpose:** Format enforcement messages for user display.

**Location:** `tapps_agents/workflow/message_formatter.py` (100 lines)

**Responsibilities:**
- Format blocking mode messages
- Format warning mode messages
- Include workflow benefits
- Provide override instructions
- Support multiple output formats (CLI, IDE)

**Public Interface:**
```python
class MessageFormatter:
    """Format enforcement messages for users."""

    def format_blocking_message(
        self,
        workflow: WorkflowType,
        user_intent: str,
        file_path: Path,
        confidence: float
    ) -> str:
        """Format blocking mode message with benefits and examples."""

    def format_warning_message(
        self,
        workflow: WorkflowType,
        user_intent: str,
        confidence: float
    ) -> str:
        """Format warning mode message."""

    def _get_workflow_benefits(self, workflow: WorkflowType) -> list[str]:
        """Get benefits list for workflow type."""

    def _get_override_instructions(self) -> str:
        """Get override instructions."""
```

**Message Templates:**

**Blocking Mode:**
```
⚠️  Detected direct code edit for: {file_path}

TappsCodingAgents workflow enforcement is active.
Use @simple-mode {workflow} instead for automatic quality gates.

Detected Intent: {workflow} (confidence: {confidence}%)

Recommended:
@simple-mode {workflow} "{user_intent}"

This workflow will automatically:
  ✅ Implement code
  ✅ Review (Ruff, mypy, security)
  ✅ Generate tests (≥80% coverage)
  ✅ Enforce quality gates (loopback if <70)

Why workflows?
- Write code fast and correct the first time
- Automatic quality gates and loopbacks
- Comprehensive test generation (≥80% coverage)
- Early bug detection
- Full traceability

To proceed with direct edit:
- Add --skip-enforcement flag
- Or set enforcement_mode: "warning" in .tapps-agents/config.yaml

TappsCodingAgents: Senior Developer behavior by default.
```

**Warning Mode:**
```
⚠️  Workflow Suggestion

Detected Intent: {workflow} (confidence: {confidence}%)

For best results, consider using:
@simple-mode {workflow} "{user_intent}"

Benefits: Auto-validation, auto-testing, quality gates

Press Enter to continue with direct edit, or use workflow.
```

---

### 4. EnforcementConfig

**Purpose:** Load and manage enforcement configuration.

**Location:** `tapps_agents/core/llm_behavior.py` (150 lines)

**Responsibilities:**
- Load configuration from `.tapps-agents/config.yaml`
- Validate configuration structure
- Provide defaults when config missing
- Support hot-reload for configuration changes

**Public Interface:**
```python
@dataclass
class EnforcementConfig:
    """Workflow enforcement configuration."""

    mode: Literal["blocking", "warning", "silent"] = "blocking"
    confidence_threshold: float = 60.0  # 0-100%
    suggest_workflows: bool = True
    block_direct_edits: bool = True
    log_events: bool = True
    analytics_enabled: bool = True

    @classmethod
    def from_config_file(cls, config_path: Optional[Path] = None) -> "EnforcementConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file (default: .tapps-agents/config.yaml)

        Returns:
            EnforcementConfig with loaded or default values

        Raises:
            ConfigValidationError: If configuration is invalid
        """

    def validate(self) -> list[str]:
        """
        Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """

    @property
    def is_blocking(self) -> bool:
        """Check if enforcement mode is blocking."""
        return self.mode == "blocking"

    @property
    def is_warning(self) -> bool:
        """Check if enforcement mode is warning."""
        return self.mode == "warning"

    @property
    def is_silent(self) -> bool:
        """Check if enforcement mode is silent."""
        return self.mode == "silent"
```

**Configuration Schema (YAML):**
```yaml
llm_behavior:
  # Mode: senior-developer (proactive) or intern (reactive)
  mode: "senior-developer"

  # Workflow enforcement configuration
  workflow_enforcement:
    # Enforcement mode: blocking, warning, silent
    # - blocking: Prevent direct edits, require workflow
    # - warning: Warn but allow bypass
    # - silent: No enforcement, only logging
    mode: "blocking"

    # Confidence threshold (0-100%)
    # Only trigger suggestion if confidence >= threshold
    confidence_threshold: 60

    # Suggest workflows proactively
    suggest_workflows: true

    # Block direct edits (requires workflow usage)
    block_direct_edits: true

    # Log enforcement events
    log_events: true

    # Enable analytics
    analytics_enabled: true
```

**Validation Rules:**
- `mode`: Must be "blocking", "warning", or "silent"
- `confidence_threshold`: Must be 0-100
- Boolean flags: Must be true/false

---

## Integration Architecture

### Integration Point 1: ImplementerAgent

**File:** `tapps_agents/agents/implementer/agent.py`

**Integration:**
```python
class ImplementerAgent:
    def __init__(self, ...):
        # Add enforcer dependency
        self.enforcer = WorkflowEnforcer.from_config()

    def implement(self, prompt: str, file_path: str, skip_enforcement: bool = False):
        """Implement code with enforcement check."""

        # ENFORCEMENT HOOK (before implementation)
        if not skip_enforcement:
            result = self.enforcer.intercept_code_edit(
                file_path=Path(file_path),
                user_intent=prompt,
                is_new_file=not Path(file_path).exists()
            )

            if result.action == "block":
                # Block implementation, show message
                raise EnforcementError(result.message)
            elif result.action == "warn":
                # Show warning, continue
                print(result.message)
                # Wait for user confirmation...

        # Continue with implementation
        ...
```

### Integration Point 2: CLI

**File:** `tapps_agents/cli.py`

**Integration:**
```python
@cli.command()
@click.option('--skip-enforcement', is_flag=True, help='Skip workflow enforcement')
def implement(prompt: str, file: str, skip_enforcement: bool):
    """Implement code in file."""

    # ENFORCEMENT HOOK (CLI level)
    if not skip_enforcement:
        enforcer = WorkflowEnforcer.from_config()
        result = enforcer.intercept_code_edit(
            file_path=Path(file),
            user_intent=prompt
        )

        if result.action == "block":
            click.echo(result.message, err=True)
            sys.exit(1)
        elif result.action == "warn":
            click.echo(result.message, err=True)
            if not click.confirm("Continue anyway?"):
                sys.exit(0)

    # Continue with command
    implementer = ImplementerAgent()
    implementer.implement(prompt, file, skip_enforcement=True)
```

---

## Security Architecture

### Threat Model

**Threats:**
1. **Configuration Injection**: Malicious YAML in config file
2. **Bypass Vulnerabilities**: Unauthorized enforcement bypass
3. **Information Disclosure**: Leaking sensitive data in logs

**Mitigations:**

**T1: Configuration Injection**
- **Control:** YAML schema validation
- **Implementation:**
  ```python
  def validate_config(config: dict) -> list[str]:
      # Whitelist allowed keys
      allowed_keys = {"mode", "confidence_threshold", ...}
      if any(key not in allowed_keys for key in config):
          return ["Invalid configuration key"]

      # Validate types
      if not isinstance(config["mode"], str):
          return ["mode must be string"]

      # Validate values
      if config["mode"] not in ["blocking", "warning", "silent"]:
          return ["Invalid mode value"]

      return []
  ```

**T2: Bypass Vulnerabilities**
- **Control:** Audit logging of bypass attempts
- **Implementation:**
  ```python
  if skip_enforcement:
      analytics_logger.log_bypass(
          user=get_current_user(),
          file_path=file_path,
          timestamp=datetime.now()
      )
  ```
- **Rate Limiting:** Max 10 bypasses/hour per user

**T3: Information Disclosure**
- **Control:** Sanitize logs (no sensitive data)
- **Implementation:**
  ```python
  def sanitize_log_entry(entry: dict) -> dict:
      # Remove sensitive fields
      entry.pop("user_token", None)
      entry.pop("api_key", None)
      return entry
  ```

### Security Checklist

- [ ] YAML configuration validated against schema
- [ ] No code execution from configuration
- [ ] Bypass attempts logged and audited
- [ ] Rate limiting on bypass usage
- [ ] No sensitive data in logs
- [ ] Secure file permissions (0600) on config

---

## Performance Architecture

### Performance Requirements

| Metric | Requirement | Strategy |
|--------|-------------|----------|
| Latency | <50ms (p95) | Cache config, optimize keyword matching |
| Memory | <10MB | Lazy initialization, minimal state |
| CPU | <5% | No blocking I/O, pre-compiled patterns |
| Throughput | 1000+ ops/sec | Stateless design, minimal locking |

### Optimization Strategies

**1. Configuration Caching**
```python
class WorkflowEnforcer:
    _config_cache: ClassVar[Optional[EnforcementConfig]] = None
    _cache_timestamp: ClassVar[Optional[datetime]] = None

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "WorkflowEnforcer":
        # Cache config for 60 seconds
        if cls._config_cache and (datetime.now() - cls._cache_timestamp) < timedelta(seconds=60):
            return cls(cls._config_cache, ...)

        # Load and cache
        config = EnforcementConfig.from_config_file(config_path)
        cls._config_cache = config
        cls._cache_timestamp = datetime.now()
        return cls(config, ...)
```

**2. Keyword Pre-compilation**
```python
class IntentDetector:
    def __init__(self):
        # Pre-compile keyword patterns
        self._build_pattern = self._compile_keywords(self.BUILD_KEYWORDS)
        self._fix_pattern = self._compile_keywords(self.FIX_KEYWORDS)
        ...

    def _compile_keywords(self, keywords: list[str]) -> re.Pattern:
        # Compile regex pattern once
        pattern = r'\b(' + '|'.join(keywords) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
```

**3. Lazy Initialization**
```python
class WorkflowEnforcer:
    def __init__(self, config: EnforcementConfig):
        self.config = config
        self._intent_detector: Optional[IntentDetector] = None
        self._message_formatter: Optional[MessageFormatter] = None

    @property
    def intent_detector(self) -> IntentDetector:
        if self._intent_detector is None:
            self._intent_detector = IntentDetector()
        return self._intent_detector
```

### Performance Benchmarks

**Target Metrics:**
```python
def test_interception_latency():
    enforcer = WorkflowEnforcer.from_config()

    start = time.time()
    result = enforcer.intercept_code_edit("test.py", "add feature")
    latency = (time.time() - start) * 1000  # ms

    assert latency < 50, f"Latency {latency}ms exceeds 50ms threshold"

def test_memory_overhead():
    mem_before = get_memory_usage()
    enforcer = WorkflowEnforcer.from_config()
    enforcer.intercept_code_edit("test.py", "add feature")
    mem_after = get_memory_usage()

    overhead = mem_after - mem_before
    assert overhead < 10 * 1024 * 1024, f"Memory overhead {overhead} exceeds 10MB"
```

---

## Deployment Architecture

### File Structure

```
tapps_agents/
├── workflow/
│   ├── __init__.py
│   ├── enforcer.py              # WorkflowEnforcer (250 lines)
│   ├── intent_detector.py       # IntentDetector (150 lines)
│   └── message_formatter.py     # MessageFormatter (100 lines)
├── core/
│   ├── __init__.py
│   └── llm_behavior.py          # EnforcementConfig (150 lines)
└── agents/
    └── implementer/
        └── agent.py             # Modified (add enforcement hook)

tests/
├── test_workflow_enforcer.py    # Unit tests (200 lines)
├── test_intent_detector.py      # Unit tests (150 lines)
├── test_message_formatter.py    # Unit tests (100 lines)
├── test_llm_behavior.py         # Unit tests (100 lines)
├── integration/
│   └── test_enforcer_integration.py  # Integration tests (150 lines)
└── e2e/
    └── test_workflow_enforcement_e2e.py  # E2E tests (100 lines)

.tapps-agents/
└── config.yaml                  # Configuration file
```

### Configuration Deployment

**Default Configuration:**
```yaml
# .tapps-agents/config.yaml
llm_behavior:
  mode: "senior-developer"
  workflow_enforcement:
    mode: "blocking"
    confidence_threshold: 60
    suggest_workflows: true
    block_direct_edits: true
    log_events: true
    analytics_enabled: true
```

**Per-Project Override:**
```yaml
# project-specific-config.yaml (optional)
llm_behavior:
  workflow_enforcement:
    mode: "warning"  # Less strict for this project
    confidence_threshold: 70  # Higher threshold
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Language | Python 3.12+ | Type hints, dataclasses, modern syntax |
| Configuration | PyYAML | Standard, human-readable format |
| Logging | Python logging | Built-in, flexible, performant |
| Testing | pytest | De facto standard, rich ecosystem |

### Dependencies

**Production Dependencies:**
```toml
[tool.poetry.dependencies]
python = "^3.12"
pyyaml = "^6.0"
```

**Development Dependencies:**
```toml
[tool.poetry.dev-dependencies]
pytest = "^7.4"
pytest-cov = "^4.1"
ruff = "^0.1"
mypy = "^1.7"
```

**Rationale:**
- **Minimal Dependencies:** Only PyYAML added (config parsing)
- **Standard Library:** Maximize use of Python stdlib
- **Performance:** No heavy dependencies (e.g., ML libraries)
- **Security:** Fewer dependencies = smaller attack surface

---

## Architecture Decision Records (ADRs)

### ADR-001: Interceptor Pattern

**Context:** Need to intercept file operations before execution.

**Decision:** Use Interceptor pattern with WorkflowEnforcer as central coordinator.

**Alternatives Considered:**
- **Decorator Pattern:** Too intrusive, requires decorating all file operations
- **Aspect-Oriented Programming:** Too complex, adds dependencies

**Rationale:**
- Clean separation of concerns
- Easy to test and mock
- Minimal coupling with existing code

**Consequences:**
- (+) Modular, testable architecture
- (+) Easy to add new enforcement modes
- (-) Adds latency (<50ms acceptable)

### ADR-002: Keyword-Based Intent Detection

**Context:** Need to classify user intent with ≥60% confidence.

**Decision:** Use keyword-based classification with confidence scoring.

**Alternatives Considered:**
- **ML-Based Classification:** Too complex, adds dependencies (transformers, torch)
- **Rule-Based System:** Too rigid, difficult to extend

**Rationale:**
- Simple, fast, no external dependencies
- Good enough for ≥60% confidence threshold
- Easy to extend with more keywords

**Consequences:**
- (+) Fast (<5ms), no ML overhead
- (+) Transparent, debuggable logic
- (-) May miss complex intents (acceptable trade-off)

### ADR-003: YAML Configuration

**Context:** Need configurable enforcement behavior.

**Decision:** Use YAML configuration in `.tapps-agents/config.yaml`.

**Alternatives Considered:**
- **JSON:** Less human-readable
- **TOML:** Less familiar to users
- **Python Code:** Security risk (code execution)

**Rationale:**
- Human-readable, familiar format
- Standard in Python ecosystem (requirements.yaml, docker-compose.yaml)
- Safe (no code execution)

**Consequences:**
- (+) User-friendly configuration
- (+) Secure (no code execution)
- (-) Requires PyYAML dependency (acceptable)

---

## Next Steps

### Implementation Order

1. ✅ **EnforcementConfig** (llm_behavior.py) - Foundation
2. ✅ **IntentDetector** (intent_detector.py) - Intelligence
3. ✅ **MessageFormatter** (message_formatter.py) - User experience
4. ✅ **WorkflowEnforcer** (enforcer.py) - Core coordination
5. ✅ **Integration** (ImplementerAgent, CLI) - Hooks
6. ✅ **Testing** (unit, integration, E2E)

### Development Workflow

```bash
# Use @simple-mode *build for each component (dogfooding)
@simple-mode *build "ENH-001-S4: Configuration System"
@simple-mode *build "ENH-001-S2: Intent Detection System"
@simple-mode *build "ENH-001-S3: User Messaging System"
@simple-mode *build "ENH-001-S1: Core Workflow Enforcer"
```

---

**Architecture Complete**
**Date:** 2026-01-29
**Next Step:** Step 4 - Design API/data models (@designer)
