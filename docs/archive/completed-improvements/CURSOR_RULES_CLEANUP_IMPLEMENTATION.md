# Cursor Rules Cleanup - Implementation Guide

**Quick Action Plan**: Add YAML frontmatter to rule files to prevent duplicate pattern matches.

---

## Immediate Solution: Add Frontmatter to Rule Files

### Problem

Rule files without explicit `alwaysApply: true` and `globs: []` cause Cursor to pattern-match them across all directories, including worktrees, creating duplicate entries in Cursor Settings.

### Solution

Add YAML frontmatter with `alwaysApply: true` to rule files that should be global.

---

## Files to Update

### ✅ Already Correct

1. **`simple-mode.mdc`** - Has `alwaysApply: true` ✅
2. **`command-reference.mdc`** - Has `alwaysApply: true` ✅

### ❌ Need Frontmatter Added

1. **`agent-capabilities.mdc`** - Should be global (agent capabilities always relevant)
2. **`project-context.mdc`** - Should be global (project context always relevant)
3. **`workflow-presets.mdc`** - Should be global (workflow presets always available)
4. **`quick-reference.mdc`** - Should be global (quick reference always available)
5. **`project-profiling.mdc`** - Should be global (profiling guide always available)

---

## Implementation

### Step 1: Update `agent-capabilities.mdc`

**Current** (no frontmatter):
```
# TappsCodingAgents: Agent Capabilities Guide
...
```

**Updated** (add frontmatter):
```yaml
---
description: Agent capabilities guide for all TappsCodingAgents agents. Use this to understand what each agent does, when to use them, and common usage patterns.
globs: []
alwaysApply: true
---

# TappsCodingAgents: Agent Capabilities Guide
...
```

### Step 2: Update `project-context.mdc`

**Add frontmatter**:
```yaml
---
description: Important context about TappsCodingAgents dual nature as both a framework and a self-hosted project. CRITICAL for understanding project structure.
globs: []
alwaysApply: true
---
```

### Step 3: Update `workflow-presets.mdc`

**Add frontmatter**:
```yaml
---
description: Workflow presets guide - quick commands for common SDLC tasks. Documents all available workflow presets and when to use them.
globs: []
alwaysApply: true
---
```

### Step 4: Update `quick-reference.mdc`

**Add frontmatter**:
```yaml
---
description: Quick reference guide for TappsCodingAgents commands and common usage patterns. For complete documentation, see command-reference.mdc.
globs: []
alwaysApply: true
---
```

### Step 5: Update `project-profiling.mdc`

**Add frontmatter**:
```yaml
---
description: Project profiling guide - how to analyze and profile projects to understand their structure, patterns, and characteristics.
globs: []
alwaysApply: true
---
```

---

## Verification Steps

After updating all rule files:

1. **Check Cursor Settings**:
   - Open Cursor Settings → Rules
   - Verify rules appear in "Always Applied" section (not "Pattern Matched")
   - Verify no duplicate pattern matches for worktree directories

2. **Test Rule Application**:
   - Open a file in the project
   - Verify rules are still available in context
   - Test a Cursor chat command to ensure rules work

3. **Test with Worktree** (optional):
   - Create a test worktree: `git worktree add ../test-worktree`
   - Check Cursor Settings again
   - Verify no new duplicate pattern matches appear

---

## Why This Works

1. **`alwaysApply: true`**: Makes rule apply globally without pattern matching
2. **`globs: []`**: Explicitly indicates no file-specific patterns
3. **Result**: Rule appears in "Always Applied" section, not "Pattern Matched"
4. **No Duplicates**: Worktrees won't create duplicate pattern matches because rule doesn't use patterns

---

## Alternative: If Rules Should Be Pattern-Matched

If a rule should only apply to specific files/directories (not global), use:

```yaml
---
description: Rule description
globs:
  - ".cursor/rules/**"
  - "!**/.tapps-agents/worktrees/**"  # Exclude worktrees (if supported)
alwaysApply: false
---
```

**Note**: Exclusion syntax (`!`) may not be supported by Cursor - needs testing.

---

## Additional Cleanup

### Clean Up Old Worktrees

After fixing rule files, clean up old worktrees to remove existing duplicate matches:

```bash
# Preview what would be removed
tapps-agents workflow state cleanup --dry-run --retention-days 1

# Remove old worktrees (older than 1 day)
tapps-agents workflow state cleanup --retention-days 1 --remove-completed
```

This provides immediate cleanup while the rule file fixes prevent future duplicates.

---

## Expected Outcome

**Before**:
- Cursor Settings shows many duplicate `agent-capabilities` entries
- One entry per worktree directory
- Cluttered "Pattern Matched" section

**After**:
- All rules appear in "Always Applied" section
- No duplicate pattern matches
- Clean, organized Cursor Settings

---

## Rollback Plan

If issues occur after updating rule files:

1. Remove the YAML frontmatter from affected rule files
2. Restore original file content
3. Rules will return to pattern-matched behavior

**Note**: This should not cause issues - `alwaysApply: true` is the safer, more predictable option.
