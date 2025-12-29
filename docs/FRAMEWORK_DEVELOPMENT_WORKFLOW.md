# Framework Development Workflow

**Date:** 2025-01-16  
**Status:** Mandatory Guidelines  
**Purpose:** Ensure all framework changes follow proper SDLC workflow

## ⚠️ CRITICAL: Framework Changes MUST Use Full SDLC

When modifying the **TappsCodingAgents framework itself** (`tapps_agents/` package), you **MUST** use Simple Mode Full SDLC workflow.

## Why This Matters

### What Happens Without Full SDLC ❌

**Example: Context7 Enhancements (What We Did Wrong):**
1. Directly implemented code changes
2. Validated afterward with reviewer
3. Skipped requirements analysis
4. Skipped architecture design
5. No quality gates during development
6. No automatic loopbacks
7. No test generation (tests still pending)

**Result:** Implementation was correct, but we missed:
- Proper requirements analysis
- Architecture design documentation
- Quality gates during development
- Automatic test generation
- Full traceability

### What Happens With Full SDLC ✅

**Example: How It Should Have Been Done:**
1. Requirements analysis (analyst)
2. User stories (planner)
3. Architecture design (architect)
4. API design (designer)
5. Implementation (implementer)
6. Review with quality gates (reviewer) - loops back if < 75
7. Test generation and execution (tester)
8. Security scanning (ops)
9. Documentation generation (documenter)

**Result:** Complete SDLC with quality gates, tests, and documentation.

## Mandatory Workflow

### For Framework Changes

**ALWAYS use Simple Mode Full SDLC:**

```bash
# CLI
tapps-agents simple-mode full --prompt "Implement [enhancement description]" --auto

# Or in Cursor chat
@simple-mode *full "Implement [enhancement description]"
```

### Workflow Steps (9 Steps)

The `simple-full.yaml` workflow includes:

1. **Requirements** (`analyst`) - Gathers requirements from prompt
2. **Planning** (`planner`) - Creates user stories with acceptance criteria
3. **Design** (`architect`) - Designs system architecture
4. **API Design** (`designer`) - Designs API contracts and data models
5. **Implementation** (`implementer`) - Implements code following design
6. **Review** (`reviewer`) - Quality gates:
   - Overall score ≥ 75
   - Security score ≥ 7.5
   - Maintainability score ≥ 7.5
   - Test coverage ≥ 70%
   - **Automatic loopback** if thresholds not met
7. **Testing** (`tester`) - Generates and runs tests
   - **Automatic loopback** if tests fail
8. **Security** (`ops`) - Security scanning
   - **Automatic loopback** if security issues found
9. **Documentation** (`documenter`) - Generates documentation

## Quality Gates

The workflow enforces strict quality thresholds:

- **Overall Score:** ≥ 75 (must pass)
- **Security Score:** ≥ 7.5 (must pass)
- **Maintainability Score:** ≥ 7.5 (must pass)
- **Test Coverage:** ≥ 70% (must pass)

**If any threshold is not met:**
- Workflow automatically loops back to improve code
- Maximum 3 loopback attempts
- Workflow fails if thresholds still not met after 3 attempts

## Automatic Loopbacks

The workflow includes automatic loopbacks:

1. **Review fails** → `improve_code` → `re_review` → continues
2. **Tests fail** → `fix_tests` → `fix_implementation` → `re_test` → continues
3. **Security fails** → `fix_security` → `re_security` → continues

This ensures quality before proceeding to next phase.

## What Gets Generated

### Artifacts Created

1. **Requirements** (`requirements.md`)
   - Functional requirements
   - Non-functional requirements
   - Acceptance criteria

2. **User Stories** (`stories/`)
   - Story breakdown
   - Story points
   - Dependencies

3. **Architecture** (`architecture.md`)
   - System design
   - Component architecture
   - Integration patterns

4. **API Design** (`api-specs/`)
   - API contracts
   - Data models
   - Interface specifications

5. **Implementation** (`src/`)
   - Code following design
   - Following architecture patterns

6. **Review Scores** (in workflow state)
   - Quality metrics
   - Security scores
   - Maintainability scores

7. **Tests** (`tests/`)
   - Unit tests
   - Integration tests
   - Test execution results

8. **Security Report** (in workflow state)
   - Security scan results
   - Vulnerability assessment

9. **Documentation** (`docs/`)
   - API documentation
   - Usage guides
   - Architecture documentation

## Examples

### ✅ Correct: Using Full SDLC

```bash
# Framework enhancement
tapps-agents simple-mode full --prompt "Add Context7 automatic integration to all SDLC agents" --auto
```

**Result:**
- Requirements analyzed
- Architecture designed
- Code implemented with quality gates
- Tests generated and executed
- Security validated
- Documentation generated

### ❌ Incorrect: Direct Implementation

```bash
# Directly implementing without workflow
# (What we did wrong)
```

**Result:**
- Code implemented
- Validated afterward
- No requirements analysis
- No architecture design
- No quality gates during development
- No automatic test generation
- No structured documentation

## When to Use Full SDLC

### ✅ Use Full SDLC For:

- **Framework enhancements** (adding new features)
- **New agent development** (creating new agents)
- **Major refactoring** (significant code changes)
- **Integration changes** (adding new integrations)
- **Architecture changes** (modifying core architecture)

### ⚠️ Can Use Simpler Workflows For:

- **Bug fixes** → Use `workflow fix` or `@simple-mode *fix`
- **Code reviews** → Use `@simple-mode *review`
- **Test generation** → Use `@simple-mode *test`
- **Documentation updates** → Use `@documenter *document`

## Configuration

The workflow uses these quality thresholds (from `simple-full.yaml`):

```yaml
scoring:
  enabled: true
  thresholds:
    overall_min: 75
    security_min: 7.5
    maintainability_min: 7.5
    test_coverage_min: 70
```

These can be adjusted in `.tapps-agents/config.yaml` if needed.

## Benefits

### For Framework Quality
- ✅ **Consistent quality** - All changes meet minimum thresholds
- ✅ **Automatic validation** - Quality gates prevent low-quality code
- ✅ **Test coverage** - Tests generated automatically
- ✅ **Security validation** - Security scans prevent vulnerabilities

### For Documentation
- ✅ **Complete documentation** - All artifacts documented
- ✅ **Traceability** - Full requirements → implementation traceability
- ✅ **Architecture decisions** - Design decisions documented
- ✅ **API documentation** - APIs documented automatically

### For Development Process
- ✅ **Structured approach** - Follows SDLC best practices
- ✅ **Quality gates** - Prevents proceeding with low-quality code
- ✅ **Automatic loopbacks** - Fixes issues automatically
- ✅ **Complete artifacts** - All SDLC artifacts generated

## Related Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Workflow Presets](.cursor/rules/workflow-presets.mdc)
- [Command Reference](.cursor/rules/command-reference.mdc)
- [SDLC Workflow Analysis](TAPPS_AGENTS_CONTEXT7_SDLC_WORKFLOW_ANALYSIS.md)

## Conclusion

**For all framework changes, always use:**

```bash
tapps-agents simple-mode full --prompt "[enhancement description]" --auto
```

This ensures proper SDLC with quality gates, testing, security validation, and complete documentation.

