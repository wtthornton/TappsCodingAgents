# Task Management and Hydration Guide

This guide covers task specifications (task specs), the hydration pattern for multi-session workflows, and the **task** CLI for creating, listing, running, and syncing tasks with [Beads (bd)](https://github.com/steveyegge/beads).

**Related documentation:**
- [BEADS_INTEGRATION.md](BEADS_INTEGRATION.md) – Beads configuration and Epic sync
- [HOOKS_GUIDE.md](HOOKS_GUIDE.md) – Hooks (SessionStart/SessionEnd can trigger hydrate/dehydrate)

---

## Overview

- **Task specs** are YAML files in `.tapps-agents/task-specs/` that describe work items (stories, tasks, epics) with id, title, status, workflow, and optional Beads linkage.
- **Hydration** creates Beads issues from specs that don’t yet have a `beads_issue` ID and recreates the dependency graph with `bd dep add`.
- **Dehydration** updates spec files with current status from Beads (`bd list`).
- The **task CLI** (`tapps-agents task create|list|show|update|close|hydrate|dehydrate|run`) manages specs and can run workflows from a task.

Use this when you want:
- A durable, file-based task list that can sync with Beads
- Multi-session workflows (e.g. run `task run <id>` in one session, `task dehydrate` in another to refresh status)
- To drive work from `bd ready` while keeping specs as the source of truth

---

## Task spec format

Each task is a single YAML file under `.tapps-agents/task-specs/`. File naming: `<task-id>.yaml` (e.g. `enh-002-s1.yaml`).

### Schema

| Field           | Type     | Required | Description |
|----------------|----------|----------|-------------|
| `id`           | string   | Yes      | Unique task ID (e.g. `enh-002-s1`) |
| `title`        | string   | Yes      | Short title |
| `description`  | string   | No       | Longer description |
| `type`         | string   | No       | `story`, `epic`, or `task` (default: `story`) |
| `priority`     | int      | No       | 0 = highest (default: 0) |
| `story_points` | int      | No       | Estimate |
| `epic`         | string   | No       | Epic ID this task belongs to |
| `dependencies` | list[str]| No       | IDs of tasks this depends on |
| `github_issue` | str/int  | No       | GitHub issue number or ID |
| `beads_issue`  | string   | No       | Beads issue ID (set by hydration) |
| `status`       | string   | No       | `todo`, `in-progress`, `done`, `blocked` (default: `todo`) |
| `workflow`     | string   | No       | Workflow to run: `build`, `fix`, `review`, `test`, `full` (default: `build`) |
| `files`        | list[str]| No       | Files or paths affected |
| `tests`        | list[str]| No       | Test paths |

### Example

```yaml
id: enh-002-s5
title: Integrate hooks into base orchestrator
description: Call UserPromptSubmit before workflows, PostToolUse after implementer, WorkflowComplete after workflow.
type: story
priority: 0
story_points: 5
epic: enh-002
dependencies: [enh-002-s4]
status: todo
workflow: build
```

---

## Directory: `.tapps-agents/task-specs/`

- **Location:** `<project_root>/.tapps-agents/task-specs/`
- **Contents:** One YAML file per task; filename = `<id>.yaml`.
- **Creation:** The directory is created when you run `tapps-agents task create ...` (or you can create it manually). `tapps-agents init` does not create task-specs by default; use the task CLI or add files yourself.

---

## Hydration and dehydration flow

### Hydration (`task hydrate` or SessionStart hook)

1. Scan `.tapps-agents/task-specs/*.yaml` and load all valid specs.
2. For each spec **without** a `beads_issue`:
   - Run `bd create "<title>" -d "<description>"` (or equivalent).
   - Parse the new Beads issue ID from stdout and write it into the spec as `beads_issue`.
3. For each spec with `dependencies`, run `bd dep add <child_bd_id> <parent_bd_id>` so the Beads graph matches the spec dependencies.
4. Report: `created`, `skipped`, `failed`, `deps_added`.

If `bd` is not available, hydration is skipped (no crash); the CLI reports that Beads is unavailable.

### Dehydration (`task dehydrate` or SessionEnd hook)

1. Run `bd list --json` (or equivalent) to get current Beads issue status.
2. For each task spec that has a `beads_issue`, match it to the Beads output and update the spec’s `status` (and any other synced fields) in the YAML file.
3. Report how many specs were updated.

This keeps spec files in sync with what’s in Beads after a session.

### Multi-session workflow

1. **Session A:** Create specs (or pull from Epic), run `tapps-agents task hydrate` to create Beads issues and deps. Run `bd ready` to see what’s unblocked; run `tapps-agents task run <id>` to execute a task’s workflow.
2. **Session B:** Run `tapps-agents task dehydrate` to refresh spec status from Beads. Run `task list` or `task show <id>` to see current state; continue with `task run <id>` or other commands.

Optional: enable **SessionStart** and **SessionEnd** hooks so that hydrate runs at session start and dehydrate at session end (see [HOOKS_GUIDE.md](HOOKS_GUIDE.md)).

---

## Task CLI reference

All commands are run from the project root. Task specs are read/written under `.tapps-agents/task-specs/`.

### create

Create a new task spec (and optionally run hydration).

```bash
tapps-agents task create <id> --title "Title" [--description "..." ] [--workflow build|fix|review|test|full] [--beads]
```

- **id** (positional): Unique task ID.
- **--title**: Required. Short title.
- **--description**: Optional description.
- **--workflow**: Optional; default `build`.
- **--beads**: If set, run `task hydrate` after creating the spec so a Beads issue is created and linked.

Example:

```bash
tapps-agents task create enh-002-s5 --title "Integrate hooks into base orchestrator" --workflow build --beads
```

### list

List task specs, optionally filtered by status.

```bash
tapps-agents task list [--status todo|in-progress|done|blocked] [--format text|json]
```

- **--status**: Show only specs with this status.
- **--format**: `text` (default) or `json`.

### show

Show one task spec by ID.

```bash
tapps-agents task show <id>
```

### update

Update a task spec’s status.

```bash
tapps-agents task update <id> --status <todo|in-progress|done|blocked>
```

### close

Set a task’s status to `done`.

```bash
tapps-agents task close <id>
```

### hydrate

Create Beads issues for specs that don’t have `beads_issue` and recreate the dependency graph.

```bash
tapps-agents task hydrate [--force]
```

- **--force**: If supported, re-run creation for specs that already have `beads_issue` (implementation-dependent). Without `--force`, specs with `beads_issue` are skipped.

Output: `created=... skipped=... failed=... deps_added=...`. If `bd` is not available, the command exits with an error and a message to install Beads.

### dehydrate

Update spec files with current status from Beads.

```bash
tapps-agents task dehydrate
```

Output: `Updated N spec(s) from Beads.`

### run

Load a task spec, set its status to `in-progress`, run the workflow indicated by the spec’s `workflow` field (e.g. build → rapid preset), then set status to `done` on success or back to `todo` on failure.

```bash
tapps-agents task run <id>
```

- Uses the spec’s `title` or `description` as the workflow prompt and `files[0]` as target file if set.
- On workflow completion, the spec is saved with updated status.

---

## Best practices

1. **Use consistent IDs:** e.g. `<epic-id>-s<story-number>` so specs and Beads issues are easy to correlate.
2. **Set dependencies in specs:** So hydration can run `bd dep add` and `bd ready` reflects order.
3. **Run dehydrate at session end:** So the next session (or another machine) sees up-to-date status in the YAML files.
4. **Combine with hooks:** Use SessionStart to hydrate and SessionEnd to dehydrate when using hooks (see [HOOKS_GUIDE.md](HOOKS_GUIDE.md)).
5. **Keep Beads optional:** Task specs work without Beads; only `hydrate` and `dehydrate` (and optional hooks) require `bd`.

---

## Cross-references

- **Beads configuration and Epic sync:** [BEADS_INTEGRATION.md](BEADS_INTEGRATION.md)
- **Hooks (including SessionStart/SessionEnd and hydrate/dehydrate):** [HOOKS_GUIDE.md](HOOKS_GUIDE.md)
- **Configuration options for session and hydration:** [CONFIGURATION.md](CONFIGURATION.md)
