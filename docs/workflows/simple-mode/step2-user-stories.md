# Step 2: User Stories - Fix Suggestions Generation Bug

## User Stories with Acceptance Criteria

### Story 1: Add Linting Suggestions Generation
**As a** developer receiving code quality reports  
**I want** to receive actionable suggestions when my linting score is below threshold  
**So that** I can improve my code quality by fixing linting issues

**Acceptance Criteria:**
- ✅ When `linting_score` < 7.0, `_generate_category_suggestions()` returns non-empty suggestions list
- ✅ Suggestions include reference to Ruff (Python) or ESLint (TypeScript/JavaScript)
- ✅ Suggestions include actionable commands (e.g., "Run 'ruff check'")
- ✅ Python-specific suggestions mention Ruff auto-fix and configuration
- ✅ TypeScript/JavaScript-specific suggestions mention ESLint auto-fix and configuration
- ✅ Suggestions follow same format as existing categories (base + language-specific)

**Story Points:** 3  
**Priority:** High  
**Dependencies:** None

---

### Story 2: Add Type Checking Suggestions Generation
**As a** developer receiving code quality reports  
**I want** to receive actionable suggestions when my type checking score is below threshold  
**So that** I can improve type safety by fixing type errors

**Acceptance Criteria:**
- ✅ When `type_checking_score` < 7.0, `_generate_category_suggestions()` returns non-empty suggestions list
- ✅ Suggestions include reference to mypy (Python) or TypeScript compiler
- ✅ Suggestions include actionable commands (e.g., "Run 'mypy <file>'")
- ✅ Python-specific suggestions mention type hints, typing module, Optional, Union
- ✅ TypeScript-specific suggestions mention strict mode, explicit return types, avoiding 'any'
- ✅ Suggestions follow same format as existing categories

**Story Points:** 3  
**Priority:** High  
**Dependencies:** None

---

### Story 3: Add Duplication Suggestions Generation
**As a** developer receiving code quality reports  
**I want** to receive actionable suggestions when my duplication score is below threshold  
**So that** I can reduce code duplication and improve maintainability

**Acceptance Criteria:**
- ✅ When `duplication_score` < 7.0, `_generate_category_suggestions()` returns non-empty suggestions list
- ✅ Suggestions include reference to jscpd tool
- ✅ Suggestions include actionable commands (e.g., "Run 'jscpd' to identify duplicates")
- ✅ Suggestions mention extracting duplicate code into reusable functions/components
- ✅ Python-specific suggestions mention utility functions, decorators, context managers
- ✅ TypeScript/React-specific suggestions mention shared components, hooks, HOCs
- ✅ Suggestions include target threshold (e.g., "aim for < 3% duplication")

**Story Points:** 2  
**Priority:** High  
**Dependencies:** None

---

### Story 4: Add Unit Tests for New Categories
**As a** developer maintaining the codebase  
**I want** comprehensive unit tests for the new suggestion generation logic  
**So that** I can ensure correctness and prevent regressions

**Acceptance Criteria:**
- ✅ Unit test for `linting` category with score < 7.0 returns non-empty suggestions
- ✅ Unit test for `type_checking` category with score < 7.0 returns non-empty suggestions
- ✅ Unit test for `duplication` category with score < 7.0 returns non-empty suggestions
- ✅ Unit test verifies Python-specific suggestions are included for Python language
- ✅ Unit test verifies TypeScript-specific suggestions are included for TypeScript language
- ✅ Unit test verifies empty suggestions for scores ≥ 7.0 (excellent threshold)
- ✅ Edge case tests: score = 0.0, 5.0, 7.0, 10.0
- ✅ Test coverage ≥ 80% for new code

**Story Points:** 5  
**Priority:** High  
**Dependencies:** Stories 1, 2, 3

---

### Story 5: Integration Test for Full Workflow
**As a** developer maintaining the codebase  
**I want** integration tests verifying suggestions appear in review output  
**So that** I can ensure end-to-end functionality works correctly

**Acceptance Criteria:**
- ✅ Integration test: Score file with linting issues → suggestions appear in review output
- ✅ Integration test: Score file with type errors → suggestions appear in review output
- ✅ Integration test: Score file with duplication → suggestions appear in review output
- ✅ Integration test verifies suggestions are properly formatted in JSON output
- ✅ Integration test verifies no regression in existing category suggestions

**Story Points:** 3  
**Priority:** Medium  
**Dependencies:** Stories 1, 2, 3, 4

---

## Story Breakdown Summary

| Story | Points | Priority | Status |
|-------|--------|----------|--------|
| Story 1: Linting Suggestions | 3 | High | Pending |
| Story 2: Type Checking Suggestions | 3 | High | Pending |
| Story 3: Duplication Suggestions | 2 | High | Pending |
| Story 4: Unit Tests | 5 | High | Pending |
| Story 5: Integration Tests | 3 | Medium | Pending |
| **Total** | **16** | | |

## Implementation Order

1. **Story 1** - Linting suggestions (foundation)
2. **Story 2** - Type checking suggestions (foundation)
3. **Story 3** - Duplication suggestions (foundation)
4. **Story 4** - Unit tests (validation)
5. **Story 5** - Integration tests (validation)

## Definition of Done

- ✅ All stories completed and tested
- ✅ Code passes linting (Ruff score ≥ 9.0)
- ✅ Code passes type checking (mypy score ≥ 9.0)
- ✅ Test coverage ≥ 80% for new code
- ✅ All tests pass (unit + integration)
- ✅ No regression in existing functionality
- ✅ Code review approved
- ✅ Documentation updated if needed
