## Current Defaults (No Surprises)

This document is the “what happens by default” reference for this repo.

### Default runtime behavior

- **Inside Cursor (Skills / Background Agents)**:
  - Cursor uses **the developer’s configured model** (Auto or pinned).
  - The framework runs **tools-only**.
  - **MAL is disabled** (no Ollama/Anthropic/OpenAI calls from the framework).

- **Headless CLI (outside Cursor)**:
  - The framework runs normally.
  - **MAL is optional** and only enabled when you explicitly opt in:
    - `TAPPS_AGENTS_MODE=headless`
    - plus `.tapps-agents/config.yaml` `mal:` configuration if desired

### Default Background Agents behavior

- **Artifacts-only by default**
  - Output goes to `.tapps-agents/reports/`
  - No PRs unless you use the explicit PR-mode agent

### Default locations (canonical)

- **Skills**: `.claude/skills/`
- **Cursor Rules**: `.cursor/rules/*.mdc`
- **Background Agents config**: `.cursor/background-agents.yaml`
- **Runtime state**: `.tapps-agents/` (mostly machine-local)

### Default setup command

From a target project root:

```bash
tapps-agents init
```

This installs Skills, Cursor Rules, Background Agents config, workflow presets, and (optionally) `.tapps-agents/config.yaml`.

### Performance defaults

- `.cursorignore` is present to prevent indexing large/generated directories (venv, caches, reports, worktrees).


