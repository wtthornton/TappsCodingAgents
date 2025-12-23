# Epic Workflow Guide

## Overview

Epic workflows allow you to execute entire Epic documents with automatic story dependency resolution, quality gate enforcement, and progress tracking. This is ideal for implementing large features that span multiple stories.

## Quick Start

### 1. Create an Epic Document

Create a markdown file with your Epic definition:

```markdown
# Epic 51: YAML Automation Quality Enhancement

## Epic Goal
Enhance YAML automation with quality gates and validation.

## Epic Description
This epic adds comprehensive quality checks to YAML workflow execution.

## Stories

### Story 1.1: Add Quality Gates
**Description:** Implement quality gate enforcement for workflow steps.
**Acceptance criteria:**
- Quality gates check overall score ≥ 70
- Security score ≥ 7.0
- Test coverage ≥ 80%
**Dependencies:** None
**Status:** ⏳ TODO

### Story 1.2: Add Coverage Analysis
**Description:** Integrate coverage analysis for test generation.
**Acceptance criteria:**
- Coverage analyzer reads coverage.json
- Identifies gaps in coverage
- Generates targeted tests
**Dependencies:** Story 1.1
**Status:** ⏳ TODO
```

### 2. Execute the Epic

In Cursor chat:

```
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

Or via CLI (when implemented):

```bash
tapps-agents epic execute docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

## How It Works

### 1. Epic Parsing

The Epic orchestrator:
- Parses the Epic markdown document
- Extracts stories, dependencies, and acceptance criteria
- Validates Epic structure

### 2. Dependency Resolution

Stories are automatically sorted using topological sort (Kahn's algorithm):
- Stories with no dependencies execute first
- Dependent stories execute after their dependencies complete
- Circular dependencies are detected and reported

### 3. Story Execution

For each story:
1. **Create workflow** - Generate or load workflow YAML for the story
2. **Execute workflow** - Run the workflow using WorkflowExecutor
3. **Quality gates** - Check quality scores (overall ≥ 70, security ≥ 7.0, etc.)
4. **Loopback** - If quality gates fail, trigger improvement loopback (max 3 iterations)
5. **Track progress** - Update story status and execution results

### 4. Quality Gate Enforcement

Quality gates are automatically enforced:
- **Overall score** ≥ 70 (≥ 80 for critical services)
- **Security score** ≥ 7.0/10
- **Maintainability score** ≥ 7.0/10
- **Test coverage** ≥ 80%
- **No critical linting errors**

If gates fail:
- Improvement loopback is triggered automatically
- Specific issues are passed to @improver agent
- Workflow is re-executed after improvements
- Maximum 3 loopback iterations

### 5. Completion Report

After all stories complete:
- Epic completion report is generated
- Includes execution summary, quality metrics, and story status
- Saved to `docs/prd/epic-{number}-report.json`

## Epic Document Format

### Required Sections

1. **Epic Title** (H1): `# Epic {number}: {title}`
2. **Epic Goal** (H2): `## Epic Goal`
3. **Epic Description** (H2): `## Epic Description`
4. **Stories** (H2): `## Stories`

### Story Format

Each story should include:

```markdown
### Story {number}: {title}
**Description:** {story description}
**Acceptance criteria:**
- {criterion 1}
- {criterion 2}
**Dependencies:** {story IDs, comma-separated, or "None"}
**Status:** {⏳ TODO | ☑️ IN_PROGRESS | ✅ COMPLETE | ❌ FAILED | ⏸️ BLOCKED}
```

### Status Values

- `⏳ TODO` - Story not started
- `☑️ IN_PROGRESS` - Story currently executing
- `✅ COMPLETE` - Story completed successfully
- `❌ FAILED` - Story failed (will block dependent stories)
- `⏸️ BLOCKED` - Story blocked by dependencies

## Examples

### Example 1: Simple Epic

```markdown
# Epic 1: User Authentication

## Epic Goal
Implement user authentication system with JWT tokens.

## Epic Description
Add complete authentication flow with registration, login, and token management.

## Stories

### Story 1.1: User Registration
**Description:** Implement user registration endpoint.
**Acceptance criteria:**
- POST /register endpoint
- Password hashing
- Email validation
**Dependencies:** None
**Status:** ⏳ TODO

### Story 1.2: User Login
**Description:** Implement user login with JWT generation.
**Acceptance criteria:**
- POST /login endpoint
- JWT token generation
- Token refresh mechanism
**Dependencies:** Story 1.1
**Status:** ⏳ TODO
```

### Example 2: Complex Epic with Multiple Dependencies

```markdown
# Epic 2: Payment Processing

## Epic Goal
Implement secure payment processing system.

## Stories

### Story 2.1: Payment Gateway Integration
**Description:** Integrate with payment gateway API.
**Dependencies:** None
**Status:** ⏳ TODO

### Story 2.2: Payment Validation
**Description:** Validate payment requests.
**Dependencies:** Story 2.1
**Status:** ⏳ TODO

### Story 2.3: Payment Processing
**Description:** Process payments through gateway.
**Dependencies:** Story 2.1, Story 2.2
**Status:** ⏳ TODO

### Story 2.4: Payment Webhooks
**Description:** Handle payment gateway webhooks.
**Dependencies:** Story 2.3
**Status:** ⏳ TODO
```

## Configuration

Epic workflows can be configured in `.tapps-agents/config.yaml`:

```yaml
epic:
  quality_threshold: 70  # Minimum overall quality score
  critical_service_threshold: 80  # Threshold for critical services
  max_loopback_iterations: 3  # Maximum improvement loopback attempts
  enforce_quality_gates: true  # Enable/disable quality gate enforcement
  auto_fix: false  # Auto-apply fixes (requires confirmation if false)
```

## Best Practices

1. **Define Clear Dependencies**: Ensure story dependencies are accurate
2. **Keep Stories Focused**: Each story should have a single, clear goal
3. **Write Good Acceptance Criteria**: Clear, testable acceptance criteria
4. **Use Quality Gates**: Enable quality gates to ensure code quality
5. **Review Completion Reports**: Check reports for quality metrics and issues

## Troubleshooting

### Circular Dependencies

If you see:
```
Circular dependencies detected. Stories involved: Story 1.2, Story 1.3
```

**Solution:** Review your Epic document and remove circular dependencies. Each story should have a clear execution order.

### Quality Gate Failures

If quality gates fail repeatedly:
1. Check the quality report for specific issues
2. Review the improvement suggestions
3. Consider breaking the story into smaller stories
4. Adjust quality thresholds if appropriate (but maintain standards)

### Story Execution Failures

If a story fails:
1. Check the execution results in the completion report
2. Review error messages and logs
3. Fix the issue manually if needed
4. Re-run the Epic (completed stories will be skipped)

## Related Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md) - Simple Mode usage
- [Command Reference](TAPPS_AGENTS_COMMAND_REFERENCE.md) - Complete command reference
- [Workflow Execution Summary](WORKFLOW_EXECUTION_SUMMARY.md) - Workflow execution details
- [Quality Gates](QUALITY_GATES.md) - Quality gate configuration and thresholds

