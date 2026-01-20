# Rules and Commands Toggles (Cursor)

This document describes Cursor's **Rules and Commands** settings and how TappsCodingAgents uses them. For best results with TappsCodingAgents, **enable all four toggles**.

---

## Recommended Settings

| Toggle | Recommended | What TappsCodingAgents uses |
|--------|-------------|-----------------------------|
| **Import Agent Skills** | On | `.claude/skills/` (14 agent skills + simple-mode). Optionally `.codex/skills/` in the future. |
| **Include CLAUDE.md in context** | On | `CLAUDE.md`, and `CLAUDE.local.md` when present (local overrides). |
| **Import Claude Commands** | On | `.claude/commands/` (Claude Desktop-style) and `.cursor/commands/` (Cursor slash commands: /build, /fix, /review, /test). |
| **Import Claude Plugins** | On | `.claude-plugin/` may be supported in a future release. |

---

## Toggle Details

### Import Agent Skills

- **Loads:** Skills from `.claude/skills/` and `.codex/skills/`.
- **TappsCodingAgents:** Ships `.claude/skills/` with 15 skills (analyst, architect, debugger, designer, documenter, enhancer, evaluator, implementer, improver, ops, orchestrator, planner, reviewer, simple-mode, tester). These are installed by `tapps-agents init`.
- **`.codex/skills/`:** The toggle also loads skills from `.codex/skills/`. TappsCodingAgents does not ship Codex-formatted skills today; support may be added in a future release.

### Include CLAUDE.md in context

- **Loads:** `CLAUDE.md` and `CLAUDE.local.md` when relevant.
- **TappsCodingAgents:** `CLAUDE.md` is the master rule file and index to `.cursor/rules/`. Keep this **On** so the agent gets the full rule set.
- **`CLAUDE.local.md`:** You can add `CLAUDE.local.md` (copy from `CLAUDE.local.example.md`) for machine- or project-specific overrides. It is in `.gitignore` and is loaded together with `CLAUDE.md` when this toggle is On.

---

## Import Claude Commands

- **Loads:** Commands from `.claude/commands/` and `.cursor/commands/`.
- **TappsCodingAgents:**
  - **`.claude/commands/`** – Claude Desktop-style commands (e.g. @build, @fix, @review). Installed by `tapps-agents init`.
  - **`.cursor/commands/`** – Cursor slash commands. `tapps-agents init` installs: `build.md`, `fix.md`, `review.md`, `test.md`. In Cursor chat, type `/build`, `/fix`, `/review`, or `/test` to run the corresponding Simple Mode workflow.

---

## Import Claude Plugins

- **Loads:** Skills/plugins from `.claude-plugin/` directories.
- **TappsCodingAgents:** Does not ship a `.claude-plugin` today. Support may be added in a future release. Leaving this On is safe and does not affect TappsCodingAgents.

---

## Quick setup

1. In Cursor: **Settings → Rules and Commands** (or equivalent).
2. Turn **On** all four toggles.
3. Run `tapps-agents init` in your project so Skills, `.claude/commands/`, `.cursor/commands/`, and Rules are installed.
4. (Optional) Copy `CLAUDE.local.example.md` to `CLAUDE.local.md` and add local overrides.

---

## Related

- [Cursor Skills Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [CLAUDE.local.example.md](../CLAUDE.local.example.md) – template for `CLAUDE.local.md`
- [.claude/commands/README.md](../.claude/commands/README.md) – Claude Desktop commands
