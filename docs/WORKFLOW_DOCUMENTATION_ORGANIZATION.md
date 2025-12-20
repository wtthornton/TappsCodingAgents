# Workflow Documentation Organization

## Current State (Before Reorganization)

Simple Mode workflow steps previously created markdown files in the root directory:
- `simple-mode-workflow-step1-enhanced-prompt.md`
- `simple-mode-workflow-step2-user-stories.md`
- `simple-mode-workflow-step3-architecture.md`
- `simple-mode-workflow-step4-design.md`
- `simple-mode-workflow-step6-review.md`
- `simple-mode-workflow-step7-testing.md`

This created clutter in the root directory, especially when multiple workflow runs created variant files.

## New Structure (Implemented)

As of this reorganization, all workflow documentation files are now created in:
- `docs/workflows/simple-mode/`

## Proposed Structure

All workflow documentation files should be organized under `docs/workflows/`:

```
docs/
  workflows/
    simple-mode/
      step1-enhanced-prompt.md
      step2-user-stories.md
      step3-architecture.md
      step4-design.md
      step6-review.md
      step7-testing.md
      README.md (optional - explains the workflow)
```

## Benefits

1. **Cleaner root directory** - All workflow docs in one place
2. **Better organization** - Easy to find and navigate
3. **Scalability** - Can add more workflow types (e.g., `docs/workflows/full-sdlc/`)
4. **Version control friendly** - All docs in `docs/` which is typically tracked
5. **Consistent with existing structure** - Aligns with `docs/stories/`, `docs/prd/`, etc.

## Migration

1. Update Simple Mode rules (`.cursor/rules/simple-mode.mdc`)
2. Update Simple Mode skill (`.claude/skills/simple-mode/SKILL.md`)
3. Update documentation references
4. Optionally move existing files (but not required - old files can remain)

## File Naming Convention

For workflow-specific runs, files can include identifiers:
- `step1-enhanced-prompt-{identifier}.md` (if needed for multiple runs)
- Or use subdirectories: `docs/workflows/simple-mode/{run-id}/step1-enhanced-prompt.md`

For now, we'll use the simple naming without identifiers, as files can be overwritten or users can manually organize if needed.

