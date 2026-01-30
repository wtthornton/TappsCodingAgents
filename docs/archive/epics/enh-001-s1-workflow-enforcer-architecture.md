# System Architecture: ENH-001-S1 Core Workflow Enforcer

**Story ID:** ENH-001-S1
**Epic:** ENH-001 Workflow Enforcement System
**Created:** 2026-01-29
**Status:** Design Complete

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Component Design](#component-design)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Data Flow](#data-flow)
6. [Integration Points](#integration-points)
7. [Performance Architecture](#performance-architecture)
8. [Security Architecture](#security-architecture)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Technology Stack](#technology-stack)
11. [System Boundaries](#system-boundaries)
12. [Future Extensibility](#future-extensibility)

---

## System Overview

### Purpose

The Core Workflow Enforcer intercepts file write/edit operations and enforces workflow usage based on configuration, ensuring LLMs use workflows (with automatic validation, testing, and quality gates) instead of direct code edits.

### Key Objectives

1. **Intercept file operations** before execution (Write, Edit, Create)
2. **Make enforcement decisions** based on configuration (block, warn, allow)
3. **Achieve <50ms p95 latency** for minimal performance impact
4. **Fail-safe design** - never block users due to enforcer errors

### Constraints

- **Performance:** <50ms p95 latency, <10MB memory, <5% CPU overhead
- **Reliability:** No false negatives, fail-safe on errors
- **Compatibility:** Must integrate with existing AsyncFileOps and MCP filesystem server
- **Security:** Standard security level (local deployment, single-tenant)

---

## Architecture Pattern

### Selected Pattern: **Interceptor Pattern** (Decorator Variant)

**Rationale:**
- Interceptor pattern allows transparent interception of operations without modifying core logic
- Decorator-style hooks integrate cleanly with existing file operations
- Separation of concerns: enforcement logic separate from file I/O

**Alternative Patterns Considered:**
1. **Observer Pattern** - Rejected: Requires events after operation (too late)
2. **Chain of Responsibility** - Rejected: Overkill for single enforcer
3. **Proxy Pattern** - Rejected: Would require wrapping entire AsyncFileOps class

### Architecture Diagram (Component View)

```
┌─────────────────────────────────────────────────────────────────┐
│                     TappsCodingAgents System                     │
└─────────────────────────────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │   CLI    │        │  Agents  │        │   MCP    │
    │ Commands │        │ Handlers │        │ Servers  │
    └──────────┘        └──────────┘        └──────────┘
          │                    │                    │
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │  File Operation Layer       │
                ├─────────────────────────────┤
                │  AsyncFileOps.write_file()  │
                │  MCPFilesystem.write_file() │
                └──────────────┬──────────────┘
                               │
                    ╔══════════▼══════════╗
                    ║  ENFORCEMENT HOOK   ║ ◄── NEW
                    ║  (Before Write)     ║
                    ╚══════════╤══════════╝
                               │
                    ┌──────────▼──────────┐
                    │ WorkflowEnforcer    │
                    │ .intercept_code_edit│
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │  Decision  │   │   Config   │   │   Logger   │
       │   Logic    │   │   Loader   │   │            │
       └────────────┘   └────────────┘   └────────────┘
              │                │
              │                ▼
              │      ┌──────────────────┐
              │      │ EnforcementConfig│ ◄── Story 4
              │      │ (llm_behavior.py)│     (COMPLETE)
              │      └──────────────────┘
              │                │
              │                ▼
              │      ┌──────────────────┐
              │      │  config.yaml     │
              │      │  (enforcement    │
              │      │   settings)      │
              │      └──────────────────┘
              │
              ▼
       ┌────────────────────────┐
       │  EnforcementDecision   │
       │  - action: block/warn  │
       │  - message: string     │
       │  - should_block: bool  │
       └────────────────────────┘
```

---

## Component Design

### 1. WorkflowEnforcer (Core Component)

**Responsibility:** Make enforcement decisions based on configuration and context

**Location:** `tapps_agents/workflow/enforcer.py`

**Class Diagram:**

```
┌─────────────────────────────────────────────────────────┐
│                   WorkflowEnforcer                       │
├─────────────────────────────────────────────────────────┤
│ - config: EnforcementConfig                             │
│ - _config_path: Path                                    │
│ - _config_mtime: float                                  │
├─────────────────────────────────────────────────────────┤
│ + __init__(config_path?, config?)                       │
│ + intercept_code_edit(file_path, user_intent,           │
│                       is_new_file, skip_enforcement)     │
│                       -> EnforcementDecision             │
│ - _load_config(config_path?) -> EnforcementConfig       │
│ - _should_enforce(file_path, is_new_file,               │
│                   skip_enforcement) -> bool              │
│ - _create_decision(action, file_path, user_intent)      │
│                   -> EnforcementDecision                 │
└─────────────────────────────────────────────────────────┘
```

**Key Methods:**

1. **`intercept_code_edit()`** - Public API
   - **Input:** file_path, user_intent, is_new_file, skip_enforcement
   - **Output:** EnforcementDecision (action, message, should_block, confidence)
   - **Performance Target:** <50ms p95 latency
   - **Error Handling:** Try-catch with fail-safe to "allow"

2. **`_load_config()`** - Configuration loader
   - **Delegates to:** `EnforcementConfig.from_config_file()` (Story 4)
   - **Caching:** Stores config instance for reuse
   - **Error Handling:** Log warning, use defaults on error

3. **`_should_enforce()`** - Enforcement applicability check
   - **Logic:**
     - If `skip_enforcement=True` → return False
     - If `config.mode="silent"` → return False
     - Otherwise → return True
   - **Future:** Add excluded paths check

4. **`_create_decision()`** - Decision builder
   - **Input:** action (block/warn/allow), file_path, user_intent
   - **Output:** EnforcementDecision with formatted message
   - **Note:** Basic messages for Story 1; Story 3 will add MessageFormatter

**Design Principles:**
- **Single Responsibility:** Only decides enforcement actions (no intent detection, no messaging)
- **Dependency Injection:** Accepts config via constructor (testability)
- **Fail-Safe:** Errors default to "allow" (don't block users)
- **Performance:** Minimal computation, config caching

---

### 2. EnforcementDecision (Data Structure)

**Type:** TypedDict (structured data, type-safe)

**Location:** `tapps_agents/workflow/enforcer.py`

**Structure:**

```python
class EnforcementDecision(TypedDict):
    action: Literal["block", "warn", "allow"]
    message: str
    should_block: bool
    confidence: float  # Reserved for Story 2 (Intent Detection)
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `action` | `"block"` \| `"warn"` \| `"allow"` | Enforcement action based on config mode |
| `message` | `str` | Message to display to user (empty for silent/allow) |
| `should_block` | `bool` | Whether to actually block operation (action + config.block_direct_edits) |
| `confidence` | `float` | Confidence score (0.0 for Story 1; Story 2 will populate) |

**Usage:**

```python
decision = enforcer.intercept_code_edit(...)

if decision["should_block"]:
    raise RuntimeError(f"Blocked: {decision['message']}")
elif decision["action"] == "warn":
    logger.warning(decision["message"])
# Proceed with operation
```

---

### 3. EnforcementConfig (Configuration - Story 4)

**Responsibility:** Load and validate enforcement configuration

**Location:** `tapps_agents/core/llm_behavior.py` (ALREADY IMPLEMENTED)

**Structure:**

```python
@dataclass
class EnforcementConfig:
    mode: Literal["blocking", "warning", "silent"] = "blocking"
    confidence_threshold: float = 60.0  # Reserved for Story 2
    suggest_workflows: bool = True
    block_direct_edits: bool = True
```

**Configuration File:** `.tapps-agents/config.yaml`

```yaml
llm_behavior:
  mode: "senior-developer"

  workflow_enforcement:
    mode: "blocking"           # "blocking" | "warning" | "silent"
    confidence_threshold: 60   # 0-100 (reserved for Story 2)
    suggest_workflows: true    # Include workflow suggestions in messages
    block_direct_edits: true   # Actually block in blocking mode
```

**Integration:**

```python
# WorkflowEnforcer loads config via EnforcementConfig
config = EnforcementConfig.from_config_file()

# Use config to make decisions
if config.mode == "blocking" and config.block_direct_edits:
    return EnforcementDecision(action="block", ...)
```

---

### 4. File Operation Hooks (Integration Layer)

**Responsibility:** Intercept file operations and call enforcer before execution

#### Hook 1: AsyncFileOps.write_file()

**Location:** `tapps_agents/core/async_file_ops.py`

**Pattern:** Decorator/Wrapper pattern

**Implementation:**

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
        """Write file with enforcement check."""
        # Import enforcer (lazy to avoid circular import)
        from tapps_agents.workflow.enforcer import WorkflowEnforcer

        # Check enforcement
        enforcer = WorkflowEnforcer()
        decision = enforcer.intercept_code_edit(
            file_path=file_path,
            user_intent=user_intent,
            is_new_file=not file_path.exists(),
            skip_enforcement=skip_enforcement
        )

        if decision["should_block"]:
            raise RuntimeError(
                f"File operation blocked by workflow enforcer: {decision['message']}"
            )
        elif decision["action"] == "warn":
            logger.warning(decision["message"])

        # Proceed with original write logic
        if AIOFILES_AVAILABLE:
            if create_parents:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, "w", encoding=encoding) as f:
                await f.write(content)
        else:
            # Synchronous fallback
            if create_parents:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
```

**Key Design Decisions:**
- **Lazy import:** Avoid circular dependency by importing enforcer inside method
- **Backward compatibility:** New parameters are optional (default: no enforcement)
- **Error propagation:** RuntimeError raised if blocked (caller handles)
- **Warning logging:** Warnings logged but operation continues

#### Hook 2: MCP FilesystemServer.write_file()

**Location:** `tapps_agents/mcp/servers/filesystem.py`

**Pattern:** Similar decorator/wrapper pattern

**Implementation:**

```python
def write_file(
    self,
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
    user_intent: str = "",           # NEW PARAMETER
    skip_enforcement: bool = False,  # NEW PARAMETER
) -> dict[str, Any]:
    """Write file with enforcement check."""
    from tapps_agents.workflow.enforcer import WorkflowEnforcer

    path = Path(file_path)

    # Check enforcement
    enforcer = WorkflowEnforcer()
    decision = enforcer.intercept_code_edit(
        file_path=path,
        user_intent=user_intent,
        is_new_file=not path.exists(),
        skip_enforcement=skip_enforcement
    )

    if decision["should_block"]:
        return {
            "file_path": str(path),
            "written": False,
            "blocked": True,
            "message": decision["message"]
        }
    elif decision["action"] == "warn":
        logger.warning(decision["message"])

    # Proceed with original write logic
    # ... (existing MCP filesystem write code)
```

**Key Design Decisions:**
- **MCP response format:** Return dict with `blocked=True` instead of raising exception
- **Graceful handling:** MCP clients can handle blocked responses
- **Same parameters:** Consistent API across AsyncFileOps and MCP

#### Hook 3: CLI Flag `--skip-enforcement`

**Location:** `tapps_agents/cli.py`

**Purpose:** Allow users to bypass enforcement for emergency situations

**Implementation:**

```python
# In CLI argument parser
parser.add_argument(
    "--skip-enforcement",
    action="store_true",
    help="Skip workflow enforcement checks (allow direct edits)"
)

# Pass to file operations
async_file_ops.write_file(
    file_path=args.file,
    content=content,
    skip_enforcement=args.skip_enforcement  # Pass CLI flag
)
```

---

## Sequence Diagrams

### Sequence 1: File Write Operation (Blocking Mode)

```
┌─────┐    ┌────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────┐
│ CLI │    │ Agent  │    │ AsyncFileOps│    │ Workflow     │    │ Config │
│     │    │Handler │    │             │    │ Enforcer     │    │        │
└──┬──┘    └───┬────┘    └──────┬──────┘    └──────┬───────┘    └───┬────┘
   │           │                 │                  │                 │
   │ implement │                 │                  │                 │
   │ feature   │                 │                  │                 │
   ├──────────>│                 │                  │                 │
   │           │                 │                  │                 │
   │           │ write_file()    │                  │                 │
   │           ├────────────────>│                  │                 │
   │           │ file_path       │                  │                 │
   │           │ user_intent     │                  │                 │
   │           │                 │                  │                 │
   │           │                 │ intercept_code_  │                 │
   │           │                 │ edit()           │                 │
   │           │                 ├─────────────────>│                 │
   │           │                 │                  │                 │
   │           │                 │                  │ load_config()   │
   │           │                 │                  ├────────────────>│
   │           │                 │                  │                 │
   │           │                 │                  │ EnforcementConfig│
   │           │                 │                  │<────────────────┤
   │           │                 │                  │ mode="blocking" │
   │           │                 │                  │                 │
   │           │                 │                  │ _should_enforce()│
   │           │                 │                  │ -> True         │
   │           │                 │                  │                 │
   │           │                 │                  │ _create_decision()│
   │           │                 │                  │ action="block"  │
   │           │                 │                  │                 │
   │           │                 │ EnforcementDecision│               │
   │           │                 │ {action: "block",│                 │
   │           │                 │  should_block: true}│              │
   │           │                 │<─────────────────┤                 │
   │           │                 │                  │                 │
   │           │                 │ [should_block=true]│               │
   │           │                 │ raise RuntimeError│                │
   │           │                 │                  │                 │
   │           │ RuntimeError:   │                  │                 │
   │           │ "File operation │                  │                 │
   │           │  blocked"       │                  │                 │
   │           │<────────────────┤                  │                 │
   │           │                 │                  │                 │
   │ Error:    │                 │                  │                 │
   │ Workflow  │                 │                  │                 │
   │ enforcement│                 │                  │                 │
   │ blocked   │                 │                  │                 │
   │<──────────┤                 │                  │                 │
```

**Flow Description:**
1. User triggers file write operation via CLI/Agent
2. Agent handler calls `AsyncFileOps.write_file()`
3. Before writing, `WorkflowEnforcer.intercept_code_edit()` is called
4. Enforcer loads config from `EnforcementConfig` (cached)
5. Config mode is "blocking" → decision is "block"
6. `should_block=true` → `RuntimeError` is raised
7. File write is **not executed**, error propagated to user

---

### Sequence 2: File Write Operation (Warning Mode)

```
┌─────┐    ┌────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────┐
│ CLI │    │ Agent  │    │ AsyncFileOps│    │ Workflow     │    │ Config │
│     │    │Handler │    │             │    │ Enforcer     │    │        │
└──┬──┘    └───┬────┘    └──────┬──────┘    └──────┬───────┘    └───┬────┘
   │           │                 │                  │                 │
   │ implement │                 │                  │                 │
   │ feature   │                 │                  │                 │
   ├──────────>│                 │                  │                 │
   │           │                 │                  │                 │
   │           │ write_file()    │                  │                 │
   │           ├────────────────>│                  │                 │
   │           │                 │                  │                 │
   │           │                 │ intercept_code_  │                 │
   │           │                 │ edit()           │                 │
   │           │                 ├─────────────────>│                 │
   │           │                 │                  │                 │
   │           │                 │                  │ load_config()   │
   │           │                 │                  ├────────────────>│
   │           │                 │                  │                 │
   │           │                 │                  │ EnforcementConfig│
   │           │                 │                  │<────────────────┤
   │           │                 │                  │ mode="warning"  │
   │           │                 │                  │                 │
   │           │                 │                  │ _create_decision()│
   │           │                 │                  │ action="warn"   │
   │           │                 │                  │                 │
   │           │                 │ EnforcementDecision│               │
   │           │                 │ {action: "warn", │                 │
   │           │                 │  should_block: false}│             │
   │           │                 │<─────────────────┤                 │
   │           │                 │                  │                 │
   │           │                 │ [action="warn"]  │                 │
   │           │                 │ logger.warning() │                 │
   │           │                 │                  │                 │
   │           │                 │ Write file to    │                 │
   │           │                 │ disk             │                 │
   │           │                 │ ✓                │                 │
   │           │                 │                  │                 │
   │           │ Success         │                  │                 │
   │           │<────────────────┤                  │                 │
   │           │                 │                  │                 │
   │ Success   │                 │                  │                 │
   │ (with warning)│             │                  │                 │
   │<──────────┤                 │                  │                 │
```

**Flow Description:**
1. User triggers file write operation
2. `WorkflowEnforcer.intercept_code_edit()` is called
3. Config mode is "warning" → decision is "warn"
4. `should_block=false` → warning logged, but operation continues
5. File write is **executed**, user sees warning

---

### Sequence 3: Skip Enforcement (CLI Flag)

```
┌─────┐    ┌─────────────┐    ┌──────────────┐
│ CLI │    │ AsyncFileOps│    │ Workflow     │
│     │    │             │    │ Enforcer     │
└──┬──┘    └──────┬──────┘    └──────┬───────┘
   │              │                  │
   │ write_file() │                  │
   │ --skip-enforcement│             │
   ├─────────────>│                  │
   │              │                  │
   │              │ intercept_code_  │
   │              │ edit(            │
   │              │   skip_enforcement=True│
   │              ├─────────────────>│
   │              │                  │
   │              │                  │ _should_enforce()
   │              │                  │ [skip_enforcement=True]
   │              │                  │ -> False
   │              │                  │
   │              │                  │ _create_decision()
   │              │                  │ action="allow"
   │              │                  │
   │              │ EnforcementDecision│
   │              │ {action: "allow",│
   │              │  should_block: false}│
   │              │<─────────────────┤
   │              │                  │
   │              │ Write file to disk│
   │              │ ✓                │
   │              │                  │
   │ Success      │                  │
   │<─────────────┤                  │
```

**Flow Description:**
1. User passes `--skip-enforcement` CLI flag
2. Flag is passed to `write_file(skip_enforcement=True)`
3. Enforcer's `_should_enforce()` returns `False`
4. Decision is "allow" → no checks, file write proceeds

---

## Data Flow

### Data Flow Diagram

```
┌──────────────────┐
│  User Input      │
│  - Prompt        │
│  - File path     │
│  - CLI flags     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  Agent Handler / CLI         │
│  Extracts:                   │
│  - file_path: Path           │
│  - user_intent: str          │
│  - skip_enforcement: bool    │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  AsyncFileOps.write_file()   │
│  Adds:                       │
│  - is_new_file: bool         │
│    (file_path.exists())      │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  WorkflowEnforcer            │
│  .intercept_code_edit()      │
│                              │
│  Input:                      │
│  - file_path: Path           │
│  - user_intent: str          │
│  - is_new_file: bool         │
│  - skip_enforcement: bool    │
└────────┬─────────────────────┘
         │
         ├────────────────────────────┐
         │                            │
         ▼                            ▼
┌──────────────────┐    ┌──────────────────────┐
│ EnforcementConfig│    │  Decision Logic      │
│ from config.yaml │    │  - Check mode        │
│                  │    │  - Apply flags       │
│  Returns:        │    │  - Build message     │
│  - mode          │    └──────────┬───────────┘
│  - threshold     │               │
│  - suggest_*     │               │
│  - block_*       │               │
└────────┬─────────┘               │
         │                         │
         └────────┬────────────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │ EnforcementDecision  │
         │                      │
         │  Output:             │
         │  - action: str       │
         │  - message: str      │
         │  - should_block: bool│
         │  - confidence: float │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  AsyncFileOps        │
         │  Decision handling:  │
         │  - Block: Raise error│
         │  - Warn: Log warning │
         │  - Allow: Continue   │
         └──────────────────────┘
```

### Data Structures

**Input Data:**
```python
file_path: Path             # Path to file being written/edited
user_intent: str            # User's intent from prompt/context
is_new_file: bool           # True if creating, False if editing
skip_enforcement: bool      # Override flag from CLI
```

**Configuration Data:**
```python
EnforcementConfig:
    mode: "blocking" | "warning" | "silent"
    confidence_threshold: float  # 0-100 (reserved for Story 2)
    suggest_workflows: bool      # True to include workflow suggestions
    block_direct_edits: bool     # True to actually block in blocking mode
```

**Output Data:**
```python
EnforcementDecision:
    action: "block" | "warn" | "allow"
    message: str                 # User-facing message
    should_block: bool           # Computed: action=="block" && config.block_direct_edits
    confidence: float            # 0.0 for Story 1 (placeholder)
```

---

## Integration Points

### 1. Configuration System (Story 4) ✅

**Status:** COMPLETE

**Integration:**
```python
from tapps_agents.core.llm_behavior import EnforcementConfig

# WorkflowEnforcer loads config
config = EnforcementConfig.from_config_file()

# Use config to make decisions
if config.mode == "blocking":
    # Block operation
```

**Configuration File:** `.tapps-agents/config.yaml`

**Dependencies:**
- `EnforcementConfig.from_config_file()` (implemented)
- Config validation (implemented)
- Default value handling (implemented)

---

### 2. AsyncFileOps (File I/O Layer)

**Location:** `tapps_agents/core/async_file_ops.py`

**Modification:** Add enforcement hook to `write_file()` method

**Integration Pattern:**
```python
# Before write
enforcer = WorkflowEnforcer()
decision = enforcer.intercept_code_edit(...)

if decision["should_block"]:
    raise RuntimeError(...)
elif decision["action"] == "warn":
    logger.warning(...)

# Proceed with write
```

**Backward Compatibility:**
- New parameters are optional (`user_intent=""`, `skip_enforcement=False`)
- Existing callers not affected (enforcement disabled by default initially)
- Can enable enforcement via config after testing

---

### 3. MCP Filesystem Server

**Location:** `tapps_agents/mcp/servers/filesystem.py`

**Modification:** Add enforcement hook to `write_file()` method

**Integration Pattern:**
```python
# Before write
enforcer = WorkflowEnforcer()
decision = enforcer.intercept_code_edit(...)

if decision["should_block"]:
    return {"blocked": True, "message": decision["message"]}
elif decision["action"] == "warn":
    logger.warning(...)

# Proceed with write
```

**MCP Response Format:**
```python
# Blocked response
{
    "file_path": "/path/to/file.py",
    "written": False,
    "blocked": True,
    "message": "Workflow enforcement blocked this operation. Use @simple-mode *build instead."
}

# Success response (warning or allow)
{
    "file_path": "/path/to/file.py",
    "written": True,
    "blocked": False
}
```

---

### 4. CLI Integration

**Location:** `tapps_agents/cli.py`

**Modification:** Add `--skip-enforcement` flag to argument parser

**Usage:**
```bash
# Skip enforcement for emergency fix
tapps-agents implementer implement "Add logging" src/app.py --skip-enforcement

# Normal operation (enforcement enabled if configured)
tapps-agents implementer implement "Add logging" src/app.py
```

---

### 5. Future Integration Points

**Story 2 (Intent Detection):**
```python
# In WorkflowEnforcer.intercept_code_edit()
from tapps_agents.workflow.intent_detector import IntentDetector

detector = IntentDetector()
workflow_type, confidence = detector.detect_workflow(user_intent)

# Use confidence in decision
if confidence >= self.config.confidence_threshold:
    # High confidence - enforce
```

**Story 3 (Message Formatting):**
```python
# In WorkflowEnforcer._create_decision()
from tapps_agents.workflow.message_formatter import MessageFormatter

formatter = MessageFormatter()
message = formatter.format_blocking_message(
    workflow=workflow_type,  # From Story 2
    user_intent=user_intent,
    file_path=file_path
)
```

---

## Performance Architecture

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Interception Latency** | <50ms (p95) | `time.perf_counter()` in performance tests |
| **Memory Overhead** | <10MB | `tracemalloc` |
| **CPU Overhead** | <5% | `time.process_time()` |
| **Config Load Time** | <100ms | First load only (cached afterward) |

### Performance Optimizations

1. **Config Caching:**
   ```python
   # Cache config instance after first load
   if not hasattr(self, '_cached_config'):
       self._cached_config = EnforcementConfig.from_config_file()
   return self._cached_config
   ```

2. **Lazy Import:**
   ```python
   # Import enforcer inside method to avoid circular dependency
   # and defer import cost
   def write_file(...):
       from tapps_agents.workflow.enforcer import WorkflowEnforcer
       enforcer = WorkflowEnforcer()
   ```

3. **Simple Decision Logic:**
   - No expensive computations in hot path
   - No file I/O during enforcement check (config loaded once)
   - No network calls

4. **Early Exit:**
   ```python
   # Skip enforcement immediately if flag set
   if skip_enforcement:
       return self._create_decision("allow", ...)

   # Skip enforcement if mode is silent
   if self.config.mode == "silent":
       return self._create_decision("allow", ...)
   ```

### Performance Monitoring

**Performance Tests:** `tests/test_workflow_enforcer.py`

```python
def test_interception_latency_under_50ms(enforcer):
    """Verify p95 latency <50ms."""
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

## Security Architecture

### Threat Model

**Threat 1: Bypass Workflow Enforcement**

- **Attack Vector:** User finds way to bypass enforcer
- **Mitigation:** Hook at lowest level (AsyncFileOps, MCP server)
- **Detection:** Log all enforcement decisions
- **Impact:** Medium (user can disable via config anyway)

**Threat 2: Configuration Tampering**

- **Attack Vector:** User modifies config to disable enforcement
- **Mitigation:** Config is user-controlled (not a threat in single-tenant local deployment)
- **Detection:** N/A (user has full control)
- **Impact:** Low (user controls their own config)

**Threat 3: Denial of Service (Performance)**

- **Attack Vector:** Enforcer slows down file operations
- **Mitigation:** Performance targets (<50ms p95), fail-safe to allow
- **Detection:** Performance monitoring tests
- **Impact:** Low (enforcement can be disabled via config)

**Threat 4: Error-Based Bypass**

- **Attack Vector:** Trigger error in enforcer to bypass check
- **Mitigation:** Fail-safe design (errors default to "allow")
- **Detection:** Error logging
- **Impact:** Low (fail-safe is intentional)

### Security Controls

1. **Fail-Safe Design:**
   ```python
   try:
       # Enforcement logic
   except Exception as e:
       logger.error("Enforcement check failed: %s", e)
       return EnforcementDecision(action="allow", ...)  # Fail open
   ```

2. **Input Validation:**
   - Config validation in `EnforcementConfig` (Story 4)
   - Type hints enforce correct data types
   - Path validation (Path object)

3. **Logging:**
   - All enforcement decisions logged at debug level
   - Errors logged at error level with stack traces
   - Warnings logged when enforcement action is "warn"

4. **No Secrets in Config:**
   - Config contains only behavior settings
   - No sensitive data stored

### Compliance

**Project Security Level:** Standard

**Compliance Requirements:**
- GDPR: Not applicable (no personal data processed)
- HIPAA: Not applicable (no health data processed)
- PCI: Not applicable (no payment data processed)

**Security Considerations:**
- Local deployment (no network exposure)
- Single-tenant (no multi-tenant isolation concerns)
- Standard security level (no elevated security requirements)

---

## Error Handling Strategy

### Error Categories

1. **Configuration Errors:**
   - **Scenario:** Config file missing, invalid YAML, invalid values
   - **Handling:** Log warning, use default config
   - **User Impact:** None (enforcement works with defaults)

2. **Enforcement Errors:**
   - **Scenario:** Exception in `intercept_code_edit()`
   - **Handling:** Catch exception, log error, return "allow" decision
   - **User Impact:** None (operation proceeds, user not blocked)

3. **Integration Errors:**
   - **Scenario:** AsyncFileOps or MCP server errors
   - **Handling:** Propagate error to caller (not enforcer's concern)
   - **User Impact:** Standard file operation error

### Error Handling Patterns

**Pattern 1: Fail-Safe (Enforcer)**
```python
def intercept_code_edit(...):
    try:
        # Main enforcement logic
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

**Pattern 2: Graceful Degradation (Config)**
```python
def _load_config(self, config_path=None):
    try:
        return EnforcementConfig.from_config_file(config_path)
    except Exception as e:
        logger.warning("Failed to load config, using defaults: %s", e)
        return EnforcementConfig()  # Default values
```

**Pattern 3: Error Propagation (File Ops)**
```python
# In AsyncFileOps.write_file()
if decision["should_block"]:
    raise RuntimeError(f"File operation blocked: {decision['message']}")
# Error propagates to caller (agent handler, CLI)
```

### Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# Enforcement decisions (debug level)
logger.debug(
    "Enforcement decision: action=%s, file=%s, intent=%s",
    decision["action"], file_path, user_intent[:50]
)

# Configuration loads (info level)
logger.info("Loaded enforcement config: mode=%s", config.mode)

# Warnings (warning level)
logger.warning(decision["message"])

# Errors (error level with exc_info)
logger.error("Failed to load config: %s", e, exc_info=True)
```

---

## Technology Stack

### Core Technologies

| Technology | Version | Usage | Justification |
|------------|---------|-------|---------------|
| **Python** | 3.12+ | Implementation language | Modern type hints, project standard |
| **PyYAML** | Latest | Config parsing | Already in project, standard YAML library |
| **pytest** | Latest | Testing framework | Already in project |
| **pytest-cov** | Latest | Coverage measurement | Already in project |
| **typing** | stdlib | Type hints | Type safety, IDE support |
| **logging** | stdlib | Logging | Standard library, no dependencies |
| **pathlib** | stdlib | Path handling | Modern path API |

### Dependencies

**Required:**
- `tapps_agents.core.llm_behavior.EnforcementConfig` (Story 4) ✅

**Optional (Future):**
- `tapps_agents.workflow.intent_detector.IntentDetector` (Story 2)
- `tapps_agents.workflow.message_formatter.MessageFormatter` (Story 3)

### Technology Decisions

**Q: Why TypedDict instead of dataclass for EnforcementDecision?**
- **A:** TypedDict is lighter weight, doesn't require instantiation overhead, and is more natural for simple data structures. Decision is created many times (performance sensitive).

**Q: Why lazy import of WorkflowEnforcer in file ops?**
- **A:** Avoid circular dependency (enforcer → config, file ops → enforcer). Lazy import defers import until needed.

**Q: Why fail-safe to "allow" instead of raising error?**
- **A:** User experience - never block users due to enforcer bugs. Enforcement is a suggestion, not a hard requirement.

---

## System Boundaries

### Internal Boundaries

**Components within WorkflowEnforcer module:**
- WorkflowEnforcer class
- EnforcementDecision TypedDict
- Internal helpers (_load_config, _should_enforce, _create_decision)

**External Dependencies:**
- EnforcementConfig (from llm_behavior module)
- logging module (stdlib)
- pathlib module (stdlib)

### External Boundaries

**Upstream (Callers):**
- Agent handlers (ImplementerHandler, etc.)
- CLI commands
- MCP filesystem server clients

**Downstream (Dependencies):**
- EnforcementConfig (config loader)
- logging (Python stdlib)

**Configuration:**
- `.tapps-agents/config.yaml` (read-only)

**File System:**
- File existence checks (`file_path.exists()`)
- No writes, no reads (only existence check)

### API Contract

**Public API:**
```python
class WorkflowEnforcer:
    def __init__(
        self,
        config_path: Path | None = None,
        config: EnforcementConfig | None = None
    ):
        """Initialize enforcer with optional config."""

    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool,
        skip_enforcement: bool = False
    ) -> EnforcementDecision:
        """
        Intercept file operation and make enforcement decision.

        Returns:
            EnforcementDecision with action, message, should_block, confidence

        Raises:
            Never raises - errors are caught and logged
        """
```

**Integration API (AsyncFileOps):**
```python
class AsyncFileOps:
    @staticmethod
    async def write_file(
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
        user_intent: str = "",           # NEW
        skip_enforcement: bool = False,  # NEW
    ) -> None:
        """
        Write file with enforcement check.

        Raises:
            RuntimeError: If enforcement blocks operation
        """
```

---

## Future Extensibility

### Story 2: Intent Detection System

**Integration Point:**
```python
# In WorkflowEnforcer.intercept_code_edit()

# Detect intent and confidence
from tapps_agents.workflow.intent_detector import IntentDetector
detector = IntentDetector()
workflow_type, confidence = detector.detect_workflow(user_intent)

# Use confidence in decision
if confidence >= self.config.confidence_threshold:
    # High confidence - enforce
    decision = self._create_decision("block", ...)
else:
    # Low confidence - allow
    decision = self._create_decision("allow", ...)

# Populate confidence field
decision["confidence"] = confidence
return decision
```

**Changes Required:**
- Add `IntentDetector` import
- Call `detect_workflow()` in `intercept_code_edit()`
- Use confidence score in decision logic
- Populate `confidence` field in EnforcementDecision

---

### Story 3: Message Formatting System

**Integration Point:**
```python
# In WorkflowEnforcer._create_decision()

# Format message with rich content
from tapps_agents.workflow.message_formatter import MessageFormatter
formatter = MessageFormatter()

if action == "block":
    message = formatter.format_blocking_message(
        workflow=workflow_type,  # From Story 2
        user_intent=user_intent,
        file_path=file_path
    )
elif action == "warn":
    message = formatter.format_warning_message(
        workflow=workflow_type,
        user_intent=user_intent,
        file_path=file_path
    )
else:
    message = ""

return EnforcementDecision(
    action=action,
    message=message,
    ...
)
```

**Changes Required:**
- Add `MessageFormatter` import
- Replace basic messages with formatter calls
- Pass workflow type to formatter (requires Story 2)

---

### Extension Points

**1. Excluded Paths:**
```python
# In _should_enforce()
if file_path in self.config.excluded_paths:
    return False
```

**2. Custom Decision Logic:**
```python
# Allow subclassing for custom enforcement logic
class CustomWorkflowEnforcer(WorkflowEnforcer):
    def _should_enforce(self, file_path, is_new_file, skip_enforcement):
        # Custom logic
        return super()._should_enforce(...)
```

**3. Hook for Pre-Decision Callback:**
```python
# Add callback mechanism for extensions
if self._pre_decision_callback:
    self._pre_decision_callback(file_path, user_intent)
```

---

## Architecture Decision Records (ADRs)

### ADR-1: Use Interceptor Pattern

**Decision:** Use Interceptor pattern for enforcement hooks

**Rationale:**
- Transparent interception without modifying core logic
- Clean separation of concerns
- Easy to disable/enable enforcement

**Alternatives Considered:**
- Observer pattern (too late - after operation)
- Proxy pattern (too invasive - wraps entire class)

**Consequences:**
- Must hook into existing file operations
- Backward compatibility considerations
- Lazy import to avoid circular dependency

---

### ADR-2: Fail-Safe to Allow

**Decision:** On enforcer errors, default to "allow" (don't block user)

**Rationale:**
- User experience priority - never block users due to bugs
- Enforcement is guidance, not hard requirement
- Errors logged for debugging

**Alternatives Considered:**
- Fail-closed (block on error) - rejected: too disruptive

**Consequences:**
- Errors in enforcer don't prevent work
- Must rely on logging for error detection
- Performance errors don't cascade

---

### ADR-3: TypedDict for EnforcementDecision

**Decision:** Use TypedDict instead of dataclass for EnforcementDecision

**Rationale:**
- Lightweight (no instantiation overhead)
- Natural for simple data structures
- Performance-sensitive (created many times)

**Alternatives Considered:**
- dataclass (more features, but slower)
- NamedTuple (immutable, but less flexible)

**Consequences:**
- No methods on EnforcementDecision
- Type safety via type hints
- Must use dict syntax

---

### ADR-4: Cache Config Instance

**Decision:** Cache EnforcementConfig instance after first load

**Rationale:**
- Performance optimization (<100ms load time)
- Config rarely changes during execution
- Reduces file I/O overhead

**Alternatives Considered:**
- Reload config on every call (too slow)
- Hot-reload config (complex, future enhancement)

**Consequences:**
- Config changes require process restart
- Memory overhead minimal (<1KB)
- Performance target met (<50ms)

---

## Summary

### Key Architecture Decisions

1. **Interceptor Pattern:** Transparent interception at AsyncFileOps and MCP filesystem layers
2. **Fail-Safe Design:** Errors default to "allow" (never block users)
3. **Configuration-Driven:** All behavior controlled by EnforcementConfig
4. **Performance-First:** <50ms p95 latency via config caching and simple logic
5. **Extensibility:** Designed for Story 2 (Intent Detection) and Story 3 (Message Formatting)

### Components

- **WorkflowEnforcer:** Core enforcement engine (~250 lines)
- **EnforcementDecision:** Typed decision result (TypedDict)
- **File Operation Hooks:** AsyncFileOps and MCP filesystem integrations
- **CLI Integration:** --skip-enforcement flag for overrides

### Integration Points

- ✅ **Story 4 (Config):** EnforcementConfig integration complete
- 🔲 **Story 2 (Intent):** Integration points designed, ready for implementation
- 🔲 **Story 3 (Messaging):** Integration points designed, ready for implementation

### Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Latency | <50ms p95 | Config caching, simple logic |
| Memory | <10MB | Minimal state, TypedDict |
| CPU | <5% | No expensive computations |

### Security Posture

- **Threat Model:** Low risk (local, single-tenant, user-controlled)
- **Security Controls:** Fail-safe design, input validation, logging
- **Compliance:** N/A (no sensitive data)

---

**Architecture Status:** ✅ Design Complete
**Next Step:** Implementation (Task 1.1 - Create WorkflowEnforcer Class)
**Review Date:** 2026-01-29
**Architect:** TappsCodingAgents Architect Agent
