# Beads + GitHub Issues: Best Practices for TappsCodingAgents

**Status:** Mandatory (as of 2026-01-29)
**Applies to:** All TappsCodingAgents framework development

---

## Philosophy: Dual-Track Workflow Management

**Beads = Execution Engine** | **GitHub Issues = Communication Layer**

- **Beads:** Task management, workflow execution, progress tracking, dependencies
- **GitHub Issues:** Public tracking, user feedback, discussion, traceability

**Key Principle:** Use Beads to manage work, GitHub Issues to communicate about work.

---

## Quick Reference

| Task | Tool | Command |
|------|------|---------|
| Create Epic | Beads + GitHub | `bd epic create` + `gh issue create --label epic` |
| Add Story | Beads + GitHub | `bd epic add-story` + `gh issue create --label story` |
| Mark Ready | Beads | `bd ready <story-id>` |
| Execute Workflow | Simple Mode | `@simple-mode *build "Description... Closes #N"` |
| Check Progress | Beads | `bd epic status <epic-id>` |
| View Closed Work | GitHub | `gh issue list --state closed` |

---

## Configuration

**Status:** ✅ Beads is **REQUIRED** (not optional)

Beads configuration in `.tapps-agents/config.yaml`:

```yaml
beads:
  enabled: true
  required: true  # MANDATORY - fail if Beads not available
  sync_epic: true
  hooks_simple_mode: true
  hooks_workflow: true

  # Auto-sync settings
  auto_sync:
    on_workflow_start: true    # Mark story as in-progress
    on_workflow_complete: true # Mark story as done
    on_workflow_fail: true     # Mark story as blocked

  # GitHub integration
  github_sync:
    enabled: true
    auto_close_issues: true       # Close GitHub issue when story complete
    link_commits: true            # Add "Closes #N" to commit messages
    update_pr_description: true   # Add story context to PRs
```

---

## Workflow Phases

### Phase 1: Epic and Story Planning

#### Step 1: Create Epic in Beads

```bash
# Create Epic
bd epic create "ENH-001: Workflow Enforcement System"

# Add stories with dependencies
bd epic add-story enh-001-s1 "Core Workflow Enforcer"
bd epic add-story enh-001-s2 "Intent Detection System" --depends-on enh-001-s1
bd epic add-story enh-001-s3 "User Messaging System" --depends-on enh-001-s2
bd epic add-story enh-001-s4 "Configuration System"

# Set priorities
bd story set-priority enh-001-s4 high
bd story set-priority enh-001-s1 high
```

#### Step 2: Create Epic Issue in GitHub

```bash
# Create Epic tracking issue
gh issue create \
  --title "EPIC ENH-001: Workflow Enforcement System" \
  --label "epic" \
  --body "$(cat stories/enh-001-workflow-enforcement.md)"

# Note the issue number (e.g., #9)
```

#### Step 3: Create Story Issues in GitHub

```bash
# Create issue for each story
gh issue create \
  --title "ENH-001-S4: Configuration System (1 pt)" \
  --label "story,enh-001,priority-high" \
  --body "Load workflow enforcement configuration from .tapps-agents/config.yaml..." \
  --milestone "v3.6.0"

# Repeat for each story
# Note issue numbers: #10 (S4), #11 (S2), #12 (S3), #13 (S1)
```

#### Step 4: Link Beads Stories to GitHub Issues

**In story markdown** (`stories/enh-001-workflow-enforcement.md`):

```markdown
### Story 4: Configuration System

**Story ID:** ENH-001-S4
**Priority:** High
**Story Points:** 1
**Status:** Todo
**GitHub Issue:** #10
```

### Phase 2: Story Execution

#### Step 1: Mark Story Ready in Beads

```bash
# Check what's ready
bd ready

# Mark specific story ready
bd ready enh-001-s4
```

#### Step 2: Execute Workflow with Auto-Sync

```bash
# Use Simple Mode with GitHub issue reference
@simple-mode *build "ENH-001-S4: Configuration System - Load workflow enforcement configuration from .tapps-agents/config.yaml with validation. Create EnforcementConfig dataclass with mode (blocking/warning/silent), confidence_threshold (default 60), suggest_workflows, block_direct_edits. Implement from_config_file() class method with YAML parsing, schema validation, and defaults. File: tapps_agents/core/llm_behavior.py (150 lines). Closes #10"
```

**What happens automatically:**

1. ✅ Beads: Story marked as "in-progress"
2. ✅ Workflow executes (7 steps)
3. ✅ Code review passes quality gates
4. ✅ Tests generated (94% coverage)
5. ✅ Commit created with "Closes #10" message
6. ✅ GitHub: Issue #10 automatically closed
7. ✅ Beads: Story marked as "done"
8. ✅ Beads: Epic progress updated

#### Step 3: Verify Completion

```bash
# Check Beads status
bd epic status enh-001
# Output:
# Epic: ENH-001 (4 stories)
# ✅ ENH-001-S4: Configuration System (done)
# ⏳ ENH-001-S1: Core Workflow Enforcer (todo)
# ⏳ ENH-001-S2: Intent Detection System (todo)
# ⏳ ENH-001-S3: User Messaging System (todo)
# Progress: 1/4 (25%)

# Check GitHub status
gh issue view 10
# Output: Status: Closed ✅
```

### Phase 3: Review and Continuation

#### Check Next Story

```bash
# Beads shows next ready story
bd ready
# Output:
# 📋 Ready work (1 issue with no blockers):
# 1. [● P1] [story] ENH-001-S1: Core Workflow Enforcer
```

#### Proceed to Next Story

```bash
# Mark next story ready
bd ready enh-001-s1

# Execute workflow for next story
@simple-mode *build "ENH-001-S1: Core Workflow Enforcer... Closes #13"
```

---

## Commit Message Format

**Always include GitHub issue reference** in commit messages:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>

Closes #<issue-number>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Example

```
feat(core): Add EnforcementConfig for workflow enforcement

Implements ENH-001-S4 Configuration System:
- EnforcementConfig dataclass with YAML loading
- Comprehensive validation and error handling
- 94.25% test coverage (39/39 tests passing)

Quality Metrics:
- Overall Score: 85.7/100 ✅
- Security Score: 10.0/10 ✅
- Test Coverage: 94.25% ✅

Closes #10

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Key Elements:**
1. `<type>`: feat, fix, docs, refactor, test, chore
2. `<scope>`: Module or area (core, workflow, agents, cli)
3. `<subject>`: One-line summary (imperative mood)
4. `<body>`: What and why (optional)
5. `Closes #N`: Links commit to GitHub issue (auto-closes)
6. `Co-Authored-By`: Credits AI assistance

---

## Pull Request Workflow

### Creating PRs with Beads Context

```bash
# After completing story, create PR
@simple-mode *pr "Add EnforcementConfig for workflow enforcement"
```

**PR Description includes:**

```markdown
## Summary
Implements ENH-001-S4: Configuration System

## Story Details
- **Beads Story:** ENH-001-S4
- **GitHub Issue:** Closes #10
- **Epic:** ENH-001 - Workflow Enforcement System
- **Story Points:** 1

## Changes
- Created `tapps_agents/core/llm_behavior.py`
- Created `tests/test_llm_behavior.py`
- Updated `.tapps-agents/config.yaml` (beads config)

## Quality Metrics
- Overall Score: 85.7/100 ✅
- Security Score: 10.0/10 ✅
- Test Coverage: 94.25% ✅
- Tests Passing: 39/39 ✅

## Test Plan
- [x] All unit tests passing
- [x] Coverage ≥80%
- [x] Security scan clean
- [x] Integration test with actual config file

🤖 Generated with [Claude Code](https://claude.com/claude-code) via TappsCodingAgents Simple Mode
```

---

## Task Assignment Matrix

| Task | Use Beads | Use GitHub | Notes |
|------|-----------|------------|-------|
| **Epic Planning** | ✅ Primary | ✅ Create tracking issue | Beads for execution, GitHub for visibility |
| **Story Breakdown** | ✅ Primary | ✅ Create issue per story | Link story to issue |
| **Set Priorities** | ✅ Primary | ✅ Add labels | Use both for filtering |
| **Dependencies** | ✅ Primary | ❌ | Beads handles dependency resolution |
| **Mark Ready** | ✅ Primary | ❌ | Internal workflow state |
| **Execute Workflow** | ✅ Auto-update | ✅ Close via commit | "Closes #N" in commit |
| **Track Progress** | ✅ Primary | ✅ View closed issues | Beads for real-time, GitHub for history |
| **User Feedback** | ❌ | ✅ Primary | Public communication |
| **Bug Reports** | ❌ | ✅ Primary | External contributors |
| **Link Commits** | ✅ Auto-sync | ✅ Auto-close | Both stay in sync |
| **Create PRs** | ✅ Story context | ✅ Issue references | PR includes both |
| **Epic Completion** | ✅ Primary | ✅ Close epic issue | Mark epic complete in both |

---

## Status Checking

### Beads Status Commands

```bash
# Check ready stories
bd ready

# Check epic status
bd epic status enh-001

# Check specific story
bd story status enh-001-s4

# List all epics
bd epic list

# Show dependency tree
bd epic tree enh-001
```

### GitHub Status Commands

```bash
# List open issues by epic
gh issue list --label enh-001

# List closed issues
gh issue list --label enh-001 --state closed

# View specific issue
gh issue view 10

# Check PR status
gh pr list --label enh-001
```

---

## Troubleshooting

### Issue: Beads Not Available

```bash
# Check if Beads is installed
bd version

# If not installed:
# 1. Install Beads (see Beads documentation)
# 2. Configure Beads path in TappsCodingAgents

# Set Beads path (if needed)
.\scripts\set_bd_path.ps1 -BeadsPath "C:\path\to\bd.exe"
```

### Issue: GitHub Issue Not Auto-Closing

**Cause:** Commit message missing "Closes #N" keyword

**Fix:**
```bash
# Amend last commit to add issue reference
git commit --amend -m "$(git log -1 --pretty=%B)

Closes #10"

# Force push (if already pushed)
git push --force-with-lease
```

**Prevention:** Always include "Closes #N" in Simple Mode prompt.

### Issue: Beads Story Not Updating

**Cause:** Beads hooks disabled in config

**Fix:**

Check `.tapps-agents/config.yaml`:

```yaml
beads:
  enabled: true
  required: true
  hooks_simple_mode: true  # Must be true
  hooks_workflow: true     # Must be true
```

### Issue: Story Ready but Has Blockers

```bash
# Check dependencies
bd story status enh-001-s2

# Output:
# Story: ENH-001-S2
# Status: Todo
# Blockers:
#   - ENH-001-S1 (in-progress)

# Complete blocker first, then mark ready
bd ready enh-001-s2
```

---

## Best Practices Summary

### DO ✅

1. **Always use Beads for Epic and Story management**
   - Create all Epics in Beads
   - Break down stories in Beads
   - Track dependencies in Beads

2. **Always create GitHub Issues for public tracking**
   - One Epic issue per Epic
   - One issue per Story
   - Link Beads story to GitHub issue

3. **Always include "Closes #N" in commit messages**
   - Simple Mode prompts should include it
   - Enables auto-closing of GitHub issues
   - Maintains traceability

4. **Use Beads `bd ready` to manage work queue**
   - Mark stories ready when dependencies complete
   - Let Beads resolve dependency order
   - Check `bd ready` before starting work

5. **Check both Beads and GitHub for status**
   - Beads: Real-time progress and next work
   - GitHub: Historical tracking and public view

### DON'T ❌

1. **Don't bypass Beads for task management**
   - Don't manage tasks only in GitHub
   - Don't skip `bd ready` step
   - Don't ignore Beads dependencies

2. **Don't forget GitHub issue references**
   - Don't commit without "Closes #N"
   - Don't create stories without GitHub issues
   - Don't skip GitHub Epic issue

3. **Don't manually sync Beads and GitHub**
   - Let auto-sync handle updates
   - Trust the hooks
   - If sync fails, check configuration

4. **Don't mark stories complete manually in Beads**
   - Let Simple Mode workflows update Beads
   - Hooks handle automatic updates
   - Manual updates can cause sync issues

---

## Quick Start Checklist

When starting a new Epic:

- [ ] Create Epic in Beads (`bd epic create`)
- [ ] Create Epic issue in GitHub (`gh issue create --label epic`)
- [ ] Add stories to Epic in Beads (`bd epic add-story`)
- [ ] Create GitHub issue for each story
- [ ] Set story priorities in Beads
- [ ] Link stories to issues in story markdown
- [ ] Mark first story ready (`bd ready`)
- [ ] Execute workflow with Simple Mode (include "Closes #N")
- [ ] Verify auto-sync worked (check Beads and GitHub)
- [ ] Continue to next story

When completing a story:

- [ ] Workflow executed successfully
- [ ] Quality gates passed
- [ ] Commit includes "Closes #N"
- [ ] GitHub issue automatically closed
- [ ] Beads story automatically marked done
- [ ] Epic progress updated in Beads
- [ ] Check `bd ready` for next story

---

## Example: Complete ENH-001 Epic Workflow

### Initial Setup

```bash
# 1. Create Epic in Beads
bd epic create "ENH-001: Workflow Enforcement System"

# 2. Add stories
bd epic add-story enh-001-s1 "Core Workflow Enforcer"
bd epic add-story enh-001-s2 "Intent Detection" --depends-on enh-001-s1
bd epic add-story enh-001-s3 "User Messaging" --depends-on enh-001-s2
bd epic add-story enh-001-s4 "Configuration System"

# 3. Create GitHub Epic issue
gh issue create --title "EPIC ENH-001: Workflow Enforcement" --label epic

# 4. Create GitHub issues for stories
gh issue create --title "ENH-001-S1: Core Enforcer (3pt)" --label story,enh-001
gh issue create --title "ENH-001-S2: Intent Detection (2pt)" --label story,enh-001
gh issue create --title "ENH-001-S3: User Messaging (2pt)" --label story,enh-001
gh issue create --title "ENH-001-S4: Configuration (1pt)" --label story,enh-001
# Issues created: #10 (S4), #11 (S2), #12 (S3), #13 (S1)
```

### Story 1: ENH-001-S4 (Configuration)

```bash
# Mark ready
bd ready enh-001-s4

# Execute
@simple-mode *build "ENH-001-S4: Configuration System... Closes #10"

# Verify
bd epic status enh-001  # Shows: 1/4 done
gh issue view 10        # Shows: Closed ✅
```

### Story 2: ENH-001-S2 (Intent Detection)

```bash
# Check dependencies
bd ready  # ENH-001-S2 blocked by ENH-001-S1

# Complete S1 first (dependency)
bd ready enh-001-s1
@simple-mode *build "ENH-001-S1: Core Enforcer... Closes #13"

# Now S2 unblocked
bd ready enh-001-s2
@simple-mode *build "ENH-001-S2: Intent Detection... Closes #11"
```

### Continue Until Epic Complete

```bash
# Final status
bd epic status enh-001
# Output:
# Epic: ENH-001 (4 stories)
# ✅ ENH-001-S1: Core Enforcer (done)
# ✅ ENH-001-S2: Intent Detection (done)
# ✅ ENH-001-S3: User Messaging (done)
# ✅ ENH-001-S4: Configuration (done)
# Progress: 4/4 (100%) ✅ COMPLETE

# Close Epic issue
gh issue close 9 --comment "Epic complete! All 4 stories implemented and tested."
```

---

## References

- **Beads Documentation:** https://github.com/beadsdao/beads
- **GitHub CLI:** https://cli.github.com/manual/
- **TappsCodingAgents Simple Mode:** [docs/SIMPLE_MODE_GUIDE.md](SIMPLE_MODE_GUIDE.md)
- **Workflow Enforcement Guide:** [docs/WORKFLOW_ENFORCEMENT_GUIDE.md](WORKFLOW_ENFORCEMENT_GUIDE.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-29
**Status:** Mandatory for all TappsCodingAgents development
