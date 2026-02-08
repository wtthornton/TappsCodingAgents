# Init and reset behavior

This document describes what happens to each artifact when you run `tapps-agents init`, run init again ("Later init"), or run `tapps-agents init --reset`.

## Create / update / reset matrix

| Artifact | First init | Later init | init --reset |
|----------|------------|------------|--------------|
| **AGENTS.md** (project root) | Create (from template) | Overwrite (from template) | Delete and recreate from template |
| **.cursor/rules/** | Create (copy packaged rules; project-context variant by project type) | Skip if file exists (except project-context.mdc: always overwrite with correct variant) | Delete framework rules, re-copy from package |
| **.tapps-agents/config.yaml** | Create (with template application if applicable) | Skip if exists | Preserve (user data) |
| **.tapps-agents/tech-stack.yaml** | Create (from detection) | Update from detection if generated | Preserve (user data) |
| **.tapps-agents/experts/** | Create scaffold if auto_experts | Merge / preserve | Preserve (user data) |
| **.tapps-agents/knowledge/** | Create scaffold | Preserve | Preserve (user data) |
| **workflows/presets/** | Create (copy packaged presets) | Skip if file exists | Delete framework presets, re-copy |
| **.cursorignore** | Create or merge (append framework patterns) | Merge (append missing patterns) | Heuristic: if framework patterns present, overwrite/merge |
| **.cursor/mcp.json** | Create or merge | Merge (unless --reset-mcp) | Preserve unless --reset-mcp |
| **CLAUDE.md** (project root, optional) | Create if not --no-claude-md | Overwrite if include_claude_md | Delete and recreate if present (framework-managed when present) |
| **.claude/skills/** | Create (copy packaged skills) | Skip if skill dir exists | Delete framework skills, re-copy |
| **.tapps-agents/.framework-version** | Write | Write | Written after reset |

**Notes:**

- **AGENTS.md** and **CLAUDE.md** are framework-managed: created/overwritten on every init and recreated on init --reset when present.
- **project-context.mdc**: Installed content is either the framework variant (when running init from the TappsCodingAgents repo) or the user variant (when running init from any other project). Always overwritten on init so the correct variant is in place.
- User data (config, experts, knowledge, custom skills/rules/presets) is preserved during init --reset unless explicitly reset (e.g. --reset-mcp).

## How it fits together

- **AGENTS.md** ← Template + tech_stack (detection). Read by all agents (Cursor, Claude, Copilot, etc.). Primary entry point for project context.
- **.cursor/rules/** ← Packaged rules + project-context variant (framework vs user). Read by Cursor.
- **.tapps-agents/config.yaml**, **tech-stack.yaml**, **experts**, **knowledge** — Used by CLI and workflows; config and user data preserved on reset.
- **workflows/presets/** ← Packaged preset YAMLs. Framework-managed; reset replaces them.
- **.claude/skills/** ← Packaged skills. Framework-managed; reset replaces framework skills, preserves custom.
- **CLAUDE.md** (optional) ← Template. Points to AGENTS.md. Read by Claude Code when present. Framework-managed when present.

See [AGENTS_MD_GUIDE.md](AGENTS_MD_GUIDE.md) and [CONFIGURATION.md](CONFIGURATION.md) for details.
