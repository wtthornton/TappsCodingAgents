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
# beads:
#   enabled: false        # Master switch; when false, all beads features are no-ops
#   sync_epic: true       # When enabled, sync epic to bd (create issues + deps) before *epic
#   hooks_simple_mode: false  # Create/close bd issues at start/end of *build and *fix
beads:
  enabled: false
  sync_epic: true
  hooks_simple_mode: false
```

- **`beads.enabled`**  
  Must be `true` for any Beads behavior. Default `false` (opt-in).

- **`beads.sync_epic`**  
  When `enabled` and `sync_epic` are true, `load_epic` syncs the Epic to bd: one issue per story, `bd dep add` from `Story.dependencies`. `bd ready` can then drive or verify execution order.

- **`beads.hooks_simple_mode`**  
  When `enabled` and `hooks_simple_mode` are true, *build and *fix create a bd issue at start and close it on success/fail.

---

## Epic sync

With `beads.enabled` and `beads.sync_epic` true, and `bd` available:

1. **On `load_epic`**  
   For each `Story`: `bd create "<title>" -d "<description>"` (or similar). Parse stdout for the new bd id (e.g. `TappsCodingAgents-<hash>`) and store `story_id -> bd_id`.

2. **Dependencies**  
   For each story with `dependencies`, run `bd dep add <child_bd_id> <parent_bd_id>` so the parent blocks the child.

3. **`bd ready`**  
   Lists issues with no open blockers. It should align with the Epic’s topological order when deps are correct.

4. **On story DONE/FAILED**  
   The Epic orchestrator runs `bd close <bd_id>` when a story completes (or optionally `bd update <bd_id> --status cancelled` on failure; current behavior: close in both cases).

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

- **`tapps-agents doctor`** reports Beads (bd) status: available (tools/bd or PATH), not found, or not checked. All severities are informational (ok); Beads is optional.
- **`tapps-agents init`** prints an optional hint to run `bd init` or `bd init --stealth` when `bd` is detected.

---

## See also

- [AGENTS.md](../AGENTS.md) – Beads (bd) – Task Tracking
- [tools/README.md](../tools/README.md) – Running bd from `tools/bd`
- [Beads](https://github.com/steveyegge/beads) – Upstream docs and install
