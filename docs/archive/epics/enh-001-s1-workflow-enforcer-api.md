# API Design: ENH-001-S1 Core Workflow Enforcer

**Story ID:** ENH-001-S1
**Epic:** ENH-001 Workflow Enforcement System
**Created:** 2026-01-29
**Status:** API Design Complete
**API Type:** Python Library API (Internal)

---

## Table of Contents

1. [Overview](#overview)
2. [Core API: WorkflowEnforcer](#core-api-workflowenforcer)
3. [Data Models](#data-models)
4. [Integration APIs](#integration-apis)
5. [Error Handling](#error-handling)
6. [Usage Examples](#usage-examples)
7. [API Versioning](#api-versioning)
8. [Performance Contract](#performance-contract)
9. [Security Contract](#security-contract)

---

## Overview

### Purpose

The Workflow Enforcer API provides a programmatic interface for intercepting file write/edit operations and enforcing workflow usage based on configuration.

### API Type

**Python Library API** (Internal to TappsCodingAgents)

- **Language:** Python 3.12+
- **API Style:** Object-oriented, synchronous
- **Type Safety:** Fully typed with type hints
- **Documentation:** Google-style docstrings

### Key Design Principles

1. **Simple Interface:** Single primary method (`intercept_code_edit()`)
2. **Type-Safe:** Full type hints for IDE support and type checking
3. **Fail-Safe:** Never raises exceptions from main API (returns "allow" on error)
4. **Performance:** <50ms p95 latency guarantee
5. **Testable:** Dependency injection for configuration

---

## Core API: WorkflowEnforcer

### Class: `WorkflowEnforcer`

**Module:** `tapps_agents.workflow.enforcer`

**Responsibility:** Make enforcement decisions based on configuration and file operation context

#### Constructor

```python
def __init__(
    self,
    config_path: Path | None = None,
    config: EnforcementConfig | None = None
) -> None:
    """
    Initialize workflow enforcer.

    Args:
        config_path: Path to configuration file. If None, uses default
            (.tapps-agents/config.yaml in current directory).
        config: Pre-loaded EnforcementConfig instance. If provided,
            overrides config_path. Useful for testing and custom configs.

    Example:
        # Use default config from .tapps-agents/config.yaml
        enforcer = WorkflowEnforcer()

        # Use custom config path
        enforcer = WorkflowEnforcer(config_path=Path("custom.yaml"))

        # Use pre-loaded config (for testing)
        config = EnforcementConfig(mode="warning")
        enforcer = WorkflowEnforcer(config=config)

    Performance:
        - Initialization: <10ms (config load cached)
        - Memory overhead: <1MB
    """
```

**Constructor Contract:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `config_path` | `Path \| None` | No | `None` | Path to config file (default: `.tapps-agents/config.yaml`) |
| `config` | `EnforcementConfig \| None` | No | `None` | Pre-loaded config (overrides `config_path` if provided) |

**Constructor Behavior:**
- If `config` is provided, use it directly (no file loading)
- If `config_path` is provided, load config from that path
- If neither provided, load from default path (`.tapps-agents/config.yaml`)
- If config file missing or invalid, use default `EnforcementConfig()` values
- Logs info message with config mode after initialization

---

#### Method: `intercept_code_edit()`

**Primary Public API Method**

```python
def intercept_code_edit(
    self,
    file_path: Path,
    user_intent: str,
    is_new_file: bool,
    skip_enforcement: bool = False
) -> EnforcementDecision:
    """
    Intercept file write/edit operation and make enforcement decision.

    This is the main enforcement method. It evaluates the file operation
    context, checks configuration, and returns a decision indicating whether
    to block, warn, or allow the operation.

    Args:
        file_path: Path to file being written or edited. Can be absolute
            or relative. Used for enforcement decision and logging.
        user_intent: User's intent or description from prompt/conversation
            context. Used for decision logic and message generation.
            Can be empty string if intent unknown.
        is_new_file: True if creating a new file, False if editing existing
            file. Affects enforcement decision (future: may treat new files
            differently).
        skip_enforcement: Override flag to bypass enforcement. Set to True
            to always return "allow" decision. Used by CLI --skip-enforcement.

    Returns:
        EnforcementDecision: Typed dict with enforcement decision fields:
            - action: "block" | "warn" | "allow"
            - message: User-facing message (empty for silent/allow)
            - should_block: Boolean indicating if operation should be blocked
            - confidence: Confidence score (0.0 for Story 1; Story 2 populates)

    Raises:
        Never raises exceptions. Errors are caught, logged, and result in
        "allow" decision (fail-safe design).

    Performance Contract:
        - Latency: <50ms (p95) for normal operation
        - Memory: No allocations beyond return value
        - CPU: <5% overhead on file operations

    Example:
        >>> enforcer = WorkflowEnforcer()
        >>> decision = enforcer.intercept_code_edit(
        ...     file_path=Path("src/app.py"),
        ...     user_intent="Add authentication to login endpoint",
        ...     is_new_file=False
        ... )
        >>> if decision["should_block"]:
        ...     print(decision["message"])
        ...     return  # Don't perform file operation
        ... elif decision["action"] == "warn":
        ...     print(f"Warning: {decision['message']}")
        ...     # Continue with file operation
        >>> # Proceed with file operation

    Decision Logic:
        1. If skip_enforcement=True -> return "allow"
        2. If config.mode="silent" -> return "allow" (no user message)
        3. If config.mode="blocking" and config.block_direct_edits=True
           -> return "block" (should_block=True)
        4. If config.mode="warning" -> return "warn" (should_block=False)
        5. Otherwise -> return "allow"

    Thread Safety:
        This method is thread-safe. Config is loaded once during initialization
        and cached. No shared mutable state during enforcement check.
    """
```

**Method Contract:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | `Path` | Yes | - | Path to file being written/edited |
| `user_intent` | `str` | Yes | - | User's intent from prompt (can be empty) |
| `is_new_file` | `bool` | Yes | - | True if creating file, False if editing |
| `skip_enforcement` | `bool` | No | `False` | Override to bypass enforcement |

| Returns | Type | Description |
|---------|------|-------------|
| `decision` | `EnforcementDecision` | Enforcement decision with action, message, should_block |

**Decision Logic Table:**

| Config Mode | `skip_enforcement` | `block_direct_edits` | Action | `should_block` |
|-------------|-------------------|---------------------|--------|----------------|
| Any | `True` | Any | `"allow"` | `False` |
| `"silent"` | `False` | Any | `"allow"` | `False` |
| `"blocking"` | `False` | `True` | `"block"` | `True` |
| `"blocking"` | `False` | `False` | `"block"` | `False` |
| `"warning"` | `False` | Any | `"warn"` | `False` |

**Performance Guarantees:**

- **Latency:** <50ms p95 (99.5% of calls complete in <50ms)
- **Memory:** No heap allocations beyond return value (<1KB)
- **CPU:** <5% CPU overhead during file operations
- **Caching:** Config cached after first load (subsequent calls <5ms)

---

## Data Models

### TypedDict: `EnforcementDecision`

**Module:** `tapps_agents.workflow.enforcer`

**Purpose:** Structured result of enforcement decision

```python
from typing import TypedDict, Literal

class EnforcementDecision(TypedDict):
    """
    Enforcement decision result.

    Returned by WorkflowEnforcer.intercept_code_edit() to indicate whether
    to block, warn, or allow a file operation.

    Fields:
        action: Enforcement action based on configuration mode:
            - "block": Operation should be blocked (blocking mode)
            - "warn": Show warning but allow operation (warning mode)
            - "allow": Allow operation without message (silent/skip)

        message: User-facing message to display:
            - For "block": Explanation + workflow suggestion
            - For "warn": Warning + workflow suggestion
            - For "allow": Empty string (no message)

        should_block: Whether to actually block the operation:
            - True: Raise error or return error response
            - False: Log message (if any) and proceed
            - Computed: action=="block" AND config.block_direct_edits==True

        confidence: Confidence score (0-100):
            - Story 1: Always 0.0 (placeholder)
            - Story 2: Will populate with intent detection confidence
            - Used to determine if enforcement should apply

    Example:
        >>> decision: EnforcementDecision = {
        ...     "action": "block",
        ...     "message": "Use @simple-mode *build instead",
        ...     "should_block": True,
        ...     "confidence": 0.0
        ... }
        >>> if decision["should_block"]:
        ...     raise RuntimeError(decision["message"])
    """
    action: Literal["block", "warn", "allow"]
    message: str
    should_block: bool
    confidence: float
```

**Field Specifications:**

| Field | Type | Values | Required | Description |
|-------|------|--------|----------|-------------|
| `action` | `Literal["block", "warn", "allow"]` | `"block"`, `"warn"`, `"allow"` | Yes | Enforcement action |
| `message` | `str` | Any string (empty for "allow") | Yes | User-facing message |
| `should_block` | `bool` | `True`, `False` | Yes | Whether to block operation |
| `confidence` | `float` | `0.0` (Story 1), `0.0-100.0` (Story 2) | Yes | Confidence score |

**Invariants:**

1. If `action == "allow"` then `message == ""`
2. If `action == "allow"` then `should_block == False`
3. If `should_block == True` then `action == "block"`
4. `confidence` is always `0.0` for Story 1 (no intent detection yet)

**Usage Patterns:**

```python
# Check if operation should be blocked
if decision["should_block"]:
    # Block operation (raise error or return error response)
    raise RuntimeError(f"Blocked: {decision['message']}")

# Check for warning
elif decision["action"] == "warn":
    # Log warning but continue
    logger.warning(decision["message"])

# Check for allow (silent)
elif decision["action"] == "allow":
    # No message, proceed silently
    pass

# Proceed with file operation
perform_file_write()
```

---

### Dataclass: `EnforcementConfig`

**Module:** `tapps_agents.core.llm_behavior` (Story 4 - COMPLETE)

**Purpose:** Configuration for workflow enforcement system

```python
from dataclasses import dataclass
from typing import Literal
from pathlib import Path

@dataclass
class EnforcementConfig:
    """
    Configuration for workflow enforcement system.

    Controls how the system enforces workflow usage when LLMs attempt
    direct code edits. Loaded from .tapps-agents/config.yaml.

    Attributes:
        mode: Enforcement mode:
            - "blocking": Block direct edits, require workflows
            - "warning": Show warning but allow edits
            - "silent": Log only, no user-facing messages

        confidence_threshold: Minimum confidence score (0-100) to trigger
            enforcement. Lower values = more aggressive enforcement.
            Reserved for Story 2 (Intent Detection).

        suggest_workflows: Whether to suggest specific workflows in messages.
            If True, messages include workflow recommendations.

        block_direct_edits: Whether to actually block operations in
            blocking mode (vs just showing message).
            If False, "blocking" mode shows message but allows operation.

    Example:
        >>> # Load from default config file
        >>> config = EnforcementConfig.from_config_file()
        >>> print(config.mode)
        'blocking'

        >>> # Use defaults
        >>> config = EnforcementConfig()
        >>> assert config.mode == "blocking"
        >>> assert config.confidence_threshold == 60.0
    """
    mode: Literal["blocking", "warning", "silent"] = "blocking"
    confidence_threshold: float = 60.0
    suggest_workflows: bool = True
    block_direct_edits: bool = True

    @classmethod
    def from_config_file(
        cls,
        config_path: Path | None = None
    ) -> "EnforcementConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file (default: .tapps-agents/config.yaml)

        Returns:
            EnforcementConfig instance

        Raises:
            ValueError: If YAML is invalid or config values fail validation
        """
```

**Configuration File Format:** `.tapps-agents/config.yaml`

```yaml
llm_behavior:
  mode: "senior-developer"

  workflow_enforcement:
    mode: "blocking"           # "blocking" | "warning" | "silent"
    confidence_threshold: 60   # 0-100 (reserved for Story 2)
    suggest_workflows: true    # Include workflow suggestions in messages
    block_direct_edits: true   # Actually block in blocking mode
```

---

## Integration APIs

### Integration 1: AsyncFileOps Hook

**Module:** `tapps_agents.core.async_file_ops`

**Modified Method:** `AsyncFileOps.write_file()`

#### API Contract

```python
class AsyncFileOps:
    @staticmethod
    async def write_file(
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
        user_intent: str = "",           # NEW PARAMETER
        skip_enforcement: bool = False,  # NEW PARAMETER
    ) -> None:
        """
        Write file with enforcement check.

        Checks workflow enforcement before writing file. If enforcement
        blocks the operation, raises RuntimeError. Otherwise, writes file
        asynchronously.

        Args:
            file_path: Path to file to write
            content: Content to write to file
            encoding: File encoding (default: utf-8)
            create_parents: Create parent directories if needed
            user_intent: User's intent from prompt (for enforcement)
            skip_enforcement: Skip enforcement check (--skip-enforcement flag)

        Raises:
            RuntimeError: If workflow enforcement blocks the operation
            OSError: If file write fails (filesystem error)

        Example:
            # Without enforcement (backward compatible)
            await AsyncFileOps.write_file(
                file_path=Path("app.py"),
                content="print('hello')"
            )

            # With enforcement
            await AsyncFileOps.write_file(
                file_path=Path("app.py"),
                content="print('hello')",
                user_intent="Add hello world feature"
            )

            # Skip enforcement
            await AsyncFileOps.write_file(
                file_path=Path("app.py"),
                content="print('hello')",
                skip_enforcement=True
            )

        Enforcement Behavior:
            1. Import WorkflowEnforcer (lazy import)
            2. Call enforcer.intercept_code_edit(...)
            3. If decision["should_block"]:
                  raise RuntimeError(decision["message"])
            4. If decision["action"] == "warn":
                  logger.warning(decision["message"])
            5. Proceed with file write
        """
```

**Parameter Changes:**

| Parameter | Type | Required | Default | Change |
|-----------|------|----------|---------|--------|
| `user_intent` | `str` | No | `""` | **NEW** |
| `skip_enforcement` | `bool` | No | `False` | **NEW** |

**Backward Compatibility:**
- New parameters are optional with default values
- Existing callers work without modification
- Enforcement is **opt-in** until `user_intent` is populated

**Error Handling:**

```python
# Blocking enforcement
try:
    await AsyncFileOps.write_file(
        file_path=Path("app.py"),
        content="code",
        user_intent="Add feature"
    )
except RuntimeError as e:
    # Enforcement blocked operation
    print(f"Blocked: {e}")
    return
```

---

### Integration 2: MCP Filesystem Server Hook

**Module:** `tapps_agents.mcp.servers.filesystem`

**Modified Method:** `FilesystemServer.write_file()`

#### API Contract

```python
class FilesystemServer:
    def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
        user_intent: str = "",           # NEW PARAMETER
        skip_enforcement: bool = False,  # NEW PARAMETER
    ) -> dict[str, Any]:
        """
        Write file with enforcement check (MCP protocol).

        Args:
            file_path: Path to file to write (string for MCP compatibility)
            content: Content to write to file
            encoding: File encoding (default: utf-8)
            create_dirs: Create parent directories if needed
            user_intent: User's intent from prompt (for enforcement)
            skip_enforcement: Skip enforcement check

        Returns:
            dict: MCP response with status and metadata:
                - file_path: Path to file written
                - written: True if write successful, False if blocked
                - blocked: True if enforcement blocked, False otherwise
                - message: Enforcement message (if blocked)

        Example:
            # Normal operation
            result = server.write_file(
                file_path="app.py",
                content="print('hello')",
                user_intent="Add hello world"
            )
            # result = {
            #     "file_path": "app.py",
            #     "written": True,
            #     "blocked": False
            # }

            # Blocked by enforcement
            result = server.write_file(
                file_path="app.py",
                content="print('hello')",
                user_intent="Add hello world"
            )
            # result = {
            #     "file_path": "app.py",
            #     "written": False,
            #     "blocked": True,
            #     "message": "Use @simple-mode *build instead..."
            # }

        Enforcement Behavior:
            1. Convert file_path string to Path object
            2. Call enforcer.intercept_code_edit(...)
            3. If decision["should_block"]:
                  return {"blocked": True, "message": ...}
            4. If decision["action"] == "warn":
                  logger.warning(decision["message"])
            5. Proceed with file write
            6. Return {"written": True, "blocked": False}
        """
```

**Response Schema:**

```python
# Success response (allowed or warned)
{
    "file_path": str,       # Path to file written
    "written": bool,        # True if write successful
    "blocked": bool,        # False for success
}

# Blocked response
{
    "file_path": str,       # Path that was blocked
    "written": bool,        # False (not written)
    "blocked": bool,        # True (enforcement blocked)
    "message": str,         # Enforcement message
}
```

**MCP Client Usage:**

```python
# Call MCP server
response = mcp_client.call("filesystem.write_file", {
    "file_path": "app.py",
    "content": "print('hello')",
    "user_intent": "Add hello world"
})

# Check if blocked
if response["blocked"]:
    print(f"Blocked: {response['message']}")
else:
    print(f"Written: {response['file_path']}")
```

---

### Integration 3: CLI Flag `--skip-enforcement`

**Module:** `tapps_agents/cli.py`

**CLI Argument:**

```python
parser.add_argument(
    "--skip-enforcement",
    action="store_true",
    help="Skip workflow enforcement checks (allow direct edits)"
)
```

**Usage:**

```bash
# Skip enforcement for emergency fix
tapps-agents implementer implement "Add logging" src/app.py --skip-enforcement

# Normal operation (enforcement enabled if configured)
tapps-agents implementer implement "Add logging" src/app.py
```

**Flag Behavior:**
- Sets `skip_enforcement=True` parameter on file operations
- Bypasses all enforcement checks (returns "allow" immediately)
- Intended for emergency situations or testing

---

## Error Handling

### Error Categories

#### 1. Configuration Errors

**Scenario:** Config file missing, invalid YAML, invalid values

**Handling:**
- Log warning message
- Use default `EnforcementConfig()` values
- Continue with enforcement using defaults

**User Impact:** None (enforcement works with defaults)

```python
# Example
logger.warning("Failed to load config, using defaults: %s", e)
return EnforcementConfig()  # Default values
```

---

#### 2. Enforcement Errors

**Scenario:** Exception during `intercept_code_edit()`

**Handling:**
- Catch all exceptions
- Log error with stack trace
- Return "allow" decision (fail-safe)

**User Impact:** None (operation proceeds)

```python
# Example
try:
    # Enforcement logic
    ...
except Exception as e:
    logger.error("Enforcement check failed: %s", e, exc_info=True)
    return EnforcementDecision(
        action="allow",
        message="",
        should_block=False,
        confidence=0.0
    )
```

---

#### 3. Integration Errors (AsyncFileOps)

**Scenario:** Enforcement blocks operation

**Handling:**
- Raise `RuntimeError` with enforcement message
- Caller catches and handles

**User Impact:** File write blocked, error message shown

```python
# Example
if decision["should_block"]:
    raise RuntimeError(
        f"File operation blocked by workflow enforcer: {decision['message']}"
    )
```

---

#### 4. Integration Errors (MCP Filesystem)

**Scenario:** Enforcement blocks operation

**Handling:**
- Return MCP error response (dict with `blocked=True`)
- Caller checks response

**User Impact:** File write blocked, error message in response

```python
# Example
if decision["should_block"]:
    return {
        "file_path": str(path),
        "written": False,
        "blocked": True,
        "message": decision["message"]
    }
```

---

### Error Response Formats

**AsyncFileOps Error:**
```python
RuntimeError: File operation blocked by workflow enforcer: Use @simple-mode *build instead for automatic quality gates.
```

**MCP Filesystem Error:**
```json
{
    "file_path": "src/app.py",
    "written": false,
    "blocked": true,
    "message": "Use @simple-mode *build instead for automatic quality gates."
}
```

---

## Usage Examples

### Example 1: Basic Enforcement (Blocking Mode)

```python
from pathlib import Path
from tapps_agents.workflow.enforcer import WorkflowEnforcer

# Initialize enforcer with default config
enforcer = WorkflowEnforcer()

# Check enforcement before file write
decision = enforcer.intercept_code_edit(
    file_path=Path("src/app.py"),
    user_intent="Add authentication to login endpoint",
    is_new_file=False
)

# Handle decision
if decision["should_block"]:
    print(f"❌ Operation blocked: {decision['message']}")
    # Don't write file
else:
    print("✅ Operation allowed")
    # Write file
    with open("src/app.py", "w") as f:
        f.write("# New code")
```

**Output (Blocking Mode):**
```
❌ Operation blocked: Use @simple-mode *build instead for automatic quality gates.
```

---

### Example 2: Warning Mode

```python
# Config: mode="warning"
enforcer = WorkflowEnforcer()

decision = enforcer.intercept_code_edit(
    file_path=Path("src/app.py"),
    user_intent="Add logging",
    is_new_file=False
)

if decision["action"] == "warn":
    print(f"⚠️  Warning: {decision['message']}")

# Operation always proceeds (should_block=False)
with open("src/app.py", "w") as f:
    f.write("# New code")
```

**Output (Warning Mode):**
```
⚠️  Warning: Use @simple-mode *build instead for automatic quality gates.
```

---

### Example 3: Skip Enforcement (CLI Flag)

```python
# User passed --skip-enforcement flag
skip_enforcement = True

decision = enforcer.intercept_code_edit(
    file_path=Path("src/app.py"),
    user_intent="Emergency fix",
    is_new_file=False,
    skip_enforcement=skip_enforcement  # Bypass enforcement
)

# decision = {"action": "allow", "should_block": False, ...}
# Operation always allowed
with open("src/app.py", "w") as f:
    f.write("# Emergency fix")
```

---

### Example 4: AsyncFileOps Integration

```python
import asyncio
from pathlib import Path
from tapps_agents.core.async_file_ops import AsyncFileOps

async def main():
    try:
        await AsyncFileOps.write_file(
            file_path=Path("src/app.py"),
            content="# New feature",
            user_intent="Add user authentication"
        )
        print("✅ File written successfully")
    except RuntimeError as e:
        print(f"❌ Blocked: {e}")

asyncio.run(main())
```

**Output (Blocking Mode):**
```
❌ Blocked: File operation blocked by workflow enforcer: Use @simple-mode *build instead for automatic quality gates.
```

---

### Example 5: MCP Filesystem Integration

```python
from tapps_agents.mcp.servers.filesystem import FilesystemServer

server = FilesystemServer()

# Write file via MCP
response = server.write_file(
    file_path="src/app.py",
    content="# New feature",
    user_intent="Add user authentication"
)

if response["blocked"]:
    print(f"❌ Blocked: {response['message']}")
else:
    print(f"✅ Written: {response['file_path']}")
```

**Output (Blocking Mode):**
```json
{
    "file_path": "src/app.py",
    "written": false,
    "blocked": true,
    "message": "Use @simple-mode *build instead for automatic quality gates."
}
```

---

### Example 6: Testing with Custom Config

```python
from tapps_agents.workflow.enforcer import WorkflowEnforcer
from tapps_agents.core.llm_behavior import EnforcementConfig

# Create test config
test_config = EnforcementConfig(
    mode="warning",
    confidence_threshold=60.0,
    suggest_workflows=True,
    block_direct_edits=False
)

# Initialize enforcer with test config
enforcer = WorkflowEnforcer(config=test_config)

# Test enforcement
decision = enforcer.intercept_code_edit(
    file_path=Path("test.py"),
    user_intent="test",
    is_new_file=True
)

assert decision["action"] == "warn"
assert decision["should_block"] == False
```

---

## API Versioning

### Version Strategy

**Current Version:** v1.0.0 (Story 1)

**Versioning Approach:**
- **Story 1 (Current):** Basic enforcement API
- **Story 2 (Future):** Add intent detection (populate `confidence` field)
- **Story 3 (Future):** Rich message formatting (update `message` field)

**Backward Compatibility:**
- Story 2 changes are **backward compatible** (new field populated)
- Story 3 changes are **backward compatible** (message format enhanced)
- API contract remains stable across stories

### API Evolution

**Story 1 → Story 2 (Intent Detection):**

```python
# Story 1: confidence always 0.0
decision = enforcer.intercept_code_edit(...)
# decision["confidence"] == 0.0

# Story 2: confidence populated by intent detector
decision = enforcer.intercept_code_edit(...)
# decision["confidence"] == 85.0 (high confidence)
```

**Backward Compatibility:** Existing code continues to work; `confidence` field already exists (just populated with 0.0)

---

**Story 2 → Story 3 (Message Formatting):**

```python
# Story 2: basic message
decision = enforcer.intercept_code_edit(...)
# decision["message"] == "Use @simple-mode *build instead"

# Story 3: rich formatted message
decision = enforcer.intercept_code_edit(...)
# decision["message"] == "⚠️  Detected direct code edit for: src/app.py\n\nUse @simple-mode *build instead..."
```

**Backward Compatibility:** Message field is still a string; formatting enhanced but contract unchanged

---

## Performance Contract

### Performance Guarantees

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Latency (p50)** | <10ms | `time.perf_counter()` |
| **Latency (p95)** | <50ms | `time.perf_counter()` |
| **Latency (p99)** | <100ms | `time.perf_counter()` |
| **Memory Overhead** | <10MB | `tracemalloc` |
| **CPU Overhead** | <5% | `time.process_time()` |
| **Config Load Time** | <100ms | First load only (cached) |

### Performance Testing

**Test Method:**

```python
import time

latencies = []
for _ in range(100):
    start = time.perf_counter()
    decision = enforcer.intercept_code_edit(
        file_path=Path("test.py"),
        user_intent="test",
        is_new_file=False
    )
    end = time.perf_counter()
    latencies.append((end - start) * 1000)  # ms

p95 = sorted(latencies)[94]
assert p95 < 50.0, f"p95 latency {p95}ms exceeds 50ms"
```

---

## Security Contract

### Security Guarantees

1. **No Data Leakage:** Enforcement decisions logged at debug level only
2. **No Sensitive Data:** Config contains no secrets or sensitive data
3. **Fail-Safe:** Errors never expose sensitive information
4. **Input Validation:** All inputs validated via type hints

### Threat Model

**Threat:** User bypasses enforcement

**Mitigation:**
- Enforcement at lowest level (AsyncFileOps, MCP)
- All file operations hook enforcer

**Threat:** Configuration tampering

**Mitigation:**
- Config is user-controlled (not a threat in single-tenant local deployment)

**Threat:** Denial of service (performance)

**Mitigation:**
- Performance targets (<50ms p95)
- Fail-safe to allow (don't block user)

---

## API Change Log

### v1.0.0 (Story 1 - Current)

**Release Date:** 2026-01-29

**Changes:**
- Initial API design
- `WorkflowEnforcer` class with `intercept_code_edit()` method
- `EnforcementDecision` TypedDict
- `EnforcementConfig` integration (Story 4)
- AsyncFileOps and MCP filesystem hooks
- CLI `--skip-enforcement` flag

---

### v1.1.0 (Story 2 - Planned)

**Planned Release:** TBD

**Changes:**
- Populate `confidence` field in `EnforcementDecision`
- Add `IntentDetector` integration
- Use confidence score in enforcement logic

**Backward Compatibility:** ✅ Fully backward compatible

---

### v1.2.0 (Story 3 - Planned)

**Planned Release:** TBD

**Changes:**
- Enhanced `message` field with rich formatting
- Add `MessageFormatter` integration
- Workflow suggestions in messages

**Backward Compatibility:** ✅ Fully backward compatible

---

## Summary

### API Overview

**Core API:**
- `WorkflowEnforcer` class with `intercept_code_edit()` method
- `EnforcementDecision` TypedDict result
- `EnforcementConfig` configuration (Story 4)

**Integration APIs:**
- `AsyncFileOps.write_file()` hook
- `FilesystemServer.write_file()` hook
- CLI `--skip-enforcement` flag

**Performance:**
- <50ms p95 latency
- <10MB memory overhead
- <5% CPU overhead

**Security:**
- Fail-safe design (never block on errors)
- No sensitive data in config
- Input validation via type hints

---

**API Status:** ✅ Design Complete
**Next Step:** Implementation (Task 1.1)
**Designer:** TappsCodingAgents Designer Agent
**Date:** 2026-01-29
