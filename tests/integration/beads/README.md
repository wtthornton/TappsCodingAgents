# Beads integration tests

**Setup:** run `.\scripts\ensure_test_env.ps1` from the repo root (creates `.venv` with Python 3.13 and installs the project + `[dev]` deps). If pip fails with "file is being used", close Cursor/IDE and re-run.

**Run** with **bd** in `tools/bd` or on PATH:

```powershell
.venv\Scripts\python -m pytest -m integration tests\integration\beads\ -v
```

Or:

```powershell
.\scripts\run_integration_tests.ps1
```

- **test_beads_cli.py**: `tapps-agents beads ready` when bd is present. Skipped if it times out (bd/CLI can block on some environments).
- **test_beads_epic_sync.py**: EpicOrchestrator.load_epic with `beads.enabled` and `beads.sync_epic`; uses a temp project with `git init`, `tools/bd`, `bd init --stealth`, and a minimal epic. Skipped if `bd init` fails or times out.
