# Simple Mode Workflow Documentation

This directory contains documentation files generated during Simple Mode workflow execution.

## Files

When executing a Simple Mode build workflow (`@simple-mode *build`), the following documentation files are created:

1. **step1-enhanced-prompt.md** - Enhanced prompt with requirements analysis, architecture guidance, and quality standards
2. **step2-user-stories.md** - User stories with acceptance criteria, story points, and estimates
3. **step3-architecture.md** - System architecture, component design, data flow, and performance considerations
4. **step4-design.md** - Component specifications, color palette, typography, spacing system, and animations
5. **step6-review.md** - Quality scores (5 metrics), issues found, and recommendations
6. **step7-testing.md** - Test plan, browser compatibility, accessibility checklist, and performance validation

## Workflow Steps

The Simple Mode build workflow follows these steps:

1. **Enhance** - Prompt enhancement with expert integration
2. **Plan** - User story creation
3. **Design Architecture** - System design and architecture
4. **Design Components** - API and component design
5. **Implement** - Code generation
6. **Review** - Quality scoring and code review
7. **Test** - Test generation and execution

Note: Step 5 (implementation) does not create a documentation file, as it generates actual code files.

## Organization

Files in this directory are overwritten on each workflow run. If you need to preserve specific workflow documentation, copy the files to a versioned location or rename them with timestamps.

For more information, see:
- `docs/SIMPLE_MODE_USER_GUIDE.md` - User guide
- `docs/SIMPLE_MODE_GUIDE.md` - Complete documentation
- `.cursor/rules/simple-mode.mdc` - Cursor rules

