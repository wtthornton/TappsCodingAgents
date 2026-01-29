# EPIC ENH-002: ReviewerAgent Quality Tool Improvements

**Epic ID:** ENH-002
**Title:** Improve ReviewerAgent Quality Tools (Auto-fix, Scoped Mypy, Grouped Ruff)
**Status:** In Progress
**Created:** 2026-01-29
**GitHub Epic Issue:** #TBD (to be created)

---

## Epic Summary

Enhance ReviewerAgent quality tools based on feedback from session-2026-01-29 showing 30 auto-fixable Ruff issues and verbose review output. Implement three key improvements: (1) auto-fix Ruff issues after implementation, (2) scope mypy to target file for performance, (3) group Ruff output by rule code for clarity.

**Expected Impact:**
- Zero style issues in reviews (auto-fixed)
- 70% faster mypy execution (60s → 10s)
- Cleaner, grouped Ruff reports

**Quality Gates:**
- Overall Score: ≥75
- Security Score: ≥8.5
- Test Coverage: ≥80%

---

## Stories

### Story 1: Auto-Fix Module Implementation

**Story ID:** ENH-002-S1
**Priority:** High
**Story Points:** 5
**Status:** ✅ Complete
**GitHub Issue:** #16
**Completed:** 2026-01-29

**Description:**
Implement AutoFixModule in ImplementerAgent with backup/restore, validation, and rollback capabilities. Integrates with Ruff for auto-fixes.

**Acceptance Criteria:**
- ✅ BackupManager creates timestamped backups with SHA-256 checksums
- ✅ AutoFixModule runs `ruff check --fix` after code generation
- ✅ ValidationManager validates syntax, imports, linting after fixes
- ✅ RestoreManager rolls back on validation failure
- ✅ Auto-fix completes in <5 seconds for typical files (performance tests included)
- ✅ Comprehensive error handling with graceful degradation

**Files:**
- ✅ `tapps_agents/agents/implementer/auto_fix.py` (new, 1120 lines - 4 classes, complete implementation)
- ⏸️ `tapps_agents/agents/implementer/agent.py` (integration pending - Story 4)
- ✅ `tests/agents/implementer/test_auto_fix.py` (new, 972 lines - 52 tests, 82.93% coverage)

**Dependencies:** None

**Artifacts:**
- Enhanced Prompt: ✅ Complete
- Requirements Analysis: ✅ Complete (34-49 hours estimate)
- Architecture Design: ✅ Complete (Pipeline + Strategy patterns)
- API Specification: ✅ Complete (docs/api/reviewer-quality-tools-api.md)
- Implementation: ✅ Complete (1120 lines, 4 classes)
- Code Review: ✅ Complete (88.5/100 score, 0 Ruff issues after auto-fix)
- Test Suite: ✅ Complete (52 tests, 82.93% coverage, all passing)

**Quality Metrics:**
- Overall Score: 88.5/100 ✅ (Target: ≥75)
- Security Score: 10.0/10 ✅ (Target: ≥8.5)
- Test Coverage: 82.93% ✅ (Target: ≥80%)
- Complexity: 2.0/10 ✅ (Low complexity)
- Linting: 10.0/10 ✅ (0 issues after auto-fix)

---

### Story 2: Scoped Mypy Executor

**Story ID:** ENH-002-S2
**Priority:** High
**Story Points:** 3
**Status:** Todo
**GitHub Issue:** #TBD

**Description:**
Implement ScopedMypyExecutor to run mypy with file-level scoping for 70% performance improvement.

**Acceptance Criteria:**
- ✅ Uses `--follow-imports=skip` and `--no-site-packages` flags
- ✅ Filters results to target file only
- ✅ Executes in <10 seconds (vs 30-60s unscoped)
- ✅ Maintains type checking accuracy
- ✅ Graceful fallback to full mypy on timeout

**Files:**
- `tapps_agents/agents/reviewer/tools/scoped_mypy.py` (new, ~200 lines)
- `tapps_agents/agents/reviewer/agent.py` (modified, integration)
- `tests/agents/reviewer/tools/test_scoped_mypy.py` (new, ~250 lines)

**Dependencies:** ENH-002-S1 (for integration testing)

---

### Story 3: Ruff Output Grouping

**Story ID:** ENH-002-S3
**Priority:** Medium
**Story Points:** 2
**Status:** Todo
**GitHub Issue:** #TBD

**Description:**
Implement RuffGroupingParser to group Ruff issues by error code for cleaner, more actionable reports.

**Acceptance Criteria:**
- ✅ Parses Ruff JSON output and groups by error code
- ✅ Sorts groups by severity (error > warning > info), then count
- ✅ Renders in markdown, HTML, and JSON formats
- ✅ Shows fixable count per group
- ✅ Backward compatible with ungrouped output

**Files:**
- `tapps_agents/agents/reviewer/tools/ruff_grouping.py` (new, ~150 lines)
- `tapps_agents/agents/reviewer/report_generator.py` (modified, rendering)
- `tests/agents/reviewer/tools/test_ruff_grouping.py` (new, ~200 lines)

**Dependencies:** None

---

### Story 4: Integration and Documentation

**Story ID:** ENH-002-S4
**Priority:** Medium
**Story Points:** 2
**Status:** Todo
**GitHub Issue:** #TBD

**Description:**
Integrate all three improvements, run end-to-end testing, update documentation.

**Acceptance Criteria:**
- ✅ Full workflow test with all improvements active
- ✅ Performance benchmarks confirm targets met
- ✅ Security scan passes (≥8.5 score)
- ✅ Documentation updated (API docs, user guide)
- ✅ Configuration examples added

**Files:**
- `docs/api/reviewer-quality-tools.md` (already created)
- `docs/CONFIGURATION.md` (updated)
- `tests/integration/test_quality_tools_integration.py` (new)

**Dependencies:** ENH-002-S1, ENH-002-S2, ENH-002-S3

---

## Epic Progress

**Total Story Points:** 12
**Completed:** 5 (ENH-002-S1) ✅
**In Progress:** 0
**Todo:** 3 (ENH-002-S2, ENH-002-S3, ENH-002-S4)
**Progress:** 41.7% Complete (5/12 story points)

---

## Related Documentation

- Enhanced Prompt: Generated via EnhancerAgent (7-stage enhancement)
- Requirements Analysis: 8 risks identified, 34-49 hour estimate, 79% confidence
- Architecture Design: Pipeline + Strategy + Decorator patterns, security architecture
- API Specification: docs/api/reviewer-quality-tools-api.md (11 data models, 8 classes)

---

## Implementation Timeline

**Planning Phase:** ✅ Complete (2026-01-29)
- Step 1: Enhancement ✅
- Step 2: Requirements ✅
- Step 3: Architecture ✅
- Step 4: API Design ✅

**Implementation Phase:** In Progress (41.7% complete)
- ENH-002-S1: Auto-Fix Module ✅ Complete (2026-01-29)
- ENH-002-S2: Scoped Mypy (1-2 days) - Todo
- ENH-002-S3: Ruff Grouping (1 day) - Todo
- ENH-002-S4: Integration (1 day) - Todo

**Total Estimated Time:** 5-7 days
**Actual Time (S1):** ~4 hours (planning + implementation + testing)

---

## Success Metrics

**Before:**
- 30 Ruff issues per review (auto-fixable)
- 60s mypy execution time
- Verbose, ungrouped Ruff output

**After:**
- 0 Ruff issues (auto-fixed)
- 10s mypy execution time (70% reduction)
- Grouped, actionable Ruff output

**Quality:**
- Overall Score: ≥75 ✅
- Security Score: ≥8.5 ✅
- Test Coverage: ≥80% ✅
