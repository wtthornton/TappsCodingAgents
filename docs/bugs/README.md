# Bug Reports - TappsCodingAgents

This directory contains detailed bug reports for issues discovered during testing and development.

## Active Bugs

### High Priority

| Bug ID | Title | Severity | Component | Status |
|--------|-------|----------|-----------|--------|
| [BUG-001](BUG-001-git-worktree-parallel-conflicts.md) | Git Worktree Conflicts in Parallel Execution | High | Workflow Orchestration | Open |

**Impact:** Cannot run multiple workflows in parallel due to git worktree path conflicts.

### Medium Priority

| Bug ID | Title | Severity | Component | Status |
|--------|-------|----------|-----------|--------|
| [BUG-002](BUG-002-cli-command-quotation-parsing.md) | CLI Command Quotation Parsing Error | Medium | Direct Execution | Open |
| [BUG-003](BUG-003-workflow-error-handling-recovery.md) | Workflow Error Handling and Recovery | Medium | Workflow Orchestration | Open |

**Impact:** Workflows fail silently, steps marked as completed when they failed, confusing error propagation.

## Bug Report Template

When creating new bug reports, use this structure:

```markdown
# BUG-XXX: Title

**Date:** YYYY-MM-DD
**Severity:** High/Medium/Low
**Component:** Component Name
**Status:** Open/In Progress/Fixed/Closed

---

## Summary
Brief description of the issue.

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Root Cause
Analysis of the underlying issue.

## Impact
Severity and consequences.

## Suggested Fix
Proposed solution with code examples.

## Files to Investigate
List of files to check.

## Testing Verification
How to verify the fix works.

## Related Issues
Links to related bugs.

## Workaround
Temporary solution.

---
**Reported by:** Name
**Affects:** Version
**Priority:** P1/P2/P3
```

## Summary Statistics

- **Total Open Bugs:** 3
- **High Priority:** 1
- **Medium Priority:** 2
- **Components Affected:**
  - Workflow Orchestration (2 bugs)
  - Direct Execution (1 bug)

## Recent Discoveries (2026-02-03)

All three bugs were discovered during comprehensive testing of:
- Parallel workflow execution
- Beads task management system
- Build workflow comprehensive preset

**Testing Context:** Attempting to execute 3 high-priority enhancements (ENH-001, HM-001, ENH-002) in parallel revealed these critical integration issues.

## Next Steps

1. **BUG-001:** Fix git worktree path generation to include unique identifiers (workflow_id or timestamp)
2. **BUG-002:** Replace shlex.split() with subprocess list args for safer command execution
3. **BUG-003:** Improve error propagation and add dependency validation in workflow orchestrator

## Impact on Development

These bugs currently prevent:
- ❌ Parallel workflow execution (must run sequentially)
- ❌ Reliable automatic workflows via task system
- ⚠️ Clear error reporting and debugging

**Workarounds available:**
- Use sequential task execution: `tapps-agents task run <id>` one at a time
- Use agents directly: `@implementer *implement`, `@reviewer *review`, etc.
- Manual workflow execution with careful monitoring

---

**Last Updated:** 2026-02-03
**Maintained by:** TappsCodingAgents Team
