---
story_id: workflow-suggester-001
epic: simple-mode-enhancements
user: developer
priority: high
points: 5
status: todo
---

# User Story: Workflow Suggester - Hybrid "Review + Fix" Request Handler

As a developer, I want the workflow suggester to automatically detect and handle hybrid "review + fix" requests, so that I can get comprehensive quality analysis followed by targeted fixes in a single command.

## Current State

The workflow suggester in `tapps_agents/simple_mode/workflow_suggester.py` currently:
- Detects individual workflow intents (build, review, fix, test, refactor)
- Returns a single workflow suggestion based on primary intent
- Has basic hybrid detection for "review + fix" (lines 467-489)
- Returns a two-step command suggestion but doesn't coordinate execution

**Existing Hybrid Detection** (lines 467-489):
```python
has_review = (
    intent.type == IntentType.REVIEW
    or "review" in user_input_lower
    or intent.compare_to_codebase
)
has_fix = intent.type == IntentType.FIX or "fix" in user_input_lower

if has_review and has_fix:
    return WorkflowSuggestion(
        workflow_command=(
            '@simple-mode *review <file>  # Then: @simple-mode *fix <file> "issues from review"'
        ),
        workflow_type="review-then-fix",
        benefits=[...],
        confidence=0.85,
        reason="Review + fix hybrid request detected",
    )
```

**Problem:** This only **suggests** the two-step workflow but doesn't actually **execute** it or coordinate the workflows sequentially.

## Acceptance Criteria

### 1. Enhanced Hybrid Intent Detection
- [x] Detect "review + fix" pattern in user prompts
- [ ] Detect "review + compare + fix" pattern (e.g., "review this and compare to our patterns and fix it")
- [ ] Detect implicit hybrid requests (e.g., "make this code match our standards and fix issues")
- [ ] Confidence scoring for hybrid detection (≥0.6 threshold for suggestion)

### 2. Sequential Workflow Coordination
- [ ] Execute `*review` workflow first and capture results
- [ ] Extract key issues from review results
- [ ] Automatically invoke `*fix` workflow with review issues as context
- [ ] Pass file path and fix description to second workflow
- [ ] Report progress for both workflows (Step 1/2, Step 2/2)

### 3. Integration with Intent Detection System
- [ ] Extend `IntentParser` in `tapps_agents/simple_mode/intent_parser.py` to support hybrid intent type
- [ ] Add `IntentType.REVIEW_FIX` enum value
- [ ] Update `Intent.get_agent_sequence()` to return hybrid sequence: ["reviewer", "improver", "debugger", "implementer", "tester"]
- [ ] Maintain backward compatibility with existing single-workflow intents

### 4. Workflow Suggester Enhancement
- [ ] Add `suggest_hybrid_workflow()` method to detect and suggest hybrid workflows
- [ ] Update `suggest_workflow()` to call `suggest_hybrid_workflow()` before single-workflow logic
- [ ] Add `execute_hybrid_workflow()` method to coordinate sequential execution (if needed)
- [ ] Format hybrid suggestions with clear benefits and two-step command

### 5. Quality Gates and Error Handling
- [ ] If review workflow fails, skip fix workflow and report error
- [ ] If review finds no critical issues (score ≥ 85), prompt user before proceeding to fix
- [ ] If fix workflow fails, report both review results and fix error
- [ ] Maintain full traceability from review → fix

## Tasks

### Task 1: Extend Intent Detection (2 hours)
- [ ] Add `REVIEW_FIX` to `IntentType` enum in `tapps_agents/simple_mode/intent_parser.py:14`
- [ ] Update `Intent.get_agent_sequence()` to handle `REVIEW_FIX` type
- [ ] Add unit tests for hybrid intent detection

**Files to Modify:**
- `tapps_agents/simple_mode/intent_parser.py` - Add `REVIEW_FIX` enum and handler

### Task 2: Enhance Workflow Suggester (3 hours)
- [ ] Strengthen hybrid detection in `WorkflowSuggester.suggest_workflow()` (lines 467-489)
- [ ] Add pattern detection for "compare to codebase" requests
- [ ] Update suggestion formatting to emphasize sequential execution
- [ ] Add confidence scoring for hybrid detection
- [ ] Add unit tests for hybrid detection patterns

**Files to Modify:**
- `tapps_agents/simple_mode/workflow_suggester.py` - Lines 467-489 (strengthen hybrid detection)

### Task 3: Sequential Workflow Coordination (Optional - 4 hours)
*Note: This task is optional if we only want suggestion, not automatic execution*

- [ ] Add `execute_hybrid_workflow()` method to `WorkflowSuggester`
- [ ] Implement review → fix sequential execution
- [ ] Extract key issues from review results
- [ ] Pass issues to fix workflow as context
- [ ] Add progress reporting for multi-step workflows

**Files to Modify:**
- `tapps_agents/simple_mode/workflow_suggester.py` - Add execution coordination

### Task 4: Integration and Testing (3 hours)
- [ ] Update `SimpleModeHandler` to use enhanced suggester
- [ ] Add integration tests for hybrid workflow
- [ ] Test with real user prompts:
  - "review this file and fix any issues"
  - "review this and compare to our patterns and fix it"
  - "make this code match our standards and fix issues"
- [ ] Update documentation in `.claude/skills/simple-mode/skill.md`

**Files to Modify:**
- `tapps_agents/simple_mode/nl_handler.py` - Update handler integration
- `tests/test_workflow_suggester.py` - Add integration tests
- `.claude/skills/simple-mode/skill.md` - Update documentation

## Story Points: 5

**Complexity:** Medium
- Extends existing workflow suggester with hybrid detection
- Requires coordination between multiple workflows
- Optional sequential execution adds complexity

**Scope:** Medium
- 2 primary files to modify (`intent_parser.py`, `workflow_suggester.py`)
- 1 integration file (`nl_handler.py`)
- Documentation updates
- Unit and integration tests

**Files Affected:**
1. `tapps_agents/simple_mode/intent_parser.py` (add REVIEW_FIX enum)
2. `tapps_agents/simple_mode/workflow_suggester.py` (strengthen hybrid detection)
3. `tapps_agents/simple_mode/nl_handler.py` (integration)
4. `tests/test_workflow_suggester.py` (tests)
5. `.claude/skills/simple-mode/skill.md` (docs)

## Estimated Effort: 8-12 hours

**Breakdown:**
- Intent detection: 2 hours
- Workflow suggester: 3 hours
- Sequential coordination (optional): 4 hours
- Integration & testing: 3 hours

## Priority: High

**Impact:** High user satisfaction - addresses common workflow pattern
**Frequency:** High - users frequently want to review and fix in one command
**Complexity:** Medium - builds on existing suggester infrastructure

## Dependencies

- None (self-contained within simple_mode module)

## Context7 References

- Simple Mode orchestration patterns
- Workflow suggester design patterns
- Intent detection algorithms

## Technical Notes

### Current Hybrid Detection Logic (Lines 467-489)

The existing code detects hybrid intent using:
```python
has_review = (
    intent.type == IntentType.REVIEW
    or "review" in user_input_lower
    or intent.compare_to_codebase  # Key for "compare to codebase" detection
)
has_fix = intent.type == IntentType.FIX or "fix" in user_input_lower
```

**Strengths:**
- Uses `intent.compare_to_codebase` flag (set by intent parser lines 383-402)
- Returns clear two-step command suggestion
- High confidence (0.85)

**Weaknesses:**
- Doesn't execute workflows sequentially
- Doesn't pass review results to fix workflow
- Manual two-step execution required

### Proposed Enhancement Approach

**Option 1: Suggestion Only (Minimal Scope - 8 hours)**
- Strengthen hybrid detection patterns
- Improve suggestion formatting
- Keep manual two-step execution

**Option 2: Full Coordination (Complete Scope - 12 hours)**
- Add sequential workflow execution
- Pass review results to fix workflow
- Automatic end-to-end coordination

**Recommendation:** Start with Option 1 (Suggestion Only) for Phase 1 implementation, then add Option 2 (Full Coordination) in Phase 2 if user feedback indicates need.

### Integration Points

1. **Intent Parser** (`intent_parser.py`)
   - Add `REVIEW_FIX` enum value
   - Update `parse()` method to detect hybrid pattern
   - Update `get_agent_sequence()` for hybrid type

2. **Workflow Suggester** (`workflow_suggester.py`)
   - Strengthen hybrid detection (lines 467-489)
   - Add "compare to codebase" pattern detection
   - Format clear two-step suggestion

3. **Natural Language Handler** (`nl_handler.py`)
   - Update to use enhanced suggester
   - Handle hybrid suggestions appropriately

### Testing Strategy

**Unit Tests:**
- Test hybrid intent detection with various prompts
- Test confidence scoring for hybrid detection
- Test suggestion formatting

**Integration Tests:**
- Test end-to-end hybrid workflow suggestion
- Test with real user prompts
- Test edge cases (only review, only fix, ambiguous)

**Test Prompts:**
```python
test_cases = [
    "review this file and fix any issues",
    "review this and compare to our patterns and fix it",
    "make this code match our standards and fix issues",
    "check the code quality and repair any problems",
    "inspect and correct validation errors",
]
```

## Related Files

- `tapps_agents/workflow/intent_detector.py` - Separate intent detector (may need alignment)
- `tapps_agents/simple_mode/prompt_analyzer.py` - Prompt analysis utilities
- `tapps_agents/simple_mode/nl_handler.py` - Natural language handler integration
