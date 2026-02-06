# Enhancement Recommendations — February 2026 Audit

## Summary

Full project audit of TappsCodingAgents v3.6.1 (~1,183 files, ~151K LOC). Identified 70+ issues across all modules. Organized by priority.

---

## CRITICAL (Fix Immediately)

### C1. MRO Chain Broken in BaseAgent
**File:** `core/agent_base.py` — `__init__` method
**Issue:** `BaseAgent.__init__()` doesn't call `super().__init__()`, breaking cooperative inheritance for `ExpertSupportMixin` and any other mixins.
**Impact:** Mixin `__init__` methods never execute; state not initialized.
**Fix:** Add `super().__init__()` call in `BaseAgent.__init__`.

### C2. Directory Traversal in Context7 Cache
**File:** `context7/agent_integration.py` — `cache_root` parameter
**Issue:** Unvalidated cache path allows escape from project boundary.
**Impact:** Potential read/write to arbitrary filesystem locations.
**Fix:** Validate with `Path.resolve()` and check within project root.

### C3. Missing Timezone Import in State Manager
**File:** `workflow/state_manager.py:284,294`
**Issue:** Uses `datetime.timezone.utc` but `timezone` not imported (only `datetime` is).
**Impact:** Runtime `AttributeError` when state management code executes.
**Fix:** Add `from datetime import datetime, timezone` or use `datetime.UTC` (Python 3.11+).

### C4. Python 3.11+ Incompatibility in Parallel Executor
**File:** `workflow/parallel_executor.py`
**Issue:** Uses deprecated patterns that fail on Python 3.11+.
**Impact:** Parallel story execution broken on modern Python.
**Fix:** Migrate to `TaskGroup` and `asyncio.timeout()`.

### C5. Quality Gates Not Enforced in Epic Orchestrator
**File:** `epic/orchestrator.py`
**Issue:** Quality gate checks are placeholder/no-op — always pass.
**Impact:** Low-quality stories are accepted without review.
**Fix:** Wire quality gate checks to actual reviewer scoring.

### C6. Race Condition in Global Cache Init
**File:** `context7/agent_integration.py`
**Issue:** Multiple concurrent `_ensure_cache()` calls can corrupt singleton state.
**Impact:** Intermittent cache corruption under concurrent access.
**Fix:** Use `asyncio.Lock()` for initialization guard.

---

## HIGH (Fix Soon)

### H1. Inconsistent Error Handling (3 Patterns)
**Scope:** All agent implementations
**Issue:** Agents use 3 different patterns: return tuple `(success, message)`, raise exceptions, or return `Result` object.
**Fix:** Standardize on `Result[T, E]` pattern or custom exception hierarchy.

### H2. Broad Exception Handling
**Scope:** Multiple modules (workflow, agents, CLI)
**Issue:** `except Exception` catches too broadly, hiding bugs and masking root causes.
**Fix:** Catch specific exceptions; log unexpected ones with traceback.

### H3. Silent Cache Write Failures
**File:** `context7/kb_cache.py`
**Issue:** Write failures caught and logged at DEBUG — data loss is invisible.
**Fix:** Return success/failure status; raise for critical writes.

### H4. Race Condition in Event Bus
**File:** `workflow/event_bus.py`
**Issue:** Subscriber list modified during iteration when events trigger new subscriptions.
**Fix:** Copy subscriber list before iteration; use thread-safe collections.

### H5. Excessive Defensive hasattr Checks
**Scope:** Agent implementations
**Issue:** 50+ `hasattr()` calls used instead of proper type checks or protocols.
**Fix:** Use `typing.Protocol` or ABC for interface contracts.

### H6. Blocking File I/O in Async Methods
**Scope:** Multiple async functions
**Issue:** Synchronous `open()`, `Path.read_text()` in async contexts blocks event loop.
**Fix:** Use `aiofiles` or `asyncio.to_thread()` for file operations.

### H7. No File Size Limits for Cache/RAG
**File:** `experts/simple_rag.py`, `context7/kb_cache.py`
**Issue:** Files read into memory without size validation — potential OOM.
**Fix:** Add configurable max file size (e.g., 10MB default).

### H8. Symlink Escape in Path Validation
**File:** `core/agent_base.py` — `_validate_path()`
**Issue:** Path validation doesn't resolve symlinks before boundary checks.
**Fix:** Use `Path.resolve()` before boundary validation.

---

## MEDIUM (Plan for Next Sprint)

### M1. Expand Ruff Rules
**File:** `pyproject.toml` — `[tool.ruff.lint]`
**Current:** `select = ["E", "F", "I", "UP", "B"]`
**Recommended:** Add `"SIM", "RUF", "PTH", "ASYNC", "PERF"` for:
- Simplifiable logic, Ruff-specific issues, pathlib modernization, async anti-patterns, performance

### M2. Enable mypy `check_untyped_defs`
**File:** `pyproject.toml` — `[tool.mypy]`
**Current:** `disallow_untyped_defs = false`
**Fix:** Enable `check_untyped_defs = true` to catch type errors in untyped functions.

### M3. Add Pre-commit Hooks
**Issue:** No `.pre-commit-config.yaml` — quality checks run manually.
**Fix:** Add pre-commit config with ruff, mypy, bandit, detect-secrets.

### M4. Standardize Pydantic ConfigDict
**File:** `core/config.py`
**Issue:** Uses `model_config = {"extra": "ignore"}` (dict-style).
**Fix:** Use `model_config = ConfigDict(extra="ignore")` across all models.

### M5. Add ExitCode Enum for CLI
**File:** `cli/main.py`
**Fix:** Replace raw `sys.exit(0/1)` with `ExitCode` IntEnum.

### M6. Fix Context7 Fuzzy Match Misresolutions
**File:** `context7/fuzzy_matcher.py`
**Issue:** 6+ libraries resolve to wrong Context7 IDs (e.g., pyyaml).
**Fix:** Add language-aware verification step after fuzzy resolution.

### M7. Add Cache TTL and Staleness Detection
**File:** `context7/kb_cache.py`
**Issue:** Cache entries never expire.
**Fix:** Add `fetched_at` timestamp; configurable TTL (default 14 days).

### M8. Centralize Subprocess Execution
**Scope:** Multiple modules
**Issue:** `subprocess.run()` called in 15+ places with inconsistent timeout/encoding.
**Fix:** Create `utils/subprocess_runner.py` with standard defaults.

### M9. Use SecretStr for Credentials
**File:** `core/config.py`
**Issue:** API keys stored as plain strings in config models.
**Fix:** Use `pydantic.SecretStr` for sensitive fields.

### M10. Add Cache Size Monitoring/Pruning
**File:** `context7/kb_cache.py`
**Issue:** Unbounded cache growth.
**Fix:** Add LRU eviction; configurable max entries.

---

## LOW (Backlog)

### L1. Migrate AgentOutputContract to Pydantic
**File:** `core/agent_base.py`
**Issue:** Uses manual dict validation for agent output contracts.
**Fix:** Use Pydantic model for type-safe contract validation.

### L2. Discriminated Unions for Step Configs
**File:** `workflow/models.py`
**Fix:** Use `Annotated[Union[...], Discriminator("type")]` for step configurations.

### L3. Evaluate `uv` for Dependency Management
**Issue:** pip-based installs are slower than modern alternatives.
**Fix:** Evaluate `uv` (fast pip replacement) for dev workflow.

### L4. Add Usage Analytics for Topic Pre-population
**File:** `context7/topic_prepopulator.py`
**Fix:** Track most-queried topics to optimize pre-population.

### L5. Standardize MCP Tool Naming Convention
**File:** `mcp/` modules
**Fix:** Align tool names to `verb_noun` convention per MCP spec.

### L6. RAG Upgrade: TF-IDF Scoring
**File:** `experts/simple_rag.py`
**Issue:** Keyword-only search lacks relevance ranking.
**Fix:** Add TF-IDF or BM25 scoring for better retrieval quality.

### L7. Reusable Annotated Types
**File:** `core/config.py`
**Fix:** Create `types.py` with reusable `Annotated` types for common validators.

---

## Implementation Priority

| Phase | Items | Est. Effort | Impact |
|-------|-------|-------------|--------|
| **Phase 1** | C1-C6 | 2-3 days | Fixes crashes, security holes |
| **Phase 2** | H1-H8 | 1-2 weeks | Reliability and robustness |
| **Phase 3** | M1-M10 | 2-3 weeks | Code quality and maintainability |
| **Phase 4** | L1-L7 | Ongoing | Polish and optimization |
