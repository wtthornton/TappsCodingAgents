# Workflow Quick Reference

**Purpose:** Quick reference guide for Simple Mode workflows and when to use them.

**Date:** 2026-01-16  
**Status:** Active

---

## Quick Command Reference

### Build Workflow
**Command:** `@simple-mode *build "description"`  
**When to Use:** New features, components, API endpoints, modules  
**Steps:** 7 steps (enhance → plan → architect → design → implement → review → test)  
**Output:** Code + tests + documentation + quality report

**Example:**
```cursor
@simple-mode *build "Create user authentication API with JWT tokens"
```

### Fix Workflow
**Command:** `@simple-mode *fix <file> "description"`  
**When to Use:** Bug fixes, error resolution, debugging  
**Steps:** 3 steps (debug → fix → test)  
**Output:** Fixed code + test verification + quality review

**Example:**
```cursor
@simple-mode *fix src/auth.py "Fix KeyError when processing authentication"
```

### Review Workflow
**Command:** `@simple-mode *review <file>`  
**When to Use:** Code quality checks, security audits, pre-commit reviews  
**Steps:** 2 steps (review → improve if needed)  
**Output:** Quality scores + actionable feedback + improvement suggestions

**Example:**
```cursor
@simple-mode *review src/api/users.py
```

### Test Workflow
**Command:** `@simple-mode *test <file>`  
**When to Use:** Test generation, coverage improvement, test-driven development  
**Steps:** 1 step (test generation)  
**Output:** Test files + coverage report

**Example:**
```cursor
@simple-mode *test src/services/payment.py
```

### Refactor Workflow
**Command:** `@simple-mode *refactor <file>`  
**When to Use:** Code modernization, pattern updates, legacy code improvement  
**Steps:** 4 steps (review → architect → refactor → test → review)  
**Output:** Refactored code + updated tests + quality validation

**Example:**
```cursor
@simple-mode *refactor src/utils/legacy.py
```

---

## Workflow Comparison

| Workflow | Steps | Test Coverage | Quality Gates | Documentation |
|----------|-------|---------------|---------------|---------------|
| **Build** | 7 | ✅ 80%+ | ✅ 75+ score | ✅ Full |
| **Fix** | 3 | ✅ Verification | ✅ Review | ⚠️ Minimal |
| **Review** | 2 | ❌ None | ✅ Scores | ⚠️ Report only |
| **Test** | 1 | ✅ Generated | ❌ None | ⚠️ Test plan |
| **Refactor** | 4 | ✅ Updated | ✅ Validation | ⚠️ Minimal |

---

## When to Use Each Workflow

### Use Build Workflow When:
- ✅ Creating new features
- ✅ Adding new API endpoints
- ✅ Implementing new modules
- ✅ Building new components
- ✅ Starting new functionality

**Don't use for:**
- ❌ Simple one-line changes
- ❌ Quick bug fixes (use Fix workflow)
- ❌ Code reviews (use Review workflow)

### Use Fix Workflow When:
- ✅ Fixing bugs
- ✅ Resolving errors
- ✅ Debugging issues
- ✅ Correcting logic errors

**Don't use for:**
- ❌ New features (use Build workflow)
- ❌ Code quality improvements (use Review + Refactor)

### Use Review Workflow When:
- ✅ Pre-commit reviews
- ✅ Code quality audits
- ✅ Security analysis
- ✅ Performance checks

**Don't use for:**
- ❌ Implementing features (use Build workflow)
- ❌ Fixing bugs (use Fix workflow)

### Use Test Workflow When:
- ✅ Generating tests for existing code
- ✅ Improving test coverage
- ✅ Test-driven development
- ✅ Adding missing tests

**Don't use for:**
- ❌ New features (Build workflow includes tests)
- ❌ Bug fixes (Fix workflow includes test verification)

### Use Refactor Workflow When:
- ✅ Modernizing legacy code
- ✅ Updating design patterns
- ✅ Improving code structure
- ✅ Code quality improvements

**Don't use for:**
- ❌ New features (use Build workflow)
- ❌ Bug fixes (use Fix workflow)

---

## Workflow Benefits Summary

### Build Workflow Benefits
- ✅ **Automatic test generation** (80%+ coverage)
- ✅ **Quality gate enforcement** (75+ score required)
- ✅ **Comprehensive documentation** (requirements, architecture, API specs)
- ✅ **Early bug detection** (systematic review)
- ✅ **Full traceability** (requirements → implementation)

### Fix Workflow Benefits
- ✅ **Systematic root cause analysis**
- ✅ **Automatic test verification**
- ✅ **Quality review before completion**

### Review Workflow Benefits
- ✅ **Comprehensive quality scores** (5 metrics)
- ✅ **Actionable improvement suggestions**
- ✅ **Security analysis**

### Test Workflow Benefits
- ✅ **Comprehensive test generation**
- ✅ **Coverage analysis**
- ✅ **Test framework detection**

### Refactor Workflow Benefits
- ✅ **Pattern detection and modernization**
- ✅ **Quality validation after refactoring**
- ✅ **Test updates**

---

## Natural Language Commands

You can also use natural language (Simple Mode auto-detects intent):

```
Build a user authentication feature
Fix the error in auth.py
Review my authentication code
Add tests for service.py
Refactor the legacy payment code
```

---

## Workflow Outputs

### Build Workflow Creates:
- `docs/workflows/simple-mode/step1-enhanced-prompt.md` - Enhanced requirements
- `docs/workflows/simple-mode/step2-user-stories.md` - User stories
- `docs/workflows/simple-mode/step3-architecture.md` - Architecture design
- `docs/workflows/simple-mode/step4-design.md` - API/component design
- `src/...` - Implemented code
- `docs/workflows/simple-mode/step6-review.md` - Quality review report
- `tests/...` - Test files (80%+ coverage)

### Fix Workflow Creates:
- Fixed code files
- Test verification results
- Quality review report

### Review Workflow Creates:
- Quality scores report
- Improvement suggestions
- Security analysis

### Test Workflow Creates:
- Test files
- Coverage report
- Test plan

---

## Quality Gates

### Build Workflow Gates:
- **Review Step:** Overall score ≥ 75, Security ≥ 6.5
- **Test Step:** Coverage ≥ 70% (loops back if not met)

### Fix Workflow Gates:
- **Review Step:** Overall score ≥ 70, Security ≥ 6.5

### Refactor Workflow Gates:
- **Review Step:** Overall score ≥ 75, Security ≥ 6.5

---

## Tips

1. **Always use Build workflow for new features** - Ensures tests, quality, and documentation
2. **Use Fix workflow for bugs** - Systematic debugging with test verification
3. **Review before committing** - Use Review workflow for quality checks
4. **Generate tests early** - Use Test workflow if coverage is low
5. **Refactor systematically** - Use Refactor workflow for code modernization

---

## Related Documentation

- `docs/WORKFLOW_ENFORCEMENT_GUIDE.md` - Complete enforcement guide
- `docs/HYBRID_FLOW_EVALUATION_RECOMMENDATIONS.md` - Recommendations and improvements
- `.cursor/rules/simple-mode.mdc` - Simple Mode rules

---

**Last Updated:** 2026-01-16
