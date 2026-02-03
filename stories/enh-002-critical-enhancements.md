# Epic 2: Critical Enhancements (ENH-002)

**Epic ID:** ENH-002
**Status:** Ready for Implementation
**Priority:** High
**Total Story Points:** 50
**Estimated Duration:** 7 weeks
**Target Release:** v3.6.0 (Q1 2026)

**Execution status:** Completion is tracked in `stories/epic-2-report.json`. The .md file is not updated automatically.
- **After a run:** Sync status into this file: `tapps-agents simple-mode epic-status stories/enh-002-critical-enhancements.md`.
- **While a run is in progress:** Watch the terminal, or monitor the report (it updates as stories complete):  
  `Get-Content stories\epic-2-report.json -Wait -Tail 20` (PowerShell) or `tail -f stories/epic-2-report.json` (bash).

---

## Epic Goal

Implement critical enhancements to TappsCodingAgents v3.6.0: Hook System (5 core events), Beads Hydration Pattern for multi-session persistence, Auto-Formatting Integration, Context Injection, and Session Lifecycle management—achieving parity with Claude Code automation while retaining TappsCodingAgents workflow and quality strengths.

## Epic Description

This Epic delivers the ENH-002 scope from the PRD at `.tapps-agents/context/enh-002-prd.md`. Components include: (1) Hook System with UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, WorkflowComplete; YAML configuration and env vars; (2) Beads Hydration via task specification files in `.tapps-agents/task-specs/`; (3) Auto-Formatting (PostToolUse hooks with formatter templates); (4) Context Injection (UserPromptSubmit hooks using `.tapps-agents/context/`); (5) Session Lifecycle (SessionStart/End with hydrate/dehydrate). Quality threshold ≥75; hooks module test coverage ≥85%. All public APIs documented.

---

## Stories

### Phase 1: Foundation (2 weeks, 4 stories, 13 points)

1. **Story 2.1: Hook configuration schema and loader**
**Execution status:** failed

   **Ref ID:** ENH-002-S1  
   **Priority:** 0 (highest)  
   **Points:** 3  

   Load and validate `.tapps-agents/hooks.yaml` with event definitions, matchers, and commands. Provides the configuration layer for the hook system.

   Acceptance criteria:
   - Schema validates hooks.yaml structure (events, name, command, enabled, matcher, file_patterns)
   - Loader reads from config path with safe defaults when file missing
   - Invalid YAML or schema violations raise clear errors with path/line hints
   - Supported events: UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, WorkflowComplete
   - Unit tests for valid/invalid configs and error paths

   Depends on: (none)
   Story points: 3

   - Files affected: `tapps_agents/hooks/config.py`

   - Tests required: Unit tests in `tests/unit/hooks/test_config.py` (schema, load, validation, error handling)

   - GitHub Issue: TBD

2. **Story 2.2: Hook executor with environment variables**
**Execution status:** failed

   **Ref ID:** ENH-002-S2  
   **Priority:** 0  
   **Points:** 5  

   Execute hook shell commands with TAPPS_* environment variables, timeout handling, and stdout/stderr capture so hooks can run safely and observably.

   Acceptance criteria:
   - Executor runs shell commands with env vars: TAPPS_FILE_PATH, TAPPS_FILE_PATHS, TAPPS_TOOL_NAME, TAPPS_PROMPT, TAPPS_WORKFLOW_TYPE, TAPPS_WORKFLOW_ID, TAPPS_PROJECT_ROOT, TAPPS_BEADS_ISSUE_ID
   - Configurable timeout (default 30s); on timeout, process killed and error reported
   - Stdout and stderr captured and returned; non-zero exit logged but does not fail workflow unless hook has fail_on_error
   - Unit and integration tests for execution, timeout, and env substitution

   Depends on Story 2.1
   Story points: 5

   - Files affected: `tapps_agents/hooks/executor.py`

   - Tests required: Unit tests in `tests/unit/hooks/test_executor.py`; integration test for real command execution and timeout

   - GitHub Issue: TBD

3. **Story 2.3: Hook event definitions**
**Execution status:** failed

   **Ref ID:** ENH-002-S3  
   **Priority:** 0  
   **Points:** 2  

   Define the five hook events with data structures and serialization for type-safe use across the hook system.

   Acceptance criteria:
   - Event types: UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, WorkflowComplete with clear payload fields
   - Data structures support serialization for logging and context injection
   - Unit tests for event creation and serialization

   Depends on: (none)
   Story points: 2

   - Files affected: `tapps_agents/hooks/events.py`

   - Tests required: Unit tests in `tests/unit/hooks/test_events.py`

   - GitHub Issue: TBD

4. **Story 2.4: Hook manager**
**Execution status:** failed

   **Ref ID:** ENH-002-S4  
   **Priority:** 0  
   **Points:** 3  

   Hook lifecycle management, registration, and triggering so orchestrators and CLI can fire hooks at the right points.

   Acceptance criteria:
   - Manager loads hooks from config (via config loader), registers by event type
   - Trigger method invokes executor for matching hooks with correct payload and env
   - PostToolUse supports matcher and file_patterns filtering
   - Unit tests for registration and triggering for each event type

   Depends on Story 2.1. Depends on Story 2.2. Depends on Story 2.3.
   Story points: 3

   - Files affected: `tapps_agents/hooks/manager.py`

   - Tests required: Unit tests in `tests/unit/hooks/test_manager.py` (registration, triggering, matcher logic)

   - GitHub Issue: TBD

### Phase 2: Integration (2 weeks, 3 stories, 13 points)

5. **Story 2.5: Integrate hooks into base orchestrator**
**Execution status:** failed

   **Ref ID:** ENH-002-S5  
   **Priority:** 0  
   **Points:** 5  

   Call UserPromptSubmit before workflows start, PostToolUse after implementer tool use, and WorkflowComplete after workflow finishes.

   Acceptance criteria:
   - Base orchestrator calls UserPromptSubmit with prompt and project root before workflow execution
   - PostToolUse invoked after implementer Write/Edit with file path and tool name
   - WorkflowComplete invoked with workflow type, workflow ID, and status after workflow ends
   - Hooks disabled by default (opt-in via config); no behavior change when hooks disabled
   - Integration tests for hook invocation during build workflow

   Depends on Story 2.4
   Story points: 5

   - Files affected: `tapps_agents/simple_mode/orchestrators/base.py`

   - Tests required: Integration tests in `tests/integration/hooks/` for workflow hook invocation

   - GitHub Issue: TBD

6. **Story 2.6: Session lifecycle hooks**
**Execution status:** failed

   **Ref ID:** ENH-002-S6  
   **Priority:** 0  
   **Points:** 5  

   SessionStart on first CLI command, SessionEnd on exit via atexit; session tracking with session ID and optional log/state files.

   Acceptance criteria:
   - SessionStart fired on first tapps-agents command in a process; SessionEnd registered with atexit
   - Session ID (e.g. UUID) generated at start; available as TAPPS_SESSION_ID in hooks
   - Optional session log/state under `.tapps-agents/sessions/` when configured
   - CLI main entry point integrates session start; atexit triggers SessionEnd
   - Unit tests for session creation and atexit registration; integration test for SessionStart/End

   Depends on Story 2.4
   Story points: 5

   - Files affected: `tapps_agents/session/manager.py`, `tapps_agents/cli/main.py`

   - Tests required: Unit tests in `tests/unit/session/test_manager.py`; integration test for CLI session lifecycle

   - GitHub Issue: TBD

7. **Story 2.7: Hook templates and init integration**
**Execution status:** failed

   **Ref ID:** ENH-002-S7  
   **Priority:** 1  
   **Points:** 3  

   Provide 10+ hook templates and add `tapps-agents init --hooks` to create default hooks.yaml and context directory.

   Acceptance criteria:
   - At least 10 template YAML files in `tapps_agents/resources/hooks/templates/` (e.g. auto-format-python, auto-format-js, quality-gate, add-project-context, show-beads-ready, update-docs-on-complete, notify-on-complete, git-commit-check, security-scan-on-edit, test-on-edit)
   - `tapps-agents init --hooks` creates `.tapps-agents/hooks.yaml` from templates (all disabled) and `.tapps-agents/context/` with template files
   - Standard `tapps-agents init` creates minimal empty hooks.yaml and does not enable hooks
   - Unit test for init with --hooks producing expected files

   Depends on Story 2.1
   Story points: 3

   - Files affected: `tapps_agents/resources/hooks/templates/*.yaml`, `tapps_agents/core/init_project.py`, `tapps_agents/core/init_project.py` (or equivalent init module)

   - Tests required: Unit/integration tests for init --hooks output

   - GitHub Issue: TBD

### Phase 3: Beads Hydration (2 weeks, 4 stories, 16 points)

8. **Story 2.8: Task spec schema and loader**
**Execution status:** failed

   **Ref ID:** ENH-002-S8  
   **Priority:** 0  
   **Points:** 3  

   Load and save task specification YAML files from `.tapps-agents/task-specs/` with validation (id, title, type, priority, story_points, epic, dependencies, status, workflow, files, tests).

   Acceptance criteria:
   - Schema supports fields: id, title, description, type (story/epic/task), priority, story_points, epic, dependencies, github_issue, beads_issue, status, workflow, files, tests
   - Loader scans task-specs directory and parses valid YAML; validation errors reported with file/field
   - Save updates existing spec file or creates new file with naming convention (e.g. epic-id-story-id.yaml)
   - Unit tests for load, save, and validation

   Depends on: (none)
   Story points: 3

   - Files affected: `tapps_agents/beads/specs.py`

   - Tests required: Unit tests in `tests/unit/beads/test_specs.py`

   - GitHub Issue: TBD

9. **Story 2.9: Hydration engine**
**Execution status:** failed

   **Ref ID:** ENH-002-S9  
   **Priority:** 0  
   **Points:** 5  

   Hydrate: create Beads issues from task specs (bd create, store beads_issue id); Dehydrate: update specs from Beads (bd list --json); recreate dependency graph (bd dep add).

   Acceptance criteria:
   - hydrate_to_beads creates Beads issues for specs without beads_issue; updates spec with new id; recreates dependencies via bd dep add
   - dehydrate_from_beads updates spec files with current status from Beads
   - Handles missing bd gracefully (log, no crash); optional dry-run
   - Unit tests with mocked bd; integration test with real bd when available

   Depends on Story 2.8
   Story points: 5

   - Files affected: `tapps_agents/beads/hydration.py`

   - Tests required: Unit tests in `tests/unit/beads/test_hydration.py`; integration test for multi-session hydration/dehydration

   - GitHub Issue: TBD

10. **Story 2.10: Task management CLI**
**Execution status:** failed

    **Ref ID:** ENH-002-S10  
    **Priority:** 0  
    **Points:** 5  

    Implement CLI commands: task create, list, show, update, close, hydrate, dehydrate, run (run workflow from task spec).

    Acceptance criteria:
    - `tapps-agents task create <id> --title "..." [--workflow build]` creates task spec and optionally Beads issue
    - `tapps-agents task list [--status todo|in-progress|done]` lists specs with status
    - `tapps-agents task show <id>` shows spec and Beads status
    - `tapps-agents task update <id> --status in-progress`, `task close <id>`
    - `tapps-agents task hydrate [--force]`, `task dehydrate`
    - `tapps-agents task run <id>` loads spec and runs appropriate workflow, updates spec on completion
    - All commands have help and error handling; CLI tests for each command

    Depends on Story 2.8. Depends on Story 2.9.
    Story points: 5

    - Files affected: `tapps_agents/cli/commands/task.py`

    - Tests required: CLI tests for each command in `tests/integration/cli/` or `tests/unit/cli/`

    - GitHub Issue: TBD

11. **Story 2.11: SessionStart/End hydration integration**
**Execution status:** failed

    **Ref ID:** ENH-002-S11  
    **Priority:** 0  
    **Points:** 3  

    On SessionStart call hydrate (and optionally show ready tasks); on SessionEnd call dehydrate and log hydration report.

    Acceptance criteria:
    - SessionStart triggers hydrate_to_beads when Beads and task-specs are configured; optional "bd ready" output
    - SessionEnd triggers dehydrate_from_beads and logs short hydration report (created/updated counts)
    - Configurable enable/disable for hydration in session lifecycle
    - Integration test for session lifecycle with hydration/dehydration

    Depends on Story 2.6. Depends on Story 2.9.
    Story points: 3

    - Files affected: `tapps_agents/session/manager.py`

    - Tests required: Integration test in `tests/integration/session/` or `tests/integration/beads/`

    - GitHub Issue: TBD

### Phase 4: Documentation (1 week, 4 stories, 8 points)

12. **Story 2.12: Hooks guide documentation**
**Execution status:** failed

    **Ref ID:** ENH-002-S12  
    **Priority:** 1  
    **Points:** 2  

    Write complete hooks guide: what hooks are, the 5 events, configuration, env vars, use cases, templates, troubleshooting.

    Acceptance criteria:
    - docs/HOOKS_GUIDE.md created with sections: overview, 5 events (when/use cases/env vars), configuration (hooks.yaml and config.yaml), environment variables reference, common use cases, template library, troubleshooting, security best practices
    - Examples for at least UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, WorkflowComplete
    - Review pass for clarity and accuracy

    Depends on Story 2.5. Depends on Story 2.6. Depends on Story 2.7.
    Story points: 2

    - Files affected: `docs/HOOKS_GUIDE.md`

    - Tests required: Doc build/lint if applicable; manual review

    - GitHub Issue: TBD

13. **Story 2.13: Task management documentation**
**Execution status:** failed

    **Ref ID:** ENH-002-S13  
    **Priority:** 1  
    **Points:** 2  

    Write task management and hydration guide: task specs, hydration pattern, multi-session workflows, CLI reference.

    Acceptance criteria:
    - docs/TASK_MANAGEMENT_GUIDE.md created with: task spec format, .tapps-agents/task-specs/, hydration/dehydration flow, multi-session workflows, task CLI reference (create, list, show, update, close, hydrate, dehydrate, run), best practices
    - Examples for creating specs and running hydrate/dehydrate
    - Cross-links to HOOKS_GUIDE and BEADS_INTEGRATION

    Depends on Story 2.10. Depends on Story 2.11.
    Story points: 2

    - Files affected: `docs/TASK_MANAGEMENT_GUIDE.md`

    - Tests required: Doc review

    - GitHub Issue: TBD

14. **Story 2.14: Update existing documentation**
**Execution status:** failed

    **Ref ID:** ENH-002-S14  
    **Priority:** 1  
    **Points:** 1  

    Add hooks and task management sections to README, docs/README.md, CLAUDE.md, docs/CONFIGURATION.md; update quick start.

    Acceptance criteria:
    - README.md and docs/README.md include short "Hooks" and "Task management / multi-session" sections with links to HOOKS_GUIDE and TASK_MANAGEMENT_GUIDE
    - CLAUDE.md updated with hooks overview and task management commands
    - docs/CONFIGURATION.md documents hooks and session/hydration config options
    - Quick start mentions optional init --hooks and task commands

    Depends on Story 2.12. Depends on Story 2.13.
    Story points: 1

    - Files affected: `README.md`, `docs/README.md`, `CLAUDE.md`, `docs/CONFIGURATION.md`

    - Tests required: Doc review

    - GitHub Issue: TBD

15. **Story 2.15: Integration tests and examples**
**Execution status:** failed

    **Ref ID:** ENH-002-S15  
    **Priority:** 1  
    **Points:** 3  

    Add E2E hook tests, example projects with hooks, and CI/CD integration for hook and task flows.

    Acceptance criteria:
    - tests/integration/hooks/ contains E2E tests: workflow with UserPromptSubmit/PostToolUse/WorkflowComplete, session lifecycle with SessionStart/SessionEnd
    - examples/hooks/ contains at least one example project with hooks.yaml and context files and README
    - CI runs new integration tests; docs or comments describe how to run examples
    - Hooks module coverage ≥85%

    Depends on Story 2.5. Depends on Story 2.6. Depends on Story 2.7.
    Story points: 3

    - Files affected: `tests/integration/hooks/`, `examples/hooks/`, CI config (e.g. GitHub Actions)

    - Tests required: New integration and E2E tests; coverage report for hooks

    - GitHub Issue: TBD

---

## Execution Notes

### Prerequisites

- Beads (bd) CLI available when using hydration/task commands
- Python 3.10+; PyYAML (existing dependency)
- No new external dependencies for hook execution (subprocess)

### Technical Decisions

- Hooks disabled by default; opt-in via config for backward compatibility
- Hook timeout default 30s, configurable; fail_on_error per-hook
- Task specs YAML-only; naming `<epic-id>-<story-id>.yaml`
- Session ID is UUID; session log/state optional

### Risk Mitigation

- Hook execution: document security (review scripts, no remote execution in v3.6.0)
- Hydration failures: log and continue; support --force and --dry-run
- SessionEnd: atexit + optional periodic save; document manual dehydrate if session crashes

---

## Definition of Done

- [ ] All 15 stories implemented and accepted
- [ ] Unit tests for hooks and beads modules ≥85% coverage
- [ ] Integration tests for workflow hooks, session lifecycle, and hydration
- [ ] docs/HOOKS_GUIDE.md and docs/TASK_MANAGEMENT_GUIDE.md complete
- [ ] README, CLAUDE.md, CONFIGURATION.md updated
- [ ] No regressions in existing workflows; hooks opt-in
- [ ] Quality threshold ≥75 for framework code; public APIs documented

---

## Status

Ready for Implementation

---

## Summary

| Phase              | Duration | Stories | Points |
|--------------------|----------|---------|--------|
| Phase 1: Foundation | 2 weeks  | 4       | 13     |
| Phase 2: Integration | 2 weeks | 3     | 13     |
| Phase 3: Beads Hydration | 2 weeks | 4 | 16   |
| Phase 4: Documentation | 1 week  | 4     | 8      |
| **Total**          | **7 weeks** | **15** | **50** |

**Target Release:** v3.6.0 (Q1 2026)  
**Epic ID:** ENH-002  
**Source PRD:** `.tapps-agents/context/enh-002-prd.md`
