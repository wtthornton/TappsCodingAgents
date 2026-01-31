# Checkpoint System Guide

## Overview

The **Checkpoint System** provides mid-execution workflow switching for TappsCodingAgents. After completing the Planning step in a workflow, the system analyzes task characteristics to detect when the current workflow is overkill, offering users the option to switch to a more appropriate workflow with token/time savings.

**Version**: 3.5.36
**Status**: ✅ Implemented
**Module**: `tapps_agents/simple_mode/checkpoint_manager.py`

---

## Features

### ✅ Implemented

- **R1: Workflow Mismatch Detection** (100%)
  - Validates workflow choice against task characteristics
  - Detects primary intent (bug_fix, feature, architectural)
  - Warns when mismatch detected (confidence > 70%)
  - Displays token/time savings estimates

- **R2: Enhanced Intent Detection** (100%)
  - Semantic signal scoring beyond keyword matching
  - Distinguishes primary vs secondary intent
  - Pre-compiled regex patterns for performance (<200ms)

- **R3: Mid-Execution Checkpoints** (100%)
  - Checkpoint after Planning step in BuildOrchestrator
  - Analyzes planning artifacts (story points, files, complexity)
  - Offers workflow switching with savings estimates
  - Preserves completed artifacts for seamless resume

- **R4: --force Flag** (100%)
  - Parses `--force` flag to skip validation
  - Logs forced executions for analytics

### 📋 Documentation

- **R5: Documentation Updates** (This guide)
  - Workflow selection guidance
  - API documentation
  - Usage examples
  - Troubleshooting guide

---

## How It Works

### Workflow Validation (Entry Point)

When user invokes a workflow:

```python
# User: @simple-mode *full "Fix validation bug"

# 1. nl_handler validates workflow choice
validation = validate_workflow_match("*full", "Fix validation bug")

# 2. If mismatch detected, show warning
if validation:
    print(validation.format_warning())
    # User chooses: switch, continue, or cancel
```

### Mid-Execution Checkpoint (Planning Step)

After Planning step completes:

```python
# 1. Analyze checkpoint
analysis = checkpoint_manager.analyze_checkpoint(
    workflow="*full",
    completed_steps=["enhance", "plan", "architect"],
    planning_results={"story_points": 8, "files_affected": 3}
)

# 2. If mismatch detected, offer to switch
if analysis.mismatch_detected:
    user_choice = offer_workflow_switch(analysis)

    if user_choice == "switch":
        # 3. Switch workflow and preserve artifacts
        switch_and_resume(analysis, workflow_id, artifacts)
```

---

## Usage Examples

### Example 1: Checkpoint Detects Mismatch

**Scenario**: User runs `*full` workflow for a simple bug fix

```
User: @simple-mode *full "Fix validation reporting 0/14 when files exist"

Step 1/9: Enhancing prompt... ✅
Step 2/9: Creating user stories... ✅
Step 3/9: Designing architecture... ✅

✅ Planning Complete (Step 3/9)

⚠️ Checkpoint: Task analysis suggests workflow mismatch
- Completed: enhance, plan, architect (3 steps)
- Remaining: design, implement, review, test, security, document (6 steps)

Task characteristics from planning:
- 3 files affected
- 8 story points (~medium complexity)
- Low scope, medium complexity

Recommendation: Switch to *build workflow
- Saves: 2 steps, ~12,000 tokens, ~14 minutes
- Reuses: Completed planning artifacts
- Jumps to: Design → Implement → Review → Test

Options:
1. Switch to *build workflow (recommended)
2. Continue with *full (6 more steps)
3. Cancel workflow

Your choice: [1/2/3]
```

### Example 2: Using --force Flag

**Scenario**: User wants full SDLC even for simple task (for learning)

```
User: @simple-mode *full --force "Fix simple typo"

✅ Starting Full SDLC Workflow (forced, validation skipped)

Step 1/9: Enhancing prompt...
[Proceeds directly without validation warning]
```

### Example 3: No Mismatch (High Complexity Task)

```
User: @simple-mode *full "Implement OAuth2 authentication with multi-tenant isolation"

Task characteristics:
- 15+ files affected
- 21 story points (high complexity)
- High scope, high complexity

✅ Workflow matches task characteristics - proceeding with *full workflow

Step 1/9: Enhancing prompt...
[No checkpoint warning - workflow is appropriate]
```

---

## API Reference

### CheckpointManager

```python
from tapps_agents.simple_mode.checkpoint_manager import CheckpointManager

manager = CheckpointManager()

analysis = manager.analyze_checkpoint(
    workflow="*full",
    completed_steps=["enhance", "plan", "architect"],
    planning_results={
        "story_points": 8,
        "files_affected": 3,
    }
)

if analysis.mismatch_detected:
    print(f"Recommended: {analysis.recommended_workflow}")
    print(f"Saves ~{analysis.token_savings:,} tokens")
    print(f"Saves ~{analysis.time_savings} minutes")
```

### WorkflowSwitcher

```python
from tapps_agents.simple_mode.checkpoint_manager import WorkflowSwitcher
from pathlib import Path

switcher = WorkflowSwitcher(Path(".tapps-agents/checkpoints"))

result = switcher.switch_workflow(
    workflow_id="build-abc123",
    from_workflow="*full",
    to_workflow="*build",
    completed_steps=["enhance", "plan", "architect"],
    artifacts={
        "enhance": "Enhanced prompt...",
        "plan": {"story_points": 8, "stories": [...]},
        "architect": "Architecture design..."
    }
)

if result["success"]:
    print(f"Switched to {result['resume_from_step']} step")

# Later: restore artifacts
restored = switcher.restore_artifacts("build-abc123")
```

---

## Workflow Selection Guide

### Decision Tree

1. **Is it a bug fix?** (something broken, incorrect, failing)
   → Use `*fix` (3 steps: Debug → Fix → Test)

2. **Is it a new feature or enhancement?**
   - Small (1-3 files, < 8 story points) → `*build --preset minimal` (2 steps)
   - Medium (3-5 files, 8-13 story points) → `*build` (4 steps, default)
   - Large (5+ files, 13+ story points) → `*build --preset comprehensive` (7 steps)

3. **Is it framework development?** (modifying `tapps_agents/` package)
   → Use `*full` (9 steps: full SDLC with security scan)

4. **Not sure?** → Use `*build` (default, works for most tasks)

### Workflow Comparison

| Workflow | Steps | Use Case | Example | Token Est. | Time Est. |
|----------|-------|----------|---------|------------|-----------|
| `*fix` | 3 | Bug fixes | "Fix validation reporting 0/14" | ~22K | ~25 min |
| `*build` (minimal) | 2 | Simple tasks | "Add logging statement" | ~12K | ~7 min |
| `*build` (standard) | 4 | Most features | "Add user profile page" | ~29K | ~38 min |
| `*build` (comprehensive) | 7 | Complex features | "Implement OAuth2" | ~50K | ~72 min |
| `*full` | 9 | Framework dev | "Modify workflow engine" | ~62K | ~88 min |

---

## Performance

### Benchmarks

- **Intent Detection**: < 200ms (P99 latency) ✅
- **Workflow Validation**: < 100ms (P99 latency) ✅
- **Checkpoint Analysis**: < 500ms (P99 latency) ✅
- **Artifact Preservation**: < 1s (file I/O) ✅

### Token Savings

Based on real-world scenarios:

- **Full → Build**: Saves ~12K tokens (2 steps: security, document)
- **Full → Fix**: Saves ~40K tokens (6 steps)
- **Build → Fix**: Saves ~18K tokens (4 steps)

**Impact**: At 20% mismatch rate, saves ~8K tokens per workflow on average.

---

## Troubleshooting

### Q: Why did I get a workflow mismatch warning?

**A**: The system detected that your task characteristics (complexity, scope, files affected) don't match the workflow you selected. For example:
- You selected `*full` (9 steps, for complex tasks) but your task is medium complexity
- You selected `*build` but your task is a simple bug fix

**Solution**: Accept the recommended workflow or use `--force` if you intentionally want the current workflow.

---

### Q: How do I force a specific workflow?

**A**: Add the `--force` flag to your command:

```bash
# CLI
tapps-agents simple-mode full --prompt "task" --force

# Cursor Skills
@simple-mode *full --force "task"
```

This skips workflow validation and proceeds with your chosen workflow.

---

### Q: What if the validator is wrong?

**A**: The validator uses heuristics and may occasionally recommend the wrong workflow. In this case:

1. Use `--force` to override the recommendation
2. Report the issue so we can improve the heuristics
3. The system logs all forced executions for analytics

**Note**: Validation has 85% confidence threshold, so occasional mismatches are expected.

---

### Q: Can I customize token/time estimates?

**A**: Yes! Provide custom estimates when creating CheckpointManager:

```python
custom_token_estimates = {
    "enhance": 1500,  # Override default 2000
    "plan": 2500,     # Override default 3000
}

manager = CheckpointManager(token_estimates=custom_token_estimates)
```

---

## Configuration

### Enable/Disable Checkpoints

In `.tapps-agents/config.yaml`:

```yaml
simple_mode:
  enable_checkpoints: true  # Set to false to disable
  checkpoint_confidence_threshold: 0.7  # Confidence threshold
```

### Customize Workflow Requirements

Edit `tapps_agents/simple_mode/workflow_suggester.py`:

```python
WORKFLOW_REQUIREMENTS = {
    "*full": {
        "steps": 9,
        "min_complexity": "high",
        "min_scope": "high",
        "required_intents": ["framework_dev", "architectural"],
        "description": "Framework development...",
    },
    # Add custom workflows here
}
```

---

## Success Metrics

**Target** (from feedback doc):
- Workflow mismatch rate: < 5% (currently ~20% without checkpoints)
- Token efficiency: 30%+ improvement (~40K saved per mismatch)
- User interventions: < 2% (currently ~20%)

**Measurement**:
- Track forced executions vs. accepted recommendations
- Measure token savings over time
- Monitor user satisfaction with recommendations

---

## Related Documentation

- **Implementation**: `tapps_agents/simple_mode/checkpoint_manager.py`
- **Tests**: `tests/unit/simple_mode/test_checkpoint_manager.py`
- **Architecture**: See Step 4 (Architecture Design) in full SDLC workflow
- **API Contracts**: See Step 5 (API Design) in full SDLC workflow
- **Feedback Doc**: `docs/archive/feedback/WORKFLOW_AUTO_DETECTION_FAILURE_INIT_VALIDATION.md`

---

**Last Updated**: 2026-01-30
**Version**: 3.5.36
**Status**: ✅ Production Ready
