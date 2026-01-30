# User Story: ENH-001-S1 - Core Workflow Enforcer

**Story ID:** ENH-001-S1
**Epic:** ENH-001 Workflow Enforcement System
**Priority:** High
**Story Points:** 3
**Status:** In Progress
**Estimated Effort:** 12 hours
**GitHub Issue:** #13
**Beads ID:** TappsCodingAgents-015

---

## User Story

> As a developer using TappsCodingAgents, I want my direct code edits to be intercepted before execution, so that I can be reminded to use workflows for better quality.

---

## Context

This is Story 1 of the ENH-001 Workflow Enforcement System epic. It implements the core enforcement engine that intercepts file write/edit operations and enforces workflow usage based on configuration.

**Dependencies:**
- ✅ Story 4 (Configuration System) - **COMPLETE** (`tapps_agents/core/llm_behavior.py` exists)

**Related Stories:**
- Story 2 (Intent Detection) - Will enhance confidence scoring
- Story 3 (Message Formatting) - Will replace basic messages
- Story 4 (Configuration System) - **COMPLETE** (EnforcementConfig)

**Project Context:**
- **Deployment Type:** Local (confidence: 0.5)
- **Tenancy:** Single-tenant (confidence: 0.7)
- **Security Level:** Standard
- **Tech Stack:** Python 3.12+, pytest, PyYAML

---

## Acceptance Criteria

### Functional Requirements

1. ✅ **File Operation Interception**
   - All `Write` tool invocations are intercepted before execution
   - All `Edit` tool invocations are intercepted before execution
   - File creation operations (new files) are detected
   - User intent is captured from context (prompt, file path, operation type)

2. ✅ **Enforcement Decision Making**
   - Configuration loaded from `.tapps-agents/config.yaml` via `EnforcementConfig`
   - Enforcement decision made based on mode:
     - `"blocking"` → Return `{"action": "block", "message": "...", "should_block": true}`
     - `"warning"` → Return `{"action": "warn", "message": "...", "should_block": false}`
     - `"silent"` → Return `{"action": "allow", "message": "", "should_block": false}`
   - Respects `block_direct_edits` and `suggest_workflows` config flags

3. ✅ **Integration Points**
   - Hook into `AsyncFileOps.write_file()` in `tapps_agents/core/async_file_ops.py`
   - Hook into MCP `FilesystemServer.write_file()` in `tapps_agents/mcp/servers/filesystem.py`
   - Support CLI flag `--skip-enforcement` to bypass enforcement

### Non-Functional Requirements

4. ✅ **Performance**
   - Interception latency <50ms (p95) - measured via performance tests
   - Memory overhead <10MB
   - CPU overhead <5% during file operations
   - Configuration load <100ms

5. ✅ **Quality Standards**
   - Test coverage ≥85% (verified with pytest-cov)
   - Full type hints (Python 3.12+)
   - Comprehensive docstrings (Google style)
   - Error handling with fail-safe defaults

6. ✅ **Reliability**
   - No false negatives (all operations intercepted when enabled)
   - Fail-safe design (allow operation on error, don't block)
   - Graceful degradation if config load fails (use defaults)

---

## Tasks

### Task 1.1: Create WorkflowEnforcer Class (4 hours)

**Owner:** @implementer
**Estimated Time:** 4 hours
**Priority:** High

**Description:**
Create the core `WorkflowEnforcer` class in `tapps_agents/workflow/enforcer.py` with enforcement logic.

**Subtasks:**
- [x] Create `tapps_agents/workflow/enforcer.py` with module docstring
- [ ] Define `EnforcementDecision` TypedDict:
  ```python
  class EnforcementDecision(TypedDict):
      action: Literal["block", "warn", "allow"]
      message: str
      should_block: bool
      confidence: float  # Reserved for Story 2
  ```
- [ ] Implement `WorkflowEnforcer.__init__()`:
  - Load config via `EnforcementConfig.from_config_file()`
  - Store config_path and mtime (for future hot-reload)
  - Initialize logger
- [ ] Implement `WorkflowEnforcer.intercept_code_edit()` method:
  - Call `_should_enforce()` to check if enforcement applies
  - Call `_create_decision()` to build decision
  - Add performance logging (debug level)
  - Add error handling (fail-safe to "allow")
- [ ] Implement `_load_config()` helper:
  - Use `EnforcementConfig.from_config_file()`
  - Handle errors gracefully (log warning, use defaults)
  - Cache config instance
- [ ] Implement `_should_enforce()` helper:
  - Check `skip_enforcement` flag (return False if True)
  - Check config mode (return False for "silent")
  - Return True otherwise
- [ ] Implement `_create_decision()` helper:
  - Build basic message for block/warn/allow
  - Set `should_block` flag based on action + `config.block_direct_edits`
  - Set confidence=0.0 (placeholder for Story 2)

**Acceptance Criteria:**
- Class initializes successfully with config
- `intercept_code_edit()` returns correct decision based on config mode
- Handles missing config gracefully (uses defaults)
- Logs enforcement decisions at debug level

**Files Created:**
- `tapps_agents/workflow/enforcer.py` (~250 lines)

---

### Task 1.2: Hook into File Operations (4 hours)

**Owner:** @implementer
**Estimated Time:** 4 hours
**Priority:** High

**Description:**
Integrate `WorkflowEnforcer` into file operation hooks.

**Subtasks:**
- [ ] **Hook into `AsyncFileOps.write_file()`**:
  - Add `user_intent: str = ""` parameter
  - Add `skip_enforcement: bool = False` parameter
  - Import `WorkflowEnforcer` (lazy import to avoid circular dependency)
  - Call `enforcer.intercept_code_edit()` before write
  - Raise `RuntimeError` if `should_block=True`
  - Log warning if `action="warn"`
  - Add unit test for enforcement integration

- [ ] **Hook into MCP `FilesystemServer.write_file()`**:
  - Add `user_intent: str = ""` parameter
  - Add `skip_enforcement: bool = False` parameter
  - Call `enforcer.intercept_code_edit()` before write
  - Return error response `{"blocked": true, "message": "..."}` if blocked
  - Log warning if `action="warn"`
  - Add unit test for enforcement integration

- [ ] **Add CLI flag `--skip-enforcement`**:
  - Add to CLI argument parser in `tapps_agents/cli.py`
  - Pass flag through to file operations
  - Document in `--help` output
  - Add integration test for flag

- [ ] **Update `.tapps-agents/config.yaml`**:
  - Ensure `llm_behavior.workflow_enforcement` section exists
  - Set default mode to `"warning"` initially (less disruptive for testing)
  - Document configuration options in comments

**Acceptance Criteria:**
- File write operations call enforcer before execution
- `--skip-enforcement` flag bypasses enforcement
- Config changes affect enforcement behavior
- No breaking changes to existing workflows

**Files Modified:**
- `tapps_agents/core/async_file_ops.py`
- `tapps_agents/mcp/servers/filesystem.py`
- `tapps_agents/cli.py` (add --skip-enforcement flag)
- `.tapps-agents/config.yaml` (add enforcement section if missing)

---

### Task 1.3: Write Unit Tests (4 hours)

**Owner:** @tester
**Estimated Time:** 4 hours
**Priority:** High

**Description:**
Comprehensive test suite for `WorkflowEnforcer` with ≥85% coverage.

**Test Categories:**

**1. Basic Enforcement Logic (30 tests)**
- Test blocking mode blocks operations
- Test warning mode shows warning but allows
- Test silent mode logs only (no blocking)
- Test skip_enforcement flag bypasses all modes
- Test missing config uses defaults
- Test invalid config handles gracefully

**2. Configuration Integration (15 tests)**
- Test loading from `.tapps-agents/config.yaml`
- Test custom config path
- Test partial config (missing fields)
- Test invalid YAML (error handling)
- Test config validation (mode, threshold)

**3. Decision Logic (20 tests)**
- Test new file detection (`is_new_file=True`)
- Test existing file editing (`is_new_file=False`)
- Test user intent capture
- Test decision message generation
- Test should_block flag logic (action + block_direct_edits)

**4. Performance Tests (10 tests)**
- Test interception latency <50ms (p95) - 100 iterations
- Test memory overhead <10MB (use tracemalloc)
- Test CPU overhead <5% (use time.process_time)
- Test config caching (load time <100ms after first load)

**5. Integration Tests (10 tests)**
- Test AsyncFileOps.write_file() integration
- Test MCP filesystem server integration
- Test CLI flag --skip-enforcement
- Test end-to-end enforcement flow (intercept → decide → block/warn/allow)

**Subtasks:**
- [ ] Create `tests/test_workflow_enforcer.py` with test classes:
  - `TestWorkflowEnforcerInit` - Initialization tests
  - `TestEnforcementDecision` - Decision logic tests
  - `TestConfigurationIntegration` - Config loading tests
  - `TestFileOperationHooks` - Integration tests
  - `TestPerformance` - Performance requirement tests
  - `TestEdgeCases` - Error scenarios and edge cases

- [ ] Create test fixtures:
  - `temp_config()` - Temporary config file for testing
  - `enforcer()` - WorkflowEnforcer instance with test config
  - `mock_async_file_ops()` - Mock AsyncFileOps for integration tests

- [ ] Implement performance test:
  ```python
  def test_interception_latency_under_50ms(self, enforcer):
      """Test p95 latency <50ms."""
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

      p95 = sorted(latencies)[94]  # 95th percentile
      assert p95 < 50.0, f"p95 latency {p95}ms exceeds 50ms"
  ```

- [ ] Run pytest with coverage:
  ```bash
  pytest tests/test_workflow_enforcer.py --cov=tapps_agents/workflow/enforcer --cov-report=term-missing
  ```

**Acceptance Criteria:**
- Test coverage ≥85% (verified with pytest-cov)
- All tests pass
- Performance tests verify <50ms latency, <10MB memory, <5% CPU
- Edge cases handled (missing config, invalid params, errors)

**Files Created:**
- `tests/test_workflow_enforcer.py` (~400 lines)

---

## Technical Specifications

### Files to Create/Modify

**New Files:**
1. `tapps_agents/workflow/enforcer.py` (~250 lines) - Core enforcer
2. `tests/test_workflow_enforcer.py` (~400 lines) - Test suite

**Modified Files:**
3. `tapps_agents/core/async_file_ops.py` - Add enforcement hook
4. `tapps_agents/mcp/servers/filesystem.py` - Add enforcement hook
5. `tapps_agents/cli.py` - Add --skip-enforcement flag
6. `.tapps-agents/config.yaml` - Add enforcement section (if missing)

### Key Components

**EnforcementDecision (TypedDict):**
```python
class EnforcementDecision(TypedDict):
    action: Literal["block", "warn", "allow"]
    message: str
    should_block: bool
    confidence: float  # Reserved for Story 2
```

**WorkflowEnforcer Class:**
```python
class WorkflowEnforcer:
    """Core workflow enforcement engine."""

    def __init__(
        self,
        config_path: Path | None = None,
        config: EnforcementConfig | None = None
    ):
        """Initialize enforcer with config."""

    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool,
        skip_enforcement: bool = False
    ) -> EnforcementDecision:
        """Intercept file operation and make enforcement decision."""

    def _load_config(self, config_path: Path | None = None) -> EnforcementConfig:
        """Load enforcement configuration."""

    def _should_enforce(
        self,
        file_path: Path,
        is_new_file: bool,
        skip_enforcement: bool
    ) -> bool:
        """Determine if enforcement should be applied."""

    def _create_decision(
        self,
        action: Literal["block", "warn", "allow"],
        file_path: Path,
        user_intent: str
    ) -> EnforcementDecision:
        """Create enforcement decision with message."""
```

### Integration Pattern (AsyncFileOps Hook)

```python
# In tapps_agents/core/async_file_ops.py

class AsyncFileOps:
    @staticmethod
    async def write_file(
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
        user_intent: str = "",  # NEW
        skip_enforcement: bool = False,  # NEW
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
                f"File operation blocked: {decision['message']}"
            )
        elif decision["action"] == "warn":
            logger.warning(decision["message"])

        # Proceed with write
        # ... existing write logic ...
```

---

## Dependencies

### Internal Dependencies

**Required (Already Implemented):**
- `tapps_agents.core.llm_behavior.EnforcementConfig` (Story 4) ✅
- `.tapps-agents/config.yaml` with `llm_behavior.workflow_enforcement` section ✅

**Future Stories (Will Enhance):**
- Story 2 (Intent Detection): Will enhance confidence scoring
- Story 3 (Message Formatting): Will replace basic messages with rich output

### External Dependencies

- **Python 3.12+**: Modern type hints (`Literal`, `TypedDict`)
- **PyYAML**: Configuration loading (already in project)
- **pytest**: Testing framework (already in project)
- **pytest-cov**: Coverage measurement (already in project)

---

## Non-Functional Requirements

### Performance Targets

- **Interception Latency:** <50ms (p95) - measured in performance tests
- **Memory Overhead:** <10MB total for enforcer instance
- **CPU Overhead:** <5% during file operations
- **Configuration Load:** <100ms (cached after first load)

### Quality Standards

- **Test Coverage:** ≥85% (verified with `pytest --cov`)
- **Type Safety:** Full type hints, mypy strict compatible
- **Error Handling:** Fail-safe (allow on error, don't block user)
- **Logging:** Debug-level logs for enforcement decisions

### Reliability

- **No False Negatives:** Never skip enforcement check when enabled
- **Fail-Safe:** If enforcement check errors, default to "allow"
- **Graceful Degradation:** Use defaults if config load fails

---

## Testing Strategy

### Test Coverage Breakdown

| Category | Tests | Lines | Coverage Target |
|----------|-------|-------|-----------------|
| Basic Enforcement Logic | 30 | ~150 | 100% |
| Configuration Integration | 15 | ~75 | 100% |
| Decision Logic | 20 | ~100 | 100% |
| Performance Tests | 10 | ~50 | 90% |
| Integration Tests | 10 | ~50 | 85% |
| **Total** | **85** | **~425** | **≥85%** |

### Performance Testing

**Metrics to Track:**
- Interception latency (p50, p95, p99)
- Memory overhead (tracemalloc)
- CPU overhead (time.process_time)
- Config load time

**Test Framework:**
```python
@pytest.mark.performance
class TestPerformanceRequirements:
    def test_latency_p95_under_50ms(self, enforcer):
        """Verify p95 latency <50ms."""
        # Run 100 iterations, measure p95

    def test_memory_overhead_under_10mb(self, enforcer):
        """Verify memory overhead <10MB."""
        # Use tracemalloc to measure

    def test_cpu_overhead_under_5_percent(self, enforcer):
        """Verify CPU overhead <5%."""
        # Use time.process_time to measure
```

---

## Risk Management

### Risk 1: Performance Impact

**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Cache config after load (don't reload on every call)
- Measure latency in tests (fail if >50ms p95)
- Use simple decision logic (no expensive computations)
- Profile with cProfile to identify bottlenecks

**Contingency:**
- If latency >100ms, add fast-path bypass for silent mode

### Risk 2: Breaking Existing Workflows

**Probability:** Medium
**Impact:** High

**Mitigation:**
- Make enforcement opt-in initially (default mode="warning")
- Add --skip-enforcement CLI flag for easy override
- Fail-safe design (allow on error, don't block)
- Comprehensive testing before enabling blocking mode

**Contingency:**
- If >30% of users disable enforcement, reconsider default mode

### Risk 3: Configuration Errors

**Probability:** Low
**Impact:** Low

**Mitigation:**
- Use defaults if config missing or invalid
- Validate config in EnforcementConfig (Story 4 already does this)
- Log warnings for invalid config (don't fail silently)

**Contingency:**
- Add config validation CLI command if errors frequent

---

## Success Metrics

### Story-Level Metrics

- **Interception Coverage:** 100% of Write/Edit operations intercepted
- **Latency:** <50ms p95 (measured in performance tests)
- **Memory:** <10MB overhead (measured with tracemalloc)
- **Test Coverage:** ≥85% (verified with pytest-cov)
- **False Negatives:** 0 (all operations caught when enabled)

### Epic-Level Metrics (Contribution)

- **Workflow Usage Rate:** Target 95%+ (currently ~30%)
- **Issue Detection:** 95%+ caught before user sees code
- **Performance:** <50ms interception latency
- **Test Coverage:** ≥85%

---

## Definition of Done

- [ ] `tapps_agents/workflow/enforcer.py` implemented (~250 lines)
- [ ] `tests/test_workflow_enforcer.py` implemented (~400 lines)
- [ ] All unit tests passing (≥85% coverage)
- [ ] Performance tests passing (<50ms latency, <10MB memory, <5% CPU)
- [ ] Integration with AsyncFileOps working
- [ ] Integration with MCP filesystem server working
- [ ] CLI flag `--skip-enforcement` working
- [ ] Documentation complete (docstrings, module docs)
- [ ] Code review passed (type hints, error handling)
- [ ] Manual testing: enforcement blocks/warns/allows correctly
- [ ] GitHub issue #13 updated with progress
- [ ] Beads TappsCodingAgents-015 marked as done

---

## References

### Epic and Stories
- **Epic Document:** `stories/enh-001-workflow-enforcement.md`
- **Story 1 (This Story):** ENH-001-S1 Core Workflow Enforcer
- **Story 2 (Next):** ENH-001-S2 Intent Detection System
- **Story 3 (Future):** ENH-001-S3 User Messaging System
- **Story 4 (Complete):** ENH-001-S4 Configuration System ✅

### Related Code
- **Configuration:** `tapps_agents/core/llm_behavior.py` (EnforcementConfig)
- **Config Tests:** `tests/test_llm_behavior.py`
- **File Operations:** `tapps_agents/core/async_file_ops.py`
- **MCP Server:** `tapps_agents/mcp/servers/filesystem.py`

### Documentation
- **CLAUDE.md:** Project-wide rules and guidelines
- **docs/ARCHITECTURE.md:** System architecture
- **docs/test-stack.md:** Testing strategy
- **docs/WORKFLOW_ENFORCEMENT_GUIDE.md:** Workflow enforcement user guide

---

## Next Steps

1. **Begin Task 1.1:** Create WorkflowEnforcer class (4 hours)
2. **Begin Task 1.2:** Hook into file operations (4 hours)
3. **Begin Task 1.3:** Write unit tests (4 hours)
4. **Manual Testing:** Validate enforcement in real workflows
5. **Gather Metrics:** Measure latency, false positive rate, user feedback
6. **Begin Story 2:** Intent Detection System (enhance confidence scoring)

---

**Created By:** TappsCodingAgents Planner Agent
**Date:** 2026-01-29
**Story ID:** ENH-001-S1
**Epic ID:** ENH-001
**Status:** In Progress
**Next Task:** Task 1.1 - Create WorkflowEnforcer Class
