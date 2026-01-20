# Simple Mode *build Quick Start Guide

## Overview

Use Simple Mode's `*build` workflow for React component updates instead of Full SDLC workflow. It's more flexible and doesn't require specific file structures.

## Quick Command Template

```cursor
@simple-mode *build "Update [ComponentName] to [describe changes]"
```

## Example Commands

### Example 1: Update Component with New Feature
```cursor
@simple-mode *build "Update UserProfile component to add email verification badge and improve responsive design"
```

### Example 2: Refactor Component
```cursor
@simple-mode *build "Refactor NavigationBar component to use TypeScript, add accessibility attributes, and improve performance"
```

### Example 3: Add New Component Feature
```cursor
@simple-mode *build "Add dark mode toggle to Header component with theme persistence"
```

### Example 4: Improve Component Quality
```cursor
@simple-mode *build "Improve Button component with better TypeScript types, error handling, and test coverage"
```

## What Happens When You Execute

The `*build` workflow will execute these 7 steps:

1. **@enhancer *enhance** - Enhances your prompt with requirements analysis (full-sdlc, rapid-dev, and *epic also run enhance via EnhancerHandler when the preset includes it)
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step1-enhanced-prompt.md`

2. **@planner *plan** - Creates user stories (if needed)
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step2-user-stories.md`

3. **@architect *design** - Designs architecture/component structure
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step3-architecture.md`

4. **@designer *design-api** - Designs component API/props interface
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step4-design.md`

5. **@implementer *implement** - Implements/updates the React component
   - Updates your component file directly (works with existing project structure)

6. **@reviewer *review** - Reviews code quality
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step6-review.md`
   - Quality scores (5 metrics)
   - Issues found and recommendations

7. **@tester *test** - Generates tests
   - Creates: `docs/workflows/simple-mode/{workflow-id}/step7-testing.md`
   - Test plan and test cases

## Key Benefits vs Full SDLC

| Feature | Simple Mode `*build` | Full SDLC `*full` |
|---------|---------------------|-------------------|
| **File Structure** | Works with existing structure | Requires `src/`, `stories/`, `api-specs/` |
| **Best For** | React components, brownfield projects | Greenfield projects, backend APIs |
| **Flexibility** | Adapts to your project | Strict structure requirements |
| **Documentation** | Creates docs in `docs/workflows/simple-mode/` | Creates artifacts in project root |

## Next Steps

1. **Prepare your description**: 
   - Component name
   - What changes you want
   - Any specific requirements (accessibility, performance, TypeScript, etc.)

2. **Execute the command**:
   ```cursor
   @simple-mode *build "Your description here"
   ```

3. **Review the results**:
   - Check updated component file
   - Review documentation in `docs/workflows/simple-mode/{workflow-id}/`
   - Check quality scores in step6-review.md
   - Review test plan in step7-testing.md

## Common Use Cases

### Updating Existing Component
```cursor
@simple-mode *build "Update LoginForm component to add password strength indicator and improve error messages"
```

### Adding New Props/Features
```cursor
@simple-mode *build "Add loading state and error handling to DataTable component"
```

### Refactoring for Quality
```cursor
@simple-mode *build "Refactor Modal component to use TypeScript, improve accessibility, and add animation transitions"
```

### Performance Optimization
```cursor
@simple-mode *build "Optimize ImageGallery component with lazy loading, memoization, and virtual scrolling"
```

## Tips

1. **Be specific**: Include component name and specific changes you want
2. **Mention requirements**: Accessibility, TypeScript, performance, etc.
3. **Reference existing patterns**: "Follow the same pattern as [ComponentName]"
4. **Specify constraints**: "Must be compatible with React 18+" or "Use existing design system"

## Troubleshooting

If you encounter issues:
1. Make sure you're in the correct project directory
2. Ensure Simple Mode is enabled: `tapps-agents simple-mode status`
3. Check component file path is correct
4. Review error messages in workflow documentation
