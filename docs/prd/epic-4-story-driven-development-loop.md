# Epic 4: Autonomous Story-Driven Development Loop

## Epic Goal

Make story-first delivery the default operating model for TappsCodingAgents: stories are the unit of work, have explicit lifecycle states with automated transitions, and create an auditable trail of decisions and execution—all without human intervention.

## Epic Description

### Existing System Context

- **BMAD Integration**: BMAD provides a story-driven development model with lifecycle states (Draft → Approved → In Progress → Review → Done) and canonical story templates (`.bmad-core/templates/story-tmpl.yaml`).
- **Current relevant functionality**: TappsCodingAgents has workflow execution, reporting, and multiple agents, but does not enforce a single "story is the unit of work" execution loop as the default.
- **Artifacts currently in use**: `docs/stories/` exists, but story lifecycle, permissions, and "what must be present in a story" are not standardized as a mandatory process backbone.
- **Key gap**: Stories are not treated as executable work units with automated state transitions and quality-gate-driven approvals. BMAD requires human approval (Draft → Approved); TappsCodingAgents needs autonomous approval based on quality gates.

### Enhancement Details

- **What's being added/changed**:
  - A single canonical story lifecycle with automated state transitions (Draft → Auto-Approved → In Progress → Ready for Review → Done).
  - A canonical story file structure (tasks/subtasks, Dev Agent Record, QA Results, File List, Change Log, Status).
  - Role boundaries: which sections Dev may update vs which sections QA may update, to preserve audit quality and reduce accidental edits.
  - **Autonomous approval rule**: Implementation begins automatically when quality gates pass (risk assessment, test design completeness, no blocking issues).
  - **Automated state transitions**: States change based on quality gate outcomes, not human decisions.
- **How it integrates**:
  - Applied as the default way to run enhancements in the repo (especially brownfield work).
  - Feeds directly into Progressive Task Reviews (Epic 5).
  - Integrates with existing workflow executor and quality gates.
- **Success criteria**:
  - Every change set maps to a story.
  - Every story produces a consistent audit trail and ends with an explicit review state.
  - Story execution is fully autonomous, repeatable, and predictable.
  - State transitions happen automatically based on quality gate outcomes.

## Stories

1. **Story 36.1: Canonical Story Template + Lifecycle States** (`docs/stories/36.1.canonical-story-template-and-lifecycle-states.md`)
   - Define required story sections and lifecycle states.
   - Define explicit state transition rules (who can change Status, when).
   - Acceptance criteria: A single story template exists; lifecycle states are documented; transitions are unambiguous.

2. **Story 36.2: Role-Based Editing Permissions for Story Sections** (`docs/stories/36.2.role-based-editing-permissions-for-story-sections.md`)
   - Define Dev-authorized vs QA-authorized sections (and "do not edit" rules).
   - Provide clear enforcement guidance in workflow instructions.
   - Acceptance criteria: Dev/QA boundaries are explicit; accidental edits are prevented by process and clearly detectable.

3. **Story 36.3: Story Execution Protocol (Task Sequencing + Evidence Capture)** (`docs/stories/36.3.story-execution-protocol-task-sequencing-and-evidence-capture.md`)
   - Define the canonical per-task execution order (read → implement → validate → review → mark complete).
   - Define mandatory "File List" and "Change Log" updates during execution.
   - Acceptance criteria: Stories are executed with consistent sequencing and evidence capture across runs.

4. **Story 36.4: Brownfield Story Protocol** (`docs/stories/36.4.brownfield-story-protocol.md`)
   - Add explicit brownfield constraints: regression awareness, integration verification notes, rollback hints.
   - Acceptance criteria: Brownfield stories include risk/regression notes and explicit verification expectations.

## Compatibility Requirements

- [ ] Must not break existing documentation organization.
- [ ] Must remain usable for both quick fixes and larger enhancements.
- [ ] Must be compatible with existing workflow executor and reporting conventions.

## Risk Mitigation

- **Primary Risk**: Automated approvals may proceed with issues.
  - **Mitigation**: Quality gates must be comprehensive; only low-risk stories auto-approve; high-risk stories require full assessment.
- **Primary Risk**: State transitions may be too aggressive or too conservative.
  - **Mitigation**: Configurable quality gate thresholds; automated override based on risk thresholds and learned patterns; continuous learning from transition outcomes.

## Definition of Done

- [ ] Canonical story template exists and is adopted for new stories.
- [ ] Lifecycle states and transition rules are documented and followed.
- [ ] Role-based editing boundaries are explicit and consistently applied.
- [ ] A reference “golden story” demonstrates the full loop end-to-end.

## Implementation Status

**Last Updated:** 2025-12-18  
**Overall Status:** ❌ **MARKED AS OVERKILL - NOT TO BE IMPLEMENTED**

### Decision Rationale

After review against 2025 best practices and TappsCodingAgents' "vibe coding" philosophy:

- **Over-engineered**: Adds mandatory process overhead that conflicts with autonomous, flow-focused development
- **Project management scope**: Conflicts with non-goal: "Project management features - Use external tools"
- **Developer friction**: Mandatory story lifecycle states and role-based permissions add bureaucracy
- **Not solving real problems**: Git history already tracks changes; quality gates already ensure quality

**Recommendation**: Keep Epic 5 (Progressive Reviews) which provides real value with low friction. Epic 4 adds process without solving developer problems.


