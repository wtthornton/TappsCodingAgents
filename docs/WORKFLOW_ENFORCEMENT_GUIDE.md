# Workflow Enforcement Guide

**Purpose:** Guide for AI assistants on when and how to suggest Simple Mode workflows instead of direct code edits.

**Date:** 2026-01-16  
**Status:** Active

---

## Overview

This guide helps AI assistants (like Cursor AI) understand when to suggest Simple Mode workflows instead of making direct code edits. The goal is to increase workflow adoption from 40% to 80%+ by proactively suggesting workflows.

---

## When to Suggest Workflows

### ✅ ALWAYS Suggest Workflows For:

1. **New Feature Implementation**
   - User says: "Add user authentication", "Create API endpoint", "Implement payment processing"
   - Suggest: `@simple-mode *build "description"`
   - Why: Ensures tests, quality gates, documentation

2. **Bug Fixes**
   - User says: "Fix the error in auth.py", "Debug login issue"
   - Suggest: `@simple-mode *fix <file> "description"`
   - Why: Systematic debugging with test verification

3. **Code Reviews**
   - User says: "Review my code", "Check quality", "Analyze security"
   - Suggest: `@simple-mode *review <file>`
   - Why: Comprehensive quality analysis with actionable feedback

4. **Test Generation**
   - User says: "Add tests", "Generate test coverage", "Create unit tests"
   - Suggest: `@simple-mode *test <file>`
   - Why: Comprehensive test generation with coverage analysis

5. **Code Refactoring**
   - User says: "Refactor this code", "Modernize legacy code", "Improve code quality"
   - Suggest: `@simple-mode *refactor <file>`
   - Why: Pattern detection and quality validation

### ❌ Skip Workflow Suggestions For:

1. **Simple One-Off Operations**
   - "Just lint this file"
   - "Format this code"
   - "Add a comment"

2. **Quick Exploration**
   - "What's the score of this file?"
   - "Show me the structure"
   - "List all functions"

3. **User Explicitly Requests Direct Edit**
   - User says: "Just edit it directly", "Skip the workflow", "I'll handle tests myself"

---

## Interceptor Pattern

### Before Making Any Code Edits

**MANDATORY CHECKLIST:**

```
Before making code edits for feature implementation, bug fixes, or new functionality:

1. [ ] Is this a new feature/component? → Use @simple-mode *build
2. [ ] Is this a bug fix? → Use @simple-mode *fix
3. [ ] Is this code review? → Use @simple-mode *review
4. [ ] Is this test generation? → Use @simple-mode *test
5. [ ] Only skip if: Simple one-off operation OR user explicitly requests direct edit
```

### Example Interceptor Flow

```
User: "Add user authentication to my app"

✅ CORRECT (Interceptor Pattern):
🤖 Workflow Suggestion:

"For new feature implementation, consider using:
@simple-mode *build 'Add user authentication with login, logout, and session management'

This workflow will:
✅ Generate comprehensive tests automatically (80%+ coverage)
✅ Enforce quality gates (75+ score required)
✅ Create documentation artifacts
✅ Catch bugs early with systematic review
✅ Provide full traceability (requirements → implementation)

Would you like me to proceed with the workflow?
[Yes, use workflow] [No, direct edit]"

[If user says Yes or doesn't respond]:
✅ Starting Build Workflow...
@simple-mode *build "Add user authentication..."

[If user explicitly says No]:
⚠️ Proceeding with direct edit (workflow benefits will be missed)

❌ WRONG (No Interceptor):
"I'll implement this directly..." [edits files immediately without suggesting workflow]
```

---

## Workflow Benefits to Communicate

### Build Workflow Benefits

When suggesting `@simple-mode *build`:

- ✅ **Automatic test generation** (80%+ coverage)
- ✅ **Quality gate enforcement** (75+ score required)
- ✅ **Comprehensive documentation** (requirements, architecture, API specs)
- ✅ **Early bug detection** (systematic review before completion)
- ✅ **Full traceability** (requirements → stories → architecture → implementation)

### Fix Workflow Benefits

When suggesting `@simple-mode *fix`:

- ✅ **Systematic root cause analysis** (not just surface fixes)
- ✅ **Automatic test verification** (ensures fix doesn't break existing functionality)
- ✅ **Quality review** (validates fix quality before completion)

### Review Workflow Benefits

When suggesting `@simple-mode *review`:

- ✅ **Comprehensive quality scores** (5 metrics: complexity, security, maintainability, test coverage, performance)
- ✅ **Actionable improvement suggestions** (specific issues with line numbers)
- ✅ **Security analysis** (vulnerability detection)

### Test Workflow Benefits

When suggesting `@simple-mode *test`:

- ✅ **Comprehensive test generation** (unit, integration, edge cases)
- ✅ **Coverage analysis** (identifies uncovered code paths)
- ✅ **Test framework detection** (automatically uses project's test framework)

---

## Implementation Examples

### Example 1: New Feature

```
User: "I need to add a payment processing module"

AI Response:
🤖 Workflow Suggestion:

"For new feature implementation, consider using:
@simple-mode *build 'Add payment processing module with credit card validation and transaction logging'

This workflow will:
✅ Generate comprehensive tests automatically (80%+ coverage)
✅ Enforce quality gates (75+ score required)
✅ Create documentation artifacts
✅ Catch bugs early with systematic review
✅ Provide full traceability (requirements → implementation)

Would you like me to proceed with the workflow?
[Yes, use workflow] [No, direct edit]"
```

### Example 2: Bug Fix

```
User: "Fix the KeyError in payment.py line 42"

AI Response:
🤖 Workflow Suggestion:

"For bug fixes, consider using:
@simple-mode *fix payment.py 'Fix KeyError on line 42 when processing payment data'

This workflow will:
✅ Systematic root cause analysis
✅ Automatic test verification
✅ Quality review before fix

Would you like me to proceed with the workflow?
[Yes, use workflow] [No, direct edit]"
```

### Example 3: Code Review

```
User: "Review the authentication code for security issues"

AI Response:
🤖 Workflow Suggestion:

"For code review, consider using:
@simple-mode *review src/auth.py

This workflow will:
✅ Comprehensive quality scores (5 metrics)
✅ Actionable improvement suggestions
✅ Security analysis

Would you like me to proceed with the workflow?
[Yes, use workflow] [No, direct edit]"
```

---

## Confidence Levels

Use confidence levels to determine suggestion strength:

- **High Confidence (0.8+):** Strong keywords match, clear intent
  - Example: "Build a user authentication feature"
  - **Action:** Strongly suggest workflow

- **Medium Confidence (0.6-0.8):** Some keywords match, intent somewhat clear
  - Example: "I need authentication"
  - **Action:** Suggest workflow with explanation

- **Low Confidence (<0.6):** Unclear intent, ambiguous
  - Example: "Authentication"
  - **Action:** Don't suggest (might be exploration)

---

## Handling User Responses

### User Accepts Workflow

```
User: "Yes, use workflow" or no response (default to workflow)

AI Response:
✅ Starting Build Workflow...

📝 Step 1/7: Enhancing prompt...
@enhancer *enhance "Add user authentication..."

[Execute full workflow]
```

### User Rejects Workflow

```
User: "No, direct edit" or "Just edit it directly"

AI Response:
⚠️ Proceeding with direct edit (workflow benefits will be missed)

[Proceed with direct edit, but note what's being missed]
```

---

## Metrics to Track

After implementing workflow suggestions, track:

- **Workflow Adoption Rate:** Target 80%+ (currently 40%)
- **Test Coverage:** Target 80%+ (currently 0%)
- **Quality Score:** Target 85+/100 (currently 75/100)
- **User Satisfaction:** Feedback on workflow suggestions

---

## Related Documentation

- `.cursor/rules/simple-mode.mdc` - Simple Mode rules with interceptor patterns
- `docs/HYBRID_FLOW_EVALUATION_RECOMMENDATIONS.md` - Full recommendations
- `tapps_agents/simple_mode/workflow_suggester.py` - Workflow suggestion implementation

---

**Last Updated:** 2026-01-16
