# PRD: TappsCodingAgents Critical Enhancements

**Document Type**: Product Requirements Document (PRD)
**Version**: 1.0
**Status**: Draft
**Date**: 2026-02-03
**Author**: Claude Sonnet 4.5
**Epic ID**: ENH-002

---

## Executive Summary

This PRD proposes critical enhancements to TappsCodingAgents based on competitive analysis of Claude Code's 2026 features (Tasks, Hooks, Subagents) and current Beads integration gaps.

**Focus**: Add hook system, improve Beads persistence patterns, and enhance multi-session workflows.

**Business Value**:
- **30-50% reduction in manual workflow steps** (hooks automation)
- **Zero context loss across sessions** (improved Beads hydration)
- **Better developer experience** (matches Claude Code capabilities)
- **Framework competitiveness** (parity with Claude Code + unique TappsCodingAgents strengths)

**Target Release**: v3.6.0 (Q1 2026)

---

## Problem Statement

### Current Gaps

Based on [Claude Code Comprehensive Review](./claude-code-comprehensive-review.md) and [Beads vs Claude Tasks](./tapps-beads-vs-claude-tasks.md), TappsCodingAgents lacks:

**1. Hook System** (Critical)
- ❌ No equivalent to Claude Code's UserPromptSubmit, PreToolUse, PostToolUse hooks
- ❌ No automatic code formatting after edits
- ❌ No automatic context injection before workflows
- ❌ No session lifecycle automation
- **Impact**: Users must manually format code, manually add context, manually run quality checks

**2. Beads Hydration Pattern** (Critical)
- ⚠️ Basic Beads integration exists but lacks hydration pattern
- ❌ Tasks don't automatically recreate from specification files
- ❌ No session handoff for multi-session work
- **Impact**: Users lose context between sessions, must manually recreate state

**3. Multi-Session Workflow Support** (High Priority)
- ⚠️ Workflows are session-scoped, don't persist across days
- ❌ No automatic checkpoint save/restore beyond resume
- ❌ Limited support for long-horizon tasks (weeks/months)
- **Impact**: Multi-day epics require manual state management

### Competitive Disadvantage

**Claude Code (2026)** has:
- ✅ 10 hook events (UserPromptSubmit, PostToolUse, SessionStart, etc.)
- ✅ Persistent subagent configurations
- ✅ Task hydration from specs
- ✅ Session lifecycle hooks

**TappsCodingAgents** has:
- ✅ Superior workflow orchestration (7-9 steps with quality gates)
- ✅ Expert system with adaptive learning
- ✅ Beads integration (but incomplete)
- ❌ No hook system
- ❌ Incomplete multi-session support

**Gap**: TappsCodingAgents loses on **automation** and **persistence**, wins on **workflow quality** and **intelligence**.

---

## Goals & Non-Goals

### Goals (Critical Enhancements Only)

**G1: Hook System** (Must Have)
- Implement 5 core hook events: UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, WorkflowComplete
- Support shell command execution with environment variables
- Configuration via `.tapps-agents/hooks.yaml`
- Compatible with both CLI and Cursor modes

**G2: Beads Hydration Pattern** (Must Have)
- Tasks recreate automatically from `.tapps-agents/task-specs/` on session start
- Workflow state includes Beads issue IDs
- Session handoff preserves full context
- Multi-session workflows "just work"

**G3: Auto-Formatting Integration** (Must Have)
- PostToolUse hooks for code formatting (black, prettier, etc.)
- Quality gate hooks (auto-run reviewer after edits)
- Configurable per project

**G4: Context Injection** (Must Have)
- UserPromptSubmit hook for automatic context addition
- Project-specific context files (`.tapps-agents/context/`)
- Expert consultation hints before workflows

**G5: Session Lifecycle** (Should Have)
- SessionStart: Load environment, show Beads ready tasks
- SessionEnd: Save state, log activity, cleanup
- WorkflowComplete: Update Beads, run post-workflow hooks

### Non-Goals (Out of Scope for v3.6.0)

**NG1: Full Claude Code Parity**
- Not implementing all 10 hook events (only 5 critical ones)
- Not implementing subagent system (TappsCodingAgents has agents already)
- Not implementing Task tool (Beads serves that purpose)

**NG2: Breaking Changes**
- No changes to existing workflow orchestration
- No changes to Beads required/optional behavior
- Hooks are optional (disabled by default for backward compatibility)

**NG3: UI/Dashboard**
- No web UI for hook configuration (use YAML files)
- No visual task board (use `bd ready` or community tools)
- No IDE plugin (focus on CLI + Cursor Skills)

**NG4: Advanced Features**
- Not implementing hook conditions/filters beyond tool matchers (later)
- Not implementing hook marketplace (later)
- Not implementing remote hooks (security concerns)

---

## Requirements

### Critical Requirements

#### CR1: Hook System Architecture

**CR1.1: Hook Configuration**
- **File**: `.tapps-agents/hooks.yaml`
- **Format**: YAML with hook events, matchers, and commands
- **Schema**:
  ```yaml
  hooks:
    UserPromptSubmit:
      - name: "Add project context"
        command: "cat .tapps-agents/context/project.md"
        enabled: true
    PostToolUse:
      - name: "Auto-format Python"
        matcher: "Write|Edit"
        command: "black {file_path}"
        file_patterns: ["*.py"]
        enabled: true
    SessionStart:
      - name: "Show ready tasks"
        command: "bd ready"
        enabled: true
    SessionEnd:
      - name: "Save session log"
        command: "./scripts/save-session.sh"
        enabled: true
    WorkflowComplete:
      - name: "Update documentation"
        command: "./scripts/update-docs.sh {workflow_type}"
        enabled: true
  ```

**CR1.2: Environment Variables**
- `$TAPPS_FILE_PATH`: File path for Write/Edit operations
- `$TAPPS_FILE_PATHS`: Space-separated list of affected files
- `$TAPPS_TOOL_NAME`: Tool that was used (Write, Edit, Read, etc.)
- `$TAPPS_PROMPT`: User's submitted prompt (UserPromptSubmit)
- `$TAPPS_WORKFLOW_TYPE`: Workflow type (build, fix, review, etc.)
- `$TAPPS_WORKFLOW_ID`: Unique workflow run ID
- `$TAPPS_PROJECT_ROOT`: Project root directory
- `$TAPPS_BEADS_ISSUE_ID`: Current Beads issue ID (if any)

**CR1.3: Hook Execution**
- Hooks run synchronously (block workflow)
- Stdout captured and added to context (UserPromptSubmit) or logged (others)
- Stderr logged as warnings
- Non-zero exit code logs error but doesn't fail workflow (unless critical)
- Timeout: 30 seconds default, configurable

**CR1.4: Hook Events**

| Event | When | Use Cases |
|-------|------|-----------|
| `UserPromptSubmit` | Before workflow starts | Add context, validate prompt, suggest workflows |
| `PostToolUse` | After Write/Edit completes | Auto-format, quality check, update docs |
| `SessionStart` | CLI/Cursor session begins | Load env, show tasks, initialize |
| `SessionEnd` | Session ends | Save state, cleanup, log |
| `WorkflowComplete` | After workflow success/fail | Update Beads, notify, post-process |

**CR1.5: Implementation**
- New module: `tapps_agents/hooks/`
- Submodules:
  - `hooks/config.py`: Load and validate hooks.yaml
  - `hooks/executor.py`: Execute hooks with env vars
  - `hooks/events.py`: Hook event definitions
  - `hooks/manager.py`: Hook lifecycle management
- Integration points:
  - `simple_mode/orchestrators/base.py`: Call hooks in base orchestrator
  - `workflow/executor.py`: Session lifecycle hooks
  - `cli/main.py`: SessionStart/SessionEnd

**CR1.6: Configuration Management**
- Default hooks disabled (opt-in for backward compatibility)
- Enable globally in `.tapps-agents/config.yaml`:
  ```yaml
  hooks:
    enabled: true
    config_file: ".tapps-agents/hooks.yaml"  # Default location
    timeout: 30  # Seconds
    fail_on_error: false  # Continue on hook failure
  ```
- Per-hook enable/disable in `hooks.yaml`

---

#### CR2: Beads Hydration Pattern

**CR2.1: Task Specification Files**
- **Location**: `.tapps-agents/task-specs/`
- **Format**: YAML files with task definitions
- **Naming**: `<epic-id>-<story-id>.yaml` (e.g., `enh-002-s1.yaml`)
- **Schema**:
  ```yaml
  task:
    id: "enh-002-s1"
    title: "Implement hook system"
    description: "Add 5 core hook events with YAML configuration"
    type: "story"  # story, epic, task
    priority: 0
    story_points: 5
    epic: "enh-002"
    dependencies: []
    github_issue: 25
    beads_issue: "bd-a1b2c3"  # Populated after creation
    status: "todo"  # todo, in-progress, done, blocked
    workflow: "build"  # build, fix, review, test, full
    files:
      - "tapps_agents/hooks/"
    tests:
      - "tests/unit/hooks/"
  ```

**CR2.2: Hydration on SessionStart**
- When session starts:
  1. Scan `.tapps-agents/task-specs/` for YAML files
  2. For each file with `status: todo`:
     - Check if Beads issue exists (`beads_issue` field)
     - If not exists: Create with `bd create`, store `beads_issue` ID
     - If exists: Verify with `bd show <id>`
  3. Recreate dependency graph with `bd dep add`
  4. Display ready tasks (`bd ready`)
  5. Log hydration report

**CR2.3: Dehydration on SessionEnd**
- When session ends:
  1. Query Beads for all issues (`bd list --json`)
  2. Update task spec files with current status
  3. Save workflow state to specs
  4. Commit changes (if auto-commit enabled)

**CR2.4: Workflow Integration**
- When `@simple-mode *build` starts:
  1. Check if prompt references task spec ID (e.g., "ENH-002-S1")
  2. Load task spec if referenced
  3. Use spec to populate workflow context
  4. Create/reuse Beads issue from spec
  5. Update spec on workflow complete

**CR2.5: Implementation**
- New module: `tapps_agents/beads/hydration.py`
- Functions:
  - `load_task_specs()`: Load all specs from directory
  - `hydrate_to_beads()`: Create/update Beads issues from specs
  - `dehydrate_from_beads()`: Update specs from Beads status
  - `find_spec_by_id()`: Locate spec file by task ID
- Integration points:
  - SessionStart hook: Call `hydrate_to_beads()`
  - SessionEnd hook: Call `dehydrate_from_beads()`
  - `simple_mode/orchestrators/`: Load spec if referenced

**CR2.6: CLI Commands**
- `tapps-agents task create <id> --title "..." --workflow build`
  - Creates task spec YAML file
  - Optionally creates Beads issue immediately
- `tapps-agents task hydrate`
  - Manually trigger hydration (SessionStart equivalent)
- `tapps-agents task dehydrate`
  - Manually trigger dehydration (SessionEnd equivalent)
- `tapps-agents task list`
  - List all task specs with status
- `tapps-agents task show <id>`
  - Show task spec details + Beads status

---

#### CR3: Auto-Formatting Integration

**CR3.1: Default Formatters**
- Python: `black {file_path}` (if black installed)
- JavaScript/TypeScript: `prettier --write {file_path}` (if prettier installed)
- JSON: `jq '.' {file_path} > {file_path}.tmp && mv {file_path}.tmp {file_path}`
- YAML: `yamllint {file_path}` (validation only, no auto-fix)

**CR3.2: Configuration**
- Template hooks in `tapps-agents init`:
  ```yaml
  hooks:
    PostToolUse:
      - name: "Auto-format Python"
        matcher: "Write|Edit"
        command: "black {file_path}"
        file_patterns: ["*.py"]
        enabled: false  # User must enable
      - name: "Auto-format JavaScript"
        matcher: "Write|Edit"
        command: "prettier --write {file_path}"
        file_patterns: ["*.js", "*.ts", "*.jsx", "*.tsx"]
        enabled: false
  ```

**CR3.3: Quality Gate Hook**
- Template quality gate hook:
  ```yaml
  hooks:
    PostToolUse:
      - name: "Quality gate check"
        matcher: "Write|Edit"
        command: "tapps-agents reviewer score {file_path} --threshold 70"
        file_patterns: ["*.py"]
        enabled: false
        fail_on_error: true  # Fail workflow if score < 70
  ```

**CR3.4: User Opt-In**
- Init creates disabled hooks (templates)
- User edits `hooks.yaml` to enable
- Documentation explains how to configure

---

#### CR4: Context Injection

**CR4.1: Context Files**
- **Location**: `.tapps-agents/context/`
- **Files**:
  - `project.md`: Project overview, architecture, conventions
  - `current-sprint.md`: Current sprint goals, in-progress work
  - `domain-knowledge.md`: Domain-specific info (business rules, etc.)
  - `active-tasks.txt`: Output of `bd ready` (auto-generated)

**CR4.2: UserPromptSubmit Hook**
- Template hook in `tapps-agents init`:
  ```yaml
  hooks:
    UserPromptSubmit:
      - name: "Add project context"
        command: "cat .tapps-agents/context/project.md"
        enabled: false  # User must enable
      - name: "Show ready tasks"
        command: "bd ready"
        enabled: false
      - name: "Add current sprint context"
        command: "cat .tapps-agents/context/current-sprint.md"
        enabled: false
  ```

**CR4.3: Dynamic Context Generation**
- Hook script example (`scripts/inject-context.sh`):
  ```bash
  #!/bin/bash
  PROMPT="$TAPPS_PROMPT"

  # Detect domain from prompt
  if echo "$PROMPT" | grep -iq "auth\|security\|oauth"; then
      echo "📚 Security Expert Context:"
      cat .tapps-agents/knowledge/security/oauth-guide.md
  fi

  if echo "$PROMPT" | grep -iq "test\|coverage"; then
      echo "📚 Testing Expert Context:"
      cat .tapps-agents/knowledge/testing/best-practices.md
  fi
  ```

**CR4.4: Implementation**
- Context files created by `tapps-agents init` (templates)
- UserPromptSubmit hook adds file contents to LLM context
- LLM sees context before generating workflow plan

---

#### CR5: Session Lifecycle

**CR5.1: SessionStart Hook**
- Triggered when:
  - CLI: First `tapps-agents` command in new terminal session
  - Cursor: First `@simple-mode` invocation in new Cursor session
- Use cases:
  - Load environment variables
  - Display `bd ready` tasks
  - Show project status
  - Initialize agent state

**CR5.2: SessionEnd Hook**
- Triggered when:
  - CLI: Terminal session ends (atexit handler)
  - Cursor: Cursor closes or session times out
- Use cases:
  - Save workflow state
  - Dehydrate Beads (update task specs)
  - Cleanup temp files
  - Log session summary

**CR5.3: WorkflowComplete Hook**
- Triggered when:
  - Any workflow completes (success or failure)
  - After quality gates pass/fail
  - After tests run
- Use cases:
  - Update Beads issue status
  - Close GitHub issue (if "Closes #N")
  - Notify user/team
  - Update documentation
  - Run post-workflow checks

**CR5.4: Session Tracking**
- Session ID: UUID generated on SessionStart
- Session log: `.tapps-agents/sessions/<session-id>.log`
- Session state: `.tapps-agents/sessions/<session-id>.json`
- Contains:
  - Start/end time
  - Workflows executed
  - Beads issues created/closed
  - Files modified
  - Errors/warnings

**CR5.5: Implementation**
- New module: `tapps_agents/session/`
- Submodules:
  - `session/manager.py`: Session lifecycle management
  - `session/tracker.py`: Track session activity
  - `session/state.py`: Session state persistence
- Integration points:
  - `cli/main.py`: SessionStart on first command, SessionEnd on exit
  - Cursor: SessionStart on skill load (complex, may defer)
  - `workflow/executor.py`: WorkflowComplete after execute

---

### High Priority Requirements (Should Have)

#### HP1: Hook Templates and Documentation

**HP1.1: Common Hook Templates**
- Provide 10+ common hook templates in `tapps_agents/resources/hooks/templates/`:
  - `auto-format-python.yaml`
  - `auto-format-js.yaml`
  - `quality-gate.yaml`
  - `add-project-context.yaml`
  - `show-beads-ready.yaml`
  - `update-docs-on-complete.yaml`
  - `notify-on-complete.yaml`
  - `git-commit-check.yaml`
  - `security-scan-on-edit.yaml`
  - `test-on-edit.yaml`

**HP1.2: Documentation**
- New guide: `docs/HOOKS_GUIDE.md`
- Covers:
  - What are hooks?
  - Available hook events
  - How to configure hooks
  - Environment variables
  - Common use cases
  - Template library
  - Troubleshooting

**HP1.3: Init Integration**
- `tapps-agents init --hooks`
  - Creates `.tapps-agents/hooks.yaml` with all templates (disabled)
  - Creates `.tapps-agents/context/` with template files
  - Prints usage guide
- `tapps-agents init` (standard)
  - Creates minimal hooks.yaml (empty)
  - Does not enable hooks (backward compatible)

---

#### HP2: Enhanced Beads Commands

**HP2.1: Task Management CLI**
- `tapps-agents task create <id> --title "..." [options]`
- `tapps-agents task list [--status todo|in-progress|done]`
- `tapps-agents task show <id>`
- `tapps-agents task update <id> --status in-progress`
- `tapps-agents task close <id>`
- `tapps-agents task hydrate [--force]`
- `tapps-agents task dehydrate`

**HP2.2: Epic Management**
- `tapps-agents epic create <id> --title "..."`
- `tapps-agents epic add-story <epic-id> <story-id> --title "..." [--depends-on story-id]`
- `tapps-agents epic status <id>`
- `tapps-agents epic hydrate <id>`

**HP2.3: Workflow from Task Spec**
- `tapps-agents task run <id>`
  - Loads task spec
  - Runs appropriate workflow (build, fix, etc.)
  - Updates task spec on completion
  - Closes Beads issue

---

#### HP3: Improved Multi-Session Support

**HP3.1: Resume from Last Session**
- `tapps-agents resume`
  - Shows last session summary
  - Displays in-progress workflows
  - Lists ready tasks from Beads
  - Suggests next action

**HP3.2: Session Handoff**
- When workflow is interrupted (user exits mid-workflow):
  - Save checkpoint with full context
  - Save Beads issue ID
  - Save current workflow step
- On next session:
  - Detect interrupted workflow
  - Ask if user wants to resume
  - Resume from last checkpoint with full context

**HP3.3: Long-Horizon Workflow State**
- Workflows can span multiple sessions
- State saved to `.tapps-agents/workflow-state/<workflow-id>/`
- Includes:
  - Current step
  - Beads issue ID
  - GitHub issue number
  - File changes so far
  - Quality scores
  - Test results
  - Next steps

---

### Medium Priority Requirements (Could Have)

#### MP1: Hook Conditions and Filters

**MP1.1: Conditional Hooks**
- Add `condition` field to hooks:
  ```yaml
  hooks:
    PostToolUse:
      - name: "Format only Python files"
        command: "black {file_path}"
        condition:
          file_pattern: "*.py"
          tool: "Write|Edit"
          workflow_type: "build|fix"  # Only during build/fix workflows
  ```

**MP1.2: Advanced Matchers**
- File size limits: `max_file_size: 100KB`
- Directory filters: `directory: "src/"`
- Exclude patterns: `exclude: ["node_modules/**", "venv/**"]`

---

#### MP2: Hook Marketplace / Community Hooks

**MP2.1: Share Hooks**
- Community repository: `.tapps-agents/community-hooks/`
- Download hooks: `tapps-agents hooks install <hook-name>`
- Examples:
  - `tapps-agents hooks install prettier-on-save`
  - `tapps-agents hooks install security-scan`
  - `tapps-agents hooks install slack-notify`

---

#### MP3: Remote Hook Execution

**MP3.1: HTTP Webhooks**
- POST hook events to remote URL
- Use cases: Slack notifications, CI/CD triggers
- Security: API key authentication, HTTPS only
- Configuration:
  ```yaml
  hooks:
    WorkflowComplete:
      - name: "Notify Slack"
        type: "webhook"
        url: "https://hooks.slack.com/services/..."
        payload:
          text: "Workflow {workflow_type} completed: {workflow_id}"
  ```

---

## Success Metrics

### Critical Success Metrics (Must Achieve)

**SM1: Adoption**
- **Target**: 60% of users enable at least 1 hook by v3.7.0
- **Measure**: Track `hooks.enabled: true` in config files (anonymized telemetry)

**SM2: Automation Reduction**
- **Target**: 30% reduction in manual formatting steps
- **Measure**: Survey users on time spent on formatting before/after

**SM3: Multi-Session Success**
- **Target**: Zero reported context loss across sessions with hydration
- **Measure**: GitHub issues tagged "context-loss" = 0

**SM4: Feature Parity**
- **Target**: TappsCodingAgents has equivalent automation to Claude Code hooks
- **Measure**: Checklist of 5 core hook events implemented ✅

### Key Performance Indicators (KPIs)

**KPI1: Hook Execution Time**
- **Target**: <500ms per hook on average
- **Acceptable**: <2s for complex hooks
- **Unacceptable**: >5s (timeout)

**KPI2: Session Hydration Time**
- **Target**: <3s to hydrate 50 tasks from specs
- **Acceptable**: <10s for 200 tasks
- **Unacceptable**: >30s (blocks session start)

**KPI3: Hook Reliability**
- **Target**: 99% hook success rate (no crashes)
- **Acceptable**: 95%
- **Unacceptable**: <90%

**KPI4: Documentation Quality**
- **Target**: 90% of users can configure hooks without support
- **Measure**: Support tickets tagged "hooks-help"

---

## Implementation Plan

### Phase 1: Foundation (2 weeks)

**Epic**: ENH-002-P1 - Hook System Foundation

**Stories**:
1. **ENH-002-S1**: Hook configuration schema and loader (3 points)
   - Files: `tapps_agents/hooks/config.py`
   - Load/validate `hooks.yaml`
   - Tests: Schema validation, error handling

2. **ENH-002-S2**: Hook executor with environment variables (5 points)
   - Files: `tapps_agents/hooks/executor.py`
   - Execute shell commands with env vars
   - Capture stdout/stderr
   - Timeout handling
   - Tests: Execution, timeout, error handling

3. **ENH-002-S3**: Hook event definitions (2 points)
   - Files: `tapps_agents/hooks/events.py`
   - Define 5 hook events
   - Event data structures
   - Tests: Event creation, serialization

4. **ENH-002-S4**: Hook manager (3 points)
   - Files: `tapps_agents/hooks/manager.py`
   - Hook lifecycle management
   - Event triggering
   - Tests: Hook registration, triggering

**Milestone**: Hook system can execute UserPromptSubmit and PostToolUse hooks

---

### Phase 2: Integration (2 weeks)

**Epic**: ENH-002-P2 - Workflow Integration

**Stories**:
5. **ENH-002-S5**: Integrate hooks into base orchestrator (5 points)
   - Files: `tapps_agents/simple_mode/orchestrators/base.py`
   - Call UserPromptSubmit before workflow
   - Call PostToolUse after implementer
   - Call WorkflowComplete after workflow
   - Tests: Hook invocation in workflows

6. **ENH-002-S6**: Session lifecycle hooks (5 points)
   - Files: `tapps_agents/session/manager.py`, `cli/main.py`
   - SessionStart on CLI first command
   - SessionEnd on exit (atexit)
   - Session tracking
   - Tests: Session creation, cleanup

7. **ENH-002-S7**: Hook templates and init integration (3 points)
   - Files: `tapps_agents/resources/hooks/templates/*.yaml`, `core/init_project.py`
   - Create 10 hook templates
   - Update `tapps-agents init --hooks`
   - Tests: Init creates correct files

**Milestone**: Hooks fully integrated into all workflows

---

### Phase 3: Beads Hydration (2 weeks)

**Epic**: ENH-002-P3 - Multi-Session Support

**Stories**:
8. **ENH-002-S8**: Task spec schema and loader (3 points)
   - Files: `tapps_agents/beads/specs.py`
   - Load/save task specs from YAML
   - Schema validation
   - Tests: Load, save, validation

9. **ENH-002-S9**: Hydration engine (5 points)
   - Files: `tapps_agents/beads/hydration.py`
   - Hydrate: Create Beads issues from specs
   - Dehydrate: Update specs from Beads
   - Dependency graph recreation
   - Tests: Hydration, dehydration, dependencies

10. **ENH-002-S10**: Task management CLI (5 points)
    - Files: `tapps_agents/cli/commands/task.py`
    - `task create`, `list`, `show`, `update`, `close`
    - `task hydrate`, `dehydrate`
    - `task run <id>`
    - Tests: All commands

11. **ENH-002-S11**: SessionStart/End hydration integration (3 points)
    - Files: `tapps_agents/session/manager.py`
    - Call hydrate on SessionStart
    - Call dehydrate on SessionEnd
    - Log hydration report
    - Tests: Session lifecycle

**Milestone**: Tasks persist across sessions via hydration

---

### Phase 4: Documentation and Polish (1 week)

**Epic**: ENH-002-P4 - Documentation and Release

**Stories**:
12. **ENH-002-S12**: Hooks guide documentation (2 points)
    - Files: `docs/HOOKS_GUIDE.md`
    - Complete guide with examples
    - Template library reference
    - Troubleshooting section

13. **ENH-002-S13**: Task management documentation (2 points)
    - Files: `docs/TASK_MANAGEMENT_GUIDE.md`
    - Task specs guide
    - Hydration pattern explained
    - Multi-session workflows

14. **ENH-002-S14**: Update existing documentation (1 point)
    - Files: `README.md`, `docs/README.md`, `CLAUDE.md`
    - Add hooks and task management sections
    - Update quick start
    - Update configuration reference

15. **ENH-002-S15**: Integration tests and examples (3 points)
    - Files: `tests/integration/hooks/`, `examples/hooks/`
    - End-to-end hook tests
    - Example projects with hooks
    - CI/CD integration

**Milestone**: v3.6.0 release ready

---

### Timeline Summary

| Phase | Duration | Stories | Total Points |
|-------|----------|---------|--------------|
| Phase 1: Foundation | 2 weeks | 4 | 13 |
| Phase 2: Integration | 2 weeks | 3 | 13 |
| Phase 3: Beads Hydration | 2 weeks | 4 | 16 |
| Phase 4: Documentation | 1 week | 4 | 8 |
| **Total** | **7 weeks** | **15** | **50** |

**Target Release**: v3.6.0 (Q1 2026, approximately 7 weeks from start)

---

## Dependencies

### Technical Dependencies

**TD1: Beads (bd) CLI**
- Required version: ≥1.0.0
- TappsCodingAgents already depends on this
- No changes needed

**TD2: YAML Parser**
- PyYAML already included
- No changes needed

**TD3: Shell Execution**
- subprocess module (stdlib)
- No new dependencies

**TD4: Session Management**
- atexit module (stdlib)
- No new dependencies

### External Dependencies

**ED1: User Shell Scripts**
- Hooks execute user-provided shell scripts
- Users must ensure scripts are available and executable
- Documentation must include shell script best practices

**ED2: Formatter Tools (Optional)**
- black (Python)
- prettier (JavaScript)
- Users install if they want formatting hooks
- TappsCodingAgents provides templates but doesn't require formatters

---

## Risks & Mitigations

### Critical Risks

**R1: Hook Execution Security**
- **Risk**: Hooks execute arbitrary shell commands, security risk
- **Impact**: High (code injection, malicious scripts)
- **Probability**: Medium
- **Mitigation**:
  - Hooks disabled by default (opt-in)
  - Documentation emphasizes security (review scripts before enabling)
  - No remote hook execution in v3.6.0 (defer to later)
  - Sandbox consideration (future enhancement)
  - User education: "Only enable hooks you trust"

**R2: Hook Performance Impact**
- **Risk**: Hooks slow down workflows significantly
- **Impact**: High (user frustration, abandonment)
- **Probability**: Medium
- **Mitigation**:
  - 30-second timeout (configurable)
  - Async hooks (non-blocking) for SessionEnd (future)
  - Performance metrics in hook output (execution time)
  - Documentation: "Keep hooks fast (<500ms)"

**R3: Hydration Failures**
- **Risk**: Task hydration fails, loses Beads state
- **Impact**: High (context loss, duplicate issues)
- **Probability**: Low
- **Mitigation**:
  - Robust error handling (log errors, continue)
  - Rollback on hydration failure (restore previous state)
  - Manual recovery commands (`task hydrate --force`)
  - Hydration dryrun mode (`task hydrate --dry-run`)

**R4: Backward Compatibility**
- **Risk**: Hooks break existing workflows
- **Impact**: High (user disruption)
- **Probability**: Low
- **Mitigation**:
  - Hooks disabled by default (explicit opt-in)
  - No changes to existing orchestrators (only additions)
  - Comprehensive testing (unit + integration)
  - Beta release for testing (v3.6.0-beta)

### Medium Risks

**R5: Hook Configuration Complexity**
- **Risk**: Users find hooks too complex to configure
- **Impact**: Medium (low adoption)
- **Probability**: Medium
- **Mitigation**:
  - Template library (10+ common hooks)
  - `tapps-agents init --hooks` creates working examples
  - Clear documentation with step-by-step guides
  - Video tutorials (post-release)

**R6: Beads Task Spec Conflicts**
- **Risk**: Multiple agents edit task specs simultaneously (merge conflicts)
- **Impact**: Medium (manual conflict resolution)
- **Probability**: Low
- **Mitigation**:
  - Task specs use simple YAML (easy to merge)
  - Beads uses hash-based IDs (conflict-resistant)
  - Documentation: "One agent per task" best practice
  - Git conflict resolution guide in docs

**R7: SessionEnd Hook Unreliability**
- **Risk**: SessionEnd may not trigger (crash, kill signal)
- **Impact**: Medium (state not saved, dehydration skipped)
- **Probability**: Medium
- **Mitigation**:
  - Use atexit for graceful shutdown
  - Periodic auto-save (every N minutes) as backup
  - Manual dehydrate command (`task dehydrate`)
  - Documentation: "Run dehydrate manually if session crashes"

### Low Risks

**R8: Hook Output Noise**
- **Risk**: Hooks produce too much output, clutter logs
- **Impact**: Low (annoying but not blocking)
- **Probability**: Medium
- **Mitigation**:
  - Hooks can set `silent: true` to suppress output
  - Stdout/stderr logged to separate file (`.tapps-agents/logs/hooks.log`)
  - Only errors shown to user by default

---

## Testing Strategy

### Unit Tests

**UT1: Hook System**
- `tests/unit/hooks/test_config.py`: Schema validation, loading
- `tests/unit/hooks/test_executor.py`: Command execution, env vars, timeout
- `tests/unit/hooks/test_events.py`: Event creation, serialization
- `tests/unit/hooks/test_manager.py`: Hook registration, triggering

**UT2: Beads Hydration**
- `tests/unit/beads/test_specs.py`: Task spec loading, saving, validation
- `tests/unit/beads/test_hydration.py`: Hydration, dehydration, dependencies

**UT3: Session Management**
- `tests/unit/session/test_manager.py`: Session lifecycle, tracking
- `tests/unit/session/test_state.py`: State persistence, recovery

**Coverage Target**: ≥85% for new modules

---

### Integration Tests

**IT1: Hook Integration**
- `tests/integration/hooks/test_workflow_hooks.py`
  - UserPromptSubmit adds context to workflow
  - PostToolUse formats code after Write
  - WorkflowComplete updates Beads
- `tests/integration/hooks/test_session_hooks.py`
  - SessionStart hydrates tasks
  - SessionEnd dehydrates tasks

**IT2: Hydration Integration**
- `tests/integration/beads/test_multi_session.py`
  - Create task spec in session 1
  - Hydrate in session 2
  - Task appears in Beads correctly
  - Dependencies preserved

**IT3: End-to-End Workflows**
- `tests/integration/e2e/test_hooks_build_workflow.py`
  - Enable hooks
  - Run `@simple-mode *build`
  - Verify hooks executed
  - Verify code formatted
  - Verify Beads updated
- `tests/integration/e2e/test_task_run.py`
  - Create task spec
  - Run `tapps-agents task run <id>`
  - Verify workflow executed
  - Verify task closed

---

### Manual Testing

**MT1: Hook Configuration**
- Install TappsCodingAgents
- Run `tapps-agents init --hooks`
- Enable auto-format hook
- Run `@simple-mode *build`
- Verify code is formatted

**MT2: Multi-Session Task Management**
- Session 1:
  - Create task spec
  - Start workflow
  - Exit mid-workflow
- Session 2:
  - Verify task hydrated
  - Resume workflow
  - Complete task
  - Verify Beads updated

**MT3: Error Handling**
- Create hook with invalid command
- Verify error logged but workflow continues
- Create hook with timeout
- Verify timeout occurs, workflow continues

---

## Documentation Plan

### New Documentation

**D1: docs/HOOKS_GUIDE.md** (Critical)
- What are hooks?
- Available hook events (5 core events)
- How to configure hooks
- Environment variables reference
- Common use cases (10+ examples)
- Template library
- Troubleshooting
- Security best practices

**D2: docs/TASK_MANAGEMENT_GUIDE.md** (Critical)
- Task specification files
- Hydration pattern explained
- Multi-session workflows
- Task management CLI reference
- Epic management
- Best practices
- Examples

**D3: docs/MULTI_SESSION_WORKFLOWS.md** (High Priority)
- Session lifecycle
- State persistence
- Resuming interrupted workflows
- Long-horizon task management
- Integration with Beads
- Best practices for multi-day work

**D4: Hook Template Library** (High Priority)
- `tapps_agents/resources/hooks/templates/README.md`
- Description of each template
- How to use templates
- Customization guide

---

### Updated Documentation

**D5: README.md**
- Add "Hooks System" section
- Add "Multi-Session Support" section
- Update feature list
- Update quick start (mention hooks)

**D6: docs/CONFIGURATION.md**
- Add `hooks` section
- Add `session` section
- Environment variables for hooks

**D7: CLAUDE.md**
- Add hooks overview
- Add task management commands
- Update command reference

**D8: docs/BEADS_INTEGRATION.md**
- Add hydration pattern section
- Add task spec documentation
- Update examples

---

## Rollout Plan

### Phase 1: Internal Alpha (Week 1)

**Audience**: TappsCodingAgents core team only

**Goal**: Validate foundation, catch critical bugs

**Activities**:
- Deploy to internal dev environments
- Run full test suite
- Manual testing with real workflows
- Performance benchmarking
- Security review

**Success Criteria**:
- All unit tests pass (≥85% coverage)
- All integration tests pass
- No critical bugs found
- Hook execution <500ms average

---

### Phase 2: Beta Release (Weeks 2-3)

**Audience**: Early adopters, framework contributors

**Goal**: Gather feedback, refine UX

**Version**: v3.6.0-beta

**Activities**:
- Announce on GitHub Discussions
- Invite 10-20 beta testers
- Provide beta documentation
- Gather feedback via GitHub Issues
- Monitor hook performance
- Monitor hydration success rate

**Success Criteria**:
- ≥80% beta testers enable hooks
- ≥5 feedback issues filed (good engagement)
- Zero critical bugs reported
- No performance regressions

---

### Phase 3: Release Candidate (Week 4)

**Audience**: All users (opt-in)

**Goal**: Final validation before GA

**Version**: v3.6.0-rc1

**Activities**:
- Address beta feedback
- Final documentation review
- Create video tutorials
- Prepare release notes
- Update migration guide
- Performance tuning

**Success Criteria**:
- All beta feedback addressed
- Documentation complete
- Zero known critical bugs
- Ready for general availability

---

### Phase 4: General Availability (Week 5)

**Audience**: All users

**Version**: v3.6.0

**Activities**:
- Publish release notes
- Announce on GitHub, social media
- Update documentation site
- Monitor adoption metrics
- Monitor bug reports
- Provide user support

**Success Criteria**:
- Zero critical bugs in first week
- ≥30% adoption within 30 days
- Positive user feedback
- Support tickets <10/week

---

### Phase 5: Post-Launch (Weeks 6-8)

**Goal**: Iterate based on feedback

**Activities**:
- Monitor success metrics
- Address bug reports
- Improve documentation based on support tickets
- Add more hook templates based on requests
- Plan v3.7.0 enhancements (MP1, MP2, MP3)

**Success Criteria**:
- ≥60% adoption by v3.7.0
- 30% reduction in manual steps (survey)
- Zero context loss reports
- User satisfaction ≥8/10

---

## Success Criteria Summary

**v3.6.0 is successful if**:

1. ✅ **Hook system implemented**: 5 core events working
2. ✅ **Hydration pattern implemented**: Multi-session tasks work
3. ✅ **Zero critical bugs**: Stable for 2 weeks
4. ✅ **Documentation complete**: Users can self-serve
5. ✅ **Performance targets met**: Hooks <500ms, hydration <3s
6. ✅ **Adoption**: 30% users enable hooks within 30 days
7. ✅ **No regressions**: Existing workflows unaffected

**v3.6.0 is NOT successful if**:

1. ❌ Critical bugs blocking workflows
2. ❌ Performance degradation (>10% slower)
3. ❌ Breaking changes to existing features
4. ❌ Adoption <10% after 30 days
5. ❌ Security vulnerabilities discovered
6. ❌ Negative user feedback (satisfaction <6/10)

---

## Open Questions

**OQ1: Cursor Hook Integration**
- Q: How to trigger SessionStart/SessionEnd in Cursor?
- Impact: Medium (Cursor users may not get session hooks)
- Options:
  - A) Detect Cursor context, use different session detection
  - B) SessionStart on first `@simple-mode` call per Cursor window
  - C) Defer Cursor session hooks to v3.7.0
- **Recommendation**: Option C (defer to v3.7.0, focus on CLI first)

**OQ2: Async Hook Execution**
- Q: Should some hooks run asynchronously (non-blocking)?
- Impact: Low (performance optimization)
- Options:
  - A) All hooks synchronous (simpler, safer)
  - B) SessionEnd async only (prevents exit delay)
  - C) User-configurable per hook
- **Recommendation**: Option A for v3.6.0, Option C for v3.7.0

**OQ3: Hook Failure Behavior**
- Q: What if critical hook fails (e.g., quality gate)?
- Impact: Medium (workflow blocking vs. workflow corruption)
- Options:
  - A) Fail workflow (safe but disruptive)
  - B) Log error and continue (risky but flexible)
  - C) User-configurable per hook (`fail_on_error: true/false`)
- **Recommendation**: Option C (most flexible)

**OQ4: Beads Task Spec Format**
- Q: Should task specs be YAML, JSON, or both?
- Impact: Low (developer preference)
- Options:
  - A) YAML only (human-readable)
  - B) JSON only (machine-readable)
  - C) Support both
- **Recommendation**: Option A (YAML only, simpler)

**OQ5: GitHub Sync with Hydration**
- Q: Should hydration create GitHub issues automatically?
- Impact: Medium (automation vs. control)
- Options:
  - A) Yes, create GitHub issue if `github_issue` not set
  - B) No, user must create GitHub issues manually
  - C) Opt-in via config (`hydration.create_github_issues: true`)
- **Recommendation**: Option C (opt-in, more control)

---

## Appendix A: Hook Event Reference

### UserPromptSubmit

**When**: Before workflow starts, after user submits prompt

**Use Cases**:
- Add project context
- Show ready tasks
- Validate prompt
- Suggest workflows

**Environment Variables**:
- `$TAPPS_PROMPT`: User's submitted prompt
- `$TAPPS_PROJECT_ROOT`: Project root directory

**Output**: Stdout is added to LLM context

**Example**:
```yaml
hooks:
  UserPromptSubmit:
    - name: "Add project context"
      command: "cat .tapps-agents/context/project.md"
      enabled: true
```

---

### PostToolUse

**When**: After Write/Edit/Read tool completes

**Use Cases**:
- Auto-format code
- Run linters
- Quality checks
- Update documentation

**Environment Variables**:
- `$TAPPS_FILE_PATH`: File that was modified
- `$TAPPS_FILE_PATHS`: Space-separated list of files
- `$TAPPS_TOOL_NAME`: Tool that was used (Write, Edit, Read)
- `$TAPPS_PROJECT_ROOT`: Project root

**Output**: Stdout logged, stderr logged as warning

**Example**:
```yaml
hooks:
  PostToolUse:
    - name: "Auto-format Python"
      matcher: "Write|Edit"
      command: "black {file_path}"
      file_patterns: ["*.py"]
      enabled: true
```

---

### SessionStart

**When**: CLI first command or Cursor first `@simple-mode`

**Use Cases**:
- Load environment
- Show ready tasks
- Hydrate tasks from specs
- Initialize session

**Environment Variables**:
- `$TAPPS_SESSION_ID`: Unique session ID
- `$TAPPS_PROJECT_ROOT`: Project root

**Output**: Stdout shown to user

**Example**:
```yaml
hooks:
  SessionStart:
    - name: "Show ready tasks"
      command: "bd ready"
      enabled: true
```

---

### SessionEnd

**When**: CLI exit or Cursor session ends

**Use Cases**:
- Save session state
- Dehydrate tasks to specs
- Cleanup temp files
- Log session summary

**Environment Variables**:
- `$TAPPS_SESSION_ID`: Session ID
- `$TAPPS_PROJECT_ROOT`: Project root

**Output**: Stdout logged (not shown to user)

**Example**:
```yaml
hooks:
  SessionEnd:
    - name: "Dehydrate tasks"
      command: "tapps-agents task dehydrate"
      enabled: true
```

---

### WorkflowComplete

**When**: After workflow completes (success or failure)

**Use Cases**:
- Update Beads status
- Close GitHub issue
- Notify team
- Update documentation

**Environment Variables**:
- `$TAPPS_WORKFLOW_TYPE`: Workflow type (build, fix, review, etc.)
- `$TAPPS_WORKFLOW_ID`: Unique workflow run ID
- `$TAPPS_WORKFLOW_STATUS`: success or failure
- `$TAPPS_BEADS_ISSUE_ID`: Beads issue ID (if any)
- `$TAPPS_PROJECT_ROOT`: Project root

**Output**: Stdout logged

**Example**:
```yaml
hooks:
  WorkflowComplete:
    - name: "Update documentation"
      command: "./scripts/update-docs.sh {workflow_type}"
      enabled: true
```

---

## Appendix B: Competitive Analysis Summary

**Claude Code (2026) Strengths**:
- ✅ 10 hook events (automation)
- ✅ Persistent subagents
- ✅ Task hydration pattern
- ✅ Session lifecycle hooks
- ✅ Terminal-native

**Claude Code (2026) Weaknesses**:
- ❌ No workflow orchestration (manual steps)
- ❌ No quality gates
- ❌ No expert system
- ❌ Session-scoped tasks (don't persist across sessions without hydration)

**TappsCodingAgents (Current) Strengths**:
- ✅ Superior workflow orchestration (7-9 steps)
- ✅ Quality gates with loopbacks
- ✅ Expert system with adaptive learning
- ✅ Beads integration (basic)
- ✅ Cursor Skills

**TappsCodingAgents (Current) Weaknesses**:
- ❌ No hook system
- ❌ Incomplete Beads hydration
- ❌ Limited multi-session support

**TappsCodingAgents (Post v3.6.0)**:
- ✅ All current strengths PLUS
- ✅ Hook system (5 core events)
- ✅ Complete Beads hydration
- ✅ Full multi-session support
- ✅ **Best of both worlds**

**Competitive Position**: Post v3.6.0, TappsCodingAgents will have **parity on automation** (hooks) and **superior on intelligence** (workflows, experts, quality).

---

## Appendix C: References

**Analysis Documents**:
- [Claude Code Comprehensive Review](./claude-code-comprehensive-review.md)
- [TappsCodingAgents + Beads vs Claude Tasks](./tapps-beads-vs-claude-tasks.md)

**TappsCodingAgents Documentation**:
- [docs/BEADS_GITHUB_BEST_PRACTICES.md](c:\cursor\TappsCodingAgents\docs\BEADS_GITHUB_BEST_PRACTICES.md)
- [docs/BEADS_INTEGRATION.md](c:\cursor\TappsCodingAgents\docs\BEADS_INTEGRATION.md)
- [CLAUDE.md](c:\cursor\TappsCodingAgents\CLAUDE.md)

**External References**:
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [GitHub - steveyegge/beads](https://github.com/steveyegge/beads)
- [Beads: A Git-Friendly Issue Tracker for AI Coding Agents](https://betterstack.com/community/guides/ai/beads-issue-tracker-ai-agents/)

---

**Document End**

---

**Next Steps**:
1. Review this PRD with stakeholders
2. Refine requirements based on feedback
3. Create Epic in Beads: `bd epic create "ENH-002: Critical Enhancements"`
4. Create GitHub Epic issue: `gh issue create --label epic --title "EPIC ENH-002: Critical Enhancements"`
5. Break down into 15 stories
6. Begin Phase 1 implementation

**Approval Required From**:
- [ ] Product Owner
- [ ] Tech Lead
- [ ] Security Team (for hook execution security)
- [ ] Documentation Team

**Estimated Effort**: 50 story points over 7 weeks
**Target Release**: v3.6.0 (Q1 2026)
