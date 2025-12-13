# Release Notes - TappsCodingAgents v2.0.1

**Release Date:** December 13, 2025  
**Version:** 2.0.1  
**Tag:** v2.0.1

## 🚀 Highlights

- **`tapps-agents init` now works from PyPI installs** by shipping initialization assets inside the package.
- **Docs and setup guidance aligned** around the single recommended setup command: `tapps-agents init`.
- **`doctor` targets aligned** with packaging (`requires-python >=3.13`), removing confusing version mismatches.

## ✨ Added

- Packaged init resources under `tapps_agents/resources/`:
  - Cursor Rules (`.cursor/rules/*.mdc`)
  - Cursor Skills (`.claude/skills/`)
  - Cursor Background Agents config (`.cursor/background-agents.yaml`)
  - Workflow presets (`workflows/presets/*.yaml`)

## 🔄 Changed

- `init` now prefers packaged resources via `importlib.resources` with fallback to source-checkout paths.
- Playwright messaging updated for **Cursor Playwright MCP** vs the Python Playwright package (CLI).
- Configuration template updated to include tooling targets used by `doctor`.

## 📦 Installation

```bash
pip install tapps-agents==2.0.1
```

## 📝 Full Changelog

See `CHANGELOG.md` for complete details.


