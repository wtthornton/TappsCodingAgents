# Simple Mode User Guide - Ensuring Workflow Usage in Cursor

## Overview

This guide explains how to ensure Cursor AI uses the **complete Simple Mode workflow** when you request it. The Simple Mode workflow produces better, more maintainable code through structured planning, design, and quality checks.

## Why Use Simple Mode Workflow?

Based on our comparison (`index.html` vs `index2.html`), the Simple Mode workflow provides:
- ✅ **Better Documentation** - Requirements, user stories, architecture documented
- ✅ **Higher Quality** - Formal review process catches issues (87/100 quality score)
- ✅ **Better Maintainability** - Design system, spacing variables, consistent patterns
- ✅ **Comprehensive Testing** - Test plan and validation criteria
- ✅ **Traceability** - Features traced to requirements → stories → implementation

---

## Method 1: Explicit Simple Mode Command (RECOMMENDED) ⭐

### Usage

Use the explicit `@simple-mode` skill with `*build` command:

```
@simple-mode *build "Create a user authentication feature"
@simple-mode *build "Build a modern dark HTML page with 2025 features"
```

### Why This Works Best

- ✅ **Explicit Intent** - Cursor AI recognizes you want the workflow
- ✅ **Follows Rules** - Matches the documented workflow pattern
- ✅ **Creates Artifacts** - Produces documentation files from each step
- ✅ **Most Reliable** - Highest chance of following the complete workflow

### Full Workflow Executed

1. **@enhancer** - Enhanced prompt with requirements analysis
2. **@planner** - User stories with acceptance criteria
3. **@architect** - System architecture design
4. **@designer** - Component design specifications
5. **@implementer** - Code implementation
6. **@reviewer** - Code quality review (scores, issues)
7. **@tester** - Testing plan and validation

---

## Method 2: Natural Language with Simple Mode Prefix

### Usage

Use `@simple-mode` with natural language:

```
@simple-mode Build a REST API for user management
@simple-mode Create a modern dashboard with charts
@simple-mode Implement JWT authentication system
```

### When to Use

- When you want the workflow but prefer natural language
- For complex features that need planning
- When you want documentation generated

### Tips

- Use action words: "Build", "Create", "Implement", "Add"
- Be specific about what you want
- Mention "Simple Mode workflow" if you want to be explicit

---

## Method 3: Explicit Workflow Request

### Usage

Explicitly request the workflow steps:

```
Please use the Simple Mode workflow to build [feature]:
1. Enhance the prompt
2. Create user stories
3. Design architecture
4. Design components
5. Implement code
6. Review quality
7. Create test plan
```

Or shorter:

```
Use the complete Simple Mode build workflow to create [feature]
```

### Why This Works

- ✅ **Explicit Instructions** - You're telling Cursor exactly what to do
- ✅ **Step-by-Step** - Lists the exact workflow steps
- ✅ **Clear Expectation** - Cursor knows what artifacts to create

---

## Method 4: Reference the Workflow Files

### Usage

Reference existing workflow documentation:

```
Use the Simple Mode workflow as documented in simple-mode-workflow-step1-enhanced-prompt.md
Follow the same workflow process used for index2.html
```

### When to Use

- When you want to match a previous successful workflow
- When you want consistency with existing work
- For complex features that need the same structure

---

## Method 5: Model Selection (Optional)

### Option A: Use Claude Sonnet/GPT-4 (Recommended)

For complex workflows, using a more capable model can help:

1. **In Cursor Settings:**
   - Go to Settings → Models
   - Select Claude Sonnet 4 or GPT-4
   - These models better understand complex workflows

2. **Why It Helps:**
   - Better at following multi-step instructions
   - More likely to create all workflow artifacts
   - Better at maintaining context across steps

### Option B: Keep Auto Mode (Also Works)

Auto mode works fine with explicit commands:
- Use `@simple-mode *build` explicitly
- The model selection is less important than clear commands

---

## Method 6: Prompt Engineering Tips

### Good Prompts (Use These)

✅ **Explicit and Clear:**
```
@simple-mode *build "Create a user authentication feature with JWT tokens, refresh tokens, and password reset"
```

✅ **References Workflow:**
```
Please follow the complete Simple Mode workflow (enhance → plan → architect → design → implement → review → test) to build [feature]
```

✅ **Mentions Artifacts:**
```
Use Simple Mode workflow and create the documentation files (enhanced prompt, user stories, architecture, design, review, test plan)
```

### Avoid These (Too Vague)

❌ **Too Simple:**
```
Build auth feature
```

❌ **No Workflow Mention:**
```
Create a login system
```

❌ **Unclear Intent:**
```
Make something for users
```

---

## Verification: How to Check if Workflow Was Used

### ✅ Signs the Workflow Was Followed

1. **Multiple Documentation Files Created:**
   - `simple-mode-workflow-step1-enhanced-prompt.md`
   - `simple-mode-workflow-step2-user-stories.md`
   - `simple-mode-workflow-step3-architecture.md`
   - `simple-mode-workflow-step4-design.md`
   - `simple-mode-workflow-step6-review.md`
   - `simple-mode-workflow-step7-testing.md`

2. **Implementation Shows:**
   - Design system with spacing variables
   - Architecture patterns followed
   - Quality review comments
   - Test plan mentioned

3. **Chat Messages Show:**
   - Step-by-step progress updates
   - References to workflow steps
   - Quality scores and metrics
   - Review findings

### ❌ Signs Workflow Was Skipped

1. **Direct Implementation:**
   - Code written immediately
   - No documentation files
   - No user stories
   - No architecture discussion

2. **No Review:**
   - No quality scores mentioned
   - No issues identified
   - No test plan

3. **Missing Artifacts:**
   - Only code file created
   - No workflow documentation

---

## Troubleshooting

### Problem: Cursor AI Skips the Workflow

**Solution 1: Be More Explicit**
```
@simple-mode *build "Create [feature]" - Please follow all 7 steps of the workflow
```

**Solution 2: Request Step-by-Step**
```
I want you to follow the complete Simple Mode workflow:
Step 1: Enhance the prompt
Step 2: Create user stories
... (list all steps)
```

**Solution 3: Reference Documentation**
```
Please follow the workflow documented in .cursor/rules/simple-mode.mdc
```

### Problem: Workflow Incomplete

**Check:**
- Did all 7 steps execute?
- Are documentation files created?
- Is there a review with scores?

**If Missing Steps:**
```
Please complete the workflow - I still need:
- User stories (Step 2)
- Architecture design (Step 3)
- Code review (Step 6)
```

### Problem: Not Using Simple Mode

**If Cursor Directly Implements:**

1. **Stop and Redirect:**
   ```
   Wait, please use the Simple Mode workflow first. Start with @simple-mode *build
   ```

2. **Explain Why:**
   ```
   I want the Simple Mode workflow because it provides better documentation and quality. Please follow the workflow.
   ```

3. **Use Explicit Command:**
   ```
   @simple-mode *build "[your feature request]"
   ```

---

## Best Practices

### ✅ DO

1. **Use Explicit Commands**
   ```
   @simple-mode *build "feature description"
   ```

2. **Be Specific**
   ```
   @simple-mode *build "Create a REST API for user management with CRUD operations, JWT authentication, and pagination"
   ```

3. **Request Documentation**
   ```
   @simple-mode *build "feature" - Please create all workflow documentation files
   ```

4. **Verify Completion**
   ```
   Did you complete all 7 steps? Please show me the review scores.
   ```

### ❌ DON'T

1. **Don't Use Vague Commands**
   ```
   ❌ Make something
   ❌ Add auth
   ❌ Fix it
   ```

2. **Don't Skip the Workflow**
   ```
   ❌ Just write the code
   ❌ Skip the planning
   ```

3. **Don't Accept Incomplete Workflows**
   ```
   ❌ If only code is provided, request the full workflow
   ```

---

## Quick Reference

### Command Cheat Sheet

| Intent | Command | Workflow Steps |
|--------|---------|----------------|
| Build Feature | `@simple-mode *build "description"` | 7 steps (enhance → plan → architect → design → implement → review → test) |
| Review Code | `@simple-mode *review file.py` | 2 steps (review → improve if needed) |
| Fix Bug | `@simple-mode *fix file.py "description"` | 3 steps (debug → implement → test) |
| Generate Tests | `@simple-mode *test file.py` | 1 step (test generation) |
| Full SDLC | `@simple-mode *full "description"` | 9 steps (all agents) |

### Keywords That Trigger Workflows

**Build Keywords:**
- build, create, make, generate, add, implement, develop, write, new, feature

**Review Keywords:**
- review, check, analyze, inspect, examine, score, quality, audit

**Fix Keywords:**
- fix, repair, resolve, debug, error, bug, issue, problem, broken

**Test Keywords:**
- test, verify, validate, coverage, testing

---

## Examples

### Example 1: Successful Workflow Request

**User:**
```
@simple-mode *build "Create a modern dark HTML page with 2025 CSS features"
```

**Expected Result:**
- ✅ Step 1: Enhanced prompt document created
- ✅ Step 2: User stories with acceptance criteria
- ✅ Step 3: Architecture design document
- ✅ Step 4: Component design specifications
- ✅ Step 5: index2.html implemented
- ✅ Step 6: Code review with quality scores (87/100)
- ✅ Step 7: Testing plan document

### Example 2: Failed Workflow (Direct Implementation)

**User:**
```
Create a login page
```

**Result:**
- ❌ Direct code implementation
- ❌ No documentation
- ❌ No review

**Fix:**
```
@simple-mode *build "Create a login page with email/password authentication"
```

---

## Summary

**To ensure Simple Mode workflow is used:**

1. ⭐ **Use explicit command:** `@simple-mode *build "description"`
2. **Be specific** about what you want
3. **Reference the workflow** if needed
4. **Verify completion** by checking for documentation files
5. **Request step-by-step** if workflow is skipped

**Remember:** The workflow takes more time but produces better, more maintainable code with comprehensive documentation.

---

## Related Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) - Complete Simple Mode documentation
- [Cursor Rules - Simple Mode](../.cursor/rules/simple-mode.mdc) - Cursor AI rules
- [Workflow Comparison](SIMPLE_MODE_WORKFLOW_COMPARISON.md) - index.html vs index2.html comparison

