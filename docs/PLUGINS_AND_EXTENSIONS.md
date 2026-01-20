# Plugins and Extensions

How to extend TappsCodingAgents with custom skills, commands, rules, and MCPs.

---

## Custom Skills

### Where to Add

- **Project:** `.claude/skills/<skill-name>/SKILL.md` (created by `tapps-agents init`; add your own alongside framework skills)
- **User (personal):** `~/.tapps-agents/skills/<skill-name>/SKILL.md` (user scope; created by init when used)

### SKILL.md Structure

Use YAML frontmatter and markdown body. Required frontmatter:

- `name` – skill name (must match directory)
- `description` – short description
- `allowed-tools` – e.g. `Read, Write, Edit, Grep, Glob, Bash`
- `model_profile` – e.g. `default` or a profile from `requirements/model_profiles.yaml`

Example:

```yaml
---
name: my-skill
description: My custom workflow
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model_profile: default
---

# My Skill

When invoked, do X, then call @reviewer *review...
```

### Reference

- **Example:** `tapps_agents/resources/claude/skills/example-custom-skill/SKILL.md`
- **Validation:** run `tapps-agents` with the skill loader to validate frontmatter and structure

---

## Custom Commands

### Cursor Slash Commands

- **Location:** `.cursor/commands/<name>.md`
- **Usage in Cursor:** `/name` in chat
- **Content:** Short Overview and Steps that invoke `@simple-mode *...` or specific agents

Example: `.cursor/commands/my-cmd.md`:

```markdown
# My Command

## Overview
Run @simple-mode *build "my feature".

## Steps
1. Run: @simple-mode *build "my feature"
2. Report results.
```

### Claude Desktop Commands

- **Location:** `.claude/commands/<name>.md`
- **Usage:** `@name` in Claude Desktop
- **Content:** Usage, What It Does, Integration (Cursor vs Claude vs CLI)

`tapps-agents init` copies framework commands into `.cursor/commands/` and `.claude/commands/`. Add your `.md` files alongside; init does not overwrite existing files.

---

## Custom Rules

- **Location:** `.cursor/rules/<name>.mdc`
- **Format:** YAML frontmatter (`description`, `globs`, `alwaysApply`) and markdown body

Example:

```yaml
---
description: My project rule
alwaysApply: false
---

# My Rule

Always do X when editing tests.
```

Framework rules (e.g. `security.mdc`, `coding-style.mdc`, `simple-mode.mdc`) are installed by `tapps-agents init` from `tapps_agents/resources/cursor/rules/`. Add your own `.mdc` files; init does not overwrite existing.

---

## Project Types, Tech Stacks, User Roles

- **Project types:** `templates/project_types/` – project-type-specific defaults
- **Tech stacks:** `templates/tech_stacks/` – stack-specific config (e.g. Python, Node, FastAPI)
- **User roles:** `templates/user_roles/` – role-specific agent behavior

These are applied during `tapps-agents init` when templates are used. Customize by adding or editing YAML in those directories or in project `.tapps-agents/` config.

---

## MCPs (Context7, Playwright, etc.)

MCPs extend behavior with tools (e.g. library docs, browser automation).

- **Config:** `.cursor/mcp.json` (project) or user-level MCP config
- **Context7:** library documentation; `@reviewer *docs <library>`, `*docs-refresh`; see [MCP_TOOLS_TROUBLESHOOTING.md](MCP_TOOLS_TROUBLESHOOTING.md)
- **Playwright:** E2E runs and screenshots; `@simple-mode *e2e` and `@tester *generate-e2e-tests` can use it when available

Enable only the MCPs you need per project to keep context and tool count manageable (see `.cursor/rules/performance.mdc`).

---

## See Also

- [Custom Skills Guide](CUSTOM_SKILLS_GUIDE.md) – Creating and validating custom skills
- [Cursor Rules Setup Guide](CURSOR_RULES_SETUP.md) – Rules and workflow-generated rules
- [MCP_TOOLS_TROUBLESHOOTING.md](MCP_TOOLS_TROUBLESHOOTING.md) – MCP and tool issues
- [Configuration Guide](CONFIGURATION.md) – `.tapps-agents/config.yaml` and overrides
