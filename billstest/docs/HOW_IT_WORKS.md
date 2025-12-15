## How TappsCodingAgents Works (Cursor-first, 2025)

This project is designed to work **inside Cursor** with agents and background agents, while keeping **local LLM support optional**.

### The mental model

- **Cursor is the “brain”** (LLM reasoning).
  - Cursor uses **whatever model the developer configured** (Auto or pinned).  
  - This repo does **not** hardcode a model selection for Cursor.
- **TappsCodingAgents is the “hands”** (deterministic execution).
  - Runs workflows, quality tools, reporting, worktree isolation, caching, etc.

### Key directories

- **`.claude/skills/`**: Canonical Cursor Skills definitions (13 agents).
- **`.cursor/`**:
  - `.cursor/rules/*.mdc`: Cursor Rules (project context + workflow/command reference).
  - `.cursor/background-agents.yaml`: Cursor Background Agents definitions.
- **`.tapps-agents/`**: Runtime state (config + caches + reports + worktrees).  
  Most of this is **machine-local** and should not be committed.

### Runtime model policy (prevents “double LLM”)

**Option A policy (default in this repo):**

- When running under Cursor (Skills / Background Agents), the framework runs **tools-only** and **must not call MAL**.
  - Enforced by `TAPPS_AGENTS_MODE=cursor` and a runtime guard that blocks MAL usage.
- When running headlessly (outside Cursor), MAL is **optional**:
  - Enable with `TAPPS_AGENTS_MODE=headless`
  - Configure via `.tapps-agents/config.yaml` (`mal:` section) if you want Ollama/cloud providers.

### Background Agents: two modes

- **Artifacts-only (default)**: writes results to `.tapps-agents/reports/` (no PRs).
- **PR-mode (opt-in)**: enables PR delivery explicitly (used only when you ask for a PR).

### Recommended setup for another repo

From the target project root (after installing `tapps-agents`):

- `tapps-agents init`
  - Installs Cursor Rules into `.cursor/rules/`
  - Installs Skills into `.claude/skills/`
  - Installs Background Agents into `.cursor/background-agents.yaml`
  - Optionally creates `.tapps-agents/config.yaml`

### Keeping Cursor fast

This repo includes `.cursorignore` to prevent Cursor from indexing large/generated directories (venv, caches, reports, worktrees).


