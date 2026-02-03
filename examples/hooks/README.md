# Hooks Example

This example shows a minimal project setup for TappsCodingAgents **hooks**: config and context files you can copy into your project’s `.tapps-agents/` to run commands at UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, and WorkflowComplete.

## What’s included

- **hooks.yaml** – Sample `.tapps-agents/hooks.yaml` with one hook per event (all disabled). Enable and edit as needed.
- **context/** – Sample `.tapps-agents/context/` file(s) for context injection (UserPromptSubmit hooks can read from here).

## Quick start

1. Copy the contents of this example into your project:
   - `hooks.yaml` → `<your-project>/.tapps-agents/hooks.yaml`
   - `context/` → `<your-project>/.tapps-agents/context/`
2. Edit `.tapps-agents/hooks.yaml` and set `enabled: true` for the hooks you want.
3. Run any workflow (e.g. `tapps-agents simple-mode build --prompt "Add a function"`). UserPromptSubmit and WorkflowComplete will run when hooks are enabled; PostToolUse runs after the implementer writes a file.

## Events

| Event             | When it runs                         |
|-------------------|--------------------------------------|
| UserPromptSubmit  | Before a workflow starts             |
| PostToolUse       | After implementer Write/Edit         |
| SessionStart      | First CLI command in the process     |
| SessionEnd        | Process exit (atexit)                 |
| WorkflowComplete  | After workflow ends (success/fail)   |

See [docs/HOOKS_GUIDE.md](../../docs/HOOKS_GUIDE.md) for full documentation, env vars, and security notes.

## Running the example

From the **TappsCodingAgents repo root** (not from this directory):

```bash
# Create .tapps-agents in a temp or real project and copy hooks + context
mkdir -p myproject/.tapps-agents
cp examples/hooks/hooks.yaml myproject/.tapps-agents/
cp -r examples/hooks/context myproject/.tapps-agents/
cd myproject
tapps-agents init
# Enable one hook in .tapps-agents/hooks.yaml (e.g. UserPromptSubmit), then:
tapps-agents simple-mode build --prompt "Add a hello function" --auto
```

You should see your hook run (e.g. log output) when the workflow starts and when it completes.
