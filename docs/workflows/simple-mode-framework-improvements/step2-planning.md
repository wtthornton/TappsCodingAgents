# Step 2: Planning - User Stories and Implementation Plan

**Date:** January 16, 2025  
**Workflow:** Full SDLC - Framework Improvements Based on Usage Analysis  
**Step:** Planning  
**Agent:** @planner

## Executive Summary

This document provides user stories, acceptance criteria, story point estimates, and a detailed implementation plan for addressing the critical gaps identified in the usage analysis.

## User Stories

### Story 1: Simple Mode Intent Detection

**As a** developer using TappsCodingAgents  
**I want** the system to automatically use Simple Mode when I mention "@simple-mode"  
**So that** my explicit intent is followed and I get the orchestration benefits

**Acceptance Criteria:**
- [ ] System detects "@simple-mode", "simple mode", "use simple mode" keywords
- [ ] When detected, Simple Mode workflow is forced (no CLI fallback)
- [ ] Clear error message if Simple Mode requested but not available
- [ ] Works in both Cursor Skills and CLI contexts
- [ ] Unit tests with ≥80% coverage

**Story Points:** 5  
**Priority:** P1 - Critical  
**Dependencies:** None

### Story 2: Code Generation Syntax Validation

**As a** developer using code generation  
**I want** generated code to be validated for syntax errors before writing  
**So that** I don't get broken code files

**Acceptance Criteria:**
- [ ] Python code validated using `ast.parse()` before writing
- [ ] Syntax errors caught and reported with helpful context
- [ ] System attempts to fix common syntax errors automatically
- [ ] Works for Python, TypeScript, JavaScript
- [ ] Unit tests with ≥80% coverage

**Story Points:** 8  
**Priority:** P1 - Critical  
**Dependencies:** None

### Story 3: Module Path Sanitization

**As a** developer using test generation  
**I want** module import paths to be automatically sanitized  
**So that** I don't get syntax errors from hyphens in module names

**Acceptance Criteria:**
- [ ] Hyphens replaced with underscores in module paths
- [ ] Invalid characters removed or replaced
- [ ] Works for absolute and relative imports
- [ ] Applied in test generation and code generation
- [ ] Unit tests with ≥80% coverage

**Story Points:** 3  
**Priority:** P1 - Critical  
**Dependencies:** Story 2 (Code Validation)

### Story 4: CLI Implement Direct Execution

**As a** developer using CLI commands  
**I want** the `implement` command to write code directly to files  
**So that** I don't have to manually execute instruction objects

**Acceptance Criteria:**
- [ ] CLI `implement` writes code directly (default behavior)
- [ ] `--dry-run` flag available for preview
- [ ] Instruction objects optional (backward compatible)
- [ ] Clear documentation on behavior
- [ ] Unit tests with ≥80% coverage

**Story Points:** 5  
**Priority:** P1 - High  
**Dependencies:** Story 2 (Code Validation)

### Story 5: Workflow Enforcement

**As a** framework maintainer  
**I want** the system to detect and suggest Simple Mode for workflow-style tasks  
**So that** users get better orchestration automatically

**Acceptance Criteria:**
- [ ] System detects workflow-style task requests
- [ ] System suggests Simple Mode when appropriate
- [ ] System warns when workflows are bypassed
- [ ] Configurable enforcement (strict vs. advisory)
- [ ] Unit tests with ≥80% coverage

**Story Points:** 5  
**Priority:** P2 - Medium  
**Dependencies:** Story 1 (Intent Detection)

### Story 6: Workflow Artifact Generation

**As a** developer using Simple Mode workflows  
**I want** documentation artifacts generated for each workflow step  
**So that** I have full traceability of workflow execution

**Acceptance Criteria:**
- [ ] Each workflow step generates markdown artifact
- [ ] Artifacts saved to `docs/workflows/simple-mode/`
- [ ] Artifacts include step name, inputs, outputs, metadata
- [ ] Consistent formatting across all artifacts
- [ ] Unit tests with ≥80% coverage

**Story Points:** 5  
**Priority:** P2 - Medium  
**Dependencies:** None

### Story 7: Better Error Messages

**As a** developer encountering errors  
**I want** context-aware error messages with actionable guidance  
**So that** I can quickly fix issues

**Acceptance Criteria:**
- [ ] Syntax errors include file location, line number, error type
- [ ] Module path errors suggest sanitization fixes
- [ ] Simple Mode errors include setup instructions
- [ ] Error messages formatted for readability
- [ ] Error messages include "Tip" sections

**Story Points:** 3  
**Priority:** P2 - Medium  
**Dependencies:** Story 2 (Code Validation), Story 3 (Sanitization)

## Implementation Plan

### Phase 1: Critical Fixes (Week 1)

**Goal:** Fix the three critical issues identified in the analysis

1. **Simple Mode Intent Detection** (Story 1)
   - Add intent detection to `IntentParser`
   - Add Simple Mode keyword detection
   - Update `SimpleModeHandler` to force Simple Mode when detected
   - Add error handling for unavailable Simple Mode
   - Write unit tests

2. **Code Generation Validation** (Story 2)
   - Create `CodeValidator` utility class
   - Add validation to `TestGenerator`
   - Add validation to `ImplementerAgent`
   - Add syntax error fixing logic
   - Write unit tests

3. **Module Path Sanitization** (Story 3)
   - Create `ModulePathSanitizer` utility class
   - Integrate into `TestGenerator`
   - Integrate into import statement generation
   - Write unit tests

**Deliverables:**
- Simple Mode intent detection working
- Code validation preventing syntax errors
- Module path sanitization fixing import issues

### Phase 2: High Priority Improvements (Week 2)

**Goal:** Improve CLI experience and workflow enforcement

4. **CLI Implement Direct Execution** (Story 4)
   - Update `ImplementerAgent.implement()` to write directly
   - Add `--dry-run` flag support
   - Maintain backward compatibility
   - Update documentation
   - Write unit tests

5. **Workflow Enforcement** (Story 5)
   - Add workflow detection logic
   - Add Simple Mode suggestions
   - Add bypass warnings
   - Add configuration options
   - Write unit tests

**Deliverables:**
- CLI implement writes code directly
- Workflow enforcement with suggestions

### Phase 3: Quality of Life (Week 3)

**Goal:** Improve documentation and error messages

6. **Workflow Artifact Generation** (Story 6)
   - Create `WorkflowArtifactGenerator` class
   - Integrate into all Simple Mode orchestrators
   - Generate markdown artifacts
   - Write unit tests

7. **Better Error Messages** (Story 7)
   - Create `ErrorMessageFormatter` class
   - Update all error handling
   - Add context-aware messages
   - Write unit tests

**Deliverables:**
- Workflow artifacts generated automatically
- Improved error messages

## Story Point Summary

| Story | Points | Priority | Phase |
|-------|--------|----------|-------|
| Story 1: Intent Detection | 5 | P1 | Phase 1 |
| Story 2: Code Validation | 8 | P1 | Phase 1 |
| Story 3: Path Sanitization | 3 | P1 | Phase 1 |
| Story 4: CLI Direct Execution | 5 | P1 | Phase 2 |
| Story 5: Workflow Enforcement | 5 | P2 | Phase 2 |
| Story 6: Artifact Generation | 5 | P2 | Phase 3 |
| Story 7: Better Errors | 3 | P2 | Phase 3 |
| **Total** | **34** | | |

## Risk Assessment

### High Risk
- **Breaking Changes:** CLI behavior changes may break existing scripts
  - **Mitigation:** Feature flags, backward compatibility, migration guide

### Medium Risk
- **Performance Impact:** Code validation may slow generation
  - **Mitigation:** Optimize validation, async where possible, cache results

### Low Risk
- **False Positives:** Intent detection may incorrectly detect Simple Mode
  - **Mitigation:** Confidence thresholds, manual override, feedback mechanism

## Dependencies

```
Story 1 (Intent Detection)
  └─ No dependencies

Story 2 (Code Validation)
  └─ No dependencies

Story 3 (Path Sanitization)
  └─ Story 2 (Code Validation)

Story 4 (CLI Direct Execution)
  └─ Story 2 (Code Validation)

Story 5 (Workflow Enforcement)
  └─ Story 1 (Intent Detection)

Story 6 (Artifact Generation)
  └─ No dependencies

Story 7 (Better Errors)
  └─ Story 2 (Code Validation)
  └─ Story 3 (Path Sanitization)
```

## Success Metrics

- ✅ Simple Mode used when requested: **100%** (target)
- ✅ Generated code syntax errors: **0%** (target)
- ✅ Module path issues auto-fixed: **100%** (target)
- ✅ CLI implement writes directly: **Default behavior** (target)
- ✅ Workflow artifacts generated: **100% of workflows** (target)
- ✅ Error message helpfulness: **≥4/5 user rating** (target)

## Next Steps

1. **Step 3:** Design architecture for new features
2. **Step 4:** Design API specifications
3. **Step 5:** Implement features (Phase 1 - Critical Fixes)
4. **Step 6:** Review and quality check
5. **Step 7:** Generate and run tests
6. **Step 8:** Security scan
7. **Step 9:** Document API

---

**Document Version:** 1.0  
**Last Updated:** January 16, 2025  
**Status:** Complete - Ready for Architecture Design Phase
