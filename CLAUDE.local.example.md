# CLAUDE.local.example.md

Copy this file to `CLAUDE.local.md` to add **local-only** rules and context.
`CLAUDE.local.md` is loaded when Cursor's **"Include CLAUDE.md in context"** is enabled,
and is in `.gitignore` so it stays private to your machine.

## How to use

1. Copy: `cp CLAUDE.local.example.md CLAUDE.local.md` (or `copy CLAUDE.local.example.md CLAUDE.local.md` on Windows)
2. Edit `CLAUDE.local.md` with your overrides (team norms, tool preferences, local paths, etc.).
3. Keep `CLAUDE.local.md` out of commits (it is in `.gitignore`).

## Example overrides

```markdown
# Local overrides

- Prefer Python 3.12 for this repo.
- Our API base URL for this project is https://staging.example.com.
- Always run `ruff check` before committing.
```

You can add any project- or machine-specific rules here. They are merged with `CLAUDE.md` and `.cursor/rules/` when the agent context is built.
