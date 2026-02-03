# Hooks Guide

Hooks let you run custom shell commands at specific points in the TappsCodingAgents lifecycle: when a user prompt is submitted, after a tool (e.g. Write/Edit) is used, when a session starts or ends, and when a workflow completes. Hooks are **opt-in** and disabled by default.

**Related documentation:**
- [TASK_MANAGEMENT_GUIDE.md](TASK_MANAGEMENT_GUIDE.md) – Task specs and hydration (SessionStart/End can run hydrate/dehydrate)
- [BEADS_INTEGRATION.md](BEADS_INTEGRATION.md) – Beads configuration
- [CONFIGURATION.md](CONFIGURATION.md) – config.yaml and hooks/session options

---

## Overview

- **What:** Hooks are shell commands defined in `.tapps-agents/hooks.yaml` and grouped by **event**. When an event fires, all enabled hooks for that event run in order with a set of `TAPPS_*` environment variables.
- **When:** Events are fired by the base orchestrator and session manager: UserPromptSubmit (before workflow), PostToolUse (after implementer Write/Edit), SessionStart (first CLI command), SessionEnd (atexit), WorkflowComplete (after workflow ends).
- **Opt-in:** If `hooks.yaml` is missing or has no enabled hooks, nothing runs. No behavior change when hooks are disabled.

---

## The five events

| Event               | When it runs | Typical use |
|---------------------|--------------|-------------|
| **UserPromptSubmit**| Before a workflow starts (prompt and project root known). | Log prompts, inject context from `.tapps-agents/context/`, validation. |
| **PostToolUse**     | After the implementer step writes/edits a file (file path and tool name known). | Auto-format (e.g. ruff, prettier), lint, run tests on changed file, security scan. |
| **SessionStart**    | On first `tapps-agents` command in the process. | Hydrate task specs to Beads, show `bd ready`, load session state. |
| **SessionEnd**      | On process exit (atexit). | Dehydrate specs from Beads, log session summary, cleanup. |
| **WorkflowComplete**| After a workflow finishes (success or failure). | Notify, update docs, run quality gate, git commit check. |

### UserPromptSubmit

- **When:** Base orchestrator calls it before workflow execution with the user prompt and project root.
- **Use cases:** Log prompt length (avoid logging secrets), add context from `.tapps-agents/context/` into the prompt, validate or enrich the prompt.
- **Env vars:** `TAPPS_PROMPT`, `TAPPS_PROJECT_ROOT`, optionally `TAPPS_WORKFLOW_TYPE`.

### PostToolUse

- **When:** After the implementer step completes; for each file written, the orchestrator fires PostToolUse with file path and tool name (e.g. `Write`).
- **Use cases:** Auto-format (ruff, prettier), run linters or tests on the changed file, trigger security scan on edit.
- **Env vars:** `TAPPS_FILE_PATH`, `TAPPS_FILE_PATHS`, `TAPPS_TOOL_NAME`, `TAPPS_PROJECT_ROOT`, optionally `TAPPS_WORKFLOW_ID`.
- **Filtering:** You can set `matcher` (regex on tool name, e.g. `Write|Edit`) and `file_patterns` (e.g. `["*.py"]`) so the hook runs only for matching tools/files.

### SessionStart

- **When:** Session manager fires it on the first `tapps-agents` command in the process.
- **Use cases:** Run `task hydrate`, show `bd ready`, load session state.
- **Env vars:** `TAPPS_SESSION_ID`, `TAPPS_PROJECT_ROOT`.

### SessionEnd

- **When:** Registered with atexit; runs when the process exits.
- **Use cases:** Run `task dehydrate`, write session log, cleanup.
- **Env vars:** `TAPPS_SESSION_ID`, `TAPPS_PROJECT_ROOT`.

### WorkflowComplete

- **When:** Base orchestrator fires it in a `finally` block when the workflow ends (completed, failed, or cancelled).
- **Use cases:** Notify (e.g. desktop or chat), update docs, run a quality gate, run git commit checks.
- **Env vars:** `TAPPS_WORKFLOW_TYPE`, `TAPPS_WORKFLOW_ID`, `TAPPS_WORKFLOW_STATUS`, `TAPPS_PROJECT_ROOT`, optionally `TAPPS_BEADS_ISSUE_ID`.

---

## Configuration

### hooks.yaml

Location: `.tapps-agents/hooks.yaml`. Create this file to enable hooks; if the file is missing, no hooks run.

Structure:

```yaml
hooks:
  UserPromptSubmit:
    - name: my-log
      command: echo "Prompt length: {{TAPPS_PROMPT}}"
      enabled: true
      fail_on_error: false
  PostToolUse:
    - name: format-python
      command: ruff format {{TAPPS_FILE_PATH}}
      enabled: true
      matcher: "Write|Edit"
      file_patterns: ["*.py"]
      fail_on_error: false
  WorkflowComplete:
    - name: notify
      command: echo "Workflow {{TAPPS_WORKFLOW_STATUS}}: {{TAPPS_WORKFLOW_ID}}"
      enabled: true
      fail_on_error: false
```

Per-hook fields:

| Field            | Required | Description |
|------------------|----------|-------------|
| `name`           | Yes      | Display name for the hook. |
| `command`        | Yes      | Shell command. Use `{TAPPS_*}` placeholders; they are replaced by the runner with the event’s env. |
| `enabled`        | No       | Default `true`. Set to `false` to disable. |
| `matcher`        | No       | (PostToolUse) Regex on tool name; only run if it matches (e.g. `Write|Edit`). |
| `file_patterns`  | No       | (PostToolUse) Glob list (e.g. `["*.py"]`); only run if file path matches. |
| `fail_on_error`  | No       | Default `false`. If `true`, a non-zero exit or timeout fails the workflow. |

Placeholders in `command`: use `{TAPPS_PROMPT}`, `{TAPPS_FILE_PATH}`, etc. (same as the env var names). The executor replaces these with the current event’s values. On Windows, prefer scripts that accept args or use env vars instead of relying on shell expansion.

### config.yaml

Hooks are driven by the presence and content of `hooks.yaml`. Optional project config (e.g. in `.tapps-agents/config.yaml`) can influence session or timeout behavior; see [CONFIGURATION.md](CONFIGURATION.md) for hooks and session options.

---

## Environment variables reference

| Variable | Events | Description |
|----------|--------|-------------|
| `TAPPS_PROMPT` | UserPromptSubmit | User prompt text. |
| `TAPPS_PROJECT_ROOT` | All | Project root path. |
| `TAPPS_WORKFLOW_TYPE` | UserPromptSubmit, WorkflowComplete | e.g. `build`, `full`. |
| `TAPPS_FILE_PATH` | PostToolUse | Single file path (e.g. the file just written). |
| `TAPPS_FILE_PATHS` | PostToolUse | Space-separated list of file paths. |
| `TAPPS_TOOL_NAME` | PostToolUse | e.g. `Write`, `Edit`. |
| `TAPPS_WORKFLOW_ID` | PostToolUse, WorkflowComplete | Workflow run ID. |
| `TAPPS_WORKFLOW_STATUS` | WorkflowComplete | `completed`, `failed`, `cancelled`. |
| `TAPPS_SESSION_ID` | SessionStart, SessionEnd | Session UUID. |
| `TAPPS_BEADS_ISSUE_ID` | WorkflowComplete | Beads issue ID when available. |

---

## Common use cases

1. **Auto-format after edit:** PostToolUse hook with `matcher: "Write|Edit"` and `file_patterns: ["*.py"]`, command e.g. `ruff format {TAPPS_FILE_PATH}`. See template `auto-format-python.yaml`.
2. **Log prompt (no secrets):** UserPromptSubmit hook that echoes prompt length or a hash; avoid logging raw prompt if it may contain secrets.
3. **Context injection:** UserPromptSubmit hook that reads from `.tapps-agents/context/` and appends to the prompt (implementation is project-specific).
4. **Session hydration/dehydration:** SessionStart hook that runs `tapps-agents task hydrate`; SessionEnd that runs `tapps-agents task dehydrate`. See [TASK_MANAGEMENT_GUIDE.md](TASK_MANAGEMENT_GUIDE.md).
5. **Notify on workflow complete:** WorkflowComplete hook that runs a script to post to chat or desktop. See template `notify-on-complete.yaml`.
6. **Quality gate:** WorkflowComplete hook that runs tests or a lint script and uses `fail_on_error: true` to fail the run on failure.

---

## Template library

Templates are under `tapps_agents/resources/hooks/templates/`. Use `tapps-agents init --hooks` to create `.tapps-agents/hooks.yaml` from templates (all disabled by default). You can also copy templates manually into `hooks.yaml`.

| Template | Event | Purpose |
|----------|--------|---------|
| `user-prompt-log.yaml` | UserPromptSubmit | Log prompt length (example). |
| `add-project-context.yaml` | UserPromptSubmit | Add project context (example). |
| `auto-format-python.yaml` | PostToolUse | Run `ruff format` on edited `.py` files. |
| `auto-format-js.yaml` | PostToolUse | Format JS/TS (e.g. prettier). |
| `test-on-edit.yaml` | PostToolUse | Run tests on edited file. |
| `security-scan-on-edit.yaml` | PostToolUse | Run security scan on edited file. |
| `quality-gate.yaml` | WorkflowComplete | Quality gate (example). |
| `update-docs-on-complete.yaml` | WorkflowComplete | Update docs after workflow. |
| `notify-on-complete.yaml` | WorkflowComplete | Notify on completion. |
| `git-commit-check.yaml` | WorkflowComplete | Git commit checks. |
| `session-end-log.yaml` | SessionEnd | Log session end. |
| `show-beads-ready.yaml` | SessionStart | Show `bd ready` (example). |

---

## Troubleshooting

- **Hooks don’t run:** Ensure `.tapps-agents/hooks.yaml` exists and at least one hook for that event has `enabled: true`. Check that the event is actually fired (e.g. UserPromptSubmit only when a workflow starts via the base orchestrator).
- **PostToolUse not firing:** Only runs after the implementer step writes a file in workflows that use the base orchestrator (e.g. build). Ensure `matcher` and `file_patterns` match the tool name and file path.
- **Command fails or times out:** Default timeout is 30 seconds. Non-zero exit is logged; if `fail_on_error: true`, the workflow fails. Run the command manually with the same env to debug.
- **Placeholders not replaced:** Use `{TAPPS_VAR}` (single braces). Double braces `{{}}` are not substituted by the executor.
- **Windows:** Use commands that work in your shell (e.g. PowerShell/cmd). Prefer `.cmd`/`.ps1` scripts or executables that read from env vars instead of complex shell-only syntax.

---

## Security best practices

1. **No secrets in hooks.yaml:** Do not put API keys or passwords in `command`. Use env vars or a secret manager and reference them from the command (e.g. `$ENV:MY_KEY` or `%MY_KEY%`).
2. **Review hook commands:** Hooks run with the same privileges as the CLI. Only add hooks you trust; avoid executing remote content without verification.
3. **Limit prompt logging:** UserPromptSubmit can see the full prompt; log length or a hash, not raw content, to avoid leaking secrets.
4. **File paths:** PostToolUse receives file paths from the workflow; validate inside your script if you pass them to other tools.

---

## Examples

**UserPromptSubmit – log prompt length (no secrets):**

```yaml
hooks:
  UserPromptSubmit:
    - name: log-prompt-len
      command: echo "Prompt length: (see TAPPS_PROMPT in env)"
      enabled: true
      fail_on_error: false
```

(The executor substitutes `{TAPPS_PROMPT}` with the prompt text; use a script that reads from the environment and echoes only length to avoid logging secrets.)

**PostToolUse – format Python:**

```yaml
hooks:
  PostToolUse:
    - name: format-python
      command: ruff format {TAPPS_FILE_PATH}
      enabled: true
      matcher: "Write|Edit"
      file_patterns: ["*.py"]
      fail_on_error: false
```

**WorkflowComplete – notify:**

```yaml
hooks:
  WorkflowComplete:
    - name: notify
      command: echo "Workflow {TAPPS_WORKFLOW_STATUS}: {TAPPS_WORKFLOW_ID}"
      enabled: true
      fail_on_error: false
```

**SessionStart / SessionEnd:** See [TASK_MANAGEMENT_GUIDE.md](TASK_MANAGEMENT_GUIDE.md) for hydrate/dehydrate examples.
