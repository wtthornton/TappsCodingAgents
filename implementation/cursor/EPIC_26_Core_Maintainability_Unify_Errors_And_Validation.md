# Epic 26: Core Maintainability — Unify Errors and Validation (Reduce Footguns)

## Epic Goal

Improve maintainability and correctness of the existing framework by eliminating confusing patterns (e.g., built-in exception shadowing) and centralizing security-critical validation logic—without changing feature scope.

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - Custom exception types exist in `tapps_agents/core/exceptions.py`.
  - Multiple agents implement overlapping validation patterns (path traversal checks, etc.).
  - Error envelope system exists for structured error reporting.
- **Technology stack**: Python 3.13+, Pydantic config, structured logging/error envelopes.
- **Integration points**:
  - Exceptions: `tapps_agents/core/exceptions.py`
  - Base agent: `tapps_agents/core/agent_base.py`
  - Agent implementations: `tapps_agents/agents/*`

### Enhancement Details

- **What’s being improved (no new features)**:
  - Remove exception names that shadow Python built-ins (e.g., `FileNotFoundError`) to reduce ambiguity and tooling confusion.
  - Define a centralized validation API for path and file operations and ensure all agents use it.
  - Clarify which errors are user-facing vs internal and ensure consistent mapping to CLI exit codes.
- **How it integrates**:
  - Preserves the same error semantics; improves naming and reuse.
- **2025 standards / guardrails**:
  - **No shadowing of stdlib symbols**: avoid confusing stack traces and type checks.
  - **Centralize security-critical logic**: one implementation for validation; tests cover it.
  - **Typed, structured errors**: map internal exceptions into stable error envelopes for CLI/API users.
- **Success criteria**:
  - Reduced duplication and clearer debugging.
  - Consistent error behavior across agents and CLI.

## Stories

1. **Story 26.1: Replace stdlib-shadowing exception names** ✅ **COMPLETED**
   - **Goal**: Remove ambiguous exception naming.
   - **Acceptance Criteria**:
     - ✅ No project-defined exception class shares names with Python built-ins.
     - ✅ If backwards compatibility is required, provide explicit aliases with deprecation notes (documented).
   - **Implementation**: Renamed `FileNotFoundError` to `AgentFileNotFoundError` with backwards-compatible alias. Updated error envelope system to handle both.

2. **Story 26.2: Centralize validation and remove duplicated checks** ✅ **COMPLETED**
   - **Goal**: Ensure one authoritative implementation for path/file validation and enforcement.
   - **Acceptance Criteria**:
     - ✅ A single shared validation module/API is used by `BaseAgent` and all agents performing file operations.
     - ✅ Agent-specific ad-hoc traversal checks are removed or reduced to thin wrappers.
   - **Implementation**: Removed duplicate validation logic from ReviewerAgent. All agents now use `BaseAgent._validate_path()` which uses `PathValidator`.

3. **Story 26.3: Error envelope and CLI mapping consistency** ✅ **COMPLETED**
   - **Goal**: Ensure consistent error reporting across CLI commands.
   - **Acceptance Criteria**:
     - ✅ All errors map to structured envelopes with stable error codes and categories.
     - ✅ CLI consistently converts errors into non-zero exit codes and stable JSON output contract (align with Epic 22).
   - **Implementation**: Added `get_exit_code_from_error_category()` function to map error categories to exit codes. Updated `handle_agent_error()` to extract error envelope information and use appropriate exit codes.

4. **Story 26.4: Maintainability tests** ✅ **COMPLETED**
   - **Goal**: Prevent regression into duplication/shadowing.
   - **Acceptance Criteria**:
     - ✅ Tests (or static checks) fail if stdlib-shadowing exceptions are reintroduced.
     - ✅ Tests cover centralized validation behavior and ensure agent usage.
   - **Implementation**: Created `tests/unit/core/test_exceptions_maintainability.py` with tests for exception naming and centralized validation usage.

## Compatibility Requirements

- [x] Maintain backwards compatibility for external callers where feasible (documented deprecations if needed).
- [x] No changes to top-level CLI command names or agent commands.

## Risk Mitigation

- **Primary Risk**: Refactoring exception names could break imports for internal code/users.
- **Mitigation**:
  - Provide compatibility aliases and a deprecation window if external usage exists.
  - Communicate clearly in docs/changelog.
- **Rollback Plan**:
  - Restore old names while keeping centralized validation improvements.

## Definition of Done

- [x] No stdlib-shadowing exception names remain.
- [x] Validation logic is centralized and used consistently across agents.
- [x] Error envelope behavior and CLI mapping are consistent and tested.

## Integration Verification

- **IV1**: Existing workflows and CLI commands still operate normally.
- **IV2**: Errors appear with stable codes/categories and correct exit codes.
- **IV3**: Validation enforcement prevents unsafe operations consistently.


