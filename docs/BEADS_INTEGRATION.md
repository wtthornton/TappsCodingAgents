# Beads (bd) Integration

Optional integration with [Beads (bd)](https://github.com/steveyegge/beads) for dependency-aware task tracking and agent memory. Beads stores a task graph in `.beads/` (git-backed). TappsCodingAgents can sync epics to bd, close issues when stories complete, and optionally create/close issues for *build and *fix workflows.

---

## Overview and when to use Beads

- **Beads** = task/issue graph: `bd create`, `bd dep add`, `bd ready`, `bd close`. Use it for "what can I work on next?" and for persisting work across sessions.
- **TappsCodingAgents** = workflow engine: `*epic` runs stories from an Epic markdown doc; `*build`/`*fix` run step-by-step flows. Workflow state (checkpoints, resume) lives in `.tapps-agents/`.

Use Beads when:
- You want a durable task list and dependency graph across sessions.
- You run long-horizon or multi-session work (epics, large builds).
- You want `bd ready` to drive or verify "what to do next."

Use `*epic` and `*build` as today; Beads is an optional layer on top.

---

## Installing bd

- **Upstream:** [Beads – Installation](https://github.com/steveyegge/beads#-installation) (Homebrew, npm, Go, Windows install.ps1).
- **This repo:** If the project includes `tools/bd/` (e.g. `tools/bd/bd.exe` on Windows), use that. Add `tools/bd` to PATH to run `bd` directly. Run `bd init` or `bd init --stealth` once at project root (see [tools/README.md](../tools/README.md)).

---

## Configuration

In `.tapps-agents/config.yaml`:

```yaml
beads:
  enabled: true           # Master switch. Set to false to disable all Beads use.
  sync_epic: true         # Sync epic to bd (create issues + deps) before *epic
  hooks_simple_mode: true # Create/close bd issues at start/end of *build and *fix
  hooks_workflow: true    # Create/close for CLI `workflow` runs (WorkflowExecutor, CursorWorkflowExecutor)
  hooks_review: false     # Create/close for *review (optional)
  hooks_test: false       # Create/close for *test (optional)
  hooks_refactor: false   # Create/close for *refactor (optional)
```

- **`beads.enabled`**  
  Must be `true` for any Beads behavior. Default `true` when bd is installed; set to `false` to opt out of all Beads use.

- **`beads.sync_epic`**  
  When `enabled` and `sync_epic` are true, `load_epic` syncs the Epic to bd: one issue per story, `bd dep add` from `Story.dependencies`, and optionally a parent Epic issue (see Epic sync). `bd ready` can then drive or verify execution order.

- **`beads.hooks_simple_mode`**  
  When `enabled` and `hooks_simple_mode` are true, *build and *fix create a bd issue at start and close it on success/fail. continuous-bug-fix and @bug-fix-agent *fix-bug use FixOrchestrator and get the same create/close behavior.

- **`beads.hooks_workflow`**  
  When `enabled` and `hooks_workflow` are true, CLI `workflow` runs (including `--autonomous`) create a bd issue at start and close it when the run ends.

- **`beads.hooks_review`**, **`beads.hooks_test`**, **`beads.hooks_refactor`**  
  When `enabled` and the respective flag is true, *review, *test, or *refactor create a bd issue at start and close it in a `finally` when the run ends. Defaults are `false` (opt-in).

---

## Epic sync

With `beads.enabled` and `beads.sync_epic` true, and `bd` available:

1. **On `load_epic`**  
   - Optionally create a **parent Epic issue**: `bd create "Epic <N>: <title>" -d "..."`. This is for grouping only; we do **not** add `bd dep add` from story issues to this parent.
   - For each `Story`: `bd create "<title>" -d "<description>"` (or similar). Parse stdout for the new bd id and store `story_id -> bd_id`.

2. **Dependencies**  
   For each story with `dependencies`, run `bd dep add <child_bd_id> <parent_bd_id>` so the parent blocks the child. Story–parent deps are not added.

3. **`bd ready`**  
   Lists issues with no open blockers. It should align with the Epic’s topological order when deps are correct.

4. **On story DONE/FAILED**  
   The Epic orchestrator runs `bd close <bd_id>` when a story completes (or optionally `bd update <bd_id> --status cancelled` on failure; current behavior: close in both cases).

5. **When the epic run completes**  
   If a parent Epic issue was created in `load_epic`, the orchestrator runs `bd close <epic_parent_id>` after the loop over stories and before the completion report.

---

## Workflows and Beads

- **\*build, \*fix**  
  Create/close via `hooks_simple_mode`. continuous-bug-fix and @bug-fix-agent \*fix-bug use FixOrchestrator and get the same create/close behavior.

- **\*epic**  
  `sync_epic` + per-story close + optional Epic parent issue and its close when the epic completes.

- **\*review, \*test, \*refactor**  
  Create/close when `hooks_review`, `hooks_test`, or `hooks_refactor` are true, respectively.

- **CLI `workflow`** (including `--autonomous`)  
  Create/close when `hooks_workflow` is true. WorkflowExecutor and CursorWorkflowExecutor create in `start()` and close in `finally` in `execute()`/`run()`.

---

## CLI: `tapps-agents beads`

```bash
tapps-agents beads [bd args...]
```

Forwards to `bd` when it’s available (`tools/bd` or PATH). Examples:

- `tapps-agents beads ready`
- `tapps-agents beads create "Task title" -p 0`
- `tapps-agents beads dep add <child> <parent>`
- `tapps-agents beads show <id>`

If `bd` is not found, the command prints a short message and exits 1.

---

## Simple Mode hooks

When `beads.enabled` and `beads.hooks_simple_mode` are true:

- ** *build***  
  - At start: `bd create "Build: <description>" -p 0`; store bd id.  
  - On success or fail: `bd close <bd_id>`.

- ** *fix***  
  - At start: `bd create "Fix: <file> – <description>" -p 0`; store bd id.  
  - On success or fail: `bd close <bd_id>`.

- ** *epic***  
  Epic sync and per-story close are handled in the Epic orchestrator (see **Epic sync**). No extra hooks in the *epic Simple Mode handler.

---

## Agent conventions

- **Session start**  
  For long-horizon or multi-session work, run `bd ready` to see unblocked tasks.

- **After *build, *fix, or an epic story**  
  Create or close a bd issue as appropriate (e.g. `bd create "Done: ..."` or `bd close <id>`). When hooks are enabled, *build and *fix do this automatically.

---

## Doctor and Init

- **`tapps-agents doctor`** reports Beads (bd) status and config: available (tools/bd or PATH), not found, or not checked; and `beads.enabled`, `sync_epic`, `hooks_simple_mode`, `hooks_workflow`, `hooks_review`, `hooks_test`, `hooks_refactor`. Remediations: when `beads.enabled` is false but bd is available; when `beads.enabled` is true but bd is not found. See docs/BEADS_INTEGRATION.md.
- **`tapps-agents init`** when bd is available: if `.beads` does not exist, prints "Run `bd init` or `bd init --stealth` to enable Beads for this project."; if `.beads` exists, prints "Beads is ready. Use `bd ready` to see unblocked tasks."

---

## Implementation notes (gaps addressed)

- **Exit paths:** All exit paths in FixOrchestrator and BuildOrchestrator call `close_issue` (including implementer-failed, security-scan-blocked, and `try`/`finally` in BuildOrchestrator).
- **Build resume:** Resume reuses one bd issue (persisted under `.tapps-agents/workflow-state/<workflow_id>/.beads_issue_id`); no duplicate issues on resume.
- **WorkflowExecutor and CursorWorkflowExecutor:** Create in `start()` (or at run begin), close in `finally` in `execute()`/`run()`, so every run creates and closes one bd issue when `hooks_workflow` is true.

---

## See also

- [AGENTS.md](../AGENTS.md) – Beads (bd) – Task Tracking
- [tools/README.md](../tools/README.md) – Running bd from `tools/bd`
- [Beads](https://github.com/steveyegge/beads) – Upstream docs and install
