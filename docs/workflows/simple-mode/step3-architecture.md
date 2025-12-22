# Step 3 — Architecture (for the documentation change)

## Where the guidance lives (Cursor-first)

- **Rules**: `.cursor/rules/*.mdc`
  - Always-on “project context and constraints”
  - Should be small, stable, and scoped via `globs` when possible
- **Skills**: `.claude/skills/*/SKILL.md`
  - Actionable, task-specific capabilities
  - Should be discoverable via a clear `description`
- **Docs**: `docs/*.md`
  - Human-facing “how to use / how to extend” documentation

## Change approach

1. Update docs only (no behavioral code changes)
2. Keep changes additive and consistent with existing docs tone
3. Avoid duplicating content already present in `.cursor/rules/*`; instead link/point to it

