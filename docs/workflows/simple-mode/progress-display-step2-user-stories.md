# Step 2: User Stories — Progress Display Format

**Workflow:** Full SDLC (Progress Display Format Implementation)  
**Created:** 2026-02-05

## User Stories

1. **As a** workflow user, **I want** workflow completion and state to be shown in a scannable phase grid (icons, progress bars, TOTAL) **so that** I can see status at a glance in terminal and chat.
2. **As a** Windows/CI user, **I want** an ASCII-safe progress display when Unicode is not available **so that** I get no encoding errors.
3. **As a** framework integrator, **I want** a single formatter API (phase list → string) in core **so that** workflow, epic, and health can reuse the same format.
4. **As a** operator, **I want** optional config `progress_display_format: phasegrid | legacy | plain` **so that** I can enable the new format or force ASCII.

## Task Breakdown (from Implementation Plan)

- Phase 1: Core formatter (`progress_display.py`) + tests
- Phase 2: Phase list builder from Workflow+State; WorkflowSummaryGenerator integration; optional workflow state show
- Phase 3: Config key, docs (CONFIGURATION.md, guide)
