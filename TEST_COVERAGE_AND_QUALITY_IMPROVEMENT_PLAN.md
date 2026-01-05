# Test Coverage and Quality Improvement Plan

## Current State

Based on tapps-agents validation:
- **Complexity:** ✅ All files pass threshold (< 5.0)
- **Test Coverage:** ❌ 2 files have 0% coverage (main.py, cursor_executor.py)
- **Type Hints:** ⚠️ All files score 5.0/10 (need improvement)
- **Quality Gates:** 2 files failing due to test coverage

## Phase 1: Add Test Coverage for CLI Main (P0)

### 1.1 Create Test File for CLI Main

**File:** `tests/unit/cli/test_main.py` (NEW)

**Tests to Create:**
1. Test `route_command()` with agent commands (reviewer, planner, implementer, etc.)
2. Test `route_command()` with top-level commands (create, init, workflow, etc.)
3. Test `route_command()` with special commands (cleanup, health, hardware-profile)
4. Test handler dictionary lookups
5. Test prompt enhancement middleware
6. Test help display when no agent specified

**Target Coverage:** >80%

## Phase 2: Add Test Coverage for Cursor Executor (P0)

### 2.1 Create Test File for Cursor Executor

**File:** `tests/unit/workflow/test_cursor_executor_refactored.py` (NEW)

**Tests to Create:**
1. Test `run()` method execution flow
2. Test step execution and artifact extraction
3. Test error handling and timeout scenarios
4. Test worktree management
5. Test marker writing (DONE/FAILED)

**Target Coverage:** >80%

## Phase 3: Improve Type Hints (P1)

### 3.1 Add Type Hints to CLI Main

**File:** `tapps_agents/cli/main.py`

**Actions:**
- Add return type annotations to all functions
- Add parameter type hints
- Use `Optional[T]` for nullable types
- Add type hints to handler dictionaries

**Target:** Improve type checking score from 5.0 to 8.0+

### 3.2 Add Type Hints to Cursor Executor

**File:** `tapps_agents/workflow/cursor_executor.py`

**Actions:**
- Add return type annotations
- Add parameter type hints
- Type hint class attributes
- Use proper generic types

**Target:** Improve type checking score from 5.0 to 8.0+

## Phase 4: Fix Remaining Linting Issues (P2)

### 4.1 Fix Line Length Violations

**File:** `tapps_agents/workflow/cursor_executor.py`

**Actions:**
- Break long lines (>88 chars) into multiple lines
- Extract long expressions into variables

**Target:** Improve linting score from 5.0 to 10.0

## Success Criteria

- **Test Coverage:** >80% for main.py and cursor_executor.py
- **Type Checking:** >8.0/10 for all files
- **Overall Scores:** >80/100 for all files
- **Quality Gates:** All files pass
