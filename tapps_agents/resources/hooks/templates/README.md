# Hook templates

These YAML files are used by `tapps-agents init --hooks` to generate `.tapps-agents/hooks.yaml`. Each file defines one or more hooks for a single event; all are installed with `enabled: false`. Enable and customize in your project's `.tapps-agents/hooks.yaml`.

Events: UserPromptSubmit, PostToolUse, SessionStart, SessionEnd, WorkflowComplete.
