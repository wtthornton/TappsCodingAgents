# Project tools

## Beads (bd)

[Beads](https://github.com/steveyegge/beads) is installed here for dependency-aware task tracking.

- **Run:** `tools\bd\bd.exe` (Windows) or `tools/bd/bd` (if a Unix binary is added). To use `bd` directly: `. .\scripts\set_bd_path.ps1` (session) or `.\scripts\set_bd_path.ps1 -Persist` (User PATH). This script may be created by `tapps-agents init` when `tools/bd` exists.
- **Init:** Run `bd init` or `bd init --stealth` at project root when using Beads for task tracking. See [docs/BEADS_INTEGRATION.md](docs/BEADS_INTEGRATION.md).
- **Quick start:** `tools\bd\bd.exe quickstart` or `bd quickstart` after `set_bd_path.ps1`.
