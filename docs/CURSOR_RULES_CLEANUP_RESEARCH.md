# Cursor Rules Pattern Matching Cleanup - Research & Solutions

**Date**: January 16, 2025  
**Issue**: Cursor Settings showing duplicate pattern matches for `agent-capabilities` rule across multiple worktree directories, causing UI clutter.

---

## Problem Analysis

### Current Situation

**Symptom**: Cursor Settings UI shows many duplicate entries:
```
agent-capabilities
  .cursor/rules/**
agent-capabilities
  billstest/.tapps-agents/worktrees/workflow-full-sdlc-20251213-153256-step-requirements/**
agent-capabilities
  billstest/.tapps-agents/worktrees/workflow-full-sdlc-20251213-153313-step-planning/**
... (many more)
```

### Root Causes

1. **Cursor Rules Pattern Matching Behavior**
   - Cursor scans the entire workspace for rule pattern matches
   - Even though `.cursorignore` excludes `.tapps-agents/worktrees/` from **indexing**, it doesn't prevent **rule pattern matching**
   - Rules with implicit or broad patterns (like `.cursor/rules/**`) match across all directories

2. **Worktree Directories Contain Rule Files**
   - Worktrees created during workflow execution include `.cursor/rules/` directories
   - These worktrees are temporary but persist until cleaned up
   - Cursor detects rule files in worktrees and creates pattern matches for each

3. **Rule File Pattern Configuration**
   - `agent-capabilities.mdc` doesn't have explicit `globs` or exclusion patterns in frontmatter
   - Default behavior may match all `.cursor/rules/**` paths
   - No explicit exclusion of worktree directories

---

## Research Findings

### How Cursor Rules Work

1. **Rule File Structure**
   - Rules use YAML frontmatter for configuration
   - `alwaysApply: true` applies rule globally
   - `globs: []` can specify file patterns to match
   - Rules without explicit patterns may default to matching their directory

2. **Pattern Matching vs. Indexing**
   - **Indexing** (controlled by `.cursorignore`): Determines which files are indexed for search/autocomplete
   - **Pattern Matching** (rules): Determines where rules apply
   - These are **separate mechanisms** - `.cursorignore` doesn't prevent rule pattern matching

3. **Worktree Impact**
   - Worktrees are temporary git worktrees created during workflow execution
   - They contain full project copies including `.cursor/rules/` directories
   - Cursor detects and matches rules in worktrees even if indexed content is ignored

---

## Solutions

### Solution 1: Add Explicit Exclusion Patterns to Rules (RECOMMENDED)

**Approach**: Add explicit `globs` patterns to rule files that exclude worktree directories.

**Implementation**:

```yaml
---
description: Agent capabilities guide
globs:
  - ".cursor/rules/**"
  - "**/.cursor/rules/**"
  - "!**/.tapps-agents/worktrees/**"
alwaysApply: false
---
```

**Pros**:
- ✅ Explicitly controls where rules apply
- ✅ Excludes worktree directories from pattern matching
- ✅ Maintains compatibility with normal project directories
- ✅ No breaking changes

**Cons**:
- ⚠️ Requires updating all rule files
- ⚠️ Cursor may not support exclusion patterns (`!`) in globs (needs verification)

**Status**: **NEEDS VERIFICATION** - Check if Cursor supports exclusion patterns in `globs`.

---

### Solution 2: Use More Specific Glob Patterns

**Approach**: Limit rule patterns to only match rules in the project root, not worktrees.

**Implementation**:

```yaml
---
description: Agent capabilities guide
globs:
  - ".cursor/rules/**"
  - "!**/.tapps-agents/**"
alwaysApply: false
---
```

**Pros**:
- ✅ Simpler pattern
- ✅ Excludes all `.tapps-agents` subdirectories (worktrees, cache, etc.)

**Cons**:
- ⚠️ Won't apply to files in `.tapps-agents` if needed (probably fine)
- ⚠️ Exclusion syntax may not be supported

---

### Solution 3: Clean Up Old Worktrees

**Approach**: Remove old worktree directories to eliminate pattern matches.

**Implementation**:

```bash
# Use cleanup tool
tapps-agents workflow state cleanup --retention-days 7

# Or manually remove old worktrees
rm -rf .tapps-agents/worktrees/workflow-*-*
```

**Pros**:
- ✅ Immediate cleanup of duplicate matches
- ✅ Reduces disk usage
- ✅ Uses existing cleanup infrastructure

**Cons**:
- ⚠️ Doesn't prevent future matches
- ⚠️ Worktrees will still be created during workflow execution
- ⚠️ Temporary solution, not a permanent fix

**Status**: **SHORT-TERM FIX** - Reduces current clutter but doesn't solve root cause.

---

### Solution 4: Use `alwaysApply: true` with No Patterns

**Approach**: Rules with `alwaysApply: true` don't need pattern matching, so they won't show in "Pattern Matched" section.

**Current State**: `simple-mode.mdc` already uses this:
```yaml
---
description: Simple Mode guide
globs: []
alwaysApply: true
---
```

**Implementation**: Convert `agent-capabilities.mdc` to use `alwaysApply: true`:

```yaml
---
description: Agent capabilities guide
globs: []
alwaysApply: true
---
```

**Pros**:
- ✅ Rules with `alwaysApply: true` apply globally without pattern matching
- ✅ Won't show duplicate entries in "Pattern Matched" section
- ✅ Simplest solution

**Cons**:
- ⚠️ Rule applies to all files, even when not needed
- ⚠️ May impact performance (though likely negligible)

**Status**: **BEST OPTION IF RULE SHOULD APPLY GLOBALLY** - If `agent-capabilities` is meant to be always available, use this.

---

### Solution 5: Combine Solutions - Cleanup + Pattern Optimization

**Approach**: 
1. Clean up old worktrees (immediate relief)
2. Optimize rule patterns for new worktrees
3. Add automatic cleanup to workflow completion

**Implementation**:

1. **Immediate Cleanup**:
```bash
tapps-agents workflow state cleanup --retention-days 1 --remove-completed
```

2. **Update Rule Files**:
```yaml
---
description: Agent capabilities guide
globs: []
alwaysApply: true  # If rule should be global
# OR
globs:
  - ".cursor/rules/**"
  - "!**/.tapps-agents/worktrees/**"  # If exclusion supported
alwaysApply: false
---
```

3. **Add Auto-Cleanup to Workflow**:
- Modify workflow executor to clean up worktrees after completion
- Or add cleanup task to workflow state management

**Pros**:
- ✅ Immediate cleanup
- ✅ Prevents future issues
- ✅ Comprehensive solution

**Cons**:
- ⚠️ More complex implementation
- ⚠️ Requires changes in multiple places

**Status**: **RECOMMENDED COMPREHENSIVE APPROACH**.

---

## Recommended Implementation Plan

### Phase 1: Immediate Cleanup (Quick Win)

1. **Clean up old worktrees**:
```bash
# Check what would be removed
tapps-agents workflow state cleanup --dry-run --retention-days 1

# Remove old worktrees
tapps-agents workflow state cleanup --retention-days 1 --remove-completed
```

2. **Verify cleanup worked**:
- Check Cursor Settings to see if duplicate pattern matches are reduced

### Phase 2: Rule Pattern Optimization

1. **Review rule file purposes**:
   - **`agent-capabilities.mdc`**: Should this be global? (Probably yes)
   - **`command-reference.mdc`**: Should this be global? (Probably yes)
   - **`project-context.mdc`**: Should this be global? (Probably yes)
   - **`simple-mode.mdc`**: Already uses `alwaysApply: true` ✅

2. **Update rule files**:
   - For rules that should be global: Set `alwaysApply: true`, `globs: []`
   - For rules that need patterns: Test exclusion syntax if supported

3. **Test pattern matching**:
   - Create a test worktree
   - Verify rules don't create duplicate pattern matches
   - Verify rules still apply correctly in main project

### Phase 3: Long-Term Maintenance

1. **Add automatic cleanup**:
   - Integrate worktree cleanup into workflow completion
   - Or add scheduled cleanup task

2. **Document best practices**:
   - Update `.cursor/rules/` documentation
   - Document rule pattern best practices
   - Add guidelines for when to use `alwaysApply` vs. patterns

---

## Testing Plan

### Test Case 1: Verify Pattern Exclusion Works

**Steps**:
1. Update `agent-capabilities.mdc` with exclusion pattern
2. Create a test worktree: `git worktree add ../test-worktree`
3. Check Cursor Settings for duplicate pattern matches
4. Verify rule still applies in main project

**Expected Result**: No duplicate pattern matches, rule still works in main project.

### Test Case 2: Verify `alwaysApply` Works

**Steps**:
1. Update `agent-capabilities.mdc` to use `alwaysApply: true`
2. Create a test worktree
3. Check Cursor Settings
4. Verify rule applies globally

**Expected Result**: Rule appears in "Always Applied" section, not "Pattern Matched".

### Test Case 3: Verify Cleanup Works

**Steps**:
1. Create multiple test worktrees
2. Run cleanup command
3. Verify worktrees are removed
4. Verify Cursor Settings no longer shows matches

**Expected Result**: Old worktrees removed, duplicate matches eliminated.

---

## Cursor IDE Behavior Notes

### Pattern Matching Behavior

Based on research:
- Cursor scans **all directories** in workspace for rule files
- Pattern matching happens **independently** of `.cursorignore`
- Rules in worktrees are detected and matched even if content is ignored
- `alwaysApply: true` rules bypass pattern matching entirely

### `.cursorignore` vs. Rule Patterns

- **`.cursorignore`**: Controls file **indexing** (search, autocomplete, context)
- **Rule `globs`**: Controls rule **application** (where rules are active)
- These are **separate mechanisms** - `.cursorignore` doesn't affect rule patterns

### Best Practices

1. **Use `alwaysApply: true` for global rules**: Avoids pattern matching complexity
2. **Use specific `globs` for targeted rules**: Only apply where needed
3. **Exclude worktrees in patterns**: If exclusion syntax is supported
4. **Clean up old worktrees**: Regular maintenance prevents clutter

---

## References

- Cursor Rules Documentation: [Cursor Docs - Rules](https://docs.cursor.com/en/context/rules)
- Current `.cursorignore`: `.cursorignore` (already excludes `.tapps-agents/worktrees/`)
- Worktree Cleanup Tool: `tapps_agents/core/cleanup_tool.py`
- Rule Files: `.cursor/rules/*.mdc`

---

## Next Steps

1. ✅ **Verify Cursor exclusion syntax** - Test if `!` patterns work in `globs`
2. ✅ **Decide on rule scope** - Which rules should be global vs. pattern-matched?
3. ✅ **Implement Phase 1** - Clean up old worktrees
4. ✅ **Implement Phase 2** - Optimize rule patterns
5. ✅ **Document solution** - Update rule documentation

---

## Questions to Resolve

1. **Does Cursor support exclusion patterns in `globs`?** (`!**/.tapps-agents/worktrees/**`)
   - Need to test this with a sample rule file

2. **Should `agent-capabilities.mdc` be global?** (`alwaysApply: true`)
   - If yes, use Solution 4
   - If no, need exclusion patterns

3. **Should cleanup be automatic?**
   - Add to workflow completion?
   - Or manual/scheduled cleanup?

4. **Are worktrees in `billstest/` or current project?**
   - If in another project, may need different approach
   - If in current project, solutions above apply
