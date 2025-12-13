## PR Mode Guide (Background Agents)

This repo supports two safe patterns for Background Agents:

### 1) Artifacts-only (default)

Use this when you want **analysis and outputs**, not automated repo changes.

- **What it does**: runs deterministic commands (lint/type-check/tests/reports) and writes artifacts to `.tapps-agents/reports/`.
- **What it does not do**: open PRs.
- **Good for**: quality reports, audits, “tell me what’s wrong”, verification runs.

### 2) PR-mode (explicit, opt-in)

Use this when you explicitly want **a PR** created from an isolated worktree.

- **What it does**:
  - runs in an isolated worktree
  - enables PR delivery
  - runs deterministic verification commands so the PR comes with artifacts and checks
- **Who does the “reasoning”**: Cursor (using the developer’s configured model).  
  The framework remains tools-only under Cursor.

### Trigger phrases (recommended)

These map to the PR-mode background agent configured in `.cursor/background-agents.yaml`:

- “Open a PR with these changes”
- “Create a PR for this refactor”
- “Prepare a PR and run checks”
- “Make changes and open a PR”

### Where outputs go

- **Artifacts**: `.tapps-agents/reports/`
- **Worktrees**: `.tapps-agents/worktrees/`

### Safety note

PR-mode is intentionally **not the default** to prevent surprise automated changes. Use it only when you explicitly want a PR.


