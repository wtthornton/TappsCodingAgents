# Step 1 — Enhanced Prompt (Cursor-only docs improvements)

## Goal

Improve TappsCodingAgents’ Cursor documentation so:
- Cursor Rules are easier to extend safely (layering/scoping guidance)
- Custom Skills are easier to author reliably (trigger clarity + bundle layout + progressive disclosure)

## Constraints

- Cursor-first only (no Codex interoperability requirements)
- Keep guidance aligned with existing repo conventions:
  - `.cursor/rules/*.mdc` is the primary “always-on” instruction layer
  - `.claude/skills/*/SKILL.md` is the primary Skills layer
  - `tapps-agents init` remains the recommended installer

## Proposed changes (high level)

- Add a **Cursor Rules layering/scoping** section to `docs/CURSOR_RULES_SETUP.md`
- Add a **Skill design checklist** and **recommended skill bundle layout** to `docs/CUSTOM_SKILLS_GUIDE.md`
- Add a short note on **progressive disclosure** (keep top-of-skill minimal; detailed docs below)

## Success criteria

- New docs make it clear how to:
  - create folder-specific rules using `globs` and avoid overusing `alwaysApply`
  - write skill `description` text that triggers predictably
  - structure skill assets (`references/`, `assets/`, `scripts/`) consistently

