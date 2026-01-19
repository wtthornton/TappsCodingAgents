# Beads Integration Testing Plan

**Purpose:** Implement unit tests for the Beads (bd) integration to complete Section 10 (Testing outline) of the Beads Integration Implementation Plan.  
**Status:** Complete  
**Created:** 2026-01

---

## Scope

- **Unit tests** for `tapps_agents.beads.client`: `resolve_bd_path`, `is_available`, `run_bd`
- **Unit tests** for `tapps_agents.epic.beads_sync`: `sync_epic_to_beads` with a mock `run_bd`
- **Config:** Assert `BeadsConfig` and `ProjectConfig` include `beads` with defaults

No new pip dependencies; `bd` is not required (we use temp dirs and mocks).

---

## 1. `tapps_agents.beads.client`

| Test | Description |
|------|-------------|
| `resolve_bd_path` with `tools/bd/bd.exe` (Windows) | Create temp dir with `tools/bd/bd.exe`, assert returns that path |
| `resolve_bd_path` with `tools/bd/bd` (Unix) | On non-Windows, create `tools/bd/bd`, assert returns that path |
| `resolve_bd_path` when local missing | No tools/bd → returns `shutil.which("bd")` or None (we cannot force PATH; test None when which is None) |
| `is_available` true | When `resolve_bd_path` returns a path |
| `is_available` false | When `resolve_bd_path` returns None (no tools/bd and bd not on PATH in test env) |
| `run_bd` when bd not found | `FileNotFoundError` (we need a project_root where resolve_bd_path returns None; use empty temp dir without tools/bd and patch `shutil.which` to return None) |
| `run_bd` when bd exists | Use temp dir with a **fake** `bd` script that prints "ready" and exits 0; run_bd(["ready"]) and assert returncode 0 |

For `run_bd` with a real binary: we can create a small executable (or a .bat on Windows / script on Unix) that exits 0. On Windows we need .exe; a simple option is to create a `bd.exe` that is a copy of `python.exe` or use a minimal script. Simpler: **mock `subprocess.run`** and assert it is called with the expected `[path, *args]` and `cwd`. That avoids needing a real bd binary.

**Decision:** For `run_bd` we will:
- **run_bd when bd not found:** use a temp dir without tools/bd and **patch `shutil.which` to return None** so `resolve_bd_path` returns None → `run_bd` raises `FileNotFoundError`.
- **run_bd when bd exists:** **patch `resolve_bd_path` to return a dummy path** and **patch `subprocess.run`** to return a `CompletedProcess(returncode=0, stdout="", stderr="")`. Assert `subprocess.run` was called with `[dummy_path, *args]` and correct `cwd`.

---

## 2. `tapps_agents.epic.beads_sync`

- **Mock `run_bd`** with signature `(args, cwd=None)` returning an object with `.returncode`, `.stdout`, `.stderr`.
- **Stories:** Build `EpicDocument` with 2–3 `Story` (with `story_id` e.g. `"8.1"`, `"8.2"`, `"8.3"`). One story depends on another (`dependencies=["8.1"]`).
- **create:** For each story, mock returns `returncode=0` and `stdout` containing a bd id (e.g. `"Created issue: Proj-a1b2"`). Record the `args` passed to `run_bd` (create and dep add).
- **Assert:** `story_id -> bd_id` mapping; `run_bd` was called with `dep add <child_bd> <parent_bd>` for the dependent story.
- **Failure behavior:** One `create` returns `returncode=1` → that story is not in the mapping; sync still returns the partial mapping and does not raise.

---

## 3. `BeadsConfig` in `ProjectConfig`

- In `tests/unit/test_config.py`:  
  - `get_default_config()` or `ProjectConfig()` includes a `beads` key.  
  - `BeadsConfig()` defaults: `enabled=False`, `sync_epic=True`, `hooks_simple_mode=False`.

---

## 4. Files to add/change

| Path | Action |
|------|--------|
| `tests/unit/beads/__init__.py` | Create (empty or `# unit tests for beads`) |
| `tests/unit/beads/test_client.py` | Create: client tests above |
| `tests/unit/epic/__init__.py` | Create |
| `tests/unit/epic/test_beads_sync.py` | Create: beads_sync tests with mock run_bd |
| `tests/unit/test_config.py` | Add `TestBeadsConfig` and/or assert `get_default_config()` has `beads` |

---

## 5. Execution order

1. Create `implementation/BEADS_INTEGRATION_TESTING_PLAN.md` (this file).
2. Add `tests/unit/beads/__init__.py`, `tests/unit/beads/test_client.py`.
3. Add `tests/unit/epic/__init__.py`, `tests/unit/epic/test_beads_sync.py`.
4. Add BeadsConfig/defaults assertion in `tests/unit/test_config.py`.
5. Run: `pytest tests/unit/beads tests/unit/epic/test_beads_sync.py tests/unit/test_config.py -v -k "beads or BeadsConfig"`. Fix any failures.

**Completed:** All files added. Run the above in a dev environment with project deps installed (e.g. `pip install -e ".[dev]"` or activate venv).

---

## 6. Success criteria

- All new tests pass.
- No dependency on a real `bd` binary (mocks and temp dirs only).
- Beads integration plan Section 10 can be marked as complete (testing outline implemented).
