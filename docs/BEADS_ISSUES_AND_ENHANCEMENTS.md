# Beads (bd) Integration: Issues and Enhancements

This document lists known issues and suggested enhancements for TappsCodingAgents’ Beads integration. It was produced after upgrading to Beads v0.49.0 and reviewing usage across the codebase.

---

## Completed

- **Upgrade path:** `scripts/upgrade_beads.ps1` downloads and installs Beads v0.49.0 on Windows. When `bd.exe` is in use, the script saves the new binary as `bd.exe.new` and prints instructions to replace after closing locking processes.
- **Docs:** [BEADS_INTEGRATION.md](BEADS_INTEGRATION.md), [tools/README.md](../tools/README.md), and [tools/bd/README.md](../tools/bd/README.md) updated with upgrade steps and “tested with v0.49.0”.

---

## User action required (this repo)

- **Replace locked bd.exe:** If the upgrade script reported “bd.exe is in use,” close any process using bd (Cursor, terminals), then run:
  ```powershell
  Remove-Item -Force tools\bd\bd.exe; Move-Item -Force tools\bd\bd.exe.new tools\bd\bd.exe
  ```
  Then run `tapps-agents doctor` to confirm Beads is available and ready.

---

## Issues

1. **Doctor does not report bd version**  
   Doctor reports “Beads (bd): Available (ready)” but does not show the bd binary version (e.g. 0.49.0). This makes it harder to confirm an upgrade or debug version-related behavior.

2. **No minimum Beads version check**  
   We do not enforce a minimum bd version. If an older bd is used, we might rely on flags or behavior that were added in a newer release (e.g. `bd list --ready`, resolve-conflicts, gate auto-discovery). Consider documenting a minimum version (e.g. 0.47.x) and optionally having doctor warn when bd is below that.

3. **Upgrade script is Windows-only**  
   `scripts/upgrade_beads.ps1` targets Windows AMD64 only. Linux/macOS users must upgrade bd via upstream (Homebrew, npm, Go, or manual download). We could add a small note in docs or a shell script that points to upstream install/upgrade.

4. **bd.exe.new left on disk**  
   After a successful manual replace, `bd.exe.new` may still exist if the user only ran `Move-Item` (overwriting bd.exe). The script does not clean up `bd.exe.new`. Optional enhancement: document that users can remove `tools/bd/bd.exe.new` after replacing, or have the script remove it when it successfully overwrites bd.exe (current script only writes bd.exe.new when the overwrite fails).

---

## Enhancements

1. **Report bd version in doctor**  
   In the Beads check, run `bd --version` (or equivalent) and include the version string in the finding message (e.g. “Beads (bd): Available (ready), v0.49.0”). This helps confirm upgrades and troubleshoot version-specific issues.

2. **Optional minimum bd version in config**  
   Add something like `beads.min_version` in `.tapps-agents/config.yaml` (optional). If set, doctor (and optionally workflow startup) could warn or fail when the installed bd is below that version.

3. **Upgrade script: optional doctor run when bd.exe.new is used**  
   When the script falls back to writing `bd.exe.new`, it could still run doctor by temporarily preferring `bd.exe.new` (e.g. by passing a bd path to doctor or by running `tools/bd/bd.exe.new --version` and reporting the result), so the user gets immediate feedback that the new binary runs.

4. **Document bd commands we rely on**  
   We already document invocations in BEADS_INTEGRATION.md (create, close, dep add, etc.). Add a short “Minimum bd version / required commands” note and map them to Beads release notes (e.g. which version added `bd list --ready`, resolve-conflicts) so we know when we can safely bump a minimum version.

5. **Beads changelog review**  
   Periodically review [Beads CHANGELOG](https://github.com/steveyegge/beads/blob/main/CHANGELOG.md) (and the copy under `tools/bd/CHANGELOG.md` after upgrades) for new commands or flags that could improve *epic sync, *build/*fix hooks, or *todo (e.g. new JSON output, gate behavior, MCP support) and document or adopt them where useful.

6. **Cleanup bd.exe.new**  
   In the upgrade script, after a successful `Copy-Item` to bd.exe, remove `bd.exe.new` if it exists from a previous run. When we only write bd.exe.new (locked case), document that the user can delete bd.exe.new after replacing bd.exe to avoid confusion.

---

## References

- [BEADS_INTEGRATION.md](BEADS_INTEGRATION.md) – Configuration, epic sync, hooks, doctor/init.
- [tools/README.md](../tools/README.md) – Running and upgrading bd.
- [Beads upstream](https://github.com/steveyegge/beads) – Releases, install, changelog.
- `tapps_agents/beads/` – Client (`resolve_bd_path`, `run_bd`), parse, hydration, specs.
- `tapps_agents/core/doctor.py` – Beads (bd) status check (around line 873).
