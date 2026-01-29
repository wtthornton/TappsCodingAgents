# .tapps-agents/sessions Folder Review

**Date:** 2026-01-29  
**Scope:** Why the sessions folder is large, whether there is a bug, which files are "real," and what to delete.

---

## Summary

| Metric | Value |
|--------|--------|
| **Total files** | 473 |
| **Total size** | ~2.48 MB |
| **Zero-byte files** | 10 |
| **Root cause** | Enhancer saves one JSON per `*enhance` run; no cleanup is implemented or invoked. |

**Conclusion:** The folder is large because **every enhancer run writes a session file and nothing ever deletes them**. This is a **design/implementation gap** (missing cleanup), not a single “bug” in the sense of wrong data or crash. Zero-byte files are failed/crashed runs and are safe to delete.

---

## What Writes to `.tapps-agents/sessions`

Two subsystems use the same directory with **different JSON schemas**:

### 1. Enhancer agent (`tapps_agents/agents/enhancer/agent.py`)

- **When:** Every `*enhance` (full or quick) and `*enhance-stage` run.
- **Filename:** `{session_id}.json` where `session_id` is the first 8 chars of `sha256(prompt + datetime.now().isoformat())`, so each run gets a new file.
- **Schema:** `session_id`, `metadata` (e.g. `original_prompt`, `created_at`, `config`), `stages` (analysis, requirements, architecture, synthesis, etc.). **No `state` field.**
- **Purpose:** Resume interrupted enhancement by `session_id`; otherwise these are historical artifacts.

### 2. Session manager (`tapps_agents/core/session_manager.py`)

- **When:** Long-running agent sessions (e.g. resource-aware executor, long-duration support).
- **Filename:** `{session_id}.json`.
- **Schema:** `session_id`, `state` (active/paused/completed/failed), `start_time`, `last_activity`, checkpoints, etc. **Has `state` field.**
- **Purpose:** Persist and recover long-running workflows.

In your project, the 473 files are almost certainly **all from the Enhancer** (one file per enhance run). Session-manager sessions would only appear if you use long-duration/resource-aware workflows that persist to disk.

---

## Why It’s “So Big”

1. **Enhancer never deletes session files.**  
   It only writes in `_save_session()`; there is no cleanup by age or count.

2. **SessionManager has cleanup but it is never called.**  
   `SessionManager.cleanup_old_sessions(max_age_hours=168)` exists in `session_manager.py` but is **not referenced anywhere** in the codebase (no CLI, no init, no doctor).

3. **Even if cleanup were called, it wouldn’t remove enhancer files.**  
   `SessionStorage.list_sessions()` loads every `*.json` and expects `data["state"]`. Enhancer JSON has `metadata` and `stages`, not `state`, so those files raise when parsed as AgentSession and are skipped (with a warning). So `cleanup_old_sessions()` would only delete files that look like SessionManager sessions (if any).

4. **Same directory, two schemas.**  
   Sharing one folder without a shared lifecycle means enhancer artifacts accumulate indefinitely.

So the folder is “so big” because: **many enhancer runs + no cleanup + cleanup that exists isn’t wired up and wouldn’t apply to enhancer files anyway.**

---

## Bug / Design Gap?

| Issue | Severity | Description |
|-------|----------|-------------|
| Enhancer never cleans up session files | **Gap** | By design sessions are saved for resume; there is no policy (age or max count) to remove old ones. |
| `SessionManager.cleanup_old_sessions` never called | **Bug** | Cleanup exists but is never invoked (no CLI, no init/doctor). |
| Two schemas in one directory | **Design** | SessionManager cleanup cannot safely delete enhancer files (different schema); mixing both in one dir is confusing and limits simple cleanup. |

So: **yes, there is a bug** (cleanup never runs) **and a design gap** (enhaner has no cleanup; both use the same dir with different formats).

---

## What’s “Real” vs What to Delete

- **Real:** Every non-empty JSON is a “real” session artifact (either an enhancer run or a SessionManager session). They are valid historical data.
- **Needed for operation:** Only if you **resume** an enhancement by `session_id` do you need that specific enhancer file. For normal use, old files are not required.
- **Safe to delete:**
  - **Zero-byte files (10):** Failed/crashed runs; no useful content. **Recommendation: delete.**
  - **Old enhancer sessions:** Safe to delete by age (e.g. older than 7–30 days) or keep only the last N (e.g. 50). Optional; depends on whether you use resume.
- **Be careful:** If you have any **SessionManager** (long-duration) sessions, they have `state` and might be “active” or “paused.” Don’t delete those unless you’re sure they’re completed/failed and old. In your case, with 473 files and 2.48 MB, these are almost certainly all enhancer.

---

## Recommendations

### 1. Immediate: Clean Up Zero-Byte Files

Delete the 10 zero-byte session files; they are useless and indicate failed runs.

Example (PowerShell, from repo root):

```powershell
Get-ChildItem ".tapps-agents\sessions\*.json" -File | Where-Object { $_.Length -eq 0 } | Remove-Item -Force
```

Or manually delete the 0-byte files listed in the session listing.

### 2. Short-Term: Optional One-Off Prune of Old Enhancer Sessions

If you don’t need resume and want to reclaim space:

- Delete all `*.json` in `.tapps-agents/sessions` that are **not** the named exports you care about (e.g. `enh-001-enhancement-session.json`), **or**
- Keep only files modified in the last N days (e.g. 7 or 30).

This is optional and can be done with a small script or manually.

### 3. Framework: Add Enhancer Session Cleanup

- In **EnhancerAgent** (or a small helper), add cleanup that:
  - Runs on a policy: e.g. keep only the last N files (e.g. 50) and/or delete files older than X days (e.g. 7 or 30).
  - Only touches files that look like **enhancer** sessions (e.g. have `metadata` and `stages`, no `state`), so SessionManager sessions are not deleted by mistake.
- Options for when to run:
  - At start of each `enhance` (e.g. “before saving, prune old sessions”),
  - Or from a CLI/doctor step (e.g. `tapps-agents cleanup sessions` or part of `tapps-agents doctor`).

### 4. Framework: Use SessionManager Cleanup

- Call `SessionManager.cleanup_old_sessions()` from at least one place, e.g.:
  - `tapps-agents doctor`, or
  - When starting a long-duration/resource-aware workflow.
- So that SessionManager’s own session files (when present) are pruned by age.

### 5. Framework (Optional): Separate Directories

- Use e.g. `.tapps-agents/sessions/enhancer/` and `.tapps-agents/sessions/agent/` (or similar).
- Enhancer writes and cleans only under `sessions/enhancer/`; SessionManager uses `sessions/agent/` (or the current path for backward compatibility).
- This avoids schema mixing and makes cleanup and documentation clearer.

### 6. Docs and CLI

- Document in CONFIGURATION.md or a dedicated “Artifacts and cleanup” section:
  - What `.tapps-agents/sessions` contains (enhancer + optional SessionManager).
  - That enhancer sessions accumulate unless cleanup is run.
  - How to run cleanup (CLI or doctor) once implemented.
- Add a `tapps-agents cleanup sessions` (or `cleanup enhancer-sessions`) subcommand that:
  - Applies the enhancer retention policy (and optionally calls SessionManager cleanup for the rest).
  - Supports `--dry-run` and `--max-age-days` / `--keep-latest`.

---

## File Count and Size (Snapshot)

- **Total files:** 473  
- **Total size:** 2,596,734 bytes (~2.48 MB)  
- **Zero-byte files:** 10 (e.g. `1a1a795c.json`, `1cc21884.json`, `38b84acf.json`, `564bbc34.json`, `5f29e6f4.json`, `870fbc74.json`, `8953498a.json`, `a903b77b.json`, `b0d9edfd.json`, `ff63daad.json`)  
- **Notable large files:** Some single files are 200–350 KB (full 7-stage enhancement output with large prompts/context).  

All of these are consistent with many enhancer runs over time with no cleanup.

---

## Implementation (2026-01-29)

- **`tapps-agents cleanup sessions`** — Removes zero-byte JSONs, prunes enhancer sessions by `keep_latest` and `max_age_days`, and runs `SessionManager.cleanup_old_sessions()`. Config: `cleanup.sessions` in `.tapps-agents/config.yaml` (defaults: keep_latest=50, max_age_days=30).
- **`CleanupTool.cleanup_sessions()`** — In `tapps_agents/core/cleanup_tool.py`; only touches enhancer-format files (metadata + stages, no state).
- **SessionManager.cleanup_old_sessions()** — Invoked from `cleanup sessions` and from enhancer when `auto_cleanup_on_enhance` is true; SessionStorage skips enhancer-format files when listing (KeyError → debug).
- **Automatic cleanup when appropriate:**
  - **Enhancer:** After each `_save_session()`, if `cleanup.sessions.auto_cleanup_on_enhance` is true, runs `CleanupTool.cleanup_sessions()` and `SessionManager.cleanup_old_sessions()`. Default false (opt-in).
  - **Doctor:** `tapps-agents doctor` reports sessions folder size/count; more than 100 files or 1 MB, adds a warning with remediation “Run `tapps-agents cleanup sessions`”.

## References

- Enhancer session save: `tapps_agents/agents/enhancer/agent.py` — `_save_session()`, `_create_session()`
- SessionManager storage and cleanup: `tapps_agents/core/session_manager.py` — `SessionStorage`, `SessionManager.cleanup_old_sessions()`
- CLI: `tapps-agents cleanup sessions` (see `docs/CONFIGURATION.md` § Cleanup configuration)
- `.cursorignore` includes `.tapps-agents/sessions/` (so Cursor does not index these files)
