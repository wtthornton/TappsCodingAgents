# Plan: AGENTS.md as Central Part of Init (No Special Flags)

**Status:** Plan  
**Created:** 2026-02-07  
**Supersedes:** Optional/special handling from `docs/planning/AGENTS_MD_INTEGRATION_PLAN.md`

## 1. Goal

- **AGENTS.md is the central agent-facing artifact** of project setup: the main entry point for any AI coding agent (Cursor, Copilot, Aider, etc.), and the hub that references the rest (Cursor Rules, Skills, config).
- **No special-case flags.** AGENTS.md is treated like Cursor Rules or workflow presets: always created/updated by init, and reset by `init --reset`. Remove `--no-agents-md` and `--reset-agents-md`.
- **Not backwards compatible.** Existing projects that relied on “AGENTS.md only when missing” or “never overwrite” will, after this change, get AGENTS.md created/overwritten by init and by init --reset like other framework files.

## 2. Current State (Brief)

- Init has `include_agents_md` and `reset_agents_md`; CLI has `--no-agents-md` and `--reset-agents-md`.
- AGENTS.md is **not** in `identify_framework_files()` → it is **not** reset on `init --reset`; it is created only when missing (unless `--reset-agents-md`).
- Template lives at `tapps_agents/resources/AGENTS.md.template`; `init_agents_md(project_root, overwrite=False, tech_stack=...)` creates/overwrites based on flags.

## 3. Target State

- **AGENTS.md is framework-managed.** Same lifecycle as Cursor Rules and presets: created by init, overwritten on init --reset.
- **Init always creates/overwrites AGENTS.md** from the packaged template (no opt-out, no separate “reset AGENTS.md” flag).
- **init --reset** deletes root `AGENTS.md` (when present) as part of framework files, then normal init run recreates it from template.
- **AGENTS.md is “central” in two ways:**
  1. **Messaging:** In init output and docs, AGENTS.md is the first or prominent “what we install” item and the recommended first read for agents.
  2. **Content:** The template frames AGENTS.md as the hub: “Read this first; then see `.cursor/rules/`, `.tapps-agents/`, and `tapps-agents` CLI for TappsCodingAgents.”

## 4. Implementation Tasks

### 4.1 Treat AGENTS.md as framework-managed

| Task | Location | Change |
|------|----------|--------|
| Add AGENTS.md to framework files | `init_project.py` → `identify_framework_files()` | If `project_root / "AGENTS.md"` exists, append it to `result["framework_files"]`. No heuristic (e.g. “looks like our template”); any root AGENTS.md is considered framework-managed so reset replaces it. |
| Optional: detection | `init_project.py` → `detect_existing_installation()` | Add “AGENTS.md (project root)” to `result["indicators"]` when present, so “existing installation” detection is consistent. |

### 4.2 Always create/overwrite AGENTS.md from template

| Task | Location | Change |
|------|----------|--------|
| Remove include/reset params | `init_project.py` → `init_project()` | Remove `include_agents_md` and `reset_agents_md`. Always call `init_agents_md(project_root, tech_stack=results.get("tech_stack"))`. |
| Simplify init_agents_md | `init_project.py` → `init_agents_md()` | Signature: `init_agents_md(project_root, tech_stack=None)`. Behavior: always write AGENTS.md from template (overwrite if present). Remove `overwrite` parameter. Return `(success: bool, path: str | None)` unchanged. |
| Keep results key | `init_project.py` | Keep `results["agents_md"]` and appending to `results["files_created"]` when created/updated (so init output and callers still see it). |

### 4.3 Remove CLI flags and wiring

| Task | Location | Change |
|------|----------|--------|
| Parser | `cli/parsers/top_level.py` | Remove `--no-agents-md` and `--reset-agents-md` from init parser. |
| Command | `cli/commands/top_level.py` | Remove `include_agents_md` and `reset_agents_md` from `init_project()` call. |
| Init results print | `cli/commands/top_level.py` → `_print_init_results()` | Keep “AGENTS.md: Created” (or “Updated”) when `results["agents_md"]`; no branch for “skipped” due to flags (we always create/update). |

### 4.4 Make AGENTS.md central in messaging and template

| Task | Location | Change |
|------|----------|--------|
| Init “What it installs” order / emphasis | `command-reference.mdc` (and any init summary in code) | List AGENTS.md first (or immediately after project root/config) in the “What it installs” list for init. Short line: “Primary entry point for AI coding agents; see [agents.md](https://agents.md/).” |
| Template content | `tapps_agents/resources/AGENTS.md.template` | Add a short “Read this first” / “Central instructions” block at the top that says: this file is the main context for agents; for TappsCodingAgents projects, see `.cursor/rules/`, `.tapps-agents/config.yaml`, and `tapps-agents --help`. Keep existing sections (setup, testing, structure, style, git, boundaries, TappsCodingAgents). |

### 4.5 Documentation and tests

| Task | Location | Change |
|------|----------|--------|
| AGENTS_MD_GUIDE | `docs/AGENTS_MD_GUIDE.md` | Rewrite to state: AGENTS.md is always created/overwritten by init and by init --reset; no flags. Emphasize it as the central agent entry point and hub for Rules/Skills/config. Remove all mentions of `--no-agents-md` and `--reset-agents-md`. |
| Command reference | `.cursor/rules/command-reference.mdc` | Remove `--no-agents-md` and `--reset-agents-md` from init syntax and from Parameters. In “What it installs,” move AGENTS.md to position 1 (or top of list) and state it is created/overwritten every init and on reset. In “init --reset behavior,” explicitly mention that AGENTS.md is reset (deleted and recreated from template). |
| Planning doc | `docs/planning/AGENTS_MD_INTEGRATION_PLAN.md` | Add a short “Superseded by” note at the top pointing to this plan (AGENTS_MD_CENTRAL_PLAN.md) for the “no special flags, AGENTS.md central” approach. |
| Unit tests | `tests/unit/core/test_init_agents_md.py` | Update tests: remove tests that rely on `overwrite=False` “do not overwrite existing”; add or keep a test that init_agents_md always writes (overwrites) when called. Adjust tests for new signature `init_agents_md(project_root, tech_stack=None)` (no `overwrite`). |
| Init integration test | If any test asserts on init_project() and agents_md | Ensure they expect AGENTS.md to be created/overwritten (no conditional on flags). |

## 5. Behavior Summary

| Scenario | Before (current) | After (this plan) |
|----------|------------------|-------------------|
| First init | AGENTS.md created if missing | AGENTS.md always created from template |
| Init when AGENTS.md exists | Left unchanged (unless --reset-agents-md) | Overwritten from template |
| init --reset | AGENTS.md not touched | AGENTS.md deleted with other framework files, then recreated from template in same init run |
| Skip AGENTS.md | --no-agents-md | Not possible; no flag |

## 6. Out of Scope

- Nested AGENTS.md in subpackages (unchanged).
- Validating or parsing AGENTS.md content (unchanged).
- Backwards compatibility with projects that customized AGENTS.md and expect it never to be overwritten (explicitly out of scope per user).

## 7. References

- [agents.md](https://agents.md/)
- `docs/planning/AGENTS_MD_INTEGRATION_PLAN.md` (superseded by this plan for init behavior)
- `docs/AGENTS_MD_GUIDE.md` (to be updated)
