# Epic: ENH-002 Workflow Improvements

**Epic ID:** ENH-002
**Status:** Ready for Implementation
**Priority:** High
**Total Story Points:** 8
**Estimated Duration:** 2 weeks
**Created:** 2026-01-29
**Based on:** Session feedback from ENH-001-S4

---

## Epic Overview

### Goal

Implement high-priority workflow improvements identified during ENH-001-S4 session feedback, focusing on auto-commit capability, workflow resume/checkpoint functionality, and workflow preset integration.

### User Value

**As a developer using TappsCodingAgents**, I want automated commit creation and workflow resumption, **so that** I can iterate faster and recover gracefully from failures without losing work.

### Success Metrics

- Auto-commit reduces manual git operations by 100%
- Workflow resume reduces wasted time on failures by 80%
- Workflow presets reduce average workflow time by 30-50%
- User satisfaction: 95%+ adoption rate

---

## User Stories

### Story 1: Workflow Presets Integration

**Story ID:** ENH-002-S1
**Priority:** High
**Story Points:** 2
**Status:** Ready (config file already created)

#### User Story

> As a developer, I want to use predefined workflow presets (minimal, standard, comprehensive, full), so that I can choose the appropriate workflow complexity for my task without specifying all steps manually.

#### Acceptance Criteria

1. ✅ Workflow presets configuration file exists (`.tapps-agents/workflow-presets.yaml`)
2. ⏳ Simple Mode reads and validates presets
3. ⏳ `--preset` flag works with @simple-mode commands
4. ⏳ Default preset (comprehensive) applied when not specified
5. ⏳ Time estimates shown before workflow execution
6. ⏳ Quality thresholds enforced per preset
7. ⏳ Preset recommendations based on file type/task type

#### Technical Details

**Files to Modify:**
- `tapps_agents/simple_mode/handler.py` - Add preset loading
- `tapps_agents/simple_mode/preset_loader.py` - New file for preset logic

**Key Components:**
```python
class WorkflowPresetLoader:
    def load_preset(self, name: str) -> WorkflowPreset:
        """Load preset by name from config."""

    def recommend_preset(
        self,
        file_path: Path,
        task_type: str
    ) -> str:
        """Recommend preset based on context."""

@dataclass
class WorkflowPreset:
    name: str
    steps: list[str]
    quality_threshold: float
    security_threshold: float
    coverage_target: float
    estimated_time: int  # minutes
```

#### Tasks

- [ ] Task 1.1: Create WorkflowPresetLoader class (2 hours)
  - Load presets from YAML
  - Validate preset structure
  - Handle missing/invalid presets

- [ ] Task 1.2: Integrate with Simple Mode handler (2 hours)
  - Add --preset flag parsing
  - Apply preset steps to workflow
  - Show time estimates

- [ ] Task 1.3: Add preset recommendations (2 hours)
  - File pattern matching
  - Task type detection
  - Suggest appropriate preset

- [ ] Task 1.4: Write tests (2 hours)
  - Test preset loading
  - Test preset application
  - Test recommendations
  - Achieve ≥80% coverage

#### Dependencies

- None (config file already exists)

#### Estimated Effort

8 hours (2 story points)

---

### Story 2: Auto-Commit with Quality Gates

**Story ID:** ENH-002-S2
**Priority:** High
**Story Points:** 3
**Status:** Todo

#### User Story

> As a developer, I want workflows to automatically create git commits when quality gates pass, so that I don't have to manually commit after every successful workflow execution.

#### Acceptance Criteria

1. ✅ `--auto-commit` flag available on Simple Mode commands
2. ✅ Commit only created when all quality gates pass
3. ✅ Commit message includes:
   - Conventional commit format (feat/fix/docs/etc)
   - Story/issue reference ("Closes #N")
   - Quality metrics summary
   - Co-authored-by Claude attribution
4. ✅ GitHub issue auto-closed via "Closes #N"
5. ✅ Beads story auto-updated to "done"
6. ✅ Commit created on correct branch
7. ✅ Pre-commit hooks respected

#### Technical Details

**Files to Create:**
- `tapps_agents/workflow/auto_commit.py` (200 lines)

**Key Components:**
```python
class AutoCommitHandler:
    def should_auto_commit(
        self,
        quality_scores: dict[str, float],
        quality_gates_passed: bool,
        auto_commit_flag: bool
    ) -> bool:
        """Determine if auto-commit should happen."""

    def generate_commit_message(
        self,
        workflow_result: WorkflowResult,
        story_id: str,
        github_issue: int | None
    ) -> str:
        """Generate conventional commit message with metrics."""

    def create_commit(
        self,
        files: list[Path],
        message: str,
        allow_empty: bool = False
    ) -> str:
        """Create git commit and return commit SHA."""

    def notify_integrations(
        self,
        commit_sha: str,
        story_id: str,
        github_issue: int | None
    ):
        """Notify Beads and GitHub of completion."""
```

**Commit Message Format:**
```
feat(core): Add EnforcementConfig for workflow enforcement

Implements ENH-001-S4 Configuration System:
- EnforcementConfig dataclass with YAML loading
- Comprehensive validation and error handling
- 94.25% test coverage (39/39 tests passing)

Quality Metrics:
- Overall: 85.7/100 ✅
- Security: 10.0/10 ✅
- Coverage: 94.25% ✅

Closes #10

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

#### Tasks

- [ ] Task 2.1: Create AutoCommitHandler class (3 hours)
  - Implement commit logic
  - Generate commit messages
  - Handle git operations

- [ ] Task 2.2: Integrate with Simple Mode (2 hours)
  - Add --auto-commit flag
  - Call AutoCommitHandler on success
  - Handle commit failures

- [ ] Task 2.3: Beads/GitHub integration (2 hours)
  - Update Beads story status
  - Verify GitHub issue closure
  - Handle API failures

- [ ] Task 2.4: Write tests (3 hours)
  - Test commit message generation
  - Test git operations (mocked)
  - Test quality gate enforcement
  - Test integration notifications
  - Achieve ≥80% coverage

#### Dependencies

- ENH-002-S1 (Workflow Presets) - for quality threshold configuration

#### Estimated Effort

10 hours (3 story points)

---

### Story 3: Workflow Checkpoint and Resume

**Story ID:** ENH-002-S3
**Priority:** High
**Story Points:** 3
**Status:** Todo

#### User Story

> As a developer, I want workflows to save progress at each step and allow resumption from failures, so that I don't have to restart the entire workflow when something goes wrong midway.

#### Acceptance Criteria

1. ✅ Workflow state saved after each step completion
2. ✅ State includes: step outputs, context, quality metrics
3. ✅ `@simple-mode *resume` command available
4. ✅ `@simple-mode *resume --list` shows resumable workflows
5. ✅ Resume continues from failed/last step
6. ✅ Resume reuses outputs from completed steps
7. ✅ Workflow marked complete when resumed workflow finishes
8. ✅ State cleanup after configurable retention period

#### Technical Details

**Files to Create:**
- `tapps_agents/workflow/checkpoint.py` (250 lines)

**Key Components:**
```python
@dataclass
class WorkflowCheckpoint:
    workflow_id: str
    workflow_type: str  # build, fix, review, etc.
    story_id: str | None
    github_issue: int | None
    status: str  # in-progress, failed, paused
    current_step: int
    completed_steps: list[dict[str, Any]]
    context: dict[str, Any]
    quality_metrics: dict[str, float]
    created_at: datetime
    updated_at: datetime

class CheckpointManager:
    def save_checkpoint(
        self,
        workflow: Workflow,
        step_index: int,
        step_result: dict[str, Any]
    ) -> str:
        """Save workflow state and return checkpoint ID."""

    def load_checkpoint(
        self,
        checkpoint_id: str
    ) -> WorkflowCheckpoint:
        """Load checkpoint by ID."""

    def list_resumable(self) -> list[WorkflowCheckpoint]:
        """List all resumable workflows."""

    def resume_workflow(
        self,
        checkpoint_id: str,
        from_step: int | None = None
    ) -> WorkflowResult:
        """Resume workflow from checkpoint."""

    def cleanup_old_checkpoints(
        self,
        retention_days: int = 30
    ):
        """Remove old checkpoints."""
```

**State Storage:**
- Location: `.tapps-agents/workflow-state/`
- Format: JSON
- Filename: `{workflow-type}-{workflow-id}.json`

**Example State File:**
```json
{
  "workflow_id": "build-abc123",
  "workflow_type": "build",
  "story_id": "enh-001-s4",
  "github_issue": 10,
  "status": "failed",
  "current_step": 5,
  "completed_steps": [
    {
      "step": "enhancer",
      "output": "...",
      "duration": 60,
      "timestamp": "2026-01-29T10:00:00Z"
    }
  ],
  "context": {...},
  "quality_metrics": {...}
}
```

#### Tasks

- [ ] Task 3.1: Create CheckpointManager class (3 hours)
  - Implement save/load logic
  - JSON serialization
  - File management

- [ ] Task 3.2: Integrate with Simple Mode (3 hours)
  - Save checkpoint after each step
  - Implement *resume command
  - Implement *resume --list

- [ ] Task 3.3: Resume workflow execution (2 hours)
  - Skip completed steps
  - Reuse step outputs
  - Continue from failure point

- [ ] Task 3.4: Cleanup and maintenance (1 hour)
  - Automatic cleanup of old checkpoints
  - Configuration for retention

- [ ] Task 3.5: Write tests (3 hours)
  - Test checkpoint save/load
  - Test workflow resume
  - Test cleanup
  - Achieve ≥80% coverage

#### Dependencies

- ENH-002-S1 (Workflow Presets) - for workflow configuration

#### Estimated Effort

12 hours (3 story points)

---

## Epic Summary

### Stories Overview

| ID | Story | Points | Priority | Status |
|----|-------|--------|----------|--------|
| ENH-002-S1 | Workflow Presets Integration | 2 | High | Ready |
| ENH-002-S2 | Auto-Commit with Quality Gates | 3 | High | Todo |
| ENH-002-S3 | Workflow Checkpoint and Resume | 3 | High | Todo |

**Total Story Points:** 8
**Estimated Duration:** 2 weeks (30 hours total)

### Implementation Order

**Week 1:**
1. ENH-002-S1: Workflow Presets (2 days)
   - Enables faster iteration for subsequent stories
   - Foundation for other improvements

**Week 2:**
2. ENH-002-S2: Auto-Commit (3 days)
   - Immediate value for developers
   - Integrates with Beads/GitHub

3. ENH-002-S3: Workflow Resume (4 days)
   - Safety net for long workflows
   - Reduces frustration

### Dependencies Graph

```
ENH-002-S1 (Presets)
    ├─> ENH-002-S2 (Auto-Commit)
    └─> ENH-002-S3 (Resume)
```

---

## Quality Gates

All stories enforce framework quality gates:

- **Overall Score:** ≥ 75
- **Security Score:** ≥ 8.5
- **Test Coverage:** ≥ 80%
- **Automatic Loopback:** If quality gates fail, automatic fix loop (max 3 iterations)

---

## Acceptance Testing

### Story 1: Workflow Presets

```bash
# Test minimal preset
@simple-mode *build --preset minimal "Fix typo in README"
# Expected: Only implementer + tester steps

# Test standard preset
@simple-mode *build --preset standard "Add user endpoint"
# Expected: planner + implementer + reviewer + tester

# Test preset recommendation
@simple-mode *build "Update config.yaml"
# Expected: Suggests minimal preset
```

### Story 2: Auto-Commit

```bash
# Test auto-commit
@simple-mode *build --auto-commit "ENH-002-S2: Add feature... Closes #15"
# Expected: Automatic commit created, issue closed, Beads updated

# Check commit message
git log -1
# Expected: Proper format with metrics and Co-authored-by
```

### Story 3: Workflow Resume

```bash
# Simulate failure
@simple-mode *build "Feature"
# (Fails at step 5)

# Resume workflow
@simple-mode *resume --workflow-id abc123
# Expected: Continues from step 5, reuses outputs from 1-4

# List resumable
@simple-mode *resume --list
# Expected: Shows all resumable workflows
```

---

## Rollout Plan

### Phase 1: Workflow Presets (Week 1)
- Deploy preset configuration
- Update documentation
- Train team on usage
- Monitor adoption

### Phase 2: Auto-Commit (Week 2, Day 1-3)
- Deploy auto-commit feature
- Enable for opt-in testing
- Collect feedback
- Make default if successful

### Phase 3: Workflow Resume (Week 2, Day 4-5)
- Deploy checkpoint system
- Enable for all workflows
- Monitor state file growth
- Tune retention settings

---

## Metrics and KPIs

### Success Metrics

| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| Workflow Time (minimal tasks) | 90 min | 45 min | Average time for minimal preset |
| Manual Git Operations | 100% | 0% | % of workflows using auto-commit |
| Workflow Restart Rate | 80% | 20% | % of failed workflows restarted vs resumed |
| User Satisfaction | N/A | 95% | Post-deployment survey |

### Quality Metrics

- All stories must achieve ≥80% test coverage
- Zero P0/P1 bugs in first 30 days
- Performance: <5s overhead per checkpoint
- State file growth: <1MB per 100 workflows

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Auto-commit creates bad commits | Medium | High | Require quality gates pass, allow manual review |
| State files consume too much disk | Low | Medium | Implement aggressive cleanup, compression |
| Resume fails to restore context | Low | High | Comprehensive testing, validation on load |
| Presets don't match user needs | Medium | Low | Allow custom presets, collect feedback |

---

## Related Documentation

- **Feedback Report:** `docs/feedback/session-2026-01-29-enh-001-s4-feedback.md`
- **Beads Best Practices:** `docs/BEADS_GITHUB_BEST_PRACTICES.md`
- **Workflow Presets Config:** `.tapps-agents/workflow-presets.yaml`

---

**Created:** 2026-01-29
**Based on:** ENH-001-S4 session feedback
**Priority:** High - Immediate value for all developers
