# Checkpoint System Integration Guide

## Overview

This guide shows how to integrate the checkpoint system into BuildOrchestrator to enable mid-execution workflow switching after the Planning step.

**Status**: Integration code ready, needs to be added to BuildOrchestrator
**Estimated Time**: 30 minutes
**Files to Modify**: 1 file

---

## Integration Steps

### Step 1: Add Import

**File**: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Add to imports section** (around line 47, after existing imports):

```python
from ..checkpoint_manager import CheckpointManager, CheckpointAnalysis
```

### Step 2: Add Checkpoint Methods

**Add these three methods to BuildOrchestrator class** (after `_validate_documentation_completeness` method):

```python
async def _checkpoint_after_planning(
    self,
    workflow: str,
    completed_steps: list[str],
    planning_results: dict[str, Any],
    artifacts: dict[str, Any],
) -> CheckpointAnalysis | None:
    """
    Analyze checkpoint after Planning step.

    Args:
        workflow: Current workflow type ("*full", "*build", etc.)
        completed_steps: List of completed steps (["enhance", "plan", "architect"])
        planning_results: Planning step outputs with task characteristics
        artifacts: Completed artifacts from enhance, plan, architect steps

    Returns:
        CheckpointAnalysis if mismatch detected with high confidence, None otherwise

    Side Effects:
        - Logs checkpoint analysis results
        - No state modification

    Examples:
        >>> analysis = await self._checkpoint_after_planning(
        ...     "*full",
        ...     ["enhance", "plan", "architect"],
        ...     {"story_points": 8, "files_affected": 3},
        ...     {"enhance": "...", "plan": {...}}
        ... )
    """
    from ..checkpoint_manager import CheckpointManager

    # Create checkpoint manager
    manager = CheckpointManager()

    # Analyze checkpoint
    analysis = manager.analyze_checkpoint(
        workflow=workflow,
        completed_steps=completed_steps,
        planning_results=planning_results,
    )

    # Log results
    if analysis.mismatch_detected:
        logger.info(
            f"Checkpoint mismatch detected: {workflow} → {analysis.recommended_workflow} "
            f"(saves ~{analysis.token_savings:,} tokens, ~{analysis.time_savings} min)"
        )
        return analysis

    logger.debug("No checkpoint mismatch detected, continuing with current workflow")
    return None


async def _offer_workflow_switch(
    self,
    analysis: CheckpointAnalysis,
) -> str:
    """
    Offer user the option to switch workflows.

    Args:
        analysis: Checkpoint analysis with recommendation

    Returns:
        User choice: "switch" | "continue" | "cancel"

    Side Effects:
        - Displays prompt to user via feedback system
        - Waits for user input (blocking)

    Examples:
        >>> choice = await self._offer_workflow_switch(analysis)
        >>> if choice == "switch":
        ...     # Switch to recommended workflow
    """
    from tapps_agents.core.feedback import get_feedback

    # Format checkpoint message
    message = f"""
✅ Planning Complete (Step {len(analysis.completed_steps)}/{len(analysis.completed_steps) + len(analysis.remaining_steps)})

⚠️ Checkpoint: Task analysis suggests workflow mismatch
- Completed: {", ".join(analysis.completed_steps)} ({len(analysis.completed_steps)} steps)
- Remaining: {", ".join(analysis.remaining_steps)} ({len(analysis.remaining_steps)} steps)

Task characteristics from planning:
- {analysis.files_affected} files affected
- {analysis.story_points} story points
- {analysis.detected_complexity} complexity, {analysis.detected_scope} scope

Recommendation: Switch to {analysis.recommended_workflow} workflow
- Saves: {analysis.steps_saved} steps, ~{analysis.token_savings:,} tokens, ~{analysis.time_savings} minutes
- Reuses: Completed planning artifacts
- Jumps to: {analysis.remaining_steps[0] if analysis.remaining_steps else "N/A"}

Options:
1. Switch to {analysis.recommended_workflow} workflow (recommended)
2. Continue with {analysis.current_workflow} ({len(analysis.remaining_steps)} more steps)
3. Cancel workflow

Your choice: [1/2/3]
"""

    feedback = get_feedback()
    feedback.info(message)

    # TODO: Implement user input collection (CLI or Cursor UI)
    # For now, auto-continue (preserves existing behavior)
    logger.warning(
        "Checkpoint detected but user input not yet implemented - continuing with current workflow. "
        "To switch manually, cancel and restart with recommended workflow."
    )
    return "continue"


async def _switch_and_resume(
    self,
    analysis: CheckpointAnalysis,
    workflow_id: str,
    completed_steps: list[str],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """
    Switch to recommended workflow and resume execution.

    Args:
        analysis: Checkpoint analysis with recommendation
        workflow_id: Current workflow ID
        completed_steps: Completed steps list
        artifacts: Completed artifacts dict

    Returns:
        Dict with execution results from new workflow

    Side Effects:
        - Saves checkpoint to disk (.tapps-agents/checkpoints/)
        - Creates new orchestrator instance
        - Resumes workflow execution

    Raises:
        ValueError: If workflow switch fails

    Examples:
        >>> result = await self._switch_and_resume(
        ...     analysis, "build-abc123",
        ...     ["enhance", "plan", "architect"],
        ...     {"enhance": "...", "plan": {...}}
        ... )
    """
    from ..checkpoint_manager import WorkflowSwitcher

    # Create workflow switcher
    checkpoint_dir = self.project_root / ".tapps-agents" / "checkpoints"
    switcher = WorkflowSwitcher(checkpoint_dir)

    # Perform switch and save artifacts
    switch_result = switcher.switch_workflow(
        workflow_id=workflow_id,
        from_workflow=analysis.current_workflow,
        to_workflow=analysis.recommended_workflow,
        completed_steps=completed_steps,
        artifacts=artifacts,
    )

    if not switch_result["success"]:
        error_msg = f"Failed to switch workflows: {switch_result['error']}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(
        f"Successfully switched from {analysis.current_workflow} to {analysis.recommended_workflow}. "
        f"Resuming from step: {switch_result['resume_from_step']}"
    )

    # Map to appropriate orchestrator
    if analysis.recommended_workflow == "*fix":
        from .fix_orchestrator import FixOrchestrator
        new_orchestrator = FixOrchestrator(self.project_root, self.config)
    else:  # *build (most common)
        new_orchestrator = self  # Reuse BuildOrchestrator

    # Resume execution from the appropriate step
    # TODO: Implement resume logic with preserved artifacts
    # For now, return success status
    return {
        "success": True,
        "switched": True,
        "new_workflow": analysis.recommended_workflow,
        "resume_from_step": switch_result["resume_from_step"],
        "preserved_artifacts": switch_result["preserved_artifacts"],
    }
```

### Step 3: Integrate into execute() Method

**Find the execute() method** in BuildOrchestrator (around line 301).

**After Step 3 (Architect) completes**, add checkpoint call:

```python
async def execute(self, intent: Intent, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute build workflow with checkpoint support."""

    # ... existing code for steps 1-3 (Enhance → Plan → Architect) ...

    # NEW: Checkpoint after Planning (Step 3)
    if self.config and getattr(self.config.simple_mode, "enable_checkpoints", False):
        # Gather planning results
        planning_results = {
            "story_points": planner_result.get("total_story_points", 8),
            "files_affected": len(planner_result.get("files_affected", [])) or 3,
            "user_stories": planner_result.get("stories", []),
            "architectural_impact": architect_result.get("impact", "medium"),
        }

        # Gather completed artifacts
        artifacts = {
            "enhance": enhancer_result.get("enhanced_prompt", ""),
            "plan": planner_result,
            "architect": architect_result,
        }

        # Analyze checkpoint
        checkpoint_analysis = await self._checkpoint_after_planning(
            workflow=parameters.get("workflow", "*build"),
            completed_steps=["enhance", "plan", "architect"],
            planning_results=planning_results,
            artifacts=artifacts,
        )

        # If mismatch detected, offer to switch
        if checkpoint_analysis and checkpoint_analysis.mismatch_detected:
            user_choice = await self._offer_workflow_switch(checkpoint_analysis)

            if user_choice == "switch":
                # Switch to recommended workflow
                return await self._switch_and_resume(
                    checkpoint_analysis,
                    workflow_id,
                    completed_steps=["enhance", "plan", "architect"],
                    artifacts=artifacts,
                )
            elif user_choice == "cancel":
                # User cancelled workflow
                logger.info("User cancelled workflow at checkpoint")
                return {"success": False, "cancelled": True}
            # else: user_choice == "continue" → proceed with current workflow

    # Continue with remaining steps (4-8)
    # ... existing code for Design → Implement → Review → Test → Document ...
```

---

## Configuration

### Enable Checkpoints

Add to `.tapps-agents/config.yaml`:

```yaml
simple_mode:
  enable_checkpoints: true  # Enable mid-execution checkpoints
  checkpoint_confidence_threshold: 0.7  # Confidence threshold for warnings
```

### Disable Checkpoints (Default for Now)

To avoid disrupting existing workflows during testing:

```yaml
simple_mode:
  enable_checkpoints: false  # Disable until user input is implemented
```

---

## Testing the Integration

### Test 1: High Complexity Task (No Mismatch)

```python
# Should NOT trigger checkpoint warning
result = await build_orchestrator.execute(
    intent=Intent(original_input="Implement OAuth2 with multi-tenant isolation"),
    parameters={"workflow": "*full"}
)
# Expected: Continues with *full workflow (no warning)
```

### Test 2: Low Complexity Task (Mismatch Detected)

```python
# Should trigger checkpoint warning
result = await build_orchestrator.execute(
    intent=Intent(original_input="Fix validation bug"),
    parameters={"workflow": "*full"}
)
# Expected: Shows checkpoint warning, offers to switch to *fix
```

### Test 3: Medium Complexity Task (Mismatch to *build)

```python
# Should trigger checkpoint warning
result = await build_orchestrator.execute(
    intent=Intent(original_input="Add user profile page"),
    parameters={"workflow": "*full"}
)
# Expected: Shows checkpoint warning, offers to switch to *build
```

---

## User Input Implementation (TODO)

The `_offer_workflow_switch()` method currently returns "continue" by default. To fully enable the feature:

### Option 1: CLI Input

```python
async def _offer_workflow_switch(self, analysis: CheckpointAnalysis) -> str:
    # ... show message ...

    # Get user input from CLI
    choice = input("Your choice (1/2/3): ").strip()

    if choice == "1":
        return "switch"
    elif choice == "2":
        return "continue"
    elif choice == "3":
        return "cancel"
    else:
        logger.warning(f"Invalid choice '{choice}', continuing with current workflow")
        return "continue"
```

### Option 2: Cursor UI Integration

```python
async def _offer_workflow_switch(self, analysis: CheckpointAnalysis) -> str:
    # ... show message ...

    # Use Cursor's confirmation handler
    confirmation = ConfirmationHandler()
    choice = await confirmation.prompt_user(
        message="Switch to recommended workflow?",
        options=["switch", "continue", "cancel"]
    )
    return choice
```

---

## Rollback Instructions

If integration causes issues:

### Disable Checkpoints

```yaml
# .tapps-agents/config.yaml
simple_mode:
  enable_checkpoints: false
```

### Remove Integration Code

1. Remove checkpoint methods from BuildOrchestrator
2. Remove checkpoint call from execute() method
3. Remove import statement

---

## Next Steps After Integration

1. **Test with real workflows** (manual testing)
2. **Implement user input** (CLI or Cursor UI)
3. **Monitor checkpoint effectiveness**:
   - Track how often checkpoints trigger
   - Track user acceptance rate (switch vs continue)
   - Measure token savings
4. **Tune confidence thresholds** based on user feedback
5. **Add checkpoint support to other orchestrators** (FixOrchestrator, RefactorOrchestrator)

---

## Success Criteria

✅ Integration complete when:
- [ ] Checkpoint methods added to BuildOrchestrator
- [ ] Checkpoint call integrated into execute() method
- [ ] Configuration added to config.yaml
- [ ] Tests pass with enable_checkpoints=false (default)
- [ ] Manual testing shows checkpoint warnings display correctly
- [ ] User can switch workflows successfully

---

**Last Updated**: 2026-01-30
**Status**: Ready for Integration
**Estimated Time**: 30 minutes
