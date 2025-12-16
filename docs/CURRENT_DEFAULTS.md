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

**Shipped templates (in this repo/package):**
- **Skills templates**: `tapps_agents/resources/claude/skills/` (12 agent skills)
- **Cursor Rules templates**: `tapps_agents/resources/cursor/rules/*.mdc` (5 rule files)
- **Background Agents template**: `tapps_agents/resources/cursor/background-agents.yaml`
- **Workflow presets templates**: `tapps_agents/resources/workflows/presets/*.yaml` (5 presets)

**Installed locations (in target repo after `tapps-agents init`):**
- **Skills**: `.claude/skills/` (copied from packaged templates)
- **Cursor Rules**: `.cursor/rules/*.mdc` (copied from packaged templates)
- **Background Agents config**: `.cursor/background-agents.yaml` (copied from packaged template)
- **Workflow presets**: `workflows/presets/*.yaml` (copied from packaged templates)
- **Runtime state**: `.tapps-agents/` (mostly machine-local, created at runtime)

### Default setup command

From a target project root:

```bash
tapps-agents init
```

This installs Skills, Cursor Rules, Background Agents config, workflow presets, and (optionally) `.tapps-agents/config.yaml` into the target project by copying from the packaged templates in `tapps_agents/resources/*`.

### Performance defaults

- `.cursorignore` is present to prevent indexing large/generated directories (venv, caches, reports, worktrees).


