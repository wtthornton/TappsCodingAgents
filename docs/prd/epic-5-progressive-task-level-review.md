# Epic 5: Autonomous Progressive Task-Level Review

## Epic Goal

Prevent "end-of-story surprise" by adding automated progressive, task-level reviews as a standard step between "task implemented + validations pass" and "task marked complete," producing immediate feedback and accumulating evidence for final QA—all without human intervention.

## Epic Description

### Existing System Context

- **BMAD Integration**: BMAD already provides automated progressive review via `.bmad-core/tasks/progressive-code-review.md` with `auto_trigger: true` in `core-config.yaml`. The dev agent's `*develop-story` command automatically runs progressive reviews after each task.
- **Current relevant functionality**: TappsCodingAgents has strong reviewer tooling and reporting, but does not standardize task-by-task review decisions within a story execution loop.
- **Key gap**: While BMAD has progressive review automation, TappsCodingAgents needs to fully integrate this into its autonomous workflow executor and ensure reviews happen without human intervention.

### Enhancement Details

- **What's being added/changed**:
  - Integration with BMAD's existing progressive review automation (`.bmad-core/tasks/progressive-code-review.md`).
  - An automated task-level review decision model: **PASS / CONCERNS / BLOCK** (aligned with BMAD's format).
  - A severity policy where only high severity blocks progress by default (matching BMAD's `severity_blocks: [high]`).
  - Automated review execution: reviews run automatically after task validation passes (leveraging BMAD's `auto_trigger: true`).
  - A stored progressive review record per task for later rollup into final QA (using BMAD's `docs/qa/progressive/` convention).
  - An automated "defer vs fix now" protocol for CONCERNS with explicit documentation of deferral.
- **How it integrates**:
  - Requires the Story-Driven Development Loop (Epic 4) to define what a "task" is and when it's complete.
  - Integrates with existing reviewer agent and quality gates.
  - Feeds into automated final QA review, where deferred concerns are automatically revisited and resolved or waived based on configured policies.
- **Success criteria**:
  - Issues are caught earlier with lower fix cost.
  - Task completion is evidence-backed and repeatable.
  - Reviews happen automatically without human intervention.
  - Final QA becomes faster and more decisive due to accumulated task review history.

## Stories

1. **Story 37.1: Progressive Review Policy and Output Format** (`docs/stories/37.1.progressive-review-policy-and-output-format.md`)
   - Define the decision schema and severity thresholds.
   - Define required metadata (story id, task number, timestamp, affected files).
   - Acceptance criteria: Output format is consistent, human-readable, and supports rollup.

2. **Story 37.2: Task Review Storage and Naming Conventions** (`docs/stories/37.2.task-review-storage-and-naming-conventions.md`)
   - Define where progressive reviews live and naming rules.
   - Define retention expectations and how records are referenced from the story.
   - Acceptance criteria: Review records are easy to find, stable, and story-linked.

3. **Story 37.3: Developer Workflow Integration (Review Before Task Completion)** (`docs/stories/37.3.developer-workflow-integration-review-before-task-completion.md`)
   - Define the canonical "review before checkbox" rule.
   - Define how BLOCK halts progress and how CONCERNS can be fixed or deferred.
   - Acceptance criteria: No task is marked complete without a recorded decision.

4. **Story 37.4: Final QA Rollup Rules** (`docs/stories/37.4.final-qa-rollup-rules.md`)
   - Define how final QA consumes progressive review history.
   - Define required handling for deferred CONCERNS (fix, waive, or fail).
   - Acceptance criteria: Final QA outcome explicitly references any deferred items.

## Compatibility Requirements

- [ ] Must not replace existing review tooling; it adds a disciplined timing and evidence model.
- [ ] Must remain configurable (strictness and focus areas can be tuned).

## Risk Mitigation

- **Primary Risk**: Automated reviews may produce too many false positives.
  - **Mitigation**: Only high severity blocks by default; tune review prompts and categories; learn from patterns.
- **Primary Risk**: Automated deferral may accumulate too many concerns.
  - **Mitigation**: Automated final QA enforces that deferred items are resolved or automatically waived based on risk thresholds; track deferral rates and patterns.

## Definition of Done

- [ ] Progressive review format and decision policy documented.
- [ ] Storage conventions and rollup rules defined and adopted.
- [ ] A reference story demonstrates multiple task reviews and a final QA rollup.

## Implementation Status

**Last Updated:** 2025-12-18  
**Overall Status:** ✅ **IMPLEMENTED**

### Implementation Summary

All stories in Epic 5 have been implemented:

1. **Story 37.1**: ✅ Progressive Review Policy and Output Format
   - Implemented in `tapps_agents/agents/reviewer/progressive_review.py`
   - Decision schema: PASS/CONCERNS/BLOCK
   - Severity policy: Only high severity blocks by default

2. **Story 37.2**: ✅ Task Review Storage and Naming Conventions
   - Implemented in `ProgressiveReviewStorage` class
   - Storage: `docs/qa/progressive/` (BMAD convention)
   - Naming: `{epic}.{story}-task-{n}.yml`

3. **Story 37.3**: ✅ Developer Workflow Integration
   - Implemented in `ReviewerAgent.progressive_review_task()`
   - Automatic review before task completion
   - BLOCK/CONCERNS handling

4. **Story 37.4**: ✅ Final QA Rollup Rules
   - Implemented in `ProgressiveReviewRollup` class
   - Rollup via `ReviewerAgent.rollup_story_reviews()`

**See**: `docs/EPIC_5_PROGRESSIVE_REVIEW_IMPLEMENTATION.md` for full details.


